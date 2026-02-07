import requests
import sys
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

# Định nghĩa mẫu mô tả hàm cơ bản
SEARCH_FROM_RAGFLOW_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "search_from_ragflow",
        "description": "Truy vấn thông tin từ cơ sở tri thức",
        "parameters": {
            "type": "object",
            "properties": {"question": {"type": "string", "description": "Câu hỏi cần truy vấn"}},
            "required": ["question"],
        },
    },
}


@register_function(
    "search_from_ragflow", SEARCH_FROM_RAGFLOW_FUNCTION_DESC, ToolType.SYSTEM_CTL
)
def search_from_ragflow(conn: "ConnectionHandler", question=None):
    # Đảm bảo tham số chuỗi được xử lý mã hóa đúng cách
    if question and isinstance(question, str):
        # Đảm bảo tham số câu hỏi là chuỗi được mã hóa UTF-8
        pass
    else:
        question = str(question) if question is not None else ""

    ragflow_config = conn.config.get("plugins", {}).get("search_from_ragflow", {})
    base_url = ragflow_config.get("base_url", "")
    api_key = ragflow_config.get("api_key", "")
    dataset_ids = ragflow_config.get("dataset_ids", [])

    url = base_url + "/api/v1/retrieval"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Đảm bảo các chuỗi trong payload đều được mã hóa UTF-8
    payload = {"question": question, "dataset_ids": dataset_ids}

    try:
        # Sử dụng ensure_ascii=False để đảm bảo xử lý đúng tiếng Trung khi tuần tự hóa JSON
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=5,
            verify=False,
        )

        # Đặt mã hóa phản hồi rõ ràng là utf-8
        response.encoding = "utf-8"

        response.raise_for_status()

        # Lấy nội dung văn bản trước, sau đó xử lý giải mã JSON thủ công
        response_text = response.text
        import json

        result = json.loads(response_text)

        if result.get("code") != 0:
            error_detail = result.get("error", {}).get("detail", "Lỗi không xác định")
            error_message = result.get("error", {}).get("message", "")
            error_code = result.get("code", "")

            # Ghi lại thông tin lỗi một cách an toàn
            logger.bind(tag=TAG).error(
                f"Gọi API RAGFlow thất bại, mã phản hồi: {error_code}，chi tiết lỗi: {error_detail}，phản hồi đầy đủ: {result}"
            )

            # Xây dựng phản hồi lỗi chi tiết
            error_response = f"Giao diện RAG trả về bất thường (mã lỗi: {error_code})"

            if error_message:
                error_response += f": {error_message}"
            if error_detail:
                error_response += f"\nChi tiết: {error_detail}"

            return ActionResponse(Action.RESPONSE, None, error_response)

        chunks = result.get("data", {}).get("chunks", [])
        contents = []
        for chunk in chunks:
            content = chunk.get("content", "")
            if content:
                # Xử lý chuỗi nội dung một cách an toàn
                if isinstance(content, str):
                    contents.append(content)
                elif isinstance(content, bytes):
                    contents.append(content.decode("utf-8", errors="replace"))
                else:
                    contents.append(str(content))

        if contents:
            # Tổ chức nội dung cơ sở tri thức ở chế độ tham chiếu
            context_text = f"# Về câu hỏi【{question}】đã tìm thấy trong cơ sở tri thức như sau\n"
            context_text += "```\n\n\n".join(contents[:5])
            context_text += "\n```"
        else:
            context_text = "Theo kết quả truy vấn cơ sở tri thức, không có thông tin liên quan."
        return ActionResponse(Action.REQLLM, context_text, None)

    except requests.exceptions.RequestException as e:
        # Ngoại lệ yêu cầu mạng
        error_type = type(e).__name__
        logger.bind(tag=TAG).error(
            f"Yêu cầu mạng RAGflow thất bại, loại ngoại lệ: {error_type}，chi tiết: {str(e)}"
        )

        # Cung cấp thông tin lỗi và giải pháp chi tiết hơn theo loại ngoại lệ
        if isinstance(e, requests.exceptions.ConnectTimeout):
            error_response = "Giao diện RAG kết nối hết thời gian (5 giây)"
            error_response += "\nNguyên nhân có thể: Dịch vụ RAGflow chưa khởi động hoặc vấn đề kết nối mạng"
            error_response += "\nGiải pháp: Vui lòng kiểm tra trạng thái dịch vụ RAGflow và kết nối mạng"

        elif isinstance(e, requests.exceptions.ConnectionError):
            error_response = "Không thể kết nối đến giao diện RAG"
            error_response += "\nNguyên nhân có thể: Địa chỉ dịch vụ RAGflow sai hoặc dịch vụ chưa chạy"
            error_response += "\nGiải pháp: Vui lòng kiểm tra cấu hình địa chỉ dịch vụ RAGflow và trạng thái dịch vụ"

        elif isinstance(e, requests.exceptions.Timeout):
            error_response = "Yêu cầu giao diện RAG hết thời gian"
            error_response += "\nNguyên nhân có thể: Dịch vụ RAGflow phản hồi chậm hoặc độ trễ mạng"
            error_response += "\nGiải pháp: Vui lòng thử lại sau hoặc kiểm tra hiệu suất dịch vụ RAGflow"

        elif isinstance(e, requests.exceptions.HTTPError):
            # Xử lý mã trạng thái lỗi HTTP
            if hasattr(e.response, "status_code"):
                status_code = e.response.status_code
                error_response = f"Lỗi HTTP giao diện RAG (mã trạng thái: {status_code})"

                # Thử lấy thông tin lỗi trong nội dung phản hồi
                try:
                    error_detail = e.response.json().get("error", {}).get("message", "")
                    if error_detail:
                        error_response += f"\nChi tiết lỗi: {error_detail}"
                except:
                    pass
            else:
                error_response = f"Ngoại lệ HTTP giao diện RAG: {str(e)}"

        else:
            error_response = f"Ngoại lệ mạng giao diện RAG ({error_type}): {str(e)}"

        return ActionResponse(Action.RESPONSE, None, error_response)

    except Exception as e:
        # Các ngoại lệ khác
        error_type = type(e).__name__
        logger.bind(tag=TAG).error(
            f"Xử lý RAGflow bất thường, loại ngoại lệ: {error_type}，chi tiết: {str(e)}"
        )

        # Cung cấp thông tin lỗi chi tiết
        error_response = f"Xử lý giao diện RAG bất thường ({error_type}): {str(e)}"
        return ActionResponse(Action.RESPONSE, None, error_response)
