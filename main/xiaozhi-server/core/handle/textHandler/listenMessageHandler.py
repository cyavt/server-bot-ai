import time
import asyncio
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

from core.handle.receiveAudioHandle import startToChat
from core.handle.reportHandle import enqueue_asr_report
from core.handle.sendAudioHandle import send_stt_message, send_tts_message
from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType
from core.utils.util import remove_punctuation_and_length
from core.providers.asr.dto.dto import InterfaceType

TAG = __name__

class ListenTextMessageHandler(TextMessageHandler):
    """Bộ xử lý tin nhắn Listen"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.LISTEN

    async def handle(self, conn: "ConnectionHandler", msg_json: Dict[str, Any]) -> None:
        if "mode" in msg_json:
            conn.client_listen_mode = msg_json["mode"]
            conn.logger.bind(tag=TAG).debug(
                f"Chế độ thu âm của khách hàng: {conn.client_listen_mode}"
            )
        if msg_json["state"] == "start":
            # Thiết bị chuyển từ chế độ phát sang chế độ ghi âm, xóa tất cả trạng thái và bộ đệm âm thanh
            conn.reset_audio_states()
        elif msg_json["state"] == "stop":
            conn.client_voice_stop = True
            if conn.asr.interface_type == InterfaceType.STREAM:
                # Ở chế độ luồng, gửi yêu cầu kết thúc
                asyncio.create_task(conn.asr._send_stop_request())
            else:
                # Chế độ không luồng: kích hoạt nhận dạng ASR trực tiếp
                if len(conn.asr_audio) > 0:
                    asr_audio_task = conn.asr_audio.copy()
                    conn.reset_audio_states()

                    if len(asr_audio_task) > 0:
                        await conn.asr.handle_voice_stop(conn, asr_audio_task)
        elif msg_json["state"] == "detect":
            conn.client_have_voice = False
            conn.reset_audio_states()
            if "text" in msg_json:
                conn.last_activity_time = time.time() * 1000
                original_text = msg_json["text"]  # Giữ lại văn bản gốc
                filtered_len, filtered_text = remove_punctuation_and_length(
                    original_text
                )

                # Nhận dạng xem có phải từ đánh thức không
                is_wakeup_words = filtered_text in conn.config.get("wakeup_words")
                # Có bật phản hồi từ đánh thức không
                enable_greeting = conn.config.get("enable_greeting", True)

                if is_wakeup_words and not enable_greeting:
                    # Nếu là từ đánh thức và đã tắt phản hồi từ đánh thức, thì không cần trả lời
                    await send_stt_message(conn, original_text)
                    await send_tts_message(conn, "stop", None)
                    conn.client_is_speaking = False
                elif is_wakeup_words:
                    conn.just_woken_up = True
                    # Báo cáo dữ liệu văn bản thuần (tái sử dụng chức năng báo cáo ASR, nhưng không cung cấp dữ liệu âm thanh)
                    enqueue_asr_report(conn, "嘿，你好呀", [])
                    await startToChat(conn, "嘿，你好呀")
                else:
                    conn.just_woken_up = True
                    # Báo cáo dữ liệu văn bản thuần (tái sử dụng chức năng báo cáo ASR, nhưng không cung cấp dữ liệu âm thanh)
                    enqueue_asr_report(conn, original_text, [])
                    # Nếu không cần LLM trả lời nội dung văn bản
                    await startToChat(conn, original_text)