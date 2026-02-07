import random
import uuid
import json
import hmac
import hashlib
import base64
import time
import queue
import asyncio
import traceback
from asyncio import Task
import websockets
import os
from datetime import datetime
from urllib import parse
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType
from core.utils.tts import MarkdownCleaner
from core.utils import opus_encoder_utils, textUtils
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class AccessToken:
    @staticmethod
    def _encode_text(text):
        encoded_text = parse.quote_plus(text)
        return encoded_text.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")

    @staticmethod
    def _encode_dict(dic):
        keys = dic.keys()
        dic_sorted = [(key, dic[key]) for key in sorted(keys)]
        encoded_text = parse.urlencode(dic_sorted)
        return encoded_text.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")

    @staticmethod
    def create_token(access_key_id, access_key_secret):
        parameters = {
            "AccessKeyId": access_key_id,
            "Action": "CreateToken",
            "Format": "JSON",
            "RegionId": "cn-shanghai",  # Sử dụng khu vực Thượng Hải để lấy Token
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": str(uuid.uuid1()),
            "SignatureVersion": "1.0",
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "Version": "2019-02-28",
        }

        query_string = AccessToken._encode_dict(parameters)
        string_to_sign = (
            "GET"
            + "&"
            + AccessToken._encode_text("/")
            + "&"
            + AccessToken._encode_text(query_string)
        )

        secreted_string = hmac.new(
            bytes(access_key_secret + "&", encoding="utf-8"),
            bytes(string_to_sign, encoding="utf-8"),
            hashlib.sha1,
        ).digest()
        signature = base64.b64encode(secreted_string)
        signature = AccessToken._encode_text(signature)

        full_url = "http://nls-meta.cn-shanghai.aliyuncs.com/?Signature=%s&%s" % (
            signature,
            query_string,
        )

        import requests

        response = requests.get(full_url)
        if response.ok:
            root_obj = response.json()
            key = "Token"
            if key in root_obj:
                token = root_obj[key]["Id"]
                expire_time = root_obj[key]["ExpireTime"]
                return token, expire_time
        return None, None


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)

        # Thiết lập loại giao diện streaming
        self.interface_type = InterfaceType.DUAL_STREAM

        # Cấu hình cơ bản
        self.access_key_id = config.get("access_key_id")
        self.access_key_secret = config.get("access_key_secret")
        self.appkey = config.get("appkey")
        self.format = config.get("format", "pcm")
        self.audio_file_type = config.get("format", "pcm")

        # Cấu hình giọng nói - Giọng nói model lớn CosyVoice
        if config.get("private_voice"):
            self.voice = config.get("private_voice")
        else:
            self.voice = config.get("voice", "longxiaochun")  # Giọng nói mặc định CosyVoice

        # Cấu hình tham số audio
        volume = config.get("volume", "50")
        self.volume = int(volume) if volume else 50

        speech_rate = config.get("speech_rate", "0")
        self.speech_rate = int(speech_rate) if speech_rate else 0

        pitch_rate = config.get("pitch_rate", "0")
        self.pitch_rate = int(pitch_rate) if pitch_rate else 0

        # Cấu hình WebSocket
        self.host = config.get("host", "nls-gateway-cn-beijing.aliyuncs.com")
        # Nếu cấu hình là địa chỉ nội bộ (chứa -internal.aliyuncs.com), thì sử dụng giao thức ws, mặc định là giao thức wss
        if "-internal." in self.host:
            self.ws_url = f"ws://{self.host}/ws/v1"
        else:
            # Mặc định sử dụng giao thức wss
            self.ws_url = f"wss://{self.host}/ws/v1"
        self.ws = None
        self._monitor_task = None
        self.last_active_time = None

        # Cài đặt TTS riêng
        self.task_id = uuid.uuid4().hex

        # Quản lý Token
        if self.access_key_id and self.access_key_secret:
            self._refresh_token()
        else:
            self.token = config.get("token")
            self.expire_time = None

    def _refresh_token(self):
        """Làm mới Token và ghi lại thời gian hết hạn"""
        if self.access_key_id and self.access_key_secret:
            self.token, expire_time_str = AccessToken.create_token(
                self.access_key_id, self.access_key_secret
            )
            if not expire_time_str:
                raise ValueError("Không thể lấy thời gian hết hạn Token hợp lệ")

            expire_str = str(expire_time_str).strip()

            try:
                if expire_str.isdigit():
                    expire_time = datetime.fromtimestamp(int(expire_str))
                else:
                    expire_time = datetime.strptime(expire_str, "%Y-%m-%dT%H:%M:%SZ")
                self.expire_time = expire_time.timestamp() - 60
            except Exception as e:
                raise ValueError(f"Định dạng thời gian hết hạn không hợp lệ: {expire_str}") from e
        else:
            self.expire_time = None

        if not self.token:
            raise ValueError("Không thể lấy Token truy cập hợp lệ")

    def _is_token_expired(self):
        """Kiểm tra xem Token có hết hạn không"""
        if not self.expire_time:
            return False
        return time.time() > self.expire_time

    async def _ensure_connection(self):
        """Đảm bảo kết nối WebSocket khả dụng"""
        try:
            if self._is_token_expired():
                logger.bind(tag=TAG).warning("Token đã hết hạn, đang tự động làm mới...")
                self._refresh_token()
            current_time = time.time()
            if self.ws and current_time - self.last_active_time < 10:
                # Chỉ có thể tái sử dụng kết nối để đối thoại liên tục trong vòng 10 giây
                self.task_id = uuid.uuid4().hex
                logger.bind(tag=TAG).info(f"Sử dụng kết nối hiện có..., task_id: {self.task_id}")
                return self.ws
            logger.bind(tag=TAG).debug("Bắt đầu thiết lập kết nối mới...")

            self.ws = await websockets.connect(
                self.ws_url,
                additional_headers={"X-NLS-Token": self.token},
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
            )
            self.task_id = uuid.uuid4().hex
            logger.bind(tag=TAG).debug(f"Kết nối WebSocket được thiết lập thành công, task_id: {self.task_id}")
            self.last_active_time = time.time()
            return self.ws
        except Exception as e:
            logger.bind(tag=TAG).error(f"Thiết lập kết nối thất bại: {str(e)}")
            self.ws = None
            self.last_active_time = None
            raise

    def tts_text_priority_thread(self):
        """Luồng xử lý văn bản dạng luồng"""
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                logger.bind(tag=TAG).debug(
                    f"Nhận nhiệm vụ TTS｜{message.sentence_type.name} ｜ {message.content_type.name} | ID phiên: {self.conn.sentence_id}"
                )

                if message.sentence_type == SentenceType.FIRST:
                    self.conn.client_abort = False

                if self.conn.client_abort:
                    logger.bind(tag=TAG).info("Nhận thông tin ngắt, dừng luồng xử lý văn bản TTS")
                    continue

                if message.sentence_type == SentenceType.FIRST:
                    # Khởi tạo tham số
                    try:
                        logger.bind(tag=TAG).debug("Bắt đầu khởi động phiên TTS...")
                        future = asyncio.run_coroutine_threadsafe(
                            self.start_session(self.task_id),
                            loop=self.conn.loop,
                        )
                        future.result()
                        self.before_stop_play_files.clear()
                        logger.bind(tag=TAG).debug("Khởi động phiên TTS thành công")

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
                            logger.bind(tag=TAG).debug("Gửi văn bản TTS thành công")
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"Gửi văn bản TTS thất bại: {str(e)}")
                            continue

                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(
                        f"Thêm tệp âm thanh vào danh sách chờ phát: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        # Xử lý dữ liệu âm thanh tệp trước
                        self._process_audio_file_stream(message.content_file, callback=lambda audio_data: self.handle_audio_file(audio_data, message.content_detail))
                if message.sentence_type == SentenceType.LAST:
                    try:
                        logger.bind(tag=TAG).debug("Bắt đầu kết thúc phiên TTS...")
                        future = asyncio.run_coroutine_threadsafe(
                            self.finish_session(self.task_id),
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
                    f"Xử lý văn bản TTS thất bại: {str(e)}, Loại: {type(e).__name__}, Stack: {traceback.format_exc()}"
                )

    async def text_to_speak(self, text, _):
        try:
            if self.ws is None:
                logger.bind(tag=TAG).warning(f"Kết nối WebSocket không tồn tại, dừng gửi văn bản")
                return
            filtered_text = MarkdownCleaner.clean_markdown(text)
            if filtered_text:
                run_request = {
                    "header": {
                        "message_id": uuid.uuid4().hex,
                        "task_id": self.task_id,
                        "namespace": "FlowingSpeechSynthesizer",
                        "name": "RunSynthesis",
                        "appkey": self.appkey,
                    },
                    "payload": {"text": filtered_text},
                }
                await self.ws.send(json.dumps(run_request))
                self.last_active_time = time.time()
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

    async def start_session(self, task_id):
        logger.bind(tag=TAG).debug("Bắt đầu phiên～～")
        try:
            # Khi phiên bắt đầu, kiểm tra trạng thái lắng nghe của phiên trước
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

            start_request = {
                "header": {
                    "message_id": uuid.uuid4().hex,
                    "task_id": self.task_id,
                    "namespace": "FlowingSpeechSynthesizer",
                    "name": "StartSynthesis",
                    "appkey": self.appkey,
                },
                "payload": {
                    "voice": self.voice,
                    "format": self.format,
                    "sample_rate": self.conn.sample_rate,
                    "volume": self.volume,
                    "speech_rate": self.speech_rate,
                    "pitch_rate": self.pitch_rate,
                    "enable_subtitle": True,
                },
            }
            await self.ws.send(json.dumps(start_request))
            self.last_active_time = time.time()
            logger.bind(tag=TAG).debug("Yêu cầu khởi động phiên đã được gửi")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Khởi động phiên thất bại: {str(e)}")
            # Đảm bảo dọn dẹp tài nguyên
            await self.close()
            raise

    async def finish_session(self, task_id):
        logger.bind(tag=TAG).debug(f"Đóng phiên～～{task_id}")
        try:
            if self.ws:
                stop_request = {
                    "header": {
                        "message_id": uuid.uuid4().hex,
                        "task_id": self.task_id,
                        "namespace": "FlowingSpeechSynthesizer",
                        "name": "StopSynthesis",
                        "appkey": self.appkey,
                    }
                }
                await self.ws.send(json.dumps(stop_request))
                logger.bind(tag=TAG).debug("Yêu cầu kết thúc phiên đã được gửi")
                self.last_active_time = time.time()
                if self._monitor_task:
                    try:
                        await self._monitor_task
                    except Exception as e:
                        logger.bind(tag=TAG).error(
                            f"Xảy ra lỗi khi chờ tác vụ lắng nghe hoàn thành: {str(e)}"
                        )
                    finally:
                        self._monitor_task = None
        except Exception as e:
            logger.bind(tag=TAG).error(f"Đóng phiên thất bại: {str(e)}")
            # Đảm bảo dọn dẹp tài nguyên
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
                logger.bind(tag=TAG).warning(f"Lỗi khi hủy tác vụ lắng nghe khi đóng: {e}")
            self._monitor_task = None

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
            session_finished = False  # Đánh dấu xem phiên có kết thúc bình thường không
            while not self.conn.stop_event.is_set():
                try:
                    msg = await self.ws.recv()
                    self.last_active_time = time.time()
                    # Kiểm tra xem client có bị hủy không
                    if self.conn.client_abort:
                        logger.bind(tag=TAG).info("Nhận thông tin ngắt, dừng lắng nghe phản hồi TTS")
                        break
                    if isinstance(msg, str):  # Tin nhắn điều khiển văn bản
                        try:
                            data = json.loads(msg)
                            header = data.get("header", {})
                            event_name = header.get("name")
                            if event_name == "SynthesisStarted":
                                logger.bind(tag=TAG).debug("Tổng hợp TTS đã khởi động")
                                self.tts_audio_queue.put(
                                    (SentenceType.FIRST, [], None)
                                )
                            elif event_name == "SentenceEnd":
                                # Gửi dữ liệu đã lưu vào bộ đệm
                                if self.conn.tts_MessageText:
                                    logger.bind(tag=TAG).info(
                                        f"Tạo giọng nói câu thành công: {self.conn.tts_MessageText}"
                                    )
                                    self.tts_audio_queue.put(
                                        (SentenceType.FIRST, [], self.conn.tts_MessageText)
                                    )
                                    self.conn.tts_MessageText = None
                            elif event_name == "SynthesisCompleted":
                                logger.bind(tag=TAG).debug(f"Phiên kết thúc～～")
                                self._process_before_stop_play_files()
                                session_finished = True
                                break
                        except json.JSONDecodeError:
                            logger.bind(tag=TAG).warning("Nhận tin nhắn JSON không hợp lệ")
                    # Tin nhắn nhị phân (dữ liệu âm thanh)
                    elif isinstance(msg, (bytes, bytearray)):
                        self.opus_encoder.encode_pcm_to_opus_stream(msg, False, self.handle_opus)
                except websockets.ConnectionClosed:
                    logger.bind(tag=TAG).warning("Kết nối WebSocket đã đóng")
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"Xảy ra lỗi khi xử lý phản hồi TTS: {e}\n{traceback.format_exc()}"
                    )
                    break
            # Chỉ đóng khi kết nối bất thường
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
        """Xử lý TTS không luồng, dùng cho các trường hợp kiểm tra và lưu tệp âm thanh"""
        try:
            # Tạo vòng lặp sự kiện mới
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Lưu trữ dữ liệu âm thanh
            audio_data = []

            async def _generate_audio():
                # Làm mới Token (nếu cần)
                if self._is_token_expired():
                    self._refresh_token()

                # Thiết lập kết nối WebSocket
                ws = await websockets.connect(
                    self.ws_url,
                    additional_headers={"X-NLS-Token": self.token},
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10,
                )
                try:
                    # Gửi yêu cầu StartSynthesis
                    start_request = {
                        "header": {
                            "message_id": uuid.uuid4().hex,
                            "task_id": self.task_id,
                            "namespace": "FlowingSpeechSynthesizer",
                            "name": "StartSynthesis",
                            "appkey": self.appkey,
                        },
                        "payload": {
                            "voice": self.voice,
                            "format": self.format,
                            "sample_rate": self.conn.sample_rate,
                            "volume": self.volume,
                            "speech_rate": self.speech_rate,
                            "pitch_rate": self.pitch_rate,
                            "enable_subtitle": True,
                        },
                    }
                    await ws.send(json.dumps(start_request))

                    # Chờ phản hồi SynthesisStarted
                    synthesis_started = False
                    while not synthesis_started:
                        msg = await ws.recv()
                        if isinstance(msg, str):
                            data = json.loads(msg)
                            header = data.get("header", {})
                            if header.get("name") == "SynthesisStarted":
                                synthesis_started = True
                                logger.bind(tag=TAG).debug("Tổng hợp TTS đã khởi động")
                            elif header.get("name") == "TaskFailed":
                                error_info = data.get("payload", {}).get(
                                    "error_info", {}
                                )
                                error_code = error_info.get("error_code")
                                error_message = error_info.get(
                                    "error_message", "Lỗi không xác định"
                                )
                                raise Exception(
                                    f"Khởi động tổng hợp thất bại: {error_code} - {error_message}"
                                )

                    # Gửi yêu cầu tổng hợp văn bản
                    filtered_text = MarkdownCleaner.clean_markdown(text)
                    run_request = {
                        "header": {
                            "message_id": uuid.uuid4().hex,
                            "task_id": self.task_id,
                            "namespace": "FlowingSpeechSynthesizer",
                            "name": "RunSynthesis",
                            "appkey": self.appkey,
                        },
                        "payload": {"text": filtered_text},
                    }
                    await ws.send(json.dumps(run_request))

                    # Gửi yêu cầu dừng tổng hợp
                    stop_request = {
                        "header": {
                            "message_id": uuid.uuid4().hex,
                            "task_id": self.task_id,
                            "namespace": "FlowingSpeechSynthesizer",
                            "name": "StopSynthesis",
                            "appkey": self.appkey,
                        }
                    }
                    await ws.send(json.dumps(stop_request))

                    # Nhận dữ liệu âm thanh
                    synthesis_completed = False
                    while not synthesis_completed:
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
                            event_name = header.get("name")
                            if event_name == "SynthesisCompleted":
                                synthesis_completed = True
                                logger.bind(tag=TAG).debug("Tổng hợp TTS hoàn thành")
                            elif event_name == "TaskFailed":
                                error_info = data.get("payload", {}).get(
                                    "error_info", {}
                                )
                                error_code = error_info.get("error_code")
                                error_message = error_info.get(
                                    "error_message", "Lỗi không xác định"
                                )
                                raise Exception(
                                    f"Tổng hợp thất bại: {error_code} - {error_message}"
                                )
                finally:
                    try:
                        await ws.close()
                    except:
                        pass

            loop.run_until_complete(_generate_audio())
            loop.close()

            return audio_data
        except Exception as e:
            logger.bind(tag=TAG).error(f"Tạo dữ liệu âm thanh thất bại: {str(e)}")
            return []