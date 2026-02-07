import time
import json
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.utils.util import audio_to_data
from core.handle.abortHandle import handleAbortMessage
from core.handle.intentHandler import handle_user_intent
from core.utils.output_counter import check_device_output_limit
from core.handle.sendAudioHandle import send_stt_message, SentenceType

TAG = __name__


async def handleAudioMessage(conn: "ConnectionHandler", audio):
    # Đoạn hiện tại có người nói không
    have_voice = conn.vad.is_vad(conn, audio)
    # Nếu thiết bị vừa được đánh thức, tạm thời bỏ qua phát hiện VAD
    if hasattr(conn, "just_woken_up") and conn.just_woken_up:
        have_voice = False
        # Đặt một độ trễ ngắn sau đó khôi phục phát hiện VAD
        if not hasattr(conn, "vad_resume_task") or conn.vad_resume_task.done():
            conn.vad_resume_task = asyncio.create_task(resume_vad_detection(conn))
        return
    # Ở chế độ manual không ngắt nội dung đang phát
    if have_voice:
        if conn.client_is_speaking and conn.client_listen_mode != "manual":
            await handleAbortMessage(conn)
    # Phát hiện thiết bị rảnh rỗi lâu, dùng để nói tạm biệt
    await no_voice_close_connect(conn, have_voice)
    # Nhận âm thanh
    await conn.asr.receive_audio(conn, audio, have_voice)


async def resume_vad_detection(conn: "ConnectionHandler"):
    # Chờ 2 giây sau đó khôi phục phát hiện VAD
    await asyncio.sleep(2)
    conn.just_woken_up = False


async def startToChat(conn: "ConnectionHandler", text):
    # Kiểm tra đầu vào có phải định dạng JSON không (chứa thông tin người nói)
    speaker_name = None
    language_tag = None
    actual_text = text

    try:
        # Thử phân tích đầu vào định dạng JSON
        if text.strip().startswith("{") and text.strip().endswith("}"):
            data = json.loads(text)
            if "speaker" in data and "content" in data:
                speaker_name = data["speaker"]
                language_tag = data["language"]
                actual_text = data["content"]
                conn.logger.bind(tag=TAG).info(f"Phân tích được thông tin người nói: {speaker_name}")

                # Sử dụng trực tiếp văn bản định dạng JSON, không phân tích
                actual_text = text
    except (json.JSONDecodeError, KeyError):
        # Nếu phân tích thất bại, tiếp tục sử dụng văn bản gốc
        pass

    # Lưu thông tin người nói vào đối tượng kết nối
    if speaker_name:
        conn.current_speaker = speaker_name
    else:
        conn.current_speaker = None
    # Lưu thông tin ngôn ngữ vào đối tượng kết nối
    if language_tag:
        conn.current_language_tag = language_tag
    else:
        conn.current_language_tag = "zh"

    if conn.need_bind:
        await check_bind_device(conn)
        return

    # Nếu số ký tự đầu ra trong ngày lớn hơn số ký tự giới hạn
    if conn.max_output_size > 0:
        if check_device_output_limit(
            conn.headers.get("device-id"), conn.max_output_size
        ):
            await max_out_size(conn)
            return
    # Ở chế độ manual không ngắt nội dung đang phát
    if conn.client_is_speaking and conn.client_listen_mode != "manual":
        await handleAbortMessage(conn)

    # Trước tiên phân tích ý định, sử dụng nội dung văn bản thực tế
    intent_handled = await handle_user_intent(conn, actual_text)

    if intent_handled:
        # Nếu ý định đã được xử lý, không tiếp tục trò chuyện
        return

    # Ý định chưa được xử lý, tiếp tục quy trình trò chuyện thông thường, sử dụng nội dung văn bản thực tế
    await send_stt_message(conn, actual_text)
    conn.executor.submit(conn.chat, actual_text)


async def no_voice_close_connect(conn: "ConnectionHandler", have_voice):
    if have_voice:
        conn.last_activity_time = time.time() * 1000
        return
    # Chỉ kiểm tra hết thời gian khi đã khởi tạo dấu thời gian
    if conn.last_activity_time > 0.0:
        no_voice_time = time.time() * 1000 - conn.last_activity_time
        close_connection_no_voice_time = int(
            conn.config.get("close_connection_no_voice_time", 120)
        )
        if (
            not conn.close_after_chat
            and no_voice_time > 1000 * close_connection_no_voice_time
        ):
            conn.close_after_chat = True
            conn.client_abort = False
            end_prompt = conn.config.get("end_prompt", {})
            if end_prompt and end_prompt.get("enable", True) is False:
                conn.logger.bind(tag=TAG).info("Kết thúc cuộc trò chuyện, không cần gửi câu nhắc kết thúc")
                await conn.close()
                return
            prompt = end_prompt.get("prompt")
            if not prompt:
                prompt = "请你以```时间过得真快```未来头，用富有感情、依依不舍的话来结束这场对话吧。！"
            await startToChat(conn, prompt)


async def max_out_size(conn: "ConnectionHandler"):
    # Phát thông báo vượt quá số ký tự đầu ra tối đa
    conn.client_abort = False
    text = "不好意思，我现在有点事情要忙，明天这个时候我们再聊，约好了哦！明天不见不散，拜拜！"
    await send_stt_message(conn, text)
    file_path = "config/assets/max_output_size.wav"
    opus_packets = await audio_to_data(file_path)
    conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
    conn.close_after_chat = True


async def check_bind_device(conn: "ConnectionHandler"):
    if conn.bind_code:
        # Đảm bảo bind_code là 6 chữ số
        if len(conn.bind_code) != 6:
            conn.logger.bind(tag=TAG).error(f"Định dạng mã liên kết không hợp lệ: {conn.bind_code}")
            text = "Định dạng mã liên kết sai, vui lòng kiểm tra cấu hình."
            await send_stt_message(conn, text)
            return

        text = f"Vui lòng đăng nhập bảng điều khiển, nhập {conn.bind_code}，liên kết thiết bị."
        await send_stt_message(conn, text)

        # Phát âm thanh thông báo
        music_path = "config/assets/bind_code.wav"
        opus_packets = await audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.FIRST, opus_packets, text))

        # Phát từng chữ số
        for i in range(6):  # Đảm bảo chỉ phát 6 chữ số
            try:
                digit = conn.bind_code[i]
                num_path = f"config/assets/bind_code/{digit}.wav"
                num_packets = await audio_to_data(num_path)
                conn.tts.tts_audio_queue.put((SentenceType.MIDDLE, num_packets, None))
            except Exception as e:
                conn.logger.bind(tag=TAG).error(f"Phát âm thanh số thất bại: {e}")
                continue
        conn.tts.tts_audio_queue.put((SentenceType.LAST, [], None))
    else:
        # Phát thông báo chưa liên kết
        conn.client_abort = False
        text = f"Không tìm thấy thông tin phiên bản của thiết bị này, vui lòng cấu hình đúng địa chỉ OTA, sau đó biên dịch lại firmware."
        await send_stt_message(conn, text)
        music_path = "config/assets/bind_not_found.wav"
        opus_packets = await audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
