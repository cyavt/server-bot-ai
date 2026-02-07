from ..base import MemoryProviderBase, logger
import time
import json
import os
import yaml
from config.config_loader import get_project_dir
from config.manage_api_client import generate_and_save_chat_summary
import asyncio
from core.utils.util import check_model_key


short_term_memory_prompt = """
# Người dệt ký ức không-thời gian

## Sứ mệnh cốt lõi
Xây dựng mạng lưới ký ức động có thể phát triển, trong không gian hạn chế vừa giữ lại thông tin quan trọng, vừa bảo trì thông minh quỹ đạo tiến hóa thông tin
Dựa trên bản ghi hội thoại, tóm tắt thông tin quan trọng của user, để cung cấp dịch vụ cá nhân hóa hơn trong các cuộc hội thoại tương lai

## Quy tắc ký ức
### 1. Đánh giá ký ức ba chiều (phải thực hiện mỗi lần cập nhật)
| Chiều       | Tiêu chuẩn đánh giá                  | Điểm trọng số |
|------------|---------------------------|--------|
| Tính kịp thời     | Độ tươi mới thông tin (theo lượt hội thoại) | 40%    |
| Cường độ cảm xúc   | Chứa dấu 💖/số lần đề cập lặp lại     | 35%    |
| Mật độ liên kết   | Số lượng kết nối với thông tin khác      | 25%    |

### 2. Cơ chế cập nhật động
**Ví dụ xử lý thay đổi tên:**
Ký ức gốc: "Tên cũ": ["张三"], "Tên hiện tại": "张三丰"
Điều kiện kích hoạt: Khi phát hiện tín hiệu đặt tên như 「Tôi tên X」「Gọi tôi Y」
Quy trình thao tác:
1. Chuyển tên cũ vào danh sách "Tên cũ"
2. Ghi lại trục thời gian đặt tên: "2024-02-15 14:32:Kích hoạt 张三丰"
3. Thêm vào khối ký ức: 「Sự chuyển đổi danh tính từ 张三 sang 张三丰」

### 3. Chiến lược tối ưu không gian
- **Kỹ thuật nén thông tin**: Sử dụng hệ thống ký hiệu để tăng mật độ
  - ✅"张三丰[Bắc/Kỹ sư phần mềm/🐱]"
  - ❌"Kỹ sư phần mềm Bắc Kinh, nuôi mèo"
- **Cảnh báo loại bỏ**: Kích hoạt khi tổng số ký tự ≥900
  1. Xóa thông tin có điểm trọng số <60 và 3 lượt chưa đề cập
  2. Hợp nhất các mục tương tự (giữ lại mục có timestamp gần nhất)

## Cấu trúc ký ức
Định dạng đầu ra phải là chuỗi json có thể phân tích, không cần giải thích, chú thích và mô tả, khi lưu ký ức chỉ trích xuất thông tin từ hội thoại, không trộn nội dung ví dụ
```json
{
  "Hồ sơ không-thời gian": {
    "Sơ đồ danh tính": {
      "Tên hiện tại": "",
      "Dấu hiệu đặc trưng": [] 
    },
    "Khối ký ức": [
      {
        "Sự kiện": "Vào công ty mới",
        "Timestamp": "2024-03-20",
        "Giá trị cảm xúc": 0.9,
        "Mục liên quan": ["Trà chiều"],
        "Thời hạn bảo quản": 30 
      }
    ]
  },
  "Mạng lưới quan hệ": {
    "Chủ đề tần suất cao": {"Nơi làm việc": 12},
    "Liên kết ngầm": [""]
  },
  "Chờ phản hồi": {
    "Vấn đề khẩn cấp": ["Nhiệm vụ cần xử lý ngay lập tức"], 
    "Quan tâm tiềm ẩn": ["Trợ giúp có thể chủ động cung cấp"]
  },
  "Câu nói nổi bật": [
    "Khoảnh khắc cảm động nhất, biểu đạt cảm xúc mạnh mẽ, lời nói gốc của user"
  ]
}
```
"""


