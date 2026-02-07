import time
import asyncio
from collections import deque
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class AudioRateController:
    """
    Bộ điều khiển tốc độ âm thanh - Kiểm soát chính xác việc gửi âm thanh theo thời lượng khung 60ms
    Giải quyết vấn đề sai số tích lũy thời gian trong môi trường đồng thời cao
    """

    def __init__(self, frame_duration=60):
        """
        Args:
            frame_duration: Thời lượng khung âm thanh đơn lẻ (milliseconds), mặc định 60ms
        """
        self.frame_duration = frame_duration
        self.queue = deque()
        self.play_position = 0  # Vị trí phát ảo (milliseconds)
        self.start_timestamp = None  # Timestamp bắt đầu (chỉ đọc, không sửa đổi)
        self.pending_send_task = None
        self.logger = logger
        self.queue_empty_event = asyncio.Event()  # Sự kiện hàng đợi rỗng
        self.queue_empty_event.set()  # Trạng thái ban đầu là rỗng
        self.queue_has_data_event = asyncio.Event()  # Sự kiện hàng đợi có dữ liệu

    def reset(self):
        """Đặt lại trạng thái bộ điều khiển"""
        if self.pending_send_task and not self.pending_send_task.done():
            self.pending_send_task.cancel()
            # Sau khi hủy tác vụ, tác vụ sẽ được dọn dẹp trong lần lặp sự kiện tiếp theo, không cần chờ chặn

        self.queue.clear()
        self.play_position = 0
        self.start_timestamp = None  # Được thiết lập bởi gói âm thanh đầu tiên
        # Xử lý sự kiện liên quan
        self.queue_empty_event.set()
        self.queue_has_data_event.clear()

    def add_audio(self, opus_packet):
        """Thêm gói âm thanh vào hàng đợi"""
        self.queue.append(("audio", opus_packet))
        # Xử lý sự kiện liên quan
        self.queue_empty_event.clear()
        self.queue_has_data_event.set()

    def add_message(self, message_callback):
        """
        Thêm tin nhắn vào hàng đợi (gửi ngay lập tức, không chiếm thời gian phát)

        Args:
            message_callback: Hàm callback gửi tin nhắn async def()
        """
        self.queue.append(("message", message_callback))
        # Xử lý sự kiện liên quan
        self.queue_empty_event.clear()
        self.queue_has_data_event.set()

    def _get_elapsed_ms(self):
        """Lấy thời gian đã trôi qua (milliseconds)"""
        if self.start_timestamp is None:
            return 0
        return (time.monotonic() - self.start_timestamp) * 1000

    async def check_queue(self, send_audio_callback):
        """
        Kiểm tra hàng đợi và gửi âm thanh/tin nhắn đúng thời gian

        Args:
            send_audio_callback: Hàm callback gửi âm thanh async def(opus_packet)
        """
        while self.queue:
            item = self.queue[0]
            item_type = item[0]

            if item_type == "message":
                # Loại tin nhắn: gửi ngay lập tức, không chiếm thời gian phát
                _, message_callback = item
                self.queue.popleft()
                try:
                    await message_callback()
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Gửi tin nhắn thất bại: {e}")
                    raise

            elif item_type == "audio":
                if self.start_timestamp is None:
                    self.start_timestamp = time.monotonic()

                _, opus_packet = item

                # Vòng lặp chờ cho đến khi thời gian đến
                while True:
                    # Tính toán chênh lệch thời gian
                    elapsed_ms = self._get_elapsed_ms()
                    output_ms = self.play_position

                    if elapsed_ms < output_ms:
                        # Chưa đến thời gian gửi, tính toán thời gian chờ
                        wait_ms = output_ms - elapsed_ms

                        # Sau khi chờ tiếp tục kiểm tra (cho phép bị gián đoạn)
                        try:
                            await asyncio.sleep(wait_ms / 1000)
                        except asyncio.CancelledError:
                            self.logger.bind(tag=TAG).debug("Tác vụ gửi âm thanh bị hủy")
                            raise
                        # Sau khi chờ xong kiểm tra lại thời gian (quay lại vòng lặp while True)
                    else:
                        # Thời gian đã đến, thoát khỏi vòng lặp chờ
                        break

                # Thời gian đã đến, xóa khỏi hàng đợi và gửi
                self.queue.popleft()
                self.play_position += self.frame_duration
                try:
                    await send_audio_callback(opus_packet)
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Gửi âm thanh thất bại: {e}")
                    raise

        # Sau khi xử lý xong hàng đợi, xóa sự kiện
        self.queue_empty_event.set()
        self.queue_has_data_event.clear()

    def start_sending(self, send_audio_callback):
        """
        Khởi động tác vụ gửi bất đồng bộ

        Args:
            send_audio_callback: Hàm callback gửi âm thanh

        Returns:
            asyncio.Task: Tác vụ gửi
        """

        async def _send_loop():
            try:
                while True:
                    # Chờ sự kiện dữ liệu hàng đợi, không chờ polling chiếm CPU
                    await self.queue_has_data_event.wait()

                    await self.check_queue(send_audio_callback)
            except asyncio.CancelledError:
                self.logger.bind(tag=TAG).debug("Vòng lặp gửi âm thanh đã dừng")
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"Lỗi vòng lặp gửi âm thanh: {e}")

        self.pending_send_task = asyncio.create_task(_send_loop())
        return self.pending_send_task

    def stop_sending(self):
        """Dừng tác vụ gửi"""
        if self.pending_send_task and not self.pending_send_task.done():
            self.pending_send_task.cancel()
            self.logger.bind(tag=TAG).debug("Đã hủy tác vụ gửi âm thanh")
