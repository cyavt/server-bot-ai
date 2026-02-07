from abc import abstractmethod, ABC
from typing import Dict, Any

from core.handle.textMessageType import TextMessageType

TAG = __name__


class TextMessageHandler(ABC):
    """Lớp cơ sở trừu tượng cho bộ xử lý tin nhắn"""

    @abstractmethod
    async def handle(self, conn, msg_json: Dict[str, Any]) -> None:
        """Phương thức trừu tượng xử lý tin nhắn"""
        pass

    @property
    @abstractmethod
    def message_type(self) -> TextMessageType:
        """Trả về loại tin nhắn được xử lý"""
        pass
