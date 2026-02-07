import requests
from bs4 import BeautifulSoup
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.utils.util import get_ip_info
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

GET_WEATHER_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "Lấy thời tiết của một địa điểm, người dùng nên cung cấp một vị trí, ví dụ người dùng nói thời tiết Đà Nẵng, tham số là: Đà Nẵng. "
            "Nếu người dùng nói tỉnh, mặc định dùng thành phố thủ phủ. Nếu người dùng nói không phải tỉnh hoặc thành phố mà là một địa danh, mặc định dùng thành phố thủ phủ của tỉnh nơi địa danh đó thuộc về. "
            "Nếu người dùng không chỉ định địa điểm, nói 'thời tiết thế nào', 'thời tiết hôm nay ra sao', tham số location là rỗng"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Tên địa điểm, ví dụ Đà Nẵng. Tham số tùy chọn, nếu không cung cấp thì không truyền",
                },
                "lang": {
                    "type": "string",
                    "description": "Trả về mã ngôn ngữ người dùng sử dụng, ví dụ zh_CN/zh_HK/en_US/ja_JP v.v., mặc định zh_CN",
                },
            },
            "required": ["lang"],
        },
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    )
}

# Mã thời tiết https://dev.qweather.com/docs/resource/icons/#weather-icons
WEATHER_CODE_MAP = {
    "100": "Nắng",
    "101": "Nhiều mây",
    "102": "Ít mây",
    "103": "Nắng có mây",
    "104": "Âm u",
    "150": "Nắng",
    "151": "Nhiều mây",
    "152": "Ít mây",
    "153": "Nắng có mây",
    "300": "Mưa rào",
    "301": "Mưa rào mạnh",
    "302": "Mưa dông",
    "303": "Mưa dông mạnh",
    "304": "Mưa dông kèm mưa đá",
    "305": "Mưa nhỏ",
    "306": "Mưa vừa",
    "307": "Mưa to",
    "308": "Mưa cực đoan",
    "309": "Mưa phùn/Mưa nhỏ",
    "310": "Mưa bão",
    "311": "Mưa bão lớn",
    "312": "Mưa bão cực lớn",
    "313": "Mưa đông",
    "314": "Mưa nhỏ đến vừa",
    "315": "Mưa vừa đến to",
    "316": "Mưa to đến bão",
    "317": "Mưa bão đến bão lớn",
    "318": "Mưa bão lớn đến cực lớn",
    "350": "Mưa rào",
    "351": "Mưa rào mạnh",
    "399": "Mưa",
    "400": "Tuyết nhỏ",
    "401": "Tuyết vừa",
    "402": "Tuyết to",
    "403": "Bão tuyết",
    "404": "Mưa tuyết",
    "405": "Thời tiết mưa tuyết",
    "406": "Mưa rào kèm tuyết",
    "407": "Tuyết rào",
    "408": "Tuyết nhỏ đến vừa",
    "409": "Tuyết vừa đến to",
    "410": "Tuyết to đến bão",
    "456": "Mưa rào kèm tuyết",
    "457": "Tuyết rào",
    "499": "Tuyết",
    "500": "Sương mù nhẹ",
    "501": "Sương mù",
    "502": "Khói mù",
    "503": "Cát bay",
    "504": "Bụi lơ lửng",
    "507": "Bão cát",
    "508": "Bão cát mạnh",
    "509": "Sương mù dày",
    "510": "Sương mù dày mạnh",
    "511": "Khói mù trung bình",
    "512": "Khói mù nặng",
    "513": "Khói mù nghiêm trọng",
    "514": "Sương mù lớn",
    "515": "Sương mù cực dày",
    "900": "Nóng",
    "901": "Lạnh",
    "999": "Không xác định",
}


def fetch_city_info(location, api_key, api_host):
    url = f"https://{api_host}/geo/v2/city/lookup?key={api_key}&location={location}&lang=zh"
    response = requests.get(url, headers=HEADERS).json()
    if response.get("error") is not None:
        logger.bind(tag=TAG).error(
            f"Lấy thời tiết thất bại, nguyên nhân: {response.get('error', {}).get('detail')}"
        )
        return None
    return response.get("location", [])[0] if response.get("location") else None


def fetch_weather_page(url):
    response = requests.get(url, headers=HEADERS)
    return BeautifulSoup(response.text, "html.parser") if response.ok else None


