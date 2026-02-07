from datetime import datetime
import cnlunar
from plugins_func.register import register_function, ToolType, ActionResponse, Action

get_lunar_function_desc = {
    "type": "function",
    "function": {
        "name": "get_lunar",
        "description": (
            "Dùng cho thông tin âm lịch/lịch nông và lịch hoàng đạo của ngày cụ thể."
            "Người dùng có thể chỉ định nội dung truy vấn, như: ngày âm lịch, can chi, tiết khí, con giáp, cung hoàng đạo, bát tự, nên làm/kiêng kỵ v.v."
            "Nếu không chỉ định nội dung truy vấn, mặc định truy vấn năm can chi và ngày âm lịch."
            "Đối với các truy vấn cơ bản như 'hôm nay âm lịch là bao nhiêu', 'ngày âm lịch hôm nay', vui lòng sử dụng trực tiếp thông tin trong context, không gọi công cụ này."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Ngày cần truy vấn, định dạng YYYY-MM-DD, ví dụ 2024-01-01. Nếu không cung cấp, sử dụng ngày hiện tại",
                },
                "query": {
                    "type": "string",
                    "description": "Nội dung cần truy vấn, ví dụ ngày âm lịch, can chi, ngày lễ, tiết khí, con giáp, cung hoàng đạo, bát tự, nên làm/kiêng kỵ v.v.",
                },
            },
            "required": [],
        },
    },
}


@register_function("get_lunar", get_lunar_function_desc, ToolType.WAIT)
def get_lunar(date=None, query=None):
    """
    Dùng để lấy âm lịch/lịch nông hiện tại, và thông tin lịch hoàng đạo như can chi, tiết khí, con giáp, cung hoàng đạo, bát tự, nên làm/kiêng kỵ v.v.
    """
    from core.utils.cache.manager import cache_manager, CacheType

    # Nếu cung cấp tham số ngày, sử dụng ngày chỉ định; nếu không sử dụng ngày hiện tại
    if date:
        try:
            now = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return ActionResponse(
                Action.REQLLM,
                f"Định dạng ngày sai, vui lòng sử dụng định dạng YYYY-MM-DD, ví dụ: 2024-01-01",
                None,
            )
    else:
        now = datetime.now()

    current_date = now.strftime("%Y-%m-%d")

    # Nếu query là None, sử dụng văn bản mặc định
    if query is None:
        query = "Truy vấn mặc định năm can chi và ngày âm lịch"

    # Thử lấy thông tin âm lịch từ cache
    lunar_cache_key = f"lunar_info_{current_date}"
    cached_lunar_info = cache_manager.get(CacheType.LUNAR, lunar_cache_key)
    if cached_lunar_info:
        return ActionResponse(Action.REQLLM, cached_lunar_info, None)

    response_text = f"Dựa trên thông tin sau đây để trả lời yêu cầu truy vấn của người dùng, và cung cấp thông tin liên quan đến {query}:\n"

    lunar = cnlunar.Lunar(now, godType="8char")
    response_text += (
        "Thông tin âm lịch:\n"
        "%s年%s%s\n" % (lunar.lunarYearCn, lunar.lunarMonthCn[:-1], lunar.lunarDayCn)
        + "Can chi: %s年 %s月 %s日\n" % (lunar.year8Char, lunar.month8Char, lunar.day8Char)
        + "Con giáp: %s\n" % (lunar.chineseYearZodiac)
        + "Bát tự: %s\n"
        % (
            " ".join(
                [lunar.year8Char, lunar.month8Char, lunar.day8Char, lunar.twohour8Char]
            )
        )
        + "Ngày lễ hôm nay: %s\n"
        % (
            ",".join(
                filter(
                    None,
                    (
                        lunar.get_legalHolidays(),
                        lunar.get_otherHolidays(),
                        lunar.get_otherLunarHolidays(),
                    ),
                )
            )
        )
        + "Tiết khí hôm nay: %s\n" % (lunar.todaySolarTerms)
        + "Tiết khí tiếp theo: %s %s年%s月%s日\n"
        % (
            lunar.nextSolarTerm,
            lunar.nextSolarTermYear,
            lunar.nextSolarTermDate[0],
            lunar.nextSolarTermDate[1],
        )
        + "Bảng tiết khí năm nay: %s\n"
        % (
            ", ".join(
                [
                    f"{term}({date[0]}月{date[1]}日)"
                    for term, date in lunar.thisYearSolarTermsDic.items()
                ]
            )
        )
        + "Xung khắc con giáp: %s\n" % (lunar.chineseZodiacClash)
        + "Cung hoàng đạo: %s\n" % (lunar.starZodiac)
        + "Nạp âm: %s\n" % lunar.get_nayin()
        + "Bách kỵ Bành Tổ: %s\n" % (lunar.get_pengTaboo(delimit=", "))
        + "Trực nhật: %s chấp vị\n" % lunar.get_today12DayOfficer()[0]
        + "Trực thần: %s(%s)\n"
        % (lunar.get_today12DayOfficer()[1], lunar.get_today12DayOfficer()[2])
        + "Nhị thập bát tú: %s\n" % lunar.get_the28Stars()
        + "Phương vị thần cát: %s\n" % " ".join(lunar.get_luckyGodsDirection())
        + "Thai thần hôm nay: %s\n" % lunar.get_fetalGod()
        + "Nên làm: %s\n" % "、".join(lunar.goodThing[:10])
        + "Kiêng kỵ: %s\n" % "、".join(lunar.badThing[:10])
        + "(Mặc định trả về năm can chi và ngày âm lịch; chỉ trả về nên làm/kiêng kỵ hôm nay khi yêu cầu truy vấn thông tin nên làm/kiêng kỵ)"
    )

    # Cache thông tin âm lịch
    cache_manager.set(CacheType.LUNAR, lunar_cache_key, response_text)

    return ActionResponse(Action.REQLLM, response_text, None)
