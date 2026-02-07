import json
import time
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.utils import textUtils
from core.utils.util import audio_to_data
from core.providers.tts.dto.dto import SentenceType
from core.utils.audioRateController import AudioRateController

TAG = __name__
# Thời lượng khung âm thanh (mili giây)
AUDIO_FRAME_DURATION = 60
# Số lượng gói đệm trước, gửi trực tiếp để giảm độ trễ
PRE_BUFFER_COUNT = 5


async def sendAudioMessage(conn: "ConnectionHandler", sentenceType, audios, text):
    if conn.tts.tts_audio_first_sentence:
        conn.logger.bind(tag=TAG).info(f"Gửi đoạn giọng nói đầu tiên: {text}")
        conn.tts.tts_audio_first_sentence = False
        await send_tts_message(conn, "start", None)

    if sentenceType == SentenceType.FIRST:
        # Tin nhắn tiếp theo của cùng câu thêm vào hàng đợi điều khiển luồng, các trường hợp khác gửi ngay
        if (
            hasattr(conn, "audio_rate_controller")
            and conn.audio_rate_controller
            and getattr(conn, "audio_flow_control", {}).get("sentence_id")
            == conn.sentence_id
        ):
            conn.audio_rate_controller.add_message(
                lambda: send_tts_message(conn, "sentence_start", text)
            )
        else:
            # Câu mới hoặc bộ điều khiển luồng chưa khởi tạo, gửi ngay
            await send_tts_message(conn, "sentence_start", text)

    await sendAudio(conn, audios)
    # Gửi tin nhắn bắt đầu câu
    if sentenceType is not SentenceType.MIDDLE:
        conn.logger.bind(tag=TAG).info(f"Gửi tin nhắn âm thanh: {sentenceType}, {text}")

    # Gửi tin nhắn kết thúc (nếu là văn bản cuối cùng)
    if sentenceType == SentenceType.LAST:
        await send_tts_message(conn, "stop", None)
        conn.client_is_speaking = False
        if conn.close_after_chat:
            await conn.close()


async def _wait_for_audio_completion(conn: "ConnectionHandler"):
    """
    Chờ hàng đợi âm thanh trống và chờ các gói đệm trước phát xong

    Args:
        conn: Đối tượng kết nối
    """
    if hasattr(conn, "audio_rate_controller") and conn.audio_rate_controller:
        rate_controller = conn.audio_rate_controller
        conn.logger.bind(tag=TAG).debug(
            f"Chờ gửi âm thanh hoàn tất, trong hàng đợi còn {len(rate_controller.queue)} gói"
        )
        await rate_controller.queue_empty_event.wait()

        # Chờ các gói đệm trước phát xong
        # N gói đầu gửi trực tiếp, thêm 2 gói rung mạng, cần chờ thêm chúng phát xong ở phía khách hàng
        frame_duration_ms = rate_controller.frame_duration
        pre_buffer_playback_time = (PRE_BUFFER_COUNT + 2) * frame_duration_ms / 1000.0
        await asyncio.sleep(pre_buffer_playback_time)

        conn.logger.bind(tag=TAG).debug("Gửi âm thanh hoàn tất")


async def _send_to_mqtt_gateway(
    conn: "ConnectionHandler", opus_packet, timestamp, sequence
):
    """
    Gửi gói dữ liệu opus có header 16 byte đến mqtt_gateway
    Args:
        conn: Đối tượng kết nối
        opus_packet: Gói dữ liệu opus
        timestamp: Dấu thời gian
        sequence: Số thứ tự
    """
    # Thêm header 16 byte cho gói dữ liệu opus
    header = bytearray(16)
    header[0] = 1  # type
    header[2:4] = len(opus_packet).to_bytes(2, "big")  # payload length
    header[4:8] = sequence.to_bytes(4, "big")  # sequence
    header[8:12] = timestamp.to_bytes(4, "big")  # Dấu thời gian
    header[12:16] = len(opus_packet).to_bytes(4, "big")  # Độ dài opus

    # Gửi gói dữ liệu đầy đủ bao gồm header
    complete_packet = bytes(header) + opus_packet
    await conn.websocket.send(complete_packet)


