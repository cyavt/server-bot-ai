from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from ..base import IntentProviderBase
from plugins_func.functions.play_music import initialize_music_handler
from config.logger import setup_logging
from core.utils.util import get_system_error_response
import re
import json
import hashlib
import time



TAG = __name__
logger = setup_logging()


class IntentProvider(IntentProviderBase):
    def __init__(self, config):
        super().__init__(config)
        self.llm = None
        self.promot = ""
        # Import trình quản lý cache toàn cục
        from core.utils.cache.manager import cache_manager, CacheType

        self.cache_manager = cache_manager
        self.CacheType = CacheType
        self.history_count = 4  # Mặc định sử dụng 4 bản ghi hội thoại gần nhất

    def get_intent_system_prompt(self, functions_list: str) -> str:
        """
        Tạo prompt hệ thống động dựa trên các tùy chọn ý định được cấu hình và các hàm khả dụng
        Args:
            functions: Danh sách hàm khả dụng, chuỗi định dạng JSON
        Returns:
            Prompt hệ thống đã được định dạng
        """

        # Xây dựng phần mô tả hàm
        functions_desc = "Danh sách hàm khả dụng:\n"
        for func in functions_list:
            func_info = func.get("function", {})
            name = func_info.get("name", "")
            desc = func_info.get("description", "")
            params = func_info.get("parameters", {})

            functions_desc += f"\nTên hàm: {name}\n"
            functions_desc += f"Mô tả: {desc}\n"

            if params:
                functions_desc += "Tham số:\n"
                for param_name, param_info in params.get("properties", {}).items():
                    param_desc = param_info.get("description", "")
                    param_type = param_info.get("type", "")
                    functions_desc += f"- {param_name} ({param_type}): {param_desc}\n"

            functions_desc += "---\n"

        prompt = (
            "【Yêu cầu định dạng nghiêm ngặt】Bạn PHẢI chỉ trả về định dạng JSON, TUYỆT ĐỐI KHÔNG được trả về bất kỳ ngôn ngữ tự nhiên nào!\n\n"
            "Bạn là trợ lý nhận dạng ý định. Vui lòng phân tích câu cuối cùng của người dùng, xác định ý định của người dùng và gọi hàm tương ứng.\n\n"
            "【Quy tắc quan trọng】Các loại truy vấn sau đây vui lòng trả về result_for_context trực tiếp, không cần gọi hàm:\n"
            "- Hỏi thời gian hiện tại (ví dụ: bây giờ mấy giờ, thời gian hiện tại, truy vấn thời gian, v.v.)\n"
            "- Hỏi ngày hôm nay (ví dụ: hôm nay ngày mấy, hôm nay thứ mấy, hôm nay là ngày gì, v.v.)\n"
            "- Hỏi âm lịch hôm nay (ví dụ: hôm nay âm lịch ngày mấy, hôm nay tiết khí gì, v.v.)\n"
            "- Hỏi thành phố hiện tại (ví dụ: tôi đang ở đâu, bạn biết tôi ở thành phố nào không, v.v.)"
            "Hệ thống sẽ tự động xây dựng câu trả lời dựa trên thông tin ngữ cảnh.\n\n"
            "- Nếu người dùng sử dụng từ nghi vấn (như 'làm sao', 'tại sao', 'như thế nào') để hỏi về vấn đề liên quan đến thoát (ví dụ 'làm sao thoát?'), lưu ý đây không phải là yêu cầu bạn thoát, vui lòng trả về {'function_call': {'name': 'continue_chat'}\n"
            "- Chỉ khi người dùng sử dụng rõ ràng các lệnh như 'thoát hệ thống', 'kết thúc cuộc trò chuyện', 'tôi không muốn nói chuyện với bạn nữa', mới kích hoạt handle_exit_intent\n\n"
            f"{functions_desc}\n"
            "Các bước xử lý:\n"
            "1. Phân tích đầu vào của người dùng, xác định ý định của người dùng\n"
            "2. Kiểm tra xem có phải là truy vấn thông tin cơ bản ở trên (thời gian, ngày tháng, v.v.) không, nếu có thì trả về result_for_context\n"
            "3. Chọn hàm phù hợp nhất từ danh sách hàm khả dụng\n"
            "4. Nếu tìm thấy hàm phù hợp, tạo định dạng function_call tương ứng\n"
            '5. Nếu không tìm thấy hàm phù hợp, trả về {"function_call": {"name": "continue_chat"}}\n\n'
            "Yêu cầu định dạng trả về:\n"
            "1. Phải trả về định dạng JSON thuần, không chứa bất kỳ văn bản nào khác\n"
            "2. Phải chứa trường function_call\n"
            "3. function_call phải chứa trường name\n"
            "4. Nếu hàm cần tham số, phải chứa trường arguments\n\n"
            "Ví dụ:\n"
            "```\n"
            "Người dùng: Bây giờ mấy giờ?\n"
            'Trả về: {"function_call": {"name": "result_for_context"}}\n'
            "```\n"
            "```\n"
            "Người dùng: Pin hiện tại là bao nhiêu?\n"
            'Trả về: {"function_call": {"name": "get_battery_level", "arguments": {"response_success": "Pin hiện tại là {value}%", "response_failure": "Không thể lấy phần trăm pin hiện tại của Battery"}}}\n'
            "```\n"
            "```\n"
            "Người dùng: Độ sáng màn hình hiện tại là bao nhiêu?\n"
            'Trả về: {"function_call": {"name": "self_screen_get_brightness"}}\n'
            "```\n"
            "```\n"
            "Người dùng: Đặt độ sáng màn hình thành 50%\n"
            'Trả về: {"function_call": {"name": "self_screen_set_brightness", "arguments": {"brightness": 50}}}\n'
            "```\n"
            "```\n"
            "Người dùng: Tôi muốn kết thúc cuộc trò chuyện\n"
            'Trả về: {"function_call": {"name": "handle_exit_intent", "arguments": {"say_goodbye": "goodbye"}}}\n'
            "```\n"
            "```\n"
            "Người dùng: Chào bạn\n"
            'Trả về: {"function_call": {"name": "continue_chat"}}\n'
            "```\n\n"
            "Lưu ý:\n"
            "1. Chỉ trả về định dạng JSON, không chứa bất kỳ văn bản nào khác\n"
            '2. Ưu tiên kiểm tra xem truy vấn của người dùng có phải là thông tin cơ bản (thời gian, ngày tháng, v.v.) không, nếu có thì trả về {"function_call": {"name": "result_for_context"}}, không cần tham số arguments\n'
            '3. Nếu không tìm thấy hàm phù hợp, trả về {"function_call": {"name": "continue_chat"}}\n'
            "4. Đảm bảo định dạng JSON trả về đúng, chứa tất cả các trường cần thiết\n"
            "5. result_for_context không cần bất kỳ tham số nào, hệ thống sẽ tự động lấy thông tin từ ngữ cảnh\n"
            "Lưu ý đặc biệt:\n"
            "- Khi người dùng nhập một lần chứa nhiều lệnh (ví dụ 'bật đèn và tăng âm lượng')\n"
            "- Vui lòng trả về mảng JSON gồm nhiều function_call\n"
            "- Ví dụ: {'function_calls': [{name:'light_on'}, {name:'volume_up'}]}\n\n"
            "【Cảnh báo cuối cùng】TUYỆT ĐỐI CẤM xuất bất kỳ ngôn ngữ tự nhiên, biểu tượng cảm xúc hoặc văn bản giải thích nào! CHỈ được xuất định dạng JSON hợp lệ! Vi phạm quy tắc này sẽ dẫn đến lỗi hệ thống!"
        )
        return prompt

    def replyResult(self, text: str, original_text: str):
        try:
            llm_result = self.llm.response_no_stream(
                system_prompt=text,
                user_prompt="Vui lòng dựa trên nội dung trên, trả lời người dùng bằng giọng điệu như con người, yêu cầu ngắn gọn, vui lòng trả về kết quả trực tiếp. Người dùng hiện tại nói: "
                + original_text,
            )
            return llm_result
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in generating reply result: {e}")
            return get_system_error_response(self.config)

    async def detect_intent(
        self, conn: "ConnectionHandler", dialogue_history: List[Dict], text: str
    ) -> str:
        if not self.llm:
            raise ValueError("LLM provider not set")
        if conn.func_handler is None:
            return '{"function_call": {"name": "continue_chat"}}'

        # Ghi lại thời gian bắt đầu tổng thể
        total_start_time = time.time()

        # In thông tin model đang sử dụng
        model_info = getattr(self.llm, "model_name", str(self.llm.__class__.__name__))
        logger.bind(tag=TAG).debug(f"Sử dụng model nhận dạng ý định: {model_info}")

        # Tính khóa cache
        cache_key = hashlib.md5((conn.device_id + text).encode()).hexdigest()

        # Kiểm tra cache
        cached_intent = self.cache_manager.get(self.CacheType.INTENT, cache_key)
        if cached_intent is not None:
            cache_time = time.time() - total_start_time
            logger.bind(tag=TAG).debug(
                f"Sử dụng ý định đã cache: {cache_key} -> {cached_intent}, thời gian: {cache_time:.4f} giây"
            )
            return cached_intent

        if self.promot == "":
            functions = conn.func_handler.get_functions()
            if hasattr(conn, "mcp_client"):
                mcp_tools = conn.mcp_client.get_available_tools()
                if mcp_tools is not None and len(mcp_tools) > 0:
                    if functions is None:
                        functions = []
                    functions.extend(mcp_tools)

            self.promot = self.get_intent_system_prompt(functions)

        music_config = initialize_music_handler(conn)
        music_file_names = music_config["music_file_names"]
        prompt_music = f"{self.promot}\n<musicNames>{music_file_names}\n</musicNames>"

        home_assistant_cfg = conn.config["plugins"].get("home_assistant")
        if home_assistant_cfg:
            devices = home_assistant_cfg.get("devices", [])
        else:
            devices = []
        if len(devices) > 0:
            hass_prompt = "\nDưới đây là danh sách thiết bị thông minh của tôi (vị trí, tên thiết bị, entity_id), có thể điều khiển qua homeassistant\n"
            for device in devices:
                hass_prompt += device + "\n"
            prompt_music += hass_prompt

        logger.bind(tag=TAG).debug(f"User prompt: {prompt_music}")

        # Xây dựng prompt lịch sử hội thoại người dùng
        msgStr = ""

        # Lấy lịch sử hội thoại gần nhất
        start_idx = max(0, len(dialogue_history) - self.history_count)
        for i in range(start_idx, len(dialogue_history)):
            msgStr += f"{dialogue_history[i].role}: {dialogue_history[i].content}\n"

        msgStr += f"User: {text}\n"
        user_prompt = f"current dialogue:\n{msgStr}"

        # Ghi lại thời gian hoàn thành tiền xử lý
        preprocess_time = time.time() - total_start_time
        logger.bind(tag=TAG).debug(f"Thời gian tiền xử lý nhận dạng ý định: {preprocess_time:.4f} giây")

        # Sử dụng LLM để nhận dạng ý định
        llm_start_time = time.time()
        logger.bind(tag=TAG).debug(f"Bắt đầu gọi LLM nhận dạng ý định, model: {model_info}")

        try:
            intent = self.llm.response_no_stream(
                system_prompt=prompt_music, user_prompt=user_prompt
            )
        except Exception as e:
            # Xử lý exception message an toàn với Unicode
            try:
                error_msg = str(e)
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                else:
                    error_msg = str(error_msg).encode('utf-8', errors='replace').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                error_msg = repr(e)
            except Exception:
                error_msg = "Lỗi không xác định khi nhận dạng ý định"
            
            try:
                log_msg = f"Error in intent detection LLM call: {error_msg}"
                log_msg.encode('utf-8')
                logger.bind(tag=TAG).error(log_msg)
            except (UnicodeEncodeError, UnicodeDecodeError):
                logger.bind(tag=TAG).error(f"Error in intent detection LLM call: {repr(error_msg)}")
            return '{"function_call": {"name": "continue_chat"}}'

        # Ghi lại thời gian hoàn thành gọi LLM
        llm_time = time.time() - llm_start_time
        logger.bind(tag=TAG).debug(
            f"Hoàn thành nhận dạng ý định bằng model lớn ngoài, model: {model_info}, thời gian gọi: {llm_time:.4f} giây"
        )

        # Ghi lại thời gian bắt đầu hậu xử lý
        postprocess_start_time = time.time()

        # Làm sạch và phân tích phản hồi
        intent = intent.strip()
        # Thử trích xuất phần JSON
        match = re.search(r"\{.*\}", intent, re.DOTALL)
        if match:
            intent = match.group(0)

        # Ghi lại tổng thời gian xử lý
        total_time = time.time() - total_start_time
        logger.bind(tag=TAG).debug(
            f"【Hiệu suất nhận dạng ý định】Model: {model_info}, tổng thời gian: {total_time:.4f} giây, gọi LLM: {llm_time:.4f} giây, truy vấn: '{text[:20]}...'"
        )

        # Thử phân tích thành JSON
        try:
            intent_data = json.loads(intent)
            # Nếu chứa function_call, thì định dạng thành định dạng phù hợp để xử lý
            if "function_call" in intent_data:
                function_data = intent_data["function_call"]
                function_name = function_data.get("name")
                function_args = function_data.get("arguments", {})

                # Ghi lại function call đã nhận dạng
                logger.bind(tag=TAG).info(
                    f"llm đã nhận dạng ý định: {function_name}, tham số: {function_args}"
                )

                # Xử lý các loại ý định khác nhau
                if function_name == "result_for_context":
                    # Xử lý truy vấn thông tin cơ bản, xây dựng kết quả trực tiếp từ context
                    logger.bind(tag=TAG).info(
                        "Phát hiện ý định result_for_context, sẽ sử dụng thông tin ngữ cảnh để trả lời trực tiếp"
                    )

                elif function_name == "continue_chat":
                    # Xử lý hội thoại thông thường
                    # Giữ lại các tin nhắn không liên quan đến công cụ
                    clean_history = [
                        msg
                        for msg in conn.dialogue.dialogue
                        if msg.role not in ["tool", "function"]
                    ]
                    conn.dialogue.dialogue = clean_history

                else:
                    # Xử lý gọi hàm
                    logger.bind(tag=TAG).info(f"Phát hiện ý định gọi hàm: {function_name}")

            # Xử lý cache và trả về thống nhất
            self.cache_manager.set(self.CacheType.INTENT, cache_key, intent)
            postprocess_time = time.time() - postprocess_start_time
            logger.bind(tag=TAG).debug(f"Thời gian hậu xử lý ý định: {postprocess_time:.4f} giây")
            return intent
        except json.JSONDecodeError:
            # Thời gian hậu xử lý
            postprocess_time = time.time() - postprocess_start_time
            logger.bind(tag=TAG).error(
                f"Không thể phân tích JSON ý định: {intent}, thời gian hậu xử lý: {postprocess_time:.4f} giây"
            )
            # Nếu phân tích thất bại, mặc định trả về ý định tiếp tục trò chuyện
            return '{"function_call": {"name": "continue_chat"}}'
