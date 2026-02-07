import time
import json
import uuid
import random
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.utils.dialogue import Message
from core.utils.util import audio_to_data
from core.providers.tts.dto.dto import SentenceType
from core.utils.wakeup_word import WakeupWordsConfig
from core.handle.sendAudioHandle import sendAudioMessage, send_tts_message
from core.utils.util import remove_punctuation_and_length, opus_datas_to_wav_bytes
from core.providers.tools.device_mcp import MCPClient, send_mcp_initialize_message

TAG = __name__

WAKEUP_CONFIG = {
    "refresh_time": 10,
    "responses": [
        "我一直都在呢，您请说。",
        "在的呢，请随时吩咐我。",
        "来啦来啦，请告诉我吧。",
        "您请说，我正听着。",
        "请您讲话，我准备好了。",
        "请您说出指令吧。",
        "我认真听着呢，请讲。",
        "请问您需要什么帮助？",
        "我在这里，等候您的指令。",
    ],
}

# Tạo trình quản lý cấu hình từ đánh thức toàn cục
wakeup_words_config = WakeupWordsConfig()

# Khóa để ngăn gọi đồng thời wakeupWordsResponse
_wakeup_response_lock = asyncio.Lock()


async def handleHelloMessage(conn: "ConnectionHandler", msg_json):
    """Xử lý tin nhắn hello"""
    audio_params = msg_json.get("audio_params")
    if audio_params:
        format = audio_params.get("format")
        conn.logger.bind(tag=TAG).debug(f"Định dạng âm thanh khách hàng: {format}")
        conn.audio_format = format
        conn.welcome_msg["audio_params"] = audio_params
    features = msg_json.get("features")
    if features:
        conn.logger.bind(tag=TAG).debug(f"Tính năng khách hàng: {features}")
        conn.features = features
        if features.get("mcp"):
            conn.logger.bind(tag=TAG).debug("Khách hàng hỗ trợ MCP")
            conn.mcp_client = MCPClient()
            # Gửi khởi tạo
            asyncio.create_task(send_mcp_initialize_message(conn))

    await conn.websocket.send(json.dumps(conn.welcome_msg))


async def checkWakeupWords(conn: "ConnectionHandler", text):
    enable_wakeup_words_response_cache = conn.config[
        "enable_wakeup_words_response_cache"
    ]

    # Chờ khởi tạo tts, tối đa chờ 3 giây
    start_time = time.time()
    while time.time() - start_time < 3:
        if conn.tts:
            break
        await asyncio.sleep(0.1)
    else:
        return False

    if not enable_wakeup_words_response_cache:
        return False

    _, filtered_text = remove_punctuation_and_length(text)
    if filtered_text not in conn.config.get("wakeup_words"):
        return False

    conn.just_woken_up = True
    await send_tts_message(conn, "start")

    # Lấy giọng nói hiện tại
    voice = getattr(conn.tts, "voice", "default")
    if not voice:
        voice = "default"

    # Lấy cấu hình phản hồi từ đánh thức
    response = wakeup_words_config.get_wakeup_response(voice)
    if not response or not response.get("file_path"):
        response = {
            "voice": "default",
            "file_path": "config/assets/wakeup_words_short.wav",
            "time": 0,
            "text": "我在这里哦！",
        }

    # Lấy dữ liệu âm thanh
    opus_packets = await audio_to_data(response.get("file_path"), use_cache=False)
    # Phát phản hồi từ đánh thức
    conn.client_abort = False

    # Coi phản hồi từ đánh thức là phiên mới, tạo sentence_id mới, đảm bảo bộ điều khiển luồng được đặt lại
    conn.sentence_id = str(uuid.uuid4().hex)

    conn.logger.bind(tag=TAG).info(f"Phát phản hồi từ đánh thức: {response.get('text')}")
    await sendAudioMessage(conn, SentenceType.FIRST, opus_packets, response.get("text"))
    await sendAudioMessage(conn, SentenceType.LAST, [], None)

    # Bổ sung đối thoại
    conn.dialogue.put(Message(role="assistant", content=response.get("text")))

    # Kiểm tra xem có cần cập nhật phản hồi từ đánh thức không
    if time.time() - response.get("time", 0) > WAKEUP_CONFIG["refresh_time"]:
        if not _wakeup_response_lock.locked():
            asyncio.create_task(wakeupWordsResponse(conn))
    return True


async def wakeupWordsResponse(conn: "ConnectionHandler"):
    if not conn.tts:
        return

    try:
        # Thử lấy khóa, nếu không lấy được thì trả về
        if not await _wakeup_response_lock.acquire():
            return

        # Từ danh sách phản hồi định nghĩa trước, chọn ngẫu nhiên một phản hồi
        result = random.choice(WAKEUP_CONFIG["responses"])
        if not result or len(result) == 0:
            return

        # Tạo âm thanh TTS
        tts_result = await asyncio.to_thread(conn.tts.to_tts, result)
        if not tts_result:
            return

        # Lấy giọng nói hiện tại
        voice = getattr(conn.tts, "voice", "default")

        # Sử dụng sample_rate của liên kết
        wav_bytes = opus_datas_to_wav_bytes(tts_result, sample_rate=conn.sample_rate)
        file_path = wakeup_words_config.generate_file_path(voice)
        with open(file_path, "wb") as f:
            f.write(wav_bytes)
        # Cập nhật cấu hình
        wakeup_words_config.update_wakeup_response(voice, file_path, result)
    finally:
        # Đảm bảo giải phóng khóa trong mọi trường hợp
        if _wakeup_response_lock.locked():
            _wakeup_response_lock.release()
