import os
import sys
import copy
import json
import uuid
import time
import queue
import asyncio
import threading
import traceback
import subprocess
import websockets

from core.utils.util import (
    extract_json_from_string,
    check_vad_update,
    check_asr_update,
    filter_sensitive_info,
)
from typing import Dict, Any
from collections import deque
from core.utils.modules_initialize import (
    initialize_modules,
    initialize_tts,
    initialize_asr,
)
from core.handle.reportHandle import report
from core.providers.tts.default import DefaultTTS
from concurrent.futures import ThreadPoolExecutor
from core.utils.dialogue import Message, Dialogue
from core.providers.asr.dto.dto import InterfaceType
from core.handle.textHandle import handleTextMessage
from core.providers.tools.unified_tool_handler import UnifiedToolHandler
from plugins_func.loadplugins import auto_import_modules
from plugins_func.register import Action
from core.auth import AuthenticationError
from config.config_loader import get_private_config_from_api
from core.providers.tts.dto.dto import ContentType, TTSMessageDTO, SentenceType
from config.logger import setup_logging, build_module_string, create_connection_logger
from config.manage_api_client import DeviceNotFoundException, DeviceBindException
from core.utils.prompt_manager import PromptManager
from core.utils.voiceprint_provider import VoiceprintProvider
from core.utils.util import get_system_error_response
from core.utils import textUtils


TAG = __name__

auto_import_modules("plugins_func.functions")


class TTSException(RuntimeError):
    pass


