import os
import uuid
import json
import time
import queue
import asyncio
import traceback
import websockets
from asyncio import Task
from config.logger import setup_logging
from core.utils import opus_encoder_utils
from core.utils.tts import MarkdownCleaner
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)

        self.interface_type = InterfaceType.DUAL_STREAM
        # Cấu hình cơ bản
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("api_key is required for CosyVoice TTS")

        # Cấu hình WebSocket
        self.ws_url = "wss://dashscope.aliyuncs.com/api-ws/v1/inference/"
        self.ws = None
        self._monitor_task = None
        self.last_active_time = None

        # Cấu hình model và giọng nói
        self.model = config.get("model", "cosyvoice-v2")
        self.voice = config.get("voice", "longxiaochun_v2")  # Giọng nói mặc định
        if config.get("private_voice"):
            self.voice = config.get("private_voice")

        # Cấu hình tham số audio
        self.format = config.get("format", "pcm")

        volume = config.get("volume", "50")
        self.volume = int(volume) if volume else 50

        rate = config.get("rate", "1.0")
        self.rate = float(rate) if rate else 1.0

        pitch = config.get("pitch", "1.0")
        self.pitch = float(pitch) if pitch else 1.0

        self.header = {
            "Authorization": f"Bearer {self.api_key}",
            # "user-agent": "your_platform_info", // Tùy chọn
            # "X-DashScope-WorkSpace": workspace, // Tùy chọn, ID không gian nghiệp vụ Alibaba Cloud Bailian
            "X-DashScope-DataInspection": "enable",
        }

    async def _ensure_connection(self):
        """Đảm bảo kết nối WebSocket khả dụng, hỗ trợ tái sử dụng kết nối trong 60 giây"""
        try:
            current_time = time.time()
            if self.ws and current_time - self.last_active_time < 60:
                # Chỉ trong vòng một phút mới có thể tái sử dụng liên kết để hội thoại liên tục
                logger.bind(tag=TAG).info(f"Sử dụng liên kết hiện có...")
                return self.ws
            logger.bind(tag=TAG).info("Bắt đầu thiết lập kết nối mới...")

            self.ws = await websockets.connect(
                self.ws_url,
                additional_headers=self.header,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
            )

            logger.bind(tag=TAG).info("Kết nối WebSocket đã được thiết lập thành công")
            self.last_active_time = current_time
            return self.ws
        except Exception as e:
            logger.bind(tag=TAG).error(f"Thiết lập kết nối thất bại: {str(e)}")
            self.ws = None
            self.last_active_time = None
            raise

    def tts_text_priority_thread(self):
        """Luồng xử lý văn bản TTS streaming"""
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                logger.bind(tag=TAG).debug(
                    f"Nhận tác vụ TTS｜{message.sentence_type.name} ｜ {message.content_type.name} | ID phiên: {self.conn.sentence_id}"
                )

                if message.sentence_type == SentenceType.FIRST:
                    self.conn.client_abort = False

                if self.conn.client_abort:
                    try:
                        logger.bind(tag=TAG).info("Nhận thông tin ngắt, kết thúc luồng xử lý văn bản TTS")
                        continue
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Hủy phiên TTS thất bại: {str(e)}")
                        continue

                if message.sentence_type == SentenceType.FIRST:
                    # Khởi tạo phiên
                    try:
                        if not getattr(self.conn, "sentence_id", None): 
                            self.conn.sentence_id = uuid.uuid4().hex
                            logger.bind(tag=TAG).info(f"Tự động tạo ID phiên mới: {self.conn.sentence_id}")

                        logger.bind(tag=TAG).info("Bắt đầu khởi động phiên TTS...")
                        future = asyncio.run_coroutine_threadsafe(
                            self.start_session(self.conn.sentence_id),
                            loop=self.conn.loop,
                        )
                        future.result()
                        self.before_stop_play_files.clear()
                        logger.bind(tag=TAG).info("Phiên TTS đã khởi động thành công")
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Khởi động phiên TTS thất bại: {str(e)}")
                        continue

                elif ContentType.TEXT == message.content_type:
                    if message.content_detail:
                        try:
                            logger.bind(tag=TAG).debug(
                                f"Bắt đầu gửi văn bản TTS: {message.content_detail}"
                            )
                            future = asyncio.run_coroutine_threadsafe(
                                self.text_to_speak(message.content_detail, None),
                                loop=self.conn.loop,
                            )
                            future.result()
                            logger.bind(tag=TAG).debug("Văn bản TTS đã gửi thành công")
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"Gửi văn bản TTS thất bại: {str(e)}")
                            continue

                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(
                        f"Thêm file audio vào danh sách chờ phát: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        # Xử lý dữ liệu audio của file trước
                        self._process_audio_file_stream(message.content_file, callback=lambda audio_data: self.handle_audio_file(audio_data, message.content_detail))

                if message.sentence_type == SentenceType.LAST:
                    try:
                        logger.bind(tag=TAG).info("Bắt đầu kết thúc phiên TTS...")
                        future = asyncio.run_coroutine_threadsafe(
                            self.finish_session(self.conn.sentence_id),
                            loop=self.conn.loop,
                        )
                        future.result()
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Kết thúc phiên TTS thất bại: {str(e)}")
                        continue

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"Xử lý văn bản TTS thất bại: {str(e)}, loại: {type(e).__name__}, stack: {traceback.format_exc()}"
                )
                continue

    async def text_to_speak(self, text, _):
        """Gửi văn bản đến dịch vụ TTS để tổng hợp"""
        try:
            if self.ws is None:
                logger.bind(tag=TAG).warning("Kết nối WebSocket không tồn tại, dừng gửi văn bản")
                return

            # Lọc Markdown
            filtered_text = MarkdownCleaner.clean_markdown(text)

            if filtered_text:
                # Gửi tin nhắn continue-task
                continue_task_message = {
                    "header": {
                        "action": "continue-task",
                        "task_id": self.conn.sentence_id,
                        "streaming": "duplex",
                    },
                    "payload": {"input": {"text": filtered_text}},
                }

                await self.ws.send(json.dumps(continue_task_message))
                self.last_active_time = time.time()
                logger.bind(tag=TAG).debug(f"Đã gửi văn bản: {filtered_text}")
            return
        except Exception as e:
            logger.bind(tag=TAG).error(f"Gửi văn bản TTS thất bại: {str(e)}")
            if self.ws:
                try:
                    await self.ws.close()
                except:
                    pass
                self.ws = None
            raise

    async def start_session(self, session_id):
        """Khởi động phiên TTS"""
        logger.bind(tag=TAG).info(f"Bắt đầu phiên～～{session_id}")
        try:
            # Kiểm tra và dọn dẹp tác vụ lắng nghe của phiên trước
            if (
                self._monitor_task is not None
                and isinstance(self._monitor_task, Task)
                and not self._monitor_task.done()
            ):
                logger.bind(tag=TAG).info("Phát hiện phiên trước chưa hoàn thành, đóng tác vụ lắng nghe...")
                await self.close()

            # Đảm bảo kết nối khả dụng
            await self._ensure_connection()

            # Khởi động tác vụ lắng nghe
            self._monitor_task = asyncio.create_task(self._start_monitor_tts_response())

            # Gửi tin nhắn run-task để khởi động phiên
            run_task_message = {
                "header": {
                    "action": "run-task",
                    "task_id": session_id,
                    "streaming": "duplex",
                },
                "payload": {
                    "task_group": "audio",
                    "task": "tts",
                    "function": "SpeechSynthesizer",
                    "model": self.model,
                    "parameters": {
                        "text_type": "PlainText",
                        "voice": self.voice,
                        "format": self.format,
                        "sample_rate": self.conn.sample_rate,
                        "volume": self.volume,
                        "rate": self.rate,
                        "pitch": self.pitch,
                    },
                    "input": {}
                },
            }

            await self.ws.send(json.dumps(run_task_message))
            self.last_active_time = time.time()
            logger.bind(tag=TAG).info("Yêu cầu khởi động phiên đã được gửi")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Khởi động phiên thất bại: {str(e)}")
            await self.close()
            raise

    async def finish_session(self, session_id):
        """Kết thúc phiên TTS"""
        logger.bind(tag=TAG).info(f"Đóng phiên～～{session_id}")
        try:
            if self.ws and session_id:
                # Gửi tin nhắn finish-task
                finish_task_message = {
                    "header": {
                        "action": "finish-task",
                        "task_id": session_id,
                        "streaming": "duplex",
                    },
                    "payload": {
                        "input": {}
                    }
                }

                await self.ws.send(json.dumps(finish_task_message))
                self.last_active_time = time.time()
                logger.bind(tag=TAG).info("Yêu cầu kết thúc phiên đã được gửi")
                # Chờ tác vụ lắng nghe hoàn thành
                if self._monitor_task:
                    try:
                        await self._monitor_task
                    except Exception as e:
                        logger.bind(tag=TAG).error(
                            f"Lỗi khi chờ tác vụ lắng nghe hoàn thành: {str(e)}"
                        )
                    finally:
                        self._monitor_task = None

        except Exception as e:
            logger.bind(tag=TAG).error(f"Đóng phiên thất bại: {str(e)}")
            await self.close()
            raise

    async def close(self):
        """Dọn dẹp tài nguyên"""
        # Hủy tác vụ lắng nghe
        if self._monitor_task:
            try:
                self._monitor_task.cancel()
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.bind(tag=TAG).warning(f"Lỗi khi hủy tác vụ lắng nghe lúc đóng: {e}")
            self._monitor_task = None

        # Đóng kết nối WebSocket
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None
            self.last_active_time = None

    async def _start_monitor_tts_response(self):
        """Lắng nghe phản hồi TTS"""
        try:
            session_finished = False
            while not self.conn.stop_event.is_set():
                try:
                    msg = await self.ws.recv()
                    self.last_active_time = time.time()

                    # Kiểm tra client có bị hủy không
                    if self.conn.client_abort:
                        logger.bind(tag=TAG).info("Nhận thông tin ngắt, kết thúc lắng nghe phản hồi TTS")
                        break

                    if isinstance(msg, str):  # Tin nhắn điều khiển JSON
                        try:
                            data = json.loads(msg)
                            event = data["header"].get("event")

                            if event == "task-started":
                                logger.bind(tag=TAG).debug("Tác vụ TTS đã khởi động thành công~")
                                self.tts_audio_queue.put((SentenceType.FIRST, [], None))
                            elif event == "result-generated":
                                # Gửi dữ liệu đã cache
                                if self.conn.tts_MessageText:
                                    logger.bind(tag=TAG).info(
                                        f"Tạo giọng nói câu thành công: {self.conn.tts_MessageText}"
                                    )
                                    self.tts_audio_queue.put(
                                        (SentenceType.FIRST, [], self.conn.tts_MessageText)
                                    )
                                    self.conn.tts_MessageText = None
                            elif event == "task-finished":
                                logger.bind(tag=TAG).debug("Tác vụ TTS hoàn tất~")
                                self._process_before_stop_play_files()
                                session_finished = True
                                break
                            elif event == "task-failed":
                                error_code = data["header"].get("error_code", "unknown")
                                error_message = data["header"].get("error_message", "Lỗi không xác định")
                                logger.bind(tag=TAG).error(
                                    f"Tác vụ TTS thất bại: {error_code} - {error_message}"
                                )
                                break
                        except json.JSONDecodeError:
                            logger.bind(tag=TAG).warning("Nhận tin nhắn JSON không hợp lệ")
                    elif isinstance(msg, (bytes, bytearray)):
                        self.opus_encoder.encode_pcm_to_opus_stream(
                            msg, False, callback=self.handle_opus
                        )
                except websockets.ConnectionClosed:
                    logger.bind(tag=TAG).warning("Kết nối WebSocket đã đóng")
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"Lỗi khi xử lý phản hồi TTS: {e}\n{traceback.format_exc()}"
                    )
                    break

            # Chỉ đóng kết nối khi kết nối bất thường và không kết thúc bình thường
            if not session_finished and self.ws:
                try:
                    await self.ws.close()
                except:
                    pass
                self.ws = None
        # Dọn dẹp tham chiếu khi tác vụ lắng nghe thoát
        finally:
            self._monitor_task = None

    def to_tts(self, text: str) -> list:
        """Tạo dữ liệu audio không streaming, dùng cho tạo audio và test"""
        try:
            # Tạo vòng lặp sự kiện
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Tạo ID phiên
            session_id = uuid.uuid4().hex
            # Lưu trữ dữ liệu audio
            audio_data = []

            async def _generate_audio():
                ws = await websockets.connect(
                    self.ws_url,
                    additional_headers=self.header,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10,
                    max_size=10 * 1024 * 1024,
                )

                try:
                    # Gửi tin nhắn run-task để khởi động phiên
                    run_task_message = {
                        "header": {
                            "action": "run-task",
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {
                            "task_group": "audio",
                            "task": "tts",
                            "function": "SpeechSynthesizer",
                            "model": self.model,
                            "parameters": {
                                "text_type": "PlainText",
                                "voice": self.voice,
                                "format": self.format,
                                "sample_rate": self.conn.sample_rate,
                                "volume": self.volume,
                                "rate": self.rate,
                                "pitch": self.pitch,
                            },
                            "input": {}
                        },
                    }
                    await ws.send(json.dumps(run_task_message))

                    # Chờ tác vụ khởi động
                    task_started = False
                    while not task_started:
                        msg = await ws.recv()
                        if isinstance(msg, str):
                            data = json.loads(msg)
                            header = data.get("header", {})
                            if header.get("event") == "task-started":
                                task_started = True
                                logger.bind(tag=TAG).debug("Tác vụ TTS đã khởi động")
                            elif header.get("event") == "task-failed":
                                error_code = header.get("error_code", "unknown")
                                error_message = header.get("error_message", "Lỗi không xác định")
                                raise Exception(
                                    f"Khởi động tác vụ thất bại: {error_code} - {error_message}"
                                )

                    # Gửi văn bản
                    filtered_text = MarkdownCleaner.clean_markdown(text)
                    # Gửi tin nhắn continue-task
                    continue_task_message = {
                        "header": {
                            "action": "continue-task",
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {"input": {"text": filtered_text}},
                    }
                    await ws.send(json.dumps(continue_task_message))

                    # Gửi tin nhắn finish-task
                    finish_task_message = {
                        "header": {
                            "action": "finish-task",
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {
                            "input": {}
                        }
                    }
                    await ws.send(json.dumps(finish_task_message))

                    # Nhận dữ liệu audio
                    task_finished = False
                    while not task_finished:
                        msg = await ws.recv()
                        if isinstance(msg, (bytes, bytearray)):
                            self.opus_encoder.encode_pcm_to_opus_stream(
                                msg,
                                end_of_stream=False,
                                callback=lambda opus: audio_data.append(opus)
                            )
                        elif isinstance(msg, str):
                            data = json.loads(msg)
                            header = data.get("header", {})
                            if header.get("event") == "task-finished":
                                task_finished = True
                                logger.bind(tag=TAG).debug("Tác vụ TTS hoàn tất")
                            elif header.get("event") == "task-failed":
                                error_code = header.get("error_code", "unknown")
                                error_message = header.get("error_message", "Lỗi không xác định")
                                raise Exception(
                                    f"Tổng hợp thất bại: {error_code} - {error_message}"
                                )

                finally:
                    # Dọn dẹp tài nguyên
                    try:
                        await ws.close()
                    except:
                        pass

            # Chạy tác vụ bất đồng bộ
            loop.run_until_complete(_generate_audio())
            loop.close()

            return audio_data

        except Exception as e:
            logger.bind(tag=TAG).error(f"Tạo dữ liệu audio thất bại: {str(e)}")
            return []