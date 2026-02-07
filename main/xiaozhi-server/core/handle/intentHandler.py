import json
import uuid
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.utils.dialogue import Message
from core.providers.tts.dto.dto import ContentType
from core.handle.helloHandle import checkWakeupWords
from plugins_func.register import Action, ActionResponse
from core.handle.sendAudioHandle import send_stt_message
from core.utils.util import remove_punctuation_and_length
from core.providers.tts.dto.dto import TTSMessageDTO, SentenceType

TAG = __name__


async def handle_user_intent(conn: "ConnectionHandler", text):
    # Tiền xử lý văn bản đầu vào, xử lý định dạng JSON có thể có
    try:
        if text.strip().startswith("{") and text.strip().endswith("}"):
            parsed_data = json.loads(text)
            if isinstance(parsed_data, dict) and "content" in parsed_data:
                text = parsed_data["content"]  # Trích xuất content để phân tích ý định
                conn.current_speaker = parsed_data.get("speaker")  # Giữ lại thông tin người nói
    except (json.JSONDecodeError, TypeError):
        pass

    # Kiểm tra xem có lệnh thoát rõ ràng không
    _, filtered_text = remove_punctuation_and_length(text)
    if await check_direct_exit(conn, filtered_text):
        return True

    # Kiểm tra xem có phải từ đánh thức không
    if await checkWakeupWords(conn, filtered_text):
        return True

    if conn.intent_type == "function_call":
        # Sử dụng phương pháp trò chuyện hỗ trợ function calling, không phân tích ý định nữa
        return False
    # Sử dụng LLM để phân tích ý định người dùng
    intent_result = await analyze_intent_with_llm(conn, text)
    if not intent_result:
        return False
    # Khi bắt đầu phiên tạo sentence_id
    conn.sentence_id = str(uuid.uuid4().hex)
    # Xử lý các ý định khác nhau
    return await process_intent_result(conn, intent_result, text)


async def check_direct_exit(conn: "ConnectionHandler", text):
    """Kiểm tra xem có lệnh thoát rõ ràng không"""
    _, text = remove_punctuation_and_length(text)
    cmd_exit = conn.cmd_exit
    for cmd in cmd_exit:
        if text == cmd:
            conn.logger.bind(tag=TAG).info(f"Nhận diện được lệnh thoát rõ ràng: {text}")
            await send_stt_message(conn, text)
            await conn.close()
            return True
    return False


async def analyze_intent_with_llm(conn: "ConnectionHandler", text):
    """Sử dụng LLM để phân tích ý định người dùng"""
    if not hasattr(conn, "intent") or not conn.intent:
        conn.logger.bind(tag=TAG).warning("Dịch vụ nhận diện ý định chưa được khởi tạo")
        return None

    # Lịch sử đối thoại
    dialogue = conn.dialogue
    try:
        intent_result = await conn.intent.detect_intent(conn, dialogue.dialogue, text)
        return intent_result
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Nhận diện ý định thất bại: {str(e)}")

    return None


async def process_intent_result(
    conn: "ConnectionHandler", intent_result, original_text
):
    """Xử lý kết quả nhận diện ý định"""
    try:
        # Thử phân tích kết quả thành JSON
        intent_data = json.loads(intent_result)

        # Kiểm tra xem có function_call không
        if "function_call" in intent_data:
            # Trực tiếp lấy function_call từ nhận diện ý định
            conn.logger.bind(tag=TAG).debug(
                f"Phát hiện kết quả ý định định dạng function_call: {intent_data['function_call']['name']}"
            )
            function_name = intent_data["function_call"]["name"]
            if function_name == "continue_chat":
                return False

            if function_name == "result_for_context":
                await send_stt_message(conn, original_text)
                conn.client_abort = False

                def process_context_result():
                    conn.dialogue.put(Message(role="user", content=original_text))

                    from core.utils.current_time import get_current_time_info

                    current_time, today_date, today_weekday, lunar_date = (
                        get_current_time_info()
                    )

                    # Xây dựng lời nhắc cơ bản có ngữ cảnh
                    context_prompt = f"""Thời gian hiện tại: {current_time}
                                        Ngày hôm nay: {today_date} ({today_weekday})
                                        Âm lịch hôm nay: {lunar_date}

                                        Vui lòng trả lời câu hỏi của người dùng dựa trên thông tin trên: {original_text}"""

                    response = conn.intent.replyResult(context_prompt, original_text)
                    speak_txt(conn, response)

                conn.executor.submit(process_context_result)
                return True

            function_args = {}
            if "arguments" in intent_data["function_call"]:
                function_args = intent_data["function_call"]["arguments"]
                if function_args is None:
                    function_args = {}
            # Đảm bảo tham số là JSON định dạng chuỗi
            if isinstance(function_args, dict):
                function_args = json.dumps(function_args)

            function_call_data = {
                "name": function_name,
                "id": str(uuid.uuid4().hex),
                "arguments": function_args,
            }

            await send_stt_message(conn, original_text)
            conn.client_abort = False

            # Sử dụng executor để thực thi gọi hàm và xử lý kết quả
            def process_function_call():
                conn.dialogue.put(Message(role="user", content=original_text))

                # Sử dụng bộ xử lý công cụ thống nhất để xử lý tất cả các lời gọi công cụ
                try:
                    result = asyncio.run_coroutine_threadsafe(
                        conn.func_handler.handle_llm_function_call(
                            conn, function_call_data
                        ),
                        conn.loop,
                    ).result()
                except Exception as e:
                    conn.logger.bind(tag=TAG).error(f"Gọi công cụ thất bại: {e}")
                    result = ActionResponse(
                        action=Action.ERROR, result=str(e), response=str(e)
                    )

                if result:
                    if result.action == Action.RESPONSE:  # Trả lời trực tiếp frontend
                        text = result.response
                        if text is not None:
                            speak_txt(conn, text)
                    elif result.action == Action.REQLLM:  # Sau khi gọi hàm, yêu cầu llm tạo phản hồi
                        text = result.result
                        conn.dialogue.put(Message(role="tool", content=text))
                        llm_result = conn.intent.replyResult(text, original_text)
                        if llm_result is None:
                            llm_result = text
                        speak_txt(conn, llm_result)
                    elif (
                        result.action == Action.NOTFOUND
                        or result.action == Action.ERROR
                    ):
                        text = result.result
                        if text is not None:
                            speak_txt(conn, text)
                    elif function_name != "play_music":
                        # For backward compatibility with original code
                        # Lấy chỉ mục văn bản mới nhất hiện tại
                        text = result.response
                        if text is None:
                            text = result.result
                        if text is not None:
                            speak_txt(conn, text)

            # Đặt việc thực thi hàm vào thread pool
            conn.executor.submit(process_function_call)
            return True
        return False
    except json.JSONDecodeError as e:
        conn.logger.bind(tag=TAG).error(f"Lỗi khi xử lý kết quả ý định: {e}")
        return False


def speak_txt(conn: "ConnectionHandler", text):
    # Ghi lại văn bản
    conn.tts_MessageText = text

    conn.tts.tts_text_queue.put(
        TTSMessageDTO(
            sentence_id=conn.sentence_id,
            sentence_type=SentenceType.FIRST,
            content_type=ContentType.ACTION,
        )
    )
    conn.tts.tts_one_sentence(conn, ContentType.TEXT, content_detail=text)
    conn.tts.tts_text_queue.put(
        TTSMessageDTO(
            sentence_id=conn.sentence_id,
            sentence_type=SentenceType.LAST,
            content_type=ContentType.ACTION,
        )
    )
    conn.dialogue.put(Message(role="assistant", content=text))