async def sendAudio(
    conn: "ConnectionHandler", audios, frame_duration=AUDIO_FRAME_DURATION
):
    """
    Gửi gói âm thanh, sử dụng AudioRateController để điều khiển lưu lượng chính xác

    Args:
        conn: Đối tượng kết nối
        audios: Gói opus đơn (bytes) hoặc danh sách gói opus
        frame_duration: Thời lượng khung (mili giây), mặc định sử dụng hằng số toàn cục AUDIO_FRAME_DURATION
    """
    if audios is None or len(audios) == 0:
        return

    send_delay = conn.config.get("tts_audio_send_delay", -1) / 1000.0
    is_single_packet = isinstance(audios, bytes)

    # Khởi tạo hoặc lấy RateController
    rate_controller, flow_control = _get_or_create_rate_controller(
        conn, frame_duration, is_single_packet
    )

    # Chuyển đổi thống nhất thành danh sách để xử lý
    audio_list = [audios] if is_single_packet else audios

    # Gửi gói âm thanh
    await _send_audio_with_rate_control(
        conn, audio_list, rate_controller, flow_control, send_delay
    )


def _get_or_create_rate_controller(
    conn: "ConnectionHandler", frame_duration, is_single_packet
):
    """
    Lấy hoặc tạo RateController và flow_control

    Args:
        conn: Đối tượng kết nối
        frame_duration: Thời lượng khung
        is_single_packet: Có phải chế độ gói đơn không (True: TTS luồng gói đơn, False: gói hàng loạt)

    Returns:
        (rate_controller, flow_control)
    """
    # Kiểm tra xem có cần đặt lại bộ điều khiển không
    need_reset = False

    if not hasattr(conn, "audio_rate_controller"):
        # Bộ điều khiển không tồn tại, cần tạo
        need_reset = True
    else:
        rate_controller = conn.audio_rate_controller

        # Tác vụ gửi nền đã dừng, cần đặt lại
        if (
            not rate_controller.pending_send_task
            or rate_controller.pending_send_task.done()
        ):
            need_reset = True
        # Khi sentence_id thay đổi, cần đặt lại
        elif (
            getattr(conn, "audio_flow_control", {}).get("sentence_id")
            != conn.sentence_id
        ):
            need_reset = True

    if need_reset:
        # Tạo hoặc lấy rate_controller
        if not hasattr(conn, "audio_rate_controller"):
            conn.audio_rate_controller = AudioRateController(frame_duration)
        else:
            conn.audio_rate_controller.reset()

        # Khởi tạo flow_control
        conn.audio_flow_control = {
            "packet_count": 0,
            "sequence": 0,
            "sentence_id": conn.sentence_id,
        }

        # Khởi động vòng lặp gửi nền
        _start_background_sender(
            conn, conn.audio_rate_controller, conn.audio_flow_control
        )

    return conn.audio_rate_controller, conn.audio_flow_control


def _start_background_sender(conn: "ConnectionHandler", rate_controller, flow_control):
    """
    Khởi động tác vụ vòng lặp gửi nền

    Args:
        conn: Đối tượng kết nối
        rate_controller: Bộ điều khiển tốc độ
        flow_control: Trạng thái điều khiển luồng
    """

    async def send_callback(packet):
        # Kiểm tra xem có nên hủy không
        if conn.client_abort:
            raise asyncio.CancelledError("Khách hàng đã hủy")

        conn.last_activity_time = time.time() * 1000
        await _do_send_audio(conn, packet, flow_control)
        conn.client_is_speaking = True

    # Sử dụng start_sending để khởi động vòng lặp nền
    rate_controller.start_sending(send_callback)


