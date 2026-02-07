from abc import ABC, abstractmethod
from typing import List, Dict
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class IntentProviderBase(ABC):
    def __init__(self, config):
        self.config = config

    def set_llm(self, llm):
        self.llm = llm
        # Lấy thông tin tên và loại mô hình
        model_name = getattr(llm, "model_name", str(llm.__class__.__name__))
        # Ghi nhật ký chi tiết hơn
        logger.bind(tag=TAG).info(f"Nhận dạng ý định thiết lập LLM: {model_name}")

    @abstractmethod
    async def detect_intent(self, conn, dialogue_history: List[Dict], text: str) -> str:
        """
        Phát hiện ý định của câu cuối cùng của người dùng
        Args:
            dialogue_history: Danh sách lịch sử hội thoại, mỗi bản ghi chứa role và content
        Returns:
            Trả về ý định được nhận dạng, định dạng:
            - "继续聊天"
            - "结束聊天"
            - "播放音乐 歌名" hoặc "随机播放音乐"
            - "查询天气 地点名" hoặc "查询天气 [当前位置]"
        """
        pass
