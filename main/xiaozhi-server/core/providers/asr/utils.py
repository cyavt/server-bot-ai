import re
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

EMOTION_EMOJI_MAP = {
    "HAPPY": "🙂",
    "SAD": "😔",
    "ANGRY": "😡",
    "NEUTRAL": "😶",
    "FEARFUL": "😰",
    "DISGUSTED": "🤢",
    "SURPRISED": "😲",
    "EMO_UNKNOWN": "😶",  # Cảm xúc không xác định mặc định dùng biểu cảm trung tính
}
# EVENT_EMOJI_MAP = {
#     "<|BGM|>": "🎼",
#     "<|Speech|>": "",
#     "<|Applause|>": "👏",
#     "<|Laughter|>": "😀",
#     "<|Cry|>": "😭",
#     "<|Sneeze|>": "🤧",
#     "<|Breath|>": "",
#     "<|Cough|>": "🤧",
# }

def lang_tag_filter(text: str) -> dict | str:
    """
    Phân tích kết quả nhận dạng FunASR, trích xuất nhãn và nội dung văn bản thuần theo thứ tự

    Args:
        text: Văn bản gốc được ASR nhận dạng, có thể chứa nhiều loại nhãn

    Returns:
        dict: {"language": "zh", "emotion": "SAD", "emoji": "😔", "content": "你好"} nếu có nhãn
        str: Văn bản thuần, nếu không có nhãn

    Examples:
        Định dạng đầu ra FunASR: <|ngôn ngữ|><|cảm xúc|><|sự kiện|><|tùy chọn khác|>văn bản gốc
        >>> lang_tag_filter("<|zh|><|SAD|><|Speech|><|withitn|>你好啊，测试测试。")
        {"language": "zh", "emotion": "SAD", "emoji": "😔", "content": "你好啊，测试测试。"}
        >>> lang_tag_filter("<|en|><|HAPPY|><|Speech|><|withitn|>Hello hello.")
        {"language": "en", "emotion": "HAPPY", "emoji": "🙂", "content": "Hello hello."}
        >>> lang_tag_filter("plain text")
        "plain text"
    """
    # Trích xuất tất cả nhãn (theo thứ tự)
    tag_pattern = r"<\|([^|]+)\|>"
    all_tags = re.findall(tag_pattern, text)

    # Loại bỏ tất cả nhãn định dạng <|...|>, lấy văn bản thuần
    clean_text = re.sub(tag_pattern, "", text).strip()

    # Nếu không có nhãn, trả về văn bản thuần trực tiếp
    if not all_tags:
        return clean_text

    # Trích xuất nhãn theo thứ tự cố định của FunASR, trả về dict
    language = all_tags[0] if len(all_tags) > 0 else "zh"
    emotion = all_tags[1] if len(all_tags) > 1 else "NEUTRAL"
    # event = all_tags[2] if len(all_tags) > 2 else "Speech"  # Nhãn sự kiện tạm thời không sử dụng

    result = {
        "content": clean_text,
        "language": language,
        "emotion": emotion,
        # "event": event,
    }

    # Thêm ánh xạ emoji
    if emotion in EMOTION_EMOJI_MAP:
        result["emotion"] = EMOTION_EMOJI_MAP[emotion]
    # Nhãn sự kiện tạm thời không sử dụng
    # if event in EVENT_EMOJI_MAP:
    #     result["event"] = EVENT_EMOJI_MAP[event]

    return result

