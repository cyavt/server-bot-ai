import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.handle.textMessageHandlerRegistry import TextMessageHandlerRegistry

TAG = __name__


class TextMessageProcessor:
    """Lớp chính xử lý tin nhắn"""

    def __init__(self, registry: TextMessageHandlerRegistry):
        self.registry = registry

    async def process_message(self, conn: "ConnectionHandler", message: str) -> None:
        """Điểm vào chính xử lý tin nhắn"""
        try:
            # Phân tích tin nhắn JSON
            msg_json = json.loads(message)

            # Xử lý tin nhắn JSON
            if isinstance(msg_json, dict):
                message_type = msg_json.get("type")

                # Ghi nhật ký
                conn.logger.bind(tag=TAG).info(f"Nhận tin nhắn {message_type}: {message}")

                # Lấy và thực thi bộ xử lý
                handler = self.registry.get_handler(message_type)
                if handler:
                    await handler.handle(conn, msg_json)
                else:
                    conn.logger.bind(tag=TAG).error(f"Nhận tin nhắn loại không xác định: {message}")
            # Xử lý tin nhắn số thuần túy
            elif isinstance(msg_json, int):
                conn.logger.bind(tag=TAG).info(f"Nhận tin nhắn số: {message}")
                await conn.websocket.send(message)

        except json.JSONDecodeError:
            # Tin nhắn không phải JSON chuyển tiếp trực tiếp
            conn.logger.bind(tag=TAG).error(f"Phân tích tin nhắn lỗi: {message}")
            await conn.websocket.send(message)
