import json
import time
from typing import Dict, Any

from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType

TAG = __name__


class PingMessageHandler(TextMessageHandler):
    """Bộ xử lý tin nhắn Ping, dùng để duy trì kết nối WebSocket"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.PING

    async def handle(self, conn, msg_json: Dict[str, Any]) -> None:
        """
        Xử lý tin nhắn PING, gửi phản hồi PONG
        Định dạng tin nhắn: {"type": "ping"}
        Args:
            conn: Đối tượng kết nối WebSocket
            msg_json: Dữ liệu JSON của tin nhắn PING
        """
        # Kiểm tra xem chức năng nhịp tim WebSocket có được bật không
        enable_websocket_ping = conn.config.get("enable_websocket_ping", False)
        if not enable_websocket_ping:
            conn.logger.debug(f"Chức năng nhịp tim WebSocket chưa được bật, bỏ qua tin nhắn PING")
            return

        try:
            conn.logger.debug(f"Nhận tin nhắn PING, gửi phản hồi PONG")
            conn.last_activity_time = time.time() * 1000
            # Xây dựng tin nhắn phản hồi PONG
            pong_message = {
                "type": "pong",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            }

            # Gửi phản hồi PONG
            await conn.websocket.send(json.dumps(pong_message))

        except Exception as e:
            conn.logger.error(f"Lỗi khi xử lý tin nhắn PING: {e}")
