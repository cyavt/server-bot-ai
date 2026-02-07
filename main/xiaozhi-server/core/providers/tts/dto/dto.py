from enum import Enum
from typing import Union, Optional


class SentenceType(Enum):
    # Giai đoạn nói
    FIRST = "FIRST"  # Câu đầu tiên
    MIDDLE = "MIDDLE"  # Đang nói
    LAST = "LAST"  # Câu cuối cùng


class ContentType(Enum):
    # Loại nội dung
    TEXT = "TEXT"  # Nội dung văn bản
    FILE = "FILE"  # Nội dung tệp
    ACTION = "ACTION"  # Nội dung hành động


class InterfaceType(Enum):
    # Loại giao diện
    DUAL_STREAM = "DUAL_STREAM"  # Luồng kép
    SINGLE_STREAM = "SINGLE_STREAM"  # Luồng đơn
    NON_STREAM = "NON_STREAM"  # Không luồng


class TTSMessageDTO:
    def __init__(
        self,
        sentence_id: str,
        # Giai đoạn nói
        sentence_type: SentenceType,
        # Loại nội dung
        content_type: ContentType,
        # Chi tiết nội dung, thường là văn bản cần chuyển đổi hoặc lời bài hát của âm thanh
        content_detail: Optional[str] = None,
        # Nếu loại nội dung là tệp, thì cần truyền đường dẫn tệp
        content_file: Optional[str] = None,
    ):
        self.sentence_id = sentence_id
        self.sentence_type = sentence_type
        self.content_type = content_type
        self.content_detail = content_detail
        self.content_file = content_file