class ConnectionHandler:
    def __init__(
        self,
        config: Dict[str, Any],
        _vad,
        _asr,
        _llm,
        _memory,
        _intent,
        server=None,
    ):
        self.common_config = config
        self.config = copy.deepcopy(config)
        self.session_id = str(uuid.uuid4())
        self.logger = setup_logging()
        self.server = server  # Lưu tham chiếu đến instance server

        self.need_bind = False  # Có cần ràng buộc thiết bị không
        self.bind_completed_event = asyncio.Event()
        self.bind_code = None  # Mã xác minh để ràng buộc thiết bị
        self.last_bind_prompt_time = 0  # Timestamp lần phát nhắc nhở ràng buộc cuối cùng (giây)
        self.bind_prompt_interval = 60  # Khoảng thời gian phát nhắc nhở ràng buộc (giây)

        self.read_config_from_api = self.config.get("read_config_from_api", False)

        self.websocket: websockets.ServerConnection | None = None
        self.headers = None
        self.device_id = None
        self.client_ip = None
        self.prompt = None
        self.welcome_msg = None
        self.max_output_size = 0
        self.chat_history_conf = 0
        self.audio_format = "opus"
        self.sample_rate = 24000  # Tần số lấy mẫu mặc định, được cập nhật động từ thông báo hello của client

        # Trạng thái client liên quan
        self.client_abort = False
        self.client_is_speaking = False
        self.client_listen_mode = "auto"

        # Nhiệm vụ thread liên quan
        self.loop = None  # Lấy event loop đang chạy trong handle_connection
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5)

        # Thêm thread pool báo cáo
        self.report_queue = queue.Queue()
        self.report_thread = None
        # Trong tương lai có thể điều chỉnh báo cáo ASR và TTS bằng cách sửa đổi ở đây, hiện tại mặc định đều bật
        self.report_asr_enable = self.read_config_from_api
        self.report_tts_enable = self.read_config_from_api

        # Các component phụ thuộc
        self.vad = None
        self.asr = None
        self.tts = None
        self._asr = _asr
        self._vad = _vad
        self.llm = _llm
        self.memory = _memory
        self.intent = _intent

        # Quản lý nhận dạng giọng nói riêng cho mỗi kết nối
        self.voiceprint_provider = None

        # Biến liên quan đến VAD
        self.client_audio_buffer = bytearray()
        self.client_have_voice = False
        self.client_voice_window = deque(maxlen=5)
        self.first_activity_time = 0.0  # Ghi lại thời gian hoạt động đầu tiên (mili giây)
        self.last_activity_time = 0.0  # Timestamp hoạt động thống nhất (mili giây)
        self.client_voice_stop = False
        self.last_is_voice = False

        # Biến liên quan đến ASR
        # Vì khi triển khai thực tế có thể sử dụng ASR local công cộng, không thể để biến lộ ra cho ASR công cộng
        # Nên các biến liên quan đến ASR cần được định nghĩa ở đây, thuộc về biến riêng của connection
        self.asr_audio = []
        self.asr_audio_queue = queue.Queue()
        self.current_speaker = None  # Lưu trữ người nói hiện tại
        self.current_language_tag = None  # Lưu trữ nhãn ngôn ngữ được ASR nhận dạng hiện tại

        # Biến liên quan đến LLM
        self.dialogue = Dialogue()

        # Biến liên quan đến TTS
        self.sentence_id = None
        # Xử lý phản hồi TTS không có văn bản trả về
        self.tts_MessageText = ""

        # Biến liên quan đến IoT
        self.iot_descriptors = {}
        self.func_handler = None

        self.cmd_exit = self.config["exit_commands"]

        # Có đóng kết nối sau khi chat kết thúc không
        self.close_after_chat = False
        self.load_function_plugin = False
        self.intent_type = "nointent"

        self.timeout_seconds = (
            int(self.config.get("close_connection_no_voice_time", 120)) + 60
        )  # Thêm 60 giây vào lần đóng đầu tiên, thực hiện đóng lần thứ hai
        self.timeout_task = None

        # {"mcp":true} biểu thị bật chức năng MCP
        self.features = None

        # Đánh dấu kết nối có đến từ MQTT không
        self.conn_from_mqtt_gateway = False

        # Khởi tạo trình quản lý prompt
        self.prompt_manager = PromptManager(self.config, self.logger)

    async def handle_connection(self, ws: websockets.ServerConnection):
        try:
            # Lấy event loop đang chạy (phải trong ngữ cảnh async)
            self.loop = asyncio.get_running_loop()

            # Lấy và xác thực headers
            self.headers = dict(ws.request.headers)
            real_ip = self.headers.get("x-real-ip") or self.headers.get(
                "x-forwarded-for"
            )
            if real_ip:
                self.client_ip = real_ip.split(",")[0].strip()
            else:
                self.client_ip = ws.remote_address[0]
            self.logger.bind(tag=TAG).info(
                f"{self.client_ip} conn - Headers: {self.headers}"
            )

            self.device_id = self.headers.get("device-id", None)

            # Xác thực thành công, tiếp tục xử lý
            self.websocket = ws

            # Kiểm tra có đến từ kết nối MQTT không
            request_path = ws.request.path
            self.conn_from_mqtt_gateway = request_path.endswith("?from=mqtt_gateway")
            if self.conn_from_mqtt_gateway:
                self.logger.bind(tag=TAG).info("Kết nối đến từ: Cổng MQTT")

            # Khởi tạo timestamp hoạt động
            self.first_activity_time = time.time() * 1000
            self.last_activity_time = time.time() * 1000

            # Khởi động nhiệm vụ kiểm tra timeout
            self.timeout_task = asyncio.create_task(self._check_timeout())

            self.welcome_msg = self.config["xiaozhi"]
            self.welcome_msg["session_id"] = self.session_id

            # Đọc tần số lấy mẫu từ cấu hình
            self.sample_rate = self.welcome_msg["audio_params"]["sample_rate"]
            self.logger.bind(tag=TAG).info(f"Cấu hình tần số lấy mẫu audio đầu ra: {self.sample_rate}")

            # Khởi tạo cấu hình và component ở background (hoàn toàn không chặn vòng lặp chính)
            asyncio.create_task(self._background_initialize())

            try:
                async for message in self.websocket:
                    await self._route_message(message)
            except websockets.exceptions.ConnectionClosed:
                self.logger.bind(tag=TAG).info("Client ngắt kết nối")

        except AuthenticationError as e:
            self.logger.bind(tag=TAG).error(f"Authentication failed: {str(e)}")
            return
        except Exception as e:
            stack_trace = traceback.format_exc()
            self.logger.bind(tag=TAG).error(f"Connection error: {str(e)}-{stack_trace}")
            return
        finally:
            try:
                await self._save_and_close(ws)
            except Exception as final_error:
                self.logger.bind(tag=TAG).error(f"Lỗi khi dọn dẹp cuối cùng: {final_error}")
                # Đảm bảo ngay cả khi lưu bộ nhớ thất bại, cũng phải đóng kết nối
                try:
                    await self.close(ws)
                except Exception as close_error:
                    self.logger.bind(tag=TAG).error(
                        f"Lỗi khi ép buộc đóng kết nối: {close_error}"
                    )

    async def _save_and_close(self, ws):
        """Lưu bộ nhớ và đóng kết nối"""
        try:
            if self.memory:
                # Sử dụng thread pool để lưu bộ nhớ bất đồng bộ
                def save_memory_task():
                    try:
                        # Tạo event loop mới (tránh xung đột với vòng lặp chính)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            self.memory.save_memory(
                                self.dialogue.dialogue, self.session_id
                            )
                        )
                    except Exception as e:
                        self.logger.bind(tag=TAG).error(f"Lưu bộ nhớ thất bại: {e}")
                    finally:
                        try:
                            loop.close()
                        except Exception:
                            pass

                # Khởi động thread lưu bộ nhớ, không chờ hoàn thành
                threading.Thread(target=save_memory_task, daemon=True).start()
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Lưu bộ nhớ thất bại: {e}")
        finally:
            # Đóng kết nối ngay lập tức, không chờ lưu bộ nhớ hoàn thành
            try:
                await self.close(ws)
            except Exception as close_error:
                self.logger.bind(tag=TAG).error(
                    f"Đóng kết nối sau khi lưu bộ nhớ thất bại: {close_error}"
                )

    async def _discard_message_with_bind_prompt(self):
        """Loại bỏ tin nhắn và kiểm tra có cần phát nhắc nhở ràng buộc không"""
        current_time = time.time()
        # Kiểm tra có cần phát nhắc nhở ràng buộc không
        if current_time - self.last_bind_prompt_time >= self.bind_prompt_interval:
            self.last_bind_prompt_time = current_time
            # Tái sử dụng logic nhắc nhở ràng buộc hiện có
            from core.handle.receiveAudioHandle import check_bind_device

            asyncio.create_task(check_bind_device(self))

    async def _route_message(self, message):
        """Định tuyến tin nhắn"""
        # Kiểm tra đã lấy được trạng thái ràng buộc thực tế chưa
        if not self.bind_completed_event.is_set():
            # Chưa lấy được trạng thái thực tế, chờ cho đến khi lấy được trạng thái thực tế hoặc timeout
            try:
                await asyncio.wait_for(self.bind_completed_event.wait(), timeout=1)
            except asyncio.TimeoutError:
                # Timeout vẫn chưa lấy được trạng thái thực tế, loại bỏ tin nhắn
                await self._discard_message_with_bind_prompt()
                return

        # Đã lấy được trạng thái thực tế, kiểm tra có cần ràng buộc không
        if self.need_bind:
            # Cần ràng buộc, loại bỏ tin nhắn
            await self._discard_message_with_bind_prompt()
            return

        # Không cần ràng buộc, tiếp tục xử lý tin nhắn

        if isinstance(message, str):
            await handleTextMessage(self, message)
        elif isinstance(message, bytes):
            if self.vad is None or self.asr is None:
                return

            # Xử lý gói audio từ cổng MQTT
            if self.conn_from_mqtt_gateway and len(message) >= 16:
                handled = await self._process_mqtt_audio_message(message)
                if handled:
                    return

            # Không cần xử lý header hoặc không có header, xử lý tin nhắn gốc trực tiếp
            self.asr_audio_queue.put(message)

    async def _process_mqtt_audio_message(self, message):
        """
        Xử lý tin nhắn audio từ cổng MQTT, phân tích header 16 byte và trích xuất dữ liệu audio

        Args:
            message: Tin nhắn audio chứa header

        Returns:
            bool: Có xử lý thành công tin nhắn không
        """
        try:
            # Trích xuất thông tin header
            timestamp = int.from_bytes(message[8:12], "big")
            audio_length = int.from_bytes(message[12:16], "big")

            # Trích xuất dữ liệu audio
            if audio_length > 0 and len(message) >= 16 + audio_length:
                # Có độ dài được chỉ định, trích xuất dữ liệu audio chính xác
                audio_data = message[16 : 16 + audio_length]
                # Xử lý sắp xếp dựa trên timestamp
                self._process_websocket_audio(audio_data, timestamp)
                return True
            elif len(message) > 16:
                # Không có độ dài được chỉ định hoặc độ dài không hợp lệ, bỏ header và xử lý dữ liệu còn lại
                audio_data = message[16:]
                self.asr_audio_queue.put(audio_data)
                return True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Phân tích gói WebSocket audio thất bại: {e}")

        # Xử lý thất bại, trả về False biểu thị cần tiếp tục xử lý
        return False

    def _process_websocket_audio(self, audio_data, timestamp):
        """Xử lý gói audio định dạng WebSocket"""
        # Khởi tạo quản lý chuỗi timestamp
        if not hasattr(self, "audio_timestamp_buffer"):
            self.audio_timestamp_buffer = {}
            self.last_processed_timestamp = 0
            self.max_timestamp_buffer_size = 20

        # Nếu timestamp tăng dần, xử lý trực tiếp
        if timestamp >= self.last_processed_timestamp:
            self.asr_audio_queue.put(audio_data)
            self.last_processed_timestamp = timestamp

            # Xử lý các gói tiếp theo trong buffer
            processed_any = True
            while processed_any:
                processed_any = False
                for ts in sorted(self.audio_timestamp_buffer.keys()):
                    if ts > self.last_processed_timestamp:
                        buffered_audio = self.audio_timestamp_buffer.pop(ts)
                        self.asr_audio_queue.put(buffered_audio)
                        self.last_processed_timestamp = ts
                        processed_any = True
                        break
        else:
            # Gói lộn xộn, tạm lưu
            if len(self.audio_timestamp_buffer) < self.max_timestamp_buffer_size:
                self.audio_timestamp_buffer[timestamp] = audio_data
            else:
                self.asr_audio_queue.put(audio_data)

    async def handle_restart(self, message):
        """Xử lý yêu cầu khởi động lại server"""
        try:

            self.logger.bind(tag=TAG).info("Nhận được lệnh khởi động lại server, chuẩn bị thực thi...")

            # Gửi phản hồi xác nhận
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "success",
                        "message": "Server đang khởi động lại...",
                        "content": {"action": "restart"},
                    }
                )
            )

            # Thực thi thao tác khởi động lại bất đồng bộ
            def restart_server():
                """Phương thức thực thi khởi động lại thực tế"""
                time.sleep(1)
                self.logger.bind(tag=TAG).info("Thực thi khởi động lại server...")
                subprocess.Popen(
                    [sys.executable, "app.py"],
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                    start_new_session=True,
                )
                os._exit(0)

            # Sử dụng thread thực thi khởi động lại để tránh chặn event loop
            threading.Thread(target=restart_server, daemon=True).start()

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Khởi động lại thất bại: {str(e)}")
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "error",
                        "message": f"Restart failed: {str(e)}",
                        "content": {"action": "restart"},
                    }
                )
            )

    def _initialize_components(self):
        try:
            if self.tts is None:
                self.tts = self._initialize_tts()
            # Mở kênh tổng hợp giọng nói
            asyncio.run_coroutine_threadsafe(
                self.tts.open_audio_channels(self), self.loop
            )
            if self.need_bind:
                self.bind_completed_event.set()
                return
            self.selected_module_str = build_module_string(
                self.config.get("selected_module", {})
            )
            self.logger = create_connection_logger(self.selected_module_str)

            """Khởi tạo component"""
            if self.config.get("prompt") is not None:
                user_prompt = self.config["prompt"]
                # Sử dụng prompt nhanh để khởi tạo
                prompt = self.prompt_manager.get_quick_prompt(user_prompt)
                self.change_system_prompt(prompt)
                self.logger.bind(tag=TAG).info(
                    f"Khởi tạo component nhanh: prompt thành công {prompt[:50]}..."
                )

            """Khởi tạo component local"""
            if self.vad is None:
                self.vad = self._vad
            if self.asr is None:
                self.asr = self._initialize_asr()

            # Khởi tạo nhận dạng giọng nói
            self._initialize_voiceprint()
            # Mở kênh nhận dạng giọng nói
            asyncio.run_coroutine_threadsafe(
                self.asr.open_audio_channels(self), self.loop
            )

            """Tải bộ nhớ"""
            self._initialize_memory()
            """Tải nhận dạng ý định"""
            self._initialize_intent()
            """Khởi tạo thread báo cáo"""
            self._init_report_threads()
            """Cập nhật prompt hệ thống"""
            self._init_prompt_enhancement()

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Khởi tạo component thất bại: {e}")

    def _init_prompt_enhancement(self):

        # Cập nhật thông tin ngữ cảnh
        self.prompt_manager.update_context_info(self, self.client_ip)
        enhanced_prompt = self.prompt_manager.build_enhanced_prompt(
            self.config["prompt"], self.device_id, self.client_ip
        )
        if enhanced_prompt:
            self.change_system_prompt(enhanced_prompt)
            self.logger.bind(tag=TAG).debug("Prompt hệ thống đã được tăng cường cập nhật")

    def _init_report_threads(self):
        """Khởi tạo thread báo cáo ASR và TTS"""
        if not self.read_config_from_api or self.need_bind:
            return
        if self.chat_history_conf == 0:
            return
        if self.report_thread is None or not self.report_thread.is_alive():
            self.report_thread = threading.Thread(
                target=self._report_worker, daemon=True
            )
            self.report_thread.start()
            self.logger.bind(tag=TAG).info("Thread báo cáo TTS đã khởi động")

    def _initialize_tts(self):
        """Khởi tạo TTS"""
        tts = None
        if not self.need_bind:
            tts = initialize_tts(self.config)

        if tts is None:
            tts = DefaultTTS(self.config, delete_audio_file=True)

        return tts

    def _initialize_asr(self):
        """Khởi tạo ASR"""
        if (
            self._asr is not None
            and hasattr(self._asr, "interface_type")
            and self._asr.interface_type == InterfaceType.LOCAL
        ):
            # Nếu ASR công cộng là dịch vụ local, trả về trực tiếp
            # Vì một instance ASR local có thể được chia sẻ bởi nhiều kết nối
            asr = self._asr
        else:
            # Nếu ASR công cộng là dịch vụ từ xa, khởi tạo một instance mới
            # Vì ASR từ xa liên quan đến kết nối websocket và thread nhận, cần mỗi kết nối một instance
            asr = initialize_asr(self.config)

        return asr

    def _initialize_voiceprint(self):
        """Khởi tạo nhận dạng giọng nói cho kết nối hiện tại"""
        try:
            voiceprint_config = self.config.get("voiceprint", {})
            if voiceprint_config:
                voiceprint_provider = VoiceprintProvider(voiceprint_config)
                if voiceprint_provider is not None and voiceprint_provider.enabled:
                    self.voiceprint_provider = voiceprint_provider
                    self.logger.bind(tag=TAG).info("Chức năng nhận dạng giọng nói đã được bật động khi kết nối")
                else:
                    self.logger.bind(tag=TAG).warning("Chức năng nhận dạng giọng nói được bật nhưng cấu hình không đầy đủ")
            else:
                self.logger.bind(tag=TAG).info("Chức năng nhận dạng giọng nói chưa được bật")
        except Exception as e:
            self.logger.bind(tag=TAG).warning(f"Khởi tạo nhận dạng giọng nói thất bại: {str(e)}")

    async def _background_initialize(self):
        """Khởi tạo cấu hình và component ở background (hoàn toàn không chặn vòng lặp chính)"""
        try:
            # Lấy cấu hình khác biệt bất đồng bộ
            await self._initialize_private_config_async()
            # Khởi tạo component trong thread pool
            self.executor.submit(self._initialize_components)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Khởi tạo background thất bại: {e}")

    async def _initialize_private_config_async(self):
        """Lấy cấu hình khác biệt bất đồng bộ từ interface (phiên bản async, không chặn vòng lặp chính)"""
        if not self.read_config_from_api:
            self.need_bind = False
            self.bind_completed_event.set()
            return
        try:
            begin_time = time.time()
            private_config = await get_private_config_from_api(
                self.config,
                self.headers.get("device-id"),
                self.headers.get("client-id", self.headers.get("device-id")),
            )
            private_config["delete_audio"] = bool(self.config.get("delete_audio", True))
            self.logger.bind(tag=TAG).info(
                f"{time.time() - begin_time} giây, lấy cấu hình khác biệt bất đồng bộ thành công: {json.dumps(filter_sensitive_info(private_config), ensure_ascii=False)}"
            )
            self.need_bind = False
            self.bind_completed_event.set()
        except DeviceNotFoundException as e:
            self.need_bind = True
            private_config = {}
        except DeviceBindException as e:
            self.need_bind = True
            self.bind_code = e.bind_code
            private_config = {}
        except Exception as e:
            self.need_bind = True
            self.logger.bind(tag=TAG).error(f"Lấy cấu hình khác biệt bất đồng bộ thất bại: {e}")
            private_config = {}

        init_llm, init_tts, init_memory, init_intent = (
            False,
            False,
            False,
            False,
        )

        init_vad = check_vad_update(self.common_config, private_config)
        init_asr = check_asr_update(self.common_config, private_config)

        if init_vad:
            self.config["VAD"] = private_config["VAD"]
            self.config["selected_module"]["VAD"] = private_config["selected_module"][
                "VAD"
            ]
        if init_asr:
            self.config["ASR"] = private_config["ASR"]
            self.config["selected_module"]["ASR"] = private_config["selected_module"][
                "ASR"
            ]
        if private_config.get("TTS", None) is not None:
            init_tts = True
            self.config["TTS"] = private_config["TTS"]
            self.config["selected_module"]["TTS"] = private_config["selected_module"][
                "TTS"
            ]
        if private_config.get("LLM", None) is not None:
            init_llm = True
            self.config["LLM"] = private_config["LLM"]
            self.config["selected_module"]["LLM"] = private_config["selected_module"][
                "LLM"
            ]
        if private_config.get("VLLM", None) is not None:
            self.config["VLLM"] = private_config["VLLM"]
            self.config["selected_module"]["VLLM"] = private_config["selected_module"][
                "VLLM"
            ]
        if private_config.get("Memory", None) is not None:
            init_memory = True
            self.config["Memory"] = private_config["Memory"]
            self.config["selected_module"]["Memory"] = private_config[
                "selected_module"
            ]["Memory"]
        if private_config.get("Intent", None) is not None:
            init_intent = True
            self.config["Intent"] = private_config["Intent"]
            model_intent = private_config.get("selected_module", {}).get("Intent", {})
            self.config["selected_module"]["Intent"] = model_intent
            # Tải cấu hình plugin
            if model_intent != "Intent_nointent":
                plugin_from_server = private_config.get("plugins", {})
                for plugin, config_str in plugin_from_server.items():
                    plugin_from_server[plugin] = json.loads(config_str)
                self.config["plugins"] = plugin_from_server
                self.config["Intent"][self.config["selected_module"]["Intent"]][
                    "functions"
                ] = plugin_from_server.keys()
        if private_config.get("prompt", None) is not None:
            self.config["prompt"] = private_config["prompt"]
        # Lấy thông tin nhận dạng giọng nói
        if private_config.get("voiceprint", None) is not None:
            self.config["voiceprint"] = private_config["voiceprint"]
        if private_config.get("summaryMemory", None) is not None:
            self.config["summaryMemory"] = private_config["summaryMemory"]
        if private_config.get("device_max_output_size", None) is not None:
            self.max_output_size = int(private_config["device_max_output_size"])
        if private_config.get("chat_history_conf", None) is not None:
            self.chat_history_conf = int(private_config["chat_history_conf"])
        if private_config.get("mcp_endpoint", None) is not None:
            self.config["mcp_endpoint"] = private_config["mcp_endpoint"]
        if private_config.get("context_providers", None) is not None:
            self.config["context_providers"] = private_config["context_providers"]

        # Sử dụng run_in_executor để thực thi initialize_modules trong thread pool, tránh chặn vòng lặp chính
        try:
            modules = await self.loop.run_in_executor(
                None,  # Sử dụng thread pool mặc định
                initialize_modules,
                self.logger,
                private_config,
                init_vad,
                init_asr,
                init_llm,
                init_tts,
                init_memory,
                init_intent,
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Khởi tạo component thất bại: {e}")
            modules = {}
        if modules.get("tts", None) is not None:
            self.tts = modules["tts"]
        if modules.get("vad", None) is not None:
            self.vad = modules["vad"]
        if modules.get("asr", None) is not None:
            self.asr = modules["asr"]
        if modules.get("llm", None) is not None:
            self.llm = modules["llm"]
        if modules.get("intent", None) is not None:
            self.intent = modules["intent"]
        if modules.get("memory", None) is not None:
            self.memory = modules["memory"]

    def _initialize_memory(self):
        if self.memory is None:
            return
        """Khởi tạo module bộ nhớ"""
        self.memory.init_memory(
            role_id=self.device_id,
            llm=self.llm,
            summary_memory=self.config.get("summaryMemory", None),
            save_to_file=not self.read_config_from_api,
        )

        # Lấy cấu hình tóm tắt bộ nhớ
        memory_config = self.config["Memory"]
        memory_type = self.config["Memory"][self.config["selected_module"]["Memory"]][
            "type"
        ]
        # Nếu sử dụng nomem, trả về trực tiếp
        if memory_type == "nomem":
            return
        # Sử dụng chế độ mem_local_short
        elif memory_type == "mem_local_short":
            memory_llm_name = memory_config[self.config["selected_module"]["Memory"]][
                "llm"
            ]
            if memory_llm_name and memory_llm_name in self.config["LLM"]:
                # Nếu đã cấu hình LLM chuyên dụng, tạo instance LLM độc lập
                from core.utils import llm as llm_utils

                memory_llm_config = self.config["LLM"][memory_llm_name]
                memory_llm_type = memory_llm_config.get("type", memory_llm_name)
                memory_llm = llm_utils.create_instance(
                    memory_llm_type, memory_llm_config
                )
                self.logger.bind(tag=TAG).info(
                    f"Đã tạo LLM chuyên dụng cho tóm tắt bộ nhớ: {memory_llm_name}, loại: {memory_llm_type}"
                )
                self.memory.set_llm(memory_llm)
            else:
                # Ngược lại sử dụng LLM chính
                self.memory.set_llm(self.llm)
                self.logger.bind(tag=TAG).info("Sử dụng LLM chính làm mô hình nhận dạng ý định")

    def _initialize_intent(self):
        if self.intent is None:
            return
        self.intent_type = self.config["Intent"][
            self.config["selected_module"]["Intent"]
        ]["type"]
        if self.intent_type == "function_call" or self.intent_type == "intent_llm":
            self.load_function_plugin = True
        """Khởi tạo module nhận dạng ý định"""
        # Lấy cấu hình nhận dạng ý định
        intent_config = self.config["Intent"]
        intent_type = self.config["Intent"][self.config["selected_module"]["Intent"]][
            "type"
        ]

        # Nếu sử dụng nointent, trả về trực tiếp
        if intent_type == "nointent":
            return
        # Sử dụng chế độ intent_llm
        elif intent_type == "intent_llm":
            intent_llm_name = intent_config[self.config["selected_module"]["Intent"]][
                "llm"
            ]

            if intent_llm_name and intent_llm_name in self.config["LLM"]:
                # Nếu đã cấu hình LLM chuyên dụng, tạo instance LLM độc lập
                from core.utils import llm as llm_utils

                intent_llm_config = self.config["LLM"][intent_llm_name]
                intent_llm_type = intent_llm_config.get("type", intent_llm_name)
                intent_llm = llm_utils.create_instance(
                    intent_llm_type, intent_llm_config
                )
                self.logger.bind(tag=TAG).info(
                    f"Đã tạo LLM chuyên dụng cho nhận dạng ý định: {intent_llm_name}, loại: {intent_llm_type}"
                )
                self.intent.set_llm(intent_llm)
            else:
                # Ngược lại sử dụng LLM chính
                self.intent.set_llm(self.llm)
                self.logger.bind(tag=TAG).info("Sử dụng LLM chính làm mô hình nhận dạng ý định")

        """Tải trình xử lý công cụ thống nhất"""
        self.func_handler = UnifiedToolHandler(self)

        # Khởi tạo trình xử lý công cụ bất đồng bộ
        if hasattr(self, "loop") and self.loop:
            asyncio.run_coroutine_threadsafe(self.func_handler._initialize(), self.loop)

    def change_system_prompt(self, prompt):
        self.prompt = prompt
        # Cập nhật prompt hệ thống vào ngữ cảnh
        self.dialogue.update_system_message(self.prompt)

    def chat(self, query, depth=0):
        if query is not None:
            self.logger.bind(tag=TAG).info(f"Mô hình lớn nhận được tin nhắn người dùng: {query}")

        # Khi ở tầng trên cùng, tạo session ID mới và gửi yêu cầu FIRST
        if depth == 0:
            self.sentence_id = str(uuid.uuid4().hex)
            self.dialogue.put(Message(role="user", content=query))
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.FIRST,
                    content_type=ContentType.ACTION,
                )
            )

        # Thiết lập độ sâu đệ quy tối đa, tránh vòng lặp vô hạn, có thể điều chỉnh theo nhu cầu thực tế
        MAX_DEPTH = 5
        force_final_answer = False  # Đánh dấu có ép buộc trả lời cuối cùng không

        if depth >= MAX_DEPTH:
            self.logger.bind(tag=TAG).debug(
                f"Đã đạt độ sâu gọi công cụ tối đa {MAX_DEPTH}, sẽ ép buộc trả lời dựa trên thông tin hiện có"
            )
            force_final_answer = True
            # Thêm lệnh hệ thống, yêu cầu LLM trả lời dựa trên thông tin hiện có
            self.dialogue.put(
                Message(
                    role="user",
                    content="[Gợi ý hệ thống] Đã đạt giới hạn số lần gọi công cụ tối đa, bạn hãy dựa trên tất cả thông tin đã lấy được hiện tại, đưa ra câu trả lời cuối cùng trực tiếp. Không thử gọi bất kỳ công cụ nào nữa.",
                )
            )

        # Define intent functions
        functions = None
        # Khi đạt độ sâu tối đa, vô hiệu hóa gọi công cụ, ép buộc LLM trả lời trực tiếp
        if (
            self.intent_type == "function_call"
            and hasattr(self, "func_handler")
            and not force_final_answer
        ):
            functions = self.func_handler.get_functions()
        response_message = []

        try:
            # Sử dụng cuộc trò chuyện có bộ nhớ
            memory_str = None
            # Chỉ truy vấn bộ nhớ khi query không rỗng (đại diện cho câu hỏi của người dùng)
            if self.memory is not None and query:
                future = asyncio.run_coroutine_threadsafe(
                    self.memory.query_memory(query), self.loop
                )
                memory_str = future.result()

            if self.intent_type == "function_call" and functions is not None:
                # Sử dụng interface streaming hỗ trợ functions
                llm_responses = self.llm.response_with_functions(
                    self.session_id,
                    self.dialogue.get_llm_dialogue_with_memory(
                        memory_str, self.config.get("voiceprint", {})
                    ),
                    functions=functions,
                )
                self.logger.bind(tag=TAG).debug("Sử dụng LLM với function calling")
            else:
                llm_responses = self.llm.response(
                    self.session_id,
                    self.dialogue.get_llm_dialogue_with_memory(
                        memory_str, self.config.get("voiceprint", {})
                    ),
                )
                self.logger.bind(tag=TAG).debug("Sử dụng LLM response thông thường")
        except Exception as e:
            # Xử lý exception message an toàn với Unicode
            try:
                error_msg = str(e)
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                else:
                    error_msg = str(error_msg).encode('utf-8', errors='replace').decode('utf-8')
            except Exception:
                error_msg = repr(e)
            try:
                query_safe = str(query).encode('utf-8', errors='replace').decode('utf-8') if query else "None"
                log_msg = f"LLM xử lý lỗi {query_safe}: {error_msg}"
                log_msg.encode('utf-8')
                self.logger.bind(tag=TAG).error(log_msg)
            except (UnicodeEncodeError, UnicodeDecodeError):
                self.logger.bind(tag=TAG).error(f"LLM xử lý lỗi: {repr(error_msg)}")
            return None

        # Xử lý phản hồi streaming
        tool_call_flag = False
        # Hỗ trợ nhiều gọi công cụ song song - sử dụng danh sách lưu trữ
        tool_calls_list = []  # Định dạng: [{"id": "", "name": "", "arguments": ""}]
        content_arguments = ""
        self.client_abort = False
        emotion_flag = True
        response_received = False  # Đánh dấu đã nhận được phản hồi từ LLM
        try:
            for response in llm_responses:
                response_received = True
                if self.client_abort:
                    break
                if self.intent_type == "function_call" and functions is not None:
                    content, tools_call = response
                    if "content" in response:
                        content = response["content"]
                        tools_call = None
                    # Đảm bảo content là string và hỗ trợ Unicode
                    if content is not None:
                        if not isinstance(content, str):
                            content = str(content)
                        # Đảm bảo content có thể xử lý Unicode
                        try:
                            content.encode('utf-8')
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            # Nếu có lỗi encoding, bỏ qua content này
                            content = None
                    if content is not None and len(content) > 0:
                        content_arguments += content

                    if not tool_call_flag and content_arguments.startswith("<tool_call>"):
                        # print("content_arguments", content_arguments)
                        tool_call_flag = True

                    if tools_call is not None and len(tools_call) > 0:
                        tool_call_flag = True
                        self._merge_tool_calls(tool_calls_list, tools_call)
                else:
                    content = response
                    # Đảm bảo content là string và hỗ trợ Unicode
                    if content is not None:
                        if not isinstance(content, str):
                            content = str(content)
                        # Đảm bảo content có thể xử lý Unicode
                        try:
                            content.encode('utf-8')
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            # Nếu có lỗi encoding, bỏ qua content này
                            content = None

                # Lấy biểu cảm cảm xúc trong phản hồi llm, một vòng trò chuyện chỉ lấy một lần ở đầu
                if emotion_flag and content is not None and content.strip():
                    try:
                        asyncio.run_coroutine_threadsafe(
                            textUtils.get_emotion(self, content),
                            self.loop,
                        )
                    except Exception as emotion_error:
                        # Bỏ qua lỗi emotion, không ảnh hưởng đến luồng chính
                        self.logger.bind(tag=TAG).debug(f"Lỗi xử lý emotion: {emotion_error}")
                    emotion_flag = False

                if content is not None and len(content) > 0:
                    if not tool_call_flag:
                        response_message.append(content)
                        self.tts.tts_text_queue.put(
                            TTSMessageDTO(
                                sentence_id=self.sentence_id,
                                sentence_type=SentenceType.MIDDLE,
                                content_type=ContentType.TEXT,
                                content_detail=content,
                            )
                        )
            
            # Log số lượng phản hồi đã nhận được
            if response_received:
                self.logger.bind(tag=TAG).debug(
                    f"Đã nhận {len(response_message)} đoạn phản hồi từ LLM, "
                    f"tổng độ dài: {sum(len(m) for m in response_message)} ký tự"
                )
        except Exception as e:
            # Xử lý exception message an toàn với Unicode
            try:
                error_msg = str(e)
                # Đảm bảo error message có thể được encode thành UTF-8
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                else:
                    # Chuyển đổi sang string và đảm bảo encoding UTF-8
                    error_msg = str(error_msg).encode('utf-8', errors='replace').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError) as encoding_err:
                # Nếu có lỗi encoding, sử dụng repr để tránh lỗi
                try:
                    error_msg = repr(e)
                except Exception:
                    error_msg = "Lỗi xử lý Unicode trong exception message"
            except Exception:
                # Nếu vẫn lỗi, sử dụng fallback
                error_msg = "Lỗi không xác định khi xử lý exception"
            
            # Đảm bảo log message cũng được xử lý an toàn
            try:
                log_msg = f"LLM stream processing error: {error_msg}"
                # Kiểm tra xem log message có thể encode được không
                log_msg.encode('utf-8')
                self.logger.bind(tag=TAG).error(log_msg)
            except (UnicodeEncodeError, UnicodeDecodeError):
                # Nếu vẫn lỗi, sử dụng ASCII-safe message
                self.logger.bind(tag=TAG).error(f"LLM stream processing error: {repr(error_msg)}")
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.MIDDLE,
                    content_type=ContentType.TEXT,
                    content_detail=get_system_error_response(self.config),
                )
            )
            if depth == 0:
                self.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=self.sentence_id,
                        sentence_type=SentenceType.LAST,
                        content_type=ContentType.ACTION,
                    )
                )
            return
        
        # Kiểm tra xem LLM có trả về phản hồi không
        if not response_received:
            self.logger.bind(tag=TAG).warning(
                f"LLM không trả về phản hồi nào cho tin nhắn: {query}"
            )
            # Gửi phản hồi lỗi mặc định
            error_response = get_system_error_response(self.config)
            if error_response:
                self.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=self.sentence_id,
                        sentence_type=SentenceType.MIDDLE,
                        content_type=ContentType.TEXT,
                        content_detail=error_response,
                    )
                )
            if depth == 0:
                self.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=self.sentence_id,
                        sentence_type=SentenceType.LAST,
                        content_type=ContentType.ACTION,
                    )
                )
            return None
        
        # Xử lý function call
        if tool_call_flag:
            bHasError = False
            # Xử lý định dạng gọi công cụ dựa trên văn bản
            if len(tool_calls_list) == 0 and content_arguments:
                a = extract_json_from_string(content_arguments)
                if a is not None:
                    try:
                        content_arguments_json = json.loads(a)
                        tool_calls_list.append(
                            {
                                "id": str(uuid.uuid4().hex),
                                "name": content_arguments_json["name"],
                                "arguments": json.dumps(
                                    content_arguments_json["arguments"],
                                    ensure_ascii=False,
                                ),
                            }
                        )
                    except Exception as e:
                        bHasError = True
                        response_message.append(a)
                else:
                    bHasError = True
                    response_message.append(content_arguments)
                if bHasError:
                    self.logger.bind(tag=TAG).error(
                        f"function call error: {content_arguments}"
                    )

            if not bHasError and len(tool_calls_list) > 0:
                # Nếu cần mô hình lớn xử lý một vòng trước, thêm tình huống log sau khi xử lý liên quan
                if len(response_message) > 0:
                    text_buff = "".join(response_message)
                    self.tts_MessageText = text_buff
                    self.dialogue.put(Message(role="assistant", content=text_buff))
                response_message.clear()

                self.logger.bind(tag=TAG).debug(
                    f"Phát hiện {len(tool_calls_list)} lần gọi công cụ"
                )

                # Thu thập tất cả Future của gọi công cụ
                futures_with_data = []
                for tool_call_data in tool_calls_list:
                    self.logger.bind(tag=TAG).debug(
                        f"function_name={tool_call_data['name']}, function_id={tool_call_data['id']}, function_arguments={tool_call_data['arguments']}"
                    )

                    future = asyncio.run_coroutine_threadsafe(
                        self.func_handler.handle_llm_function_call(
                            self, tool_call_data
                        ),
                        self.loop,
                    )
                    futures_with_data.append((future, tool_call_data))

                # Chờ coroutine kết thúc (thời gian chờ thực tế là của cái chậm nhất)
                tool_results = []
                for future, tool_call_data in futures_with_data:
                    result = future.result()
                    tool_results.append((result, tool_call_data))

                # Xử lý thống nhất tất cả kết quả gọi công cụ
                if tool_results:
                    self._handle_function_result(tool_results, depth=depth)

        # Lưu trữ nội dung cuộc trò chuyện
        if len(response_message) > 0:
            text_buff = "".join(response_message)
            self.tts_MessageText = text_buff
            self.dialogue.put(Message(role="assistant", content=text_buff))
        else:
            # Cảnh báo khi không có nội dung phản hồi
            if not tool_call_flag:
                self.logger.bind(tag=TAG).warning(
                    f"LLM trả về phản hồi rỗng cho tin nhắn: {query}. "
                    f"response_received={response_received}, tool_call_flag={tool_call_flag}"
                )
        if depth == 0:
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.LAST,
                    content_type=ContentType.ACTION,
                )
            )
            # Sử dụng lambda tính toán trễ, chỉ thực thi get_llm_dialogue() ở mức DEBUG
            self.logger.bind(tag=TAG).debug(
                lambda: json.dumps(
                    self.dialogue.get_llm_dialogue(), indent=4, ensure_ascii=False
                )
            )

        return True

    def _handle_function_result(self, tool_results, depth):
        need_llm_tools = []

        for result, tool_call_data in tool_results:
            if result.action in [
                Action.RESPONSE,
                Action.NOTFOUND,
                Action.ERROR,
            ]:  # 直接回复前端
                text = result.response if result.response else result.result
                self.tts.tts_one_sentence(self, ContentType.TEXT, content_detail=text)
                self.dialogue.put(Message(role="assistant", content=text))
            elif result.action == Action.REQLLM:
                # 收集需要 LLM 处理的工具
                need_llm_tools.append((result, tool_call_data))
            else:
                pass

        if need_llm_tools:
            all_tool_calls = [
                {
                    "id": tool_call_data["id"],
                    "function": {
                        "arguments": (
                            "{}"
                            if tool_call_data["arguments"] == ""
                            else tool_call_data["arguments"]
                        ),
                        "name": tool_call_data["name"],
                    },
                    "type": "function",
                    "index": idx,
                }
                for idx, (_, tool_call_data) in enumerate(need_llm_tools)
            ]
            self.dialogue.put(Message(role="assistant", tool_calls=all_tool_calls))

            for result, tool_call_data in need_llm_tools:
                text = result.result
                if text is not None and len(text) > 0:
                    self.dialogue.put(
                        Message(
                            role="tool",
                            tool_call_id=(
                                str(uuid.uuid4())
                                if tool_call_data["id"] is None
                                else tool_call_data["id"]
                            ),
                            content=text,
                        )
                    )

            self.chat(None, depth=depth + 1)

    def _report_worker(self):
        """聊天记录上报工作线程"""
        while not self.stop_event.is_set():
            try:
                # 从队列获取数据，设置超时以便定期检查停止事件
                item = self.report_queue.get(timeout=1)
                if item is None:  # 检测毒丸对象
                    break
                try:
                    # 检查线程池状态
                    if self.executor is None:
                        continue
                    # 提交任务到线程池
                    self.executor.submit(self._process_report, *item)
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"聊天记录上报线程异常: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"聊天记录上报工作线程异常: {e}")

        self.logger.bind(tag=TAG).info("聊天记录上报线程已退出")

    def _process_report(self, type, text, audio_data, report_time):
        """处理上报任务"""
        try:
            # 执行异步上报（在事件循环中运行）
            asyncio.run(report(self, type, text, audio_data, report_time))
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"上报处理异常: {e}")
        finally:
            # 标记任务完成
            self.report_queue.task_done()

    def clearSpeakStatus(self):
        self.client_is_speaking = False
        self.logger.bind(tag=TAG).debug(f"清除服务端讲话状态")

    async def close(self, ws=None):
        """资源清理方法"""
        try:
            # 清理音频缓冲区
            if hasattr(self, "audio_buffer"):
                self.audio_buffer.clear()

            # 取消超时任务
            if self.timeout_task and not self.timeout_task.done():
                self.timeout_task.cancel()
                try:
                    await self.timeout_task
                except asyncio.CancelledError:
                    pass
                self.timeout_task = None

            # 清理工具处理器资源
            if hasattr(self, "func_handler") and self.func_handler:
                try:
                    await self.func_handler.cleanup()
                except Exception as cleanup_error:
                    self.logger.bind(tag=TAG).error(
                        f"清理工具处理器时出错: {cleanup_error}"
                    )

            # 触发停止事件
            if self.stop_event:
                self.stop_event.set()

            # 清空任务队列
            self.clear_queues()

            # 关闭WebSocket连接
            try:
                if ws:
                    # 安全地检查WebSocket状态并关闭
                    try:
                        if hasattr(ws, "closed") and not ws.closed:
                            await ws.close()
                        elif hasattr(ws, "state") and ws.state.name != "CLOSED":
                            await ws.close()
                        else:
                            # 如果没有closed属性，直接尝试关闭
                            await ws.close()
                    except Exception:
                        # 如果关闭失败，忽略错误
                        pass
                elif self.websocket:
                    try:
                        if (
                            hasattr(self.websocket, "closed")
                            and not self.websocket.closed
                        ):
                            await self.websocket.close()
                        elif (
                            hasattr(self.websocket, "state")
                            and self.websocket.state.name != "CLOSED"
                        ):
                            await self.websocket.close()
                        else:
                            # 如果没有closed属性，直接尝试关闭
                            await self.websocket.close()
                    except Exception:
                        # 如果关闭失败，忽略错误
                        pass
            except Exception as ws_error:
                self.logger.bind(tag=TAG).error(f"关闭WebSocket连接时出错: {ws_error}")

            if self.tts:
                await self.tts.close()
            if self.asr:
                await self.asr.close()

            # 最后关闭线程池（避免阻塞）
            if self.executor:
                try:
                    self.executor.shutdown(wait=False)
                except Exception as executor_error:
                    self.logger.bind(tag=TAG).error(
                        f"关闭线程池时出错: {executor_error}"
                    )
                self.executor = None
            self.logger.bind(tag=TAG).info("连接资源已释放")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"关闭连接时出错: {e}")
        finally:
            # 确保停止事件被设置
            if self.stop_event:
                self.stop_event.set()

    def clear_queues(self):
        """清空所有任务队列"""
        if self.tts:
            self.logger.bind(tag=TAG).debug(
                f"开始清理: TTS队列大小={self.tts.tts_text_queue.qsize()}, 音频队列大小={self.tts.tts_audio_queue.qsize()}"
            )

            # 使用非阻塞方式清空队列
            for q in [
                self.tts.tts_text_queue,
                self.tts.tts_audio_queue,
                self.report_queue,
            ]:
                if not q:
                    continue
                while True:
                    try:
                        q.get_nowait()
                    except queue.Empty:
                        break

            # 重置音频流控器（取消后台任务并清空队列）
            if hasattr(self, "audio_rate_controller") and self.audio_rate_controller:
                self.audio_rate_controller.reset()
                self.logger.bind(tag=TAG).debug("已重置音频流控器")

            self.logger.bind(tag=TAG).debug(
                f"清理结束: TTS队列大小={self.tts.tts_text_queue.qsize()}, 音频队列大小={self.tts.tts_audio_queue.qsize()}"
            )

    def reset_audio_states(self):
        """
        重置所有音频相关状态(VAD + ASR)
        """
        # Reset VAD states
        self.client_audio_buffer.clear()
        self.client_have_voice = False
        self.client_voice_stop = False
        self.client_voice_window.clear()
        self.last_is_voice = False

        # Clear ASR buffers
        self.asr_audio.clear()

        self.logger.bind(tag=TAG).debug("All audio states reset.")

    def chat_and_close(self, text):
        """Chat with the user and then close the connection"""
        try:
            # Use the existing chat method
            self.chat(text)

            # After chat is complete, close the connection
            self.close_after_chat = True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Chat and close error: {str(e)}")

    async def _check_timeout(self):
        """检查连接超时"""
        try:
            while not self.stop_event.is_set():
                last_activity_time = self.last_activity_time
                if self.need_bind:
                    last_activity_time = self.first_activity_time

                # 检查是否超时（只有在时间戳已初始化的情况下）
                if last_activity_time > 0.0:
                    current_time = time.time() * 1000
                    if current_time - last_activity_time > self.timeout_seconds * 1000:
                        if not self.stop_event.is_set():
                            self.logger.bind(tag=TAG).info("连接超时，准备关闭")
                            # 设置停止事件，防止重复处理
                            self.stop_event.set()
                            # 使用 try-except 包装关闭操作，确保不会因为异常而阻塞
                            try:
                                await self.close(self.websocket)
                            except Exception as close_error:
                                self.logger.bind(tag=TAG).error(
                                    f"超时关闭连接时出错: {close_error}"
                                )
                        break
                # 每10秒检查一次，避免过于频繁
                await asyncio.sleep(10)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"超时检查任务出错: {e}")
        finally:
            self.logger.bind(tag=TAG).info("超时检查任务已退出")

    def _merge_tool_calls(self, tool_calls_list, tools_call):
        """合并工具调用列表

        Args:
            tool_calls_list: 已收集的工具调用列表
            tools_call: 新的工具调用
        """
        for tool_call in tools_call:
            tool_index = getattr(tool_call, "index", None)
            if tool_index is None:
                if tool_call.function.name:
                    # 有 function_name，说明是新的工具调用
                    tool_index = len(tool_calls_list)
                else:
                    tool_index = len(tool_calls_list) - 1 if tool_calls_list else 0

            # 确保列表有足够的位置
            if tool_index >= len(tool_calls_list):
                tool_calls_list.append({"id": "", "name": "", "arguments": ""})

            # 更新工具调用信息
            if tool_call.id:
                tool_calls_list[tool_index]["id"] = tool_call.id
            if tool_call.function.name:
                tool_calls_list[tool_index]["name"] = tool_call.function.name
            if tool_call.function.arguments:
                tool_calls_list[tool_index]["arguments"] += tool_call.function.arguments