def extract_json_data(json_code):
    start = json_code.find("```json")
    # Từ start tìm đến kết thúc ``` tiếp theo
    end = json_code.find("```", start + 1)
    # print("start:", start, "end:", end)
    if start == -1 or end == -1:
        try:
            jsonData = json.loads(json_code)
            return json_code
        except Exception as e:
            print("Error:", e)
        return ""
    jsonData = json_code[start + 7 : end]
    return jsonData


TAG = __name__


class MemoryProvider(MemoryProviderBase):
    def __init__(self, config, summary_memory):
        super().__init__(config)
        self.short_memory = ""
        self.save_to_file = True
        self.memory_path = get_project_dir() + "data/.memory.yaml"
        self.load_memory(summary_memory)

    def init_memory(
        self, role_id, llm, summary_memory=None, save_to_file=True, **kwargs
    ):
        super().init_memory(role_id, llm, **kwargs)
        self.save_to_file = save_to_file
        self.load_memory(summary_memory)

    def load_memory(self, summary_memory):
        # API lấy được ký ức tóm tắt thì trả về trực tiếp
        if summary_memory or not self.save_to_file:
            self.short_memory = summary_memory
            return

        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        if self.role_id in all_memory:
            self.short_memory = all_memory[self.role_id]

    def save_memory_to_file(self):
        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        all_memory[self.role_id] = self.short_memory
        with open(self.memory_path, "w", encoding="utf-8") as f:
            yaml.dump(all_memory, f, allow_unicode=True)

    async def save_memory(self, msgs, session_id=None):
        # In thông tin model đang sử dụng
        model_info = getattr(self.llm, "model_name", str(self.llm.__class__.__name__))
        logger.bind(tag=TAG).debug(f"Sử dụng model lưu ký ức: {model_info}")
        api_key = getattr(self.llm, "api_key", None)
        memory_key_msg = check_model_key("LLM chuyên dùng tóm tắt ký ức", api_key)
        if memory_key_msg:
            logger.bind(tag=TAG).error(memory_key_msg)
        if self.llm is None:
            logger.bind(tag=TAG).error("LLM is not set for memory provider")
            return None

        if len(msgs) < 2:
            return None

        msgStr = ""
        for msg in msgs:
            content = msg.content

            # Extract content from JSON format if present (for ASR with emotion/language tags)
            try:
                if content and content.strip().startswith("{") and content.strip().endswith("}"):
                    data = json.loads(content)
                    if "content" in data:
                        content = data["content"]
            except (json.JSONDecodeError, KeyError, TypeError):
                # If parsing fails, use original content
                pass

            if msg.role == "user":
                msgStr += f"User: {content}\n"
            elif msg.role == "assistant":
                msgStr += f"Assistant: {content}\n"
        if self.short_memory and len(self.short_memory) > 0:
            msgStr += "Ký ức lịch sử:\n"
            msgStr += self.short_memory

        # Thời gian hiện tại
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        msgStr += f"Thời gian hiện tại: {time_str}"

        if self.save_to_file:
            try:
                result = self.llm.response_no_stream(
                    short_term_memory_prompt,
                    msgStr,
                    max_tokens=2000,
                    temperature=0.2,
                )
                json_str = extract_json_data(result)
                json.loads(json_str)  # Kiểm tra định dạng json có đúng không
                self.short_memory = json_str
                self.save_memory_to_file()
            except Exception as e:
                logger.bind(tag=TAG).error(f"Error in saving memory: {e}")
        else:
            # Khi save_to_file là False, gọi giao diện tóm tắt bản ghi chat phía Java
            summary_id = session_id if session_id else self.role_id
            await generate_and_save_chat_summary(summary_id)
        logger.bind(tag=TAG).info(
            f"Save memory successful - Role: {self.role_id}, Session: {session_id}"
        )

        return self.short_memory

    async def query_memory(self, query: str) -> str:
        return self.short_memory
