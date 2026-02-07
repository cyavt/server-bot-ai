import requests
from requests.exceptions import RequestException
from config.logger import setup_logging
from core.providers.llm.base import LLMProviderBase

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        self.agent_id = config.get("agent_id")  # Tương ứng với agent_id
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", config.get("url"))  # Mặc định sử dụng base_url
        self.api_url = f"{self.base_url}/api/conversation/process"  # Nối URL API đầy đủ

    def response(self, session_id, dialogue, **kwargs):
        # Trợ lý giọng nói home assistant có sẵn ý định, không cần sử dụng ý định tích hợp sẵn của xiaozhi ai, chỉ cần truyền những gì người dùng nói cho home assistant

        # Trích xuất content của role 'user' cuối cùng
        input_text = None
        if isinstance(dialogue, list):  # Đảm bảo dialogue là một danh sách
            # Duyệt ngược, tìm tin nhắn có role 'user' cuối cùng
            for message in reversed(dialogue):
                if message.get("role") == "user":  # Tìm tin nhắn có role 'user'
                    input_text = message.get("content", "")
                    break  # Thoát vòng lặp ngay sau khi tìm thấy

        # Xây dựng dữ liệu yêu cầu
        payload = {
            "text": input_text,
            "agent_id": self.agent_id,
            "conversation_id": session_id,  # Sử dụng session_id làm conversation_id
        }
        # Đặt tiêu đề yêu cầu
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Gửi yêu cầu POST
        response = requests.post(self.api_url, json=payload, headers=headers)

        # Kiểm tra xem yêu cầu có thành công không
        response.raise_for_status()

        # Phân tích dữ liệu trả về
        data = response.json()
        speech = (
            data.get("response", {})
            .get("speech", {})
            .get("plain", {})
            .get("speech", "")
        )

        # Trả về nội dung được tạo
        if speech:
            yield speech
        else:
            logger.bind(tag=TAG).warning("Dữ liệu trả về từ API không có nội dung speech")

    def response_with_functions(self, session_id, dialogue, functions=None):
        logger.bind(tag=TAG).error(
            f"homeassistant không hỗ trợ (function call), đề xuất sử dụng nhận dạng ý định khác"
        )