def parse_weather_info(soup):
    city_name = soup.select_one("h1.c-submenu__location").get_text(strip=True)

    current_abstract = soup.select_one(".c-city-weather-current .current-abstract")
    current_abstract = (
        current_abstract.get_text(strip=True) if current_abstract else "Không xác định"
    )

    current_basic = {}
    for item in soup.select(
        ".c-city-weather-current .current-basic .current-basic___item"
    ):
        parts = item.get_text(strip=True, separator=" ").split(" ")
        if len(parts) == 2:
            key, value = parts[1], parts[0]
            current_basic[key] = value

    temps_list = []
    for row in soup.select(".city-forecast-tabs__row")[:7]:  # Lấy dữ liệu 7 ngày đầu
        date = row.select_one(".date-bg .date").get_text(strip=True)
        weather_code = (
            row.select_one(".date-bg .icon")["src"].split("/")[-1].split(".")[0]
        )
        weather = WEATHER_CODE_MAP.get(weather_code, "Không xác định")
        temps = [span.get_text(strip=True) for span in row.select(".tmp-cont .temp")]
        high_temp, low_temp = (temps[0], temps[-1]) if len(temps) >= 2 else (None, None)
        temps_list.append((date, weather, high_temp, low_temp))

    return city_name, current_abstract, current_basic, temps_list


@register_function("get_weather", GET_WEATHER_FUNCTION_DESC, ToolType.SYSTEM_CTL)
def get_weather(conn: "ConnectionHandler", location: str = None, lang: str = "zh_CN"):
    from core.utils.cache.manager import cache_manager, CacheType

    weather_config = conn.config.get("plugins", {}).get("get_weather", {})
    api_host = weather_config.get("api_host", "mj7p3y7naa.re.qweatherapi.com")
    api_key = weather_config.get("api_key", "a861d0d5e7bf4ee1a83d9a9e4f96d4da")
    default_location = weather_config.get("default_location", "Đà Nẵng")
    client_ip = conn.client_ip

    # Ưu tiên sử dụng tham số location do người dùng cung cấp
    if not location:
        # Phân tích thành phố qua IP khách hàng
        if client_ip:
            # Lấy thông tin thành phố tương ứng với IP từ cache trước
            cached_ip_info = cache_manager.get(CacheType.IP_INFO, client_ip)
            if cached_ip_info:
                location = cached_ip_info.get("city")
            else:
                # Cache không trúng, gọi API để lấy
                ip_info = get_ip_info(client_ip, logger)
                if ip_info:
                    cache_manager.set(CacheType.IP_INFO, client_ip, ip_info)
                    location = ip_info.get("city")

            if not location:
                location = default_location
        else:
            # Nếu không có IP, sử dụng vị trí mặc định
            location = default_location
    # Thử lấy báo cáo thời tiết đầy đủ từ cache
    weather_cache_key = f"full_weather_{location}_{lang}"
    cached_weather_report = cache_manager.get(CacheType.WEATHER, weather_cache_key)
    if cached_weather_report:
        return ActionResponse(Action.REQLLM, cached_weather_report, None)

    # Cache không trúng, lấy dữ liệu thời tiết thời gian thực
    city_info = fetch_city_info(location, api_key, api_host)
    if not city_info:
        return ActionResponse(
            Action.REQLLM, f"Không tìm thấy thành phố liên quan: {location}，vui lòng xác nhận địa điểm có đúng không", None
        )
    soup = fetch_weather_page(city_info["fxLink"])
    if not soup:
        return ActionResponse(Action.REQLLM, None, "Yêu cầu thất bại")
    city_name, current_abstract, current_basic, temps_list = parse_weather_info(soup)

    weather_report = f"Vị trí bạn truy vấn là: {city_name}\n\nThời tiết hiện tại: {current_abstract}\n"

    # Thêm các tham số thời tiết hiện tại hợp lệ
    if current_basic:
        weather_report += "Tham số chi tiết:\n"
        for key, value in current_basic.items():
            if value != "0":  # Lọc giá trị không hợp lệ
                weather_report += f"  · {key}: {value}\n"

    # Thêm dự báo 7 ngày
    weather_report += "\nDự báo 7 ngày tới:\n"
    for date, weather, high, low in temps_list:
        weather_report += f"{date}: {weather}，nhiệt độ {low}~{high}\n"

    # Câu nhắc
    weather_report += "\n(Nếu cần thời tiết cụ thể của một ngày nào đó, vui lòng cho tôi biết ngày)"

    # Cache báo cáo thời tiết đầy đủ
    cache_manager.set(CacheType.WEATHER, weather_cache_key, weather_report)

    return ActionResponse(Action.REQLLM, weather_report, None)
