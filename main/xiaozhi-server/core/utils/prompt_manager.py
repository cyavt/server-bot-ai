"""
Module quản lý prompt hệ thống
Chịu trách nhiệm quản lý và cập nhật prompt hệ thống, bao gồm khởi tạo nhanh và chức năng tăng cường bất đồng bộ
"""

import os
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from config.logger import setup_logging
from jinja2 import Template

TAG = __name__

WEEKDAY_MAP = {
    "Monday": "Thứ Hai",
    "Tuesday": "Thứ Ba",
    "Wednesday": "Thứ Tư",
    "Thursday": "Thứ Năm",
    "Friday": "Thứ Sáu",
    "Saturday": "Thứ Bảy",
    "Sunday": "Chủ Nhật",
}

EMOJI_List = [
    "😶",
    "🙂",
    "😆",
    "😂",
    "😔",
    "😠",
    "😭",
    "😍",
    "😳",
    "😲",
    "😱",
    "🤔",
    "😉",
    "😎",
    "😌",
    "🤤",
    "😘",
    "😏",
    "😴",
    "😜",
    "🙄",
]


class PromptManager:
    """Trình quản lý prompt hệ thống, chịu trách nhiệm quản lý và cập nhật prompt hệ thống"""

    def __init__(self, config: Dict[str, Any], logger=None):
        self.config = config
        self.logger = logger or setup_logging()
        self.base_prompt_template = None
        self.last_update_time = 0

        # Import trình quản lý cache toàn cục
        from core.utils.cache.manager import cache_manager, CacheType

        self.cache_manager = cache_manager
        self.CacheType = CacheType

        # Khởi tạo nguồn ngữ cảnh
        from core.utils.context_provider import ContextDataProvider

        self.context_provider = ContextDataProvider(config, self.logger)
        self.context_data = {}

        self._load_base_template()

    def _load_base_template(self):
        """Tải template prompt cơ bản"""
        try:
            template_path = self.config.get("prompt_template", None)
            if not template_path:
                template_path = "agent-base-prompt.txt"
            cache_key = f"prompt_template:{template_path}"

            # Lấy từ cache trước
            cached_template = self.cache_manager.get(self.CacheType.CONFIG, cache_key)
            if cached_template is not None:
                self.base_prompt_template = cached_template
                self.logger.bind(tag=TAG).debug("Tải template prompt cơ bản từ cache")
                return

            # Cache không có, đọc từ file
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    template_content = f.read()

                # Lưu vào cache (loại CONFIG mặc định không tự động hết hạn, cần vô hiệu hóa thủ công)
                self.cache_manager.set(
                    self.CacheType.CONFIG, cache_key, template_content
                )
                self.base_prompt_template = template_content
                self.logger.bind(tag=TAG).debug("Tải template prompt cơ bản thành công và đã cache")
            else:
                self.logger.bind(tag=TAG).warning(f"Không tìm thấy file {template_path}")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Tải template prompt thất bại: {e}")

    def get_quick_prompt(self, user_prompt: str, device_id: str = None) -> str:
        """Lấy prompt hệ thống nhanh (sử dụng cấu hình người dùng)"""
        device_cache_key = f"device_prompt:{device_id}"
        cached_device_prompt = self.cache_manager.get(
            self.CacheType.DEVICE_PROMPT, device_cache_key
        )
        if cached_device_prompt is not None:
            self.logger.bind(tag=TAG).debug(f"Sử dụng prompt đã cache của thiết bị {device_id}")
            return cached_device_prompt
        else:
            self.logger.bind(tag=TAG).debug(
                f"Thiết bị {device_id} không có prompt đã cache, sử dụng prompt được truyền vào"
            )

        # Sử dụng prompt được truyền vào và cache (nếu có device ID)
        if device_id:
            device_cache_key = f"device_prompt:{device_id}"
            self.cache_manager.set(self.CacheType.CONFIG, device_cache_key, user_prompt)
            self.logger.bind(tag=TAG).debug(f"Prompt của thiết bị {device_id} đã được cache")

        self.logger.bind(tag=TAG).info(f"Sử dụng prompt nhanh: {user_prompt[:50]}...")
        return user_prompt

    def _get_current_time_info(self) -> tuple:
        """Lấy thông tin thời gian hiện tại"""
        from .current_time import (
            get_current_date,
            get_current_weekday,
            get_current_lunar_date,
        )

        today_date = get_current_date()
        today_weekday = get_current_weekday()
        lunar_date = get_current_lunar_date() + "\n"

        return today_date, today_weekday, lunar_date

    def _get_location_info(self, client_ip: str) -> str:
        """Lấy thông tin vị trí"""
        try:
            # Lấy từ cache trước
            cached_location = self.cache_manager.get(self.CacheType.LOCATION, client_ip)
            if cached_location is not None:
                return cached_location

            # Cache không có, gọi API để lấy
            from core.utils.util import get_ip_info

            ip_info = get_ip_info(client_ip, self.logger)
            city = ip_info.get("city", "Vị trí không xác định")
            location = f"{city}"

            # Lưu vào cache
            self.cache_manager.set(self.CacheType.LOCATION, client_ip, location)
            return location
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Lấy thông tin vị trí thất bại: {e}")
            return "Vị trí không xác định"

    def _get_weather_info(self, conn: "ConnectionHandler", location: str) -> str:
        """Lấy thông tin thời tiết"""
        try:
            # Lấy từ cache trước
            cached_weather = self.cache_manager.get(self.CacheType.WEATHER, location)
            if cached_weather is not None:
                return cached_weather

            # Cache không có, gọi hàm get_weather để lấy
            from plugins_func.functions.get_weather import get_weather
            from plugins_func.register import ActionResponse

            # Gọi hàm get_weather
            result = get_weather(conn, location=location, lang="zh_CN")
            if isinstance(result, ActionResponse):
                weather_report = result.result
                self.cache_manager.set(self.CacheType.WEATHER, location, weather_report)
                return weather_report
            return "Lấy thông tin thời tiết thất bại"

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Lấy thông tin thời tiết thất bại: {e}")
            return "Lấy thông tin thời tiết thất bại"

    def update_context_info(self, conn, client_ip: str):
        """Cập nhật thông tin ngữ cảnh đồng bộ"""
        try:
            local_address = ""
            if (
                client_ip
                and self.base_prompt_template
                and (
                    "local_address" in self.base_prompt_template
                    or "weather_info" in self.base_prompt_template
                )
            ):
                # Lấy thông tin vị trí (sử dụng cache toàn cục)
                local_address = self._get_location_info(client_ip)

            if (
                self.base_prompt_template
                and "weather_info" in self.base_prompt_template
                and local_address
            ):
                # Lấy thông tin thời tiết (sử dụng cache toàn cục)
                self._get_weather_info(conn, local_address)

            # Lấy dữ liệu ngữ cảnh được cấu hình
            if hasattr(conn, "device_id") and conn.device_id:
                if (
                    self.base_prompt_template
                    and "dynamic_context" in self.base_prompt_template
                ):
                    self.context_data = self.context_provider.fetch_all(conn.device_id)
                else:
                    self.context_data = ""

            self.logger.bind(tag=TAG).debug(f"Cập nhật thông tin ngữ cảnh hoàn tất")

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Cập nhật thông tin ngữ cảnh thất bại: {e}")

    def build_enhanced_prompt(
        self, user_prompt: str, device_id: str, client_ip: str = None, *args, **kwargs
    ) -> str:
        """Xây dựng prompt hệ thống được tăng cường"""
        if not self.base_prompt_template:
            return user_prompt

        try:
            # Lấy thông tin thời gian mới nhất (không cache)
            today_date, today_weekday, lunar_date = self._get_current_time_info()

            # Lấy thông tin ngữ cảnh đã cache
            local_address = ""
            weather_info = ""

            if client_ip:
                # Lấy thông tin vị trí (từ cache toàn cục)
                local_address = (
                    self.cache_manager.get(self.CacheType.LOCATION, client_ip) or ""
                )

                # Lấy thông tin thời tiết (từ cache toàn cục)
                if local_address:
                    weather_info = (
                        self.cache_manager.get(self.CacheType.WEATHER, local_address)
                        or ""
                    )

            # Thay thế biến template
            template = Template(self.base_prompt_template)
            enhanced_prompt = template.render(
                base_prompt=user_prompt,
                current_time="{{current_time}}",
                today_date=today_date,
                today_weekday=today_weekday,
                lunar_date=lunar_date,
                local_address=local_address,
                weather_info=weather_info,
                emojiList=EMOJI_List,
                device_id=device_id,
                client_ip=client_ip,
                dynamic_context=self.context_data,
                *args,
                **kwargs,
            )
            device_cache_key = f"device_prompt:{device_id}"
            self.cache_manager.set(
                self.CacheType.DEVICE_PROMPT, device_cache_key, enhanced_prompt
            )
            self.logger.bind(tag=TAG).info(
                f"Xây dựng prompt tăng cường thành công, độ dài: {len(enhanced_prompt)}"
            )
            return enhanced_prompt

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Xây dựng prompt tăng cường thất bại: {e}")
            return user_prompt