async def _send_audio_with_rate_control(
    conn: "ConnectionHandler", audio_list, rate_controller, flow_control, send_delay
):
    """
    Sử dụng rate_controller để gửi gói âm thanh

    Args:
        conn: Đối tượng kết nối
        audio_list: Danh sách gói âm thanh
        rate_controller: Bộ điều khiển tốc độ
        flow_control: Trạng thái điều khiển luồng
        send_delay: Độ trễ cố định (giây), -1 nghĩa là sử dụng điều khiển luồng động
    """
    for packet in audio_list:
        if conn.client_abort:
            return

        conn.last_activity_time = time.time() * 1000

        # Đệm trước: N gói đầu gửi trực tiếp
        if flow_control["packet_count"] < PRE_BUFFER_COUNT:
            await _do_send_audio(conn, packet, flow_control)
            conn.client_is_speaking = True
        elif send_delay > 0:
            # Chế độ độ trễ cố định
            await asyncio.sleep(send_delay)
            await _do_send_audio(conn, packet, flow_control)
            conn.client_is_speaking = True
        else:
            # Chế độ điều khiển luồng động: chỉ thêm vào hàng đợi, vòng lặp nền chịu trách nhiệm gửi
            rate_controller.add_audio(packet)


async def _do_send_audio(conn: "ConnectionHandler", opus_packet, flow_control):
    """
    Thực thi gửi âm thanh thực tế
    """
    packet_index = flow_control.get("packet_count", 0)
    sequence = flow_control.get("sequence", 0)

    if conn.conn_from_mqtt_gateway:
        # Tính dấu thời gian (dựa trên vị trí phát)
        start_time = time.time()
        timestamp = int(start_time * 1000) % (2**32)
        await _send_to_mqtt_gateway(conn, opus_packet, timestamp, sequence)
    else:
        # Gửi trực tiếp gói dữ liệu opus
        await conn.websocket.send(opus_packet)

    # Cập nhật trạng thái điều khiển luồng
    flow_control["packet_count"] = packet_index + 1
    flow_control["sequence"] = sequence + 1


async def send_tts_message(conn: "ConnectionHandler", state, text=None):
    """Gửi tin nhắn trạng thái TTS"""
    if text is None and state == "sentence_start":
        return
    message = {"type": "tts", "state": state, "session_id": conn.session_id}
    if text is not None:
        message["text"] = textUtils.check_emoji(text)

    # TTS phát xong
    if state == "stop":
        # Phát âm thanh thông báo
        tts_notify = conn.config.get("enable_stop_tts_notify", False)
        if tts_notify:
            stop_tts_notify_voice = conn.config.get(
                "stop_tts_notify_voice", "config/assets/tts_notify.mp3"
            )
            audios = await audio_to_data(stop_tts_notify_voice, is_opus=True)
            await sendAudio(conn, audios)
        # Chờ tất cả gói âm thanh gửi xong
        await _wait_for_audio_completion(conn)
        # Xóa trạng thái nói của máy chủ
        conn.clearSpeakStatus()

    # Gửi tin nhắn đến khách hàng
    await conn.websocket.send(json.dumps(message))


async def send_stt_message(conn: "ConnectionHandler", text):
    """Gửi tin nhắn trạng thái STT"""
    end_prompt_str = conn.config.get("end_prompt", {}).get("prompt")
    if end_prompt_str and end_prompt_str == text:
        await send_tts_message(conn, "start")
        return

    # Phân tích định dạng JSON, trích xuất nội dung người dùng nói thực tế
    display_text = text
    try:
        # Thử phân tích định dạng JSON
        if text.strip().startswith("{") and text.strip().endswith("}"):
            parsed_data = json.loads(text)
            if isinstance(parsed_data, dict) and "content" in parsed_data:
                # Nếu là định dạng JSON chứa thông tin người nói, chỉ hiển thị phần content
                display_text = parsed_data["content"]
                # Lưu thông tin người nói vào đối tượng conn
                if "speaker" in parsed_data:
                    conn.current_speaker = parsed_data["speaker"]
    except (json.JSONDecodeError, TypeError):
        # Nếu không phải định dạng JSON, sử dụng trực tiếp văn bản gốc
        display_text = text
    stt_text = textUtils.get_string_no_punctuation_or_emoji(display_text)
    await conn.websocket.send(
        json.dumps({"type": "stt", "text": stt_text, "session_id": conn.session_id})
    )
    await send_tts_message(conn, "start")
