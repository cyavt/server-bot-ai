import random
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler


TAG = __name__
logger = setup_logging()

GET_NEWS_FROM_CHINANEWS_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_news_from_chinanews",
        "description": (
            "Lấy tin tức mới nhất, chọn ngẫu nhiên một tin để phát sóng."
            "Người dùng có thể chỉ định loại tin tức, như tin xã hội, tin công nghệ, tin quốc tế v.v."
            "Nếu không chỉ định, mặc định phát sóng tin xã hội."
            "Người dùng có thể yêu cầu lấy nội dung chi tiết, lúc này sẽ lấy nội dung chi tiết của tin tức."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Loại tin tức, ví dụ xã hội, công nghệ, quốc tế. Tham số tùy chọn, nếu không cung cấp thì sử dụng loại mặc định",
                },
                "detail": {
                    "type": "boolean",
                    "description": "Có lấy nội dung chi tiết không, mặc định là false. Nếu là true, sẽ lấy nội dung chi tiết của tin tức trước đó",
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


def fetch_news_from_rss(rss_url):
    """Lấy danh sách tin tức từ nguồn RSS"""
    try:
        response = requests.get(rss_url)
        response.raise_for_status()

        # Phân tích XML
        root = ET.fromstring(response.content)

        # Tìm tất cả phần tử item (mục tin tức)
        news_items = []
        for item in root.findall(".//item"):
            title = (
                item.find("title").text if item.find("title") is not None else "Không có tiêu đề"
            )
            link = item.find("link").text if item.find("link") is not None else "#"
            description = (
                item.find("description").text
                if item.find("description") is not None
                else "Không có mô tả"
            )
            pubDate = (
                item.find("pubDate").text
                if item.find("pubDate") is not None
                else "Thời gian không xác định"
            )

            news_items.append(
                {
                    "title": title,
                    "link": link,
                    "description": description,
                    "pubDate": pubDate,
                }
            )

        return news_items
    except Exception as e:
        logger.bind(tag=TAG).error(f"Lấy tin tức RSS thất bại: {e}")
        return []


def fetch_news_detail(url):
    """Lấy nội dung trang chi tiết tin tức và tóm tắt"""
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Thử trích xuất nội dung chính (bộ chọn ở đây cần điều chỉnh theo cấu trúc website thực tế)
        content_div = soup.select_one(
            ".content_desc, .content, article, .article-content"
        )
        if content_div:
            paragraphs = content_div.find_all("p")
            content = "\n".join(
                [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
            )
            return content
        else:
            # Nếu không tìm thấy vùng nội dung cụ thể, thử lấy tất cả đoạn văn
            paragraphs = soup.find_all("p")
            content = "\n".join(
                [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
            )
            return content[:2000]  # Giới hạn độ dài
    except Exception as e:
        logger.bind(tag=TAG).error(f"Lấy chi tiết tin tức thất bại: {e}")
        return "Không thể lấy nội dung chi tiết"


def map_category(category_text):
    """Ánh xạ loại tiếng Trung do người dùng nhập vào khóa loại trong tệp cấu hình"""
    if not category_text:
        return None

    # Từ điển ánh xạ loại, hiện hỗ trợ tin xã hội, quốc tế, tài chính, nếu cần thêm loại, xem tệp cấu hình
    category_map = {
        # Tin xã hội
        "社会": "society_rss_url",
        "社会新闻": "society_rss_url",
        # Tin quốc tế
        "国际": "world_rss_url",
        "国际新闻": "world_rss_url",
        # Tin tài chính
        "财经": "finance_rss_url",
        "财经新闻": "finance_rss_url",
        "金融": "finance_rss_url",
        "经济": "finance_rss_url",
    }

    # Chuyển thành chữ thường và loại bỏ khoảng trắng
    normalized_category = category_text.lower().strip()

    # Trả về kết quả ánh xạ, nếu không có mục khớp thì trả về đầu vào gốc
    return category_map.get(normalized_category, category_text)


@register_function(
    "get_news_from_chinanews",
    GET_NEWS_FROM_CHINANEWS_FUNCTION_DESC,
    ToolType.SYSTEM_CTL,
)
def get_news_from_chinanews(
    conn: "ConnectionHandler",
    category: str = None,
    detail: bool = False,
    lang: str = "zh_CN",
):
    """Lấy tin tức và chọn ngẫu nhiên một tin để phát sóng, hoặc lấy nội dung chi tiết của tin tức trước đó"""
    try:
        # Nếu detail là True, lấy nội dung chi tiết của tin tức trước đó
        if detail:
            if (
                not hasattr(conn, "last_news_link")
                or not conn.last_news_link
                or "link" not in conn.last_news_link
            ):
                return ActionResponse(
                    Action.REQLLM,
                    "Xin lỗi, không tìm thấy tin tức đã truy vấn gần đây, vui lòng lấy một tin trước.",
                    None,
                )

            link = conn.last_news_link.get("link")
            title = conn.last_news_link.get("title", "Tiêu đề không xác định")

            if link == "#":
                return ActionResponse(
                    Action.REQLLM, "Xin lỗi, tin tức này không có liên kết khả dụng để lấy nội dung chi tiết.", None
                )

            logger.bind(tag=TAG).debug(f"Lấy chi tiết tin tức: {title}, URL={link}")

            # Lấy chi tiết tin tức
            detail_content = fetch_news_detail(link)

            if not detail_content or detail_content == "Không thể lấy nội dung chi tiết":
                return ActionResponse(
                    Action.REQLLM,
                    f"Xin lỗi, không thể lấy nội dung chi tiết của《{title}》，có thể liên kết đã hết hạn hoặc cấu trúc website đã thay đổi.",
                    None,
                )

            # Xây dựng báo cáo chi tiết
            detail_report = (
                f"Dựa trên dữ liệu sau đây, sử dụng {lang} để trả lời yêu cầu truy vấn chi tiết tin tức của người dùng:\n\n"
                f"Tiêu đề tin tức: {title}\n"
                f"Nội dung chi tiết: {detail_content}\n\n"
                f"(Vui lòng tóm tắt nội dung tin tức trên, trích xuất thông tin quan trọng, phát sóng cho người dùng một cách tự nhiên, trôi chảy,"
                f"không đề cập đây là tóm tắt, giống như đang kể một câu chuyện tin tức hoàn chỉnh)"
            )

            return ActionResponse(Action.REQLLM, detail_report, None)

        # Nếu không, lấy danh sách tin tức và chọn ngẫu nhiên một tin
        # Lấy URL RSS từ cấu hình
        rss_config = conn.config.get("plugins", {}).get("get_news_from_chinanews", {})
        default_rss_url = rss_config.get(
            "default_rss_url", "https://www.chinanews.com.cn/rss/society.xml"
        )

        # Ánh xạ loại do người dùng nhập vào khóa loại trong cấu hình
        mapped_category = map_category(category)

        # Nếu cung cấp loại, thử lấy URL tương ứng từ cấu hình
        rss_url = default_rss_url
        if mapped_category and mapped_category in rss_config:
            rss_url = rss_config[mapped_category]

        logger.bind(tag=TAG).info(
            f"Lấy tin tức: loại gốc={category}, loại ánh xạ={mapped_category}, URL={rss_url}"
        )

        # Lấy danh sách tin tức
        news_items = fetch_news_from_rss(rss_url)

        if not news_items:
            return ActionResponse(
                Action.REQLLM, "Xin lỗi, không thể lấy thông tin tin tức, vui lòng thử lại sau.", None
            )

        # Chọn ngẫu nhiên một tin
        selected_news = random.choice(news_items)

        # Lưu liên kết tin tức hiện tại vào đối tượng kết nối, để truy vấn chi tiết sau này
        if not hasattr(conn, "last_news_link"):
            conn.last_news_link = {}
        conn.last_news_link = {
            "link": selected_news.get("link", "#"),
            "title": selected_news.get("title", "Tiêu đề không xác định"),
        }

        # Xây dựng báo cáo tin tức
        news_report = (
            f"Dựa trên dữ liệu sau đây, sử dụng {lang} để trả lời yêu cầu truy vấn tin tức của người dùng:\n\n"
            f"Tiêu đề tin tức: {selected_news['title']}\n"
            f"Thời gian phát hành: {selected_news['pubDate']}\n"
            f"Nội dung tin tức: {selected_news['description']}\n"
            f"(Vui lòng phát sóng tin tức này cho người dùng một cách tự nhiên, trôi chảy, có thể tóm tắt nội dung một cách phù hợp,"
            f"chỉ cần đọc trực tiếp tin tức, không cần nội dung thừa."
            f"Nếu người dùng hỏi thêm chi tiết, thông báo cho người dùng có thể nói 'vui lòng giới thiệu chi tiết tin tức này' để lấy thêm nội dung)"
        )

        return ActionResponse(Action.REQLLM, news_report, None)

    except Exception as e:
        logger.bind(tag=TAG).error(f"Lỗi lấy tin tức: {e}")
        return ActionResponse(
            Action.REQLLM, "Xin lỗi, đã xảy ra lỗi khi lấy tin tức, vui lòng thử lại sau.", None
        )
