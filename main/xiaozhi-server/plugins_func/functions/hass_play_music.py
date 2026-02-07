from plugins_func.register import register_function, ToolType, ActionResponse, Action
from plugins_func.functions.hass_init import initialize_hass_handler
from config.logger import setup_logging
import asyncio
import requests
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

hass_play_music_function_desc = {
    "type": "function",
    "function": {
        "name": "hass_play_music",
        "description": "Sử dụng khi người dùng muốn nghe nhạc, sách nói, phát audio tương ứng trong trình phát media (media_player) trong phòng",
        "parameters": {
            "type": "object",
            "properties": {
                "media_content_id": {
                    "type": "string",
                    "description": "Có thể là tên album, tên bài hát, ca sĩ của nhạc hoặc sách nói, nếu không chỉ định thì điền random",
                },
                "entity_id": {
                    "type": "string",
                    "description": "ID thiết bị của loa cần thao tác, entity_id trong homeassistant, bắt đầu bằng media_player",
                },
            },
            "required": ["media_content_id", "entity_id"],
        },
    },
}


@register_function(
    "hass_play_music", hass_play_music_function_desc, ToolType.SYSTEM_CTL
)
def hass_play_music(conn: "ConnectionHandler", entity_id="", media_content_id="random"):
    try:
        # Thực thi lệnh phát nhạc
        future = asyncio.run_coroutine_threadsafe(
            handle_hass_play_music(conn, entity_id, media_content_id), conn.loop
        )
        ha_response = future.result()
        return ActionResponse(
            action=Action.RESPONSE, result="Ý định thoát đã được xử lý", response=ha_response
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"Lỗi xử lý ý định phát nhạc: {e}")


async def handle_hass_play_music(
    conn: "ConnectionHandler", entity_id, media_content_id
):
    ha_config = initialize_hass_handler(conn)
    api_key = ha_config.get("api_key")
    base_url = ha_config.get("base_url")
    url = f"{base_url}/api/services/music_assistant/play_media"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"entity_id": entity_id, "media_id": media_content_id}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return f"Đang phát nhạc {media_content_id}"
    else:
        return f"Phát nhạc thất bại, mã lỗi: {response.status_code}"
