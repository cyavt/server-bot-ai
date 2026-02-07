import os
import time
import uuid
import json
import hmac
import queue
import base64
import hashlib
import asyncio
import traceback
import websockets
from asyncio import Task
from config.logger import setup_logging
from core.utils import opus_encoder_utils
from core.utils.tts import MarkdownCleaner
from urllib.parse import urlencode, urlparse
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType

TAG = __name__
logger = setup_logging()


class XunfeiWSAuth:
    @staticmethod
    def create_auth_url(api_key, api_secret, api_url):
        """Tạo URL xác thực WebSocket của Xunfei"""
        parsed_url = urlparse(api_url)
        host = parsed_url.netloc
        path = parsed_url.path

        # Lấy thời gian UTC, Xunfei yêu cầu sử dụng định dạng RFC1123
        now = time.gmtime()
        date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', now)

        # Tạo chuỗi chữ ký
        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"

        # Tính toán chữ ký
        signature_sha = hmac.new(
            api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        # Tạo authorization
        authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # Tạo URL WebSocket cuối cùng
        v = {
            "authorization": authorization,
            "date": date,
            "host": host
        }
        url = api_url + '?' + urlencode(v)
        return url


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)

        # Thiết lập loại giao diện streaming
        self.interface_type = InterfaceType.DUAL_STREAM

        # Cấu hình cơ bản
        self.app_id = config.get("app_id")
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")

        # Địa chỉ giao diện
        self.api_url = config.get("api_url", "wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6")

        # Cấu hình giọng nói
        self.voice = config.get("voice", "x5_lingxiaoxuan_flow")
        if config.get("private_voice"):
            self.voice = config.get("private_voice")

        # Cấu hình tham số audio
        speed = config.get("speed", "50")
        self.speed = int(speed) if speed else 50

        volume = config.get("volume", "50")
        self.volume = int(volume) if volume else 50

        pitch = config.get("pitch", "50")
        self.pitch = int(pitch) if pitch else 50

        # Cấu hình mã hóa audio
        self.format = config.get("format", "raw")

        # Cấu hình ngôn ngữ nói
        self.oral_level = config.get("oral_level", "mid")

        spark_assist = config.get("spark_assist", "1")
        self.spark_assist = int(spark_assist) if spark_assist else 1

        stop_split = config.get("stop_split", "0")
        self.stop_split = int(stop_split) if stop_split else 0
    
        remain = config.get("remain", "0")
        self.remain = int(remain) if remain else 0

        # Cấu hình WebSocket
        self.ws = None
        self._monitor_task = None

        # Quản lý số thứ tự
        self.text_seq = 0

        # Xác thực tham số bắt buộc
        if not all([self.app_id, self.api_key, self.api_secret]):
            raise ValueError("Xunfei TTS cần cấu hình app_id, api_key và api_secret")

    async def _ensure_connection(self):
        """Đảm bảo kết nối WebSocket khả dụng"""
        try:
            logger.bind(tag=TAG).info("Bắt đầu thiết lập kết nối mới...")

            # Tạo URL xác thực
            auth_url = XunfeiWSAuth.create_auth_url(
                self.api_key, self.api_secret, self.api_url
            )

            self.ws = await websockets.connect(
                auth_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
            )
            logger.bind(tag=TAG).info("Kết nối WebSocket đã được thiết lập thành công")
            return self.ws
        except Exception as e:
            logger.bind(tag=TAG).error(f"Thiết lập kết nối thất bại: {str(e)}")
            self.ws = None
            raise

    def tts_text_priority_thread(self):
        """Luồng xử lý văn bản streaming"""
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                logger.bind(tag=TAG).debug(
                    f"Nhận tác vụ TTS｜{message.sentence_type.name} ｜ {message.content_type.name} | ID phiên: {self.conn.sentence_id}"
                )

                if message.sentence_type == SentenceType.FIRST:
                    # Đặt lại số thứ tự
                    self.text_seq = 0
                    self.conn.client_abort = False
                # Tăng số thứ tự
                self.text_seq += 1
                if self.conn.client_abort:
                    logger.bind(tag=TAG).info("Nhận thông tin ngắt, kết thúc luồng xử lý văn bản TTS")
                    continue

                if message.sentence_type == SentenceType.FIRST:
                    # Khởi tạo tham số
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

                # Xử lý nội dung văn bản
                if ContentType.TEXT == message.content_type:
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
                            # Không sử dụng continue, đảm bảo xử lý tiếp theo không bị gián đoạn

                # Xử lý nội dung file
                if ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(
                        f"Thêm file audio vào danh sách chờ phát: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        # Xử lý dữ liệu audio của file trước
                        self._process_audio_file_stream(message.content_file, callback=lambda audio_data: self.handle_audio_file(audio_data, message.content_detail))

                # Xử lý kết thúc phiên
                if message.sentence_type == SentenceType.LAST:
                    try:
                        logger.bind(tag=TAG).info("Bắt đầu kết thúc phiên TTS...")
                        asyncio.run_coroutine_threadsafe(
                            self.finish_session(self.conn.sentence_id),
                            loop=self.conn.loop,
                        )
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Kết thúc phiên TTS thất bại: {str(e)}")
                        continue

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"Xử lý văn bản TTS thất bại: {str(e)}, loại: {type(e).__name__}, stack: {traceback.format_exc()}"
                )

    async def text_to_speak(self, text, _):
        """Gửi văn bản đến dịch vụ TTS để tổng hợp"""
        try:
            if self.ws is None:
                logger.bind(tag=TAG).warning(f"Kết nối WebSocket không tồn tại, dừng gửi văn bản")
                return

            filtered_text = MarkdownCleaner.clean_markdown(text)
            if filtered_text:
                # Gửi yêu cầu tổng hợp văn bản
                run_request = self._build_base_request(status=1,text=filtered_text)
                await self.ws.send(json.dumps(run_request))
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
        logger.bind(tag=TAG).info(f"Bắt đầu phiên～～{session_id}")
        try:
            # Khi bắt đầu phiên, kiểm tra trạng thái lắng nghe của phiên trước
            if (
                self._monitor_task is not None
                and isinstance(self._monitor_task, Task)
                and not self._monitor_task.done()
            ):
                logger.bind(tag=TAG).info(
                    "Phát hiện phiên trước chưa hoàn thành, đóng tác vụ lắng nghe và kết nối..."
                )
                await self.close()

            # Thiết lập kết nối mới
            await self._ensure_connection()

            # Khởi động tác vụ lắng nghe
            self._monitor_task = asyncio.create_task(self._start_monitor_tts_response())

            # Gửi yêu cầu khởi động phiên
            start_request = self._build_base_request(status=0)

            await self.ws.send(json.dumps(start_request))
            logger.bind(tag=TAG).info("Yêu cầu khởi động phiên đã được gửi")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Khởi động phiên thất bại: {str(e)}")
            # Đảm bảo dọn dẹp tài nguyên
            await self.close()
            raise

    async def finish_session(self, session_id):
        logger.bind(tag=TAG).info(f"Đóng phiên～～{session_id}")
        try:
            if self.ws:
                # Gửi yêu cầu kết thúc phiên
                stop_request = self._build_base_request(status=2)
                await self.ws.send(json.dumps(stop_request))
                logger.bind(tag=TAG).info("Yêu cầu kết thúc phiên đã được gửi")

                if self._monitor_task:
                    try:
                        await self._monitor_task
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Lỗi khi chờ tác vụ lắng nghe hoàn thành: {str(e)}")
                    finally:
                        self._monitor_task = None
        except Exception as e:
            logger.bind(tag=TAG).error(f"Đóng phiên thất bại: {str(e)}")
            await self.close()
            raise

    async def close(self):
        """Dọn dẹp tài nguyên"""
        if self._monitor_task:
            try:
                self._monitor_task.cancel()
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.bind(tag=TAG).warning(f"Lỗi khi hủy tác vụ lắng nghe lúc đóng: {e}")
            self._monitor_task = None

        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None

    async def _start_monitor_tts_response(self):
        """Lắng nghe phản hồi TTS"""
        try:
            while not self.conn.stop_event.is_set():
                try:
                    msg = await self.ws.recv()

                    # Kiểm tra client có bị hủy không
                    if self.conn.client_abort:
                        logger.bind(tag=TAG).info("Nhận thông tin ngắt, kết thúc lắng nghe phản hồi TTS")
                        break

                    try:
                        data = json.loads(msg)
                        header = data.get("header", {})
                        code = header.get("code")

                        if code == 0:
                            payload = data.get("payload", {})
                            audio_payload = payload.get("audio", {})

                            if audio_payload:
                                status = audio_payload.get("status", 0)
                                audio_data = audio_payload.get("audio", "")
                                if status == 0:
                                    logger.bind(tag=TAG).debug("TTS tổng hợp đã khởi động")
                                    self.tts_audio_queue.put(
                                        (SentenceType.FIRST, [], None)
                                    )
                                elif status == 2:
                                    logger.bind(tag=TAG).debug("Nhận dữ liệu audio ở trạng thái kết thúc, TTS tổng hợp hoàn tất")
                                    self._process_before_stop_play_files()
                                    break
                                else:
                                    if self.conn.tts_MessageText:
                                        logger.bind(tag=TAG).info(
                                            f"Tạo giọng nói câu thành công: {self.conn.tts_MessageText}"
                                        )
                                        self.tts_audio_queue.put(
                                            (SentenceType.FIRST, [], self.conn.tts_MessageText)
                                        )
                                        self.conn.tts_MessageText = None
                                    try:
                                        audio_bytes = base64.b64decode(audio_data)
                                        self.opus_encoder.encode_pcm_to_opus_stream(
                                            audio_bytes, False, self.handle_opus
                                        )

                                    except Exception as e:
                                        logger.bind(tag=TAG).error(f"Xử lý dữ liệu audio thất bại: {e}")

                        else:
                            message = header.get("message", "Lỗi không xác định")
                            logger.bind(tag=TAG).error(f"Lỗi tổng hợp TTS: {code} - {message}")
                            break

                    except json.JSONDecodeError:
                        logger.bind(tag=TAG).warning("Nhận tin nhắn JSON không hợp lệ")

                except websockets.ConnectionClosed:
                    logger.bind(tag=TAG).warning("Kết nối WebSocket đã đóng")
                    break

                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"Lỗi khi xử lý phản hồi TTS: {e}\n{traceback.format_exc()}"
                    )
                    break

            # Liên kết không thể tái sử dụng
            if self.ws:
                try:
                    await self.ws.close()
                except:
                    pass
                self.ws = None
        # Dọn dẹp tham chiếu khi tác vụ lắng nghe thoát
        finally:
            self._monitor_task = None

    def to_tts(self, text: str) -> list:
        """Xử lý TTS không streaming, dùng cho test và lưu file audio"""
        try:
            # Tạo vòng lặp sự kiện mới
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Lưu trữ dữ liệu audio
            audio_data = []

            async def _generate_audio():
                # Tạo URL xác thực
                auth_url = XunfeiWSAuth.create_auth_url(
                    self.api_key, self.api_secret, self.api_url
                )

                # Thiết lập kết nối WebSocket
                ws = await websockets.connect(
                    auth_url,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10,
                )

                try:
                    filtered_text = MarkdownCleaner.clean_markdown(text)

                    text_request = self._build_base_request(status=2,text=filtered_text)

                    await ws.send(json.dumps(text_request))

                    task_finished = False
                    while not task_finished:
                        msg = await ws.recv()

                        data = json.loads(msg)
                        header = data.get("header", {})
                        code = header.get("code")

                        if code == 0:
                            payload = data.get("payload", {})
                            audio_payload = payload.get("audio", {})
                            if audio_payload:
                                status = audio_payload.get("status", 0)
                                audio_base64 = audio_payload.get("audio", "")
                                if status == 1:
                                    try:
                                        audio_bytes = base64.b64decode(audio_base64)
                                        self.opus_encoder.encode_pcm_to_opus_stream(
                                            audio_bytes,
                                            end_of_stream=False,
                                            callback=lambda opus: audio_data.append(opus)
                                        )
                                    except Exception as e:
                                        logger.bind(tag=TAG).error(f"Xử lý dữ liệu audio thất bại: {e}")
                                elif status == 2:
                                    task_finished = True
                                    logger.bind(tag=TAG).debug("Tác vụ TTS hoàn tất")

                        else:
                            message = header.get("message", "Lỗi không xác định")
                            raise Exception(f"Tổng hợp thất bại: {code} - {message}")

                finally:
                    # Dọn dẹp tài nguyên
                    try:
                        await ws.close()
                    except:
                        pass

            loop.run_until_complete(_generate_audio())
            loop.close()

            return audio_data
        except Exception as e:
            logger.bind(tag=TAG).error(f"Tạo dữ liệu audio thất bại: {str(e)}")
            return []        
    
    def _build_base_request(self, status,text=" "):
        """Xây dựng cấu trúc yêu cầu cơ bản"""
        return {
            "header": {
                "app_id": self.app_id,
                "status": status,
            },
            "parameter": {
                "oral": {
                    "oral_level": self.oral_level,
                    "spark_assist": self.spark_assist,
                    "stop_split": self.stop_split,
                    "remain": self.remain
                },
                "tts": {
                    "vcn": self.voice,
                    "speed": self.speed,
                    "volume": self.volume,
                    "pitch": self.pitch,
                    "bgs": 0,
                    "reg": 0,
                    "rdn": 0,
                    "rhy": 0,
                    "audio": {
                        "encoding": self.format,
                        "sample_rate": self.conn.sample_rate,
                        "channels": 1,
                        "bit_depth": 16,
                        "frame_size": 0
                    }
                }
            },
            "payload": {
                "text": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "plain",
                    "status": status,
                    "seq": self.text_seq,
                    "text": base64.b64encode(text.encode('utf-8')).decode('utf-8')
                }
            }
        }
