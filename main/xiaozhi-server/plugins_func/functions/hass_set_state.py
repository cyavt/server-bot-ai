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

hass_set_state_function_desc = {
    "type": "function",
    "function": {
        "name": "hass_set_state",
        "description": "Thiết lập trạng thái thiết bị trong homeassistant, bao gồm bật, tắt, điều chỉnh độ sáng đèn, màu sắc, nhiệt độ màu, điều chỉnh âm lượng trình phát, thao tác tạm dừng, tiếp tục, tắt tiếng thiết bị",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Hành động cần thực hiện, bật thiết bị:turn_on, tắt thiết bị:turn_off, tăng độ sáng:brightness_up, giảm độ sáng:brightness_down, thiết lập độ sáng:brightness_value, tăng âm lượng:volume_up, giảm âm lượng:volume_down, thiết lập âm lượng:volume_set, thiết lập nhiệt độ màu:set_kelvin, thiết lập màu sắc:set_color, tạm dừng thiết bị:pause, tiếp tục thiết bị:continue, tắt tiếng/hủy tắt tiếng:volume_mute",
                        },
                        "input": {
                            "type": "integer",
                            "description": "Chỉ cần khi thiết lập âm lượng, thiết lập độ sáng, giá trị hợp lệ là 1-100, tương ứng với 1%-100% âm lượng và độ sáng",
                        },
                        "is_muted": {
                            "type": "string",
                            "description": "Chỉ cần khi thiết lập thao tác tắt tiếng, khi thiết lập tắt tiếng giá trị này là true, khi hủy tắt tiếng giá trị này là false",
                        },
                        "rgb_color": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Chỉ cần khi thiết lập màu sắc, điền giá trị rgb của màu mục tiêu ở đây",
                        },
                    },
                    "required": ["type"],
                },
                "entity_id": {
                    "type": "string",
                    "description": "ID thiết bị cần thao tác, entity_id trong homeassistant",
                },
            },
            "required": ["state", "entity_id"],
        },
    },
}


@register_function("hass_set_state", hass_set_state_function_desc, ToolType.SYSTEM_CTL)
def hass_set_state(conn: "ConnectionHandler", entity_id="", state=None):
    if state is None:
        state = {}
    try:
        ha_response = handle_hass_set_state(conn, entity_id, state)
        return ActionResponse(Action.REQLLM, ha_response, None)
    except asyncio.TimeoutError:
        logger.bind(tag=TAG).error("Thiết lập trạng thái Home Assistant hết thời gian")
        return ActionResponse(Action.ERROR, "Yêu cầu hết thời gian", None)
    except Exception as e:
        error_msg = f"Thực thi thao tác Home Assistant thất bại"
        logger.bind(tag=TAG).error(error_msg)
        return ActionResponse(Action.ERROR, error_msg, None)


def handle_hass_set_state(conn: "ConnectionHandler", entity_id, state):
    ha_config = initialize_hass_handler(conn)
    api_key = ha_config.get("api_key")
    base_url = ha_config.get("base_url")
    """
    state = { "type":"brightness_up","input":"80","is_muted":"true"}
    """
    domains = entity_id.split(".")
    if len(domains) > 1:
        domain = domains[0]
    else:
        return "Thực thi thất bại, ID thiết bị sai"
    action = ""
    arg = ""
    value = ""
    if state["type"] == "turn_on":
        description = "Thiết bị đã bật"
        if domain == "cover":
            action = "open_cover"
        elif domain == "vacuum":
            action = "start"
        else:
            action = "turn_on"
    elif state["type"] == "turn_off":
        description = "Thiết bị đã tắt"
        if domain == "cover":
            action = "close_cover"
        elif domain == "vacuum":
            action = "stop"
        else:
            action = "turn_off"
    elif state["type"] == "brightness_up":
        description = "Đèn đã sáng hơn"
        action = "turn_on"
        arg = "brightness_step_pct"
        value = 10
    elif state["type"] == "brightness_down":
        description = "Đèn đã tối hơn"
        action = "turn_on"
        arg = "brightness_step_pct"
        value = -10
    elif state["type"] == "brightness_value":
        description = f"Độ sáng đã điều chỉnh đến {state['input']}"
        action = "turn_on"
        arg = "brightness_pct"
        value = state["input"]
    elif state["type"] == "set_color":
        description = f"Màu sắc đã điều chỉnh đến {state['rgb_color']}"
        action = "turn_on"
        arg = "rgb_color"
        value = state["rgb_color"]
    elif state["type"] == "set_kelvin":
        description = f"Nhiệt độ màu đã điều chỉnh đến {state['input']}K"
        action = "turn_on"
        arg = "kelvin"
        value = state["input"]
    elif state["type"] == "volume_up":
        description = "Âm lượng đã tăng"
        action = state["type"]
    elif state["type"] == "volume_down":
        description = "Âm lượng đã giảm"
        action = state["type"]
    elif state["type"] == "volume_set":
        description = f"Âm lượng đã điều chỉnh đến {state['input']}"
        action = state["type"]
        arg = "volume_level"
        value = state["input"]
        if state["input"] >= 1:
            value = state["input"] / 100
    elif state["type"] == "volume_mute":
        description = f"Thiết bị đã tắt tiếng"
        action = state["type"]
        arg = "is_volume_muted"
        value = state["is_muted"]
    elif state["type"] == "pause":
        description = f"Thiết bị đã tạm dừng"
        action = state["type"]
        if domain == "media_player":
            action = "media_pause"
        if domain == "cover":
            action = "stop_cover"
        if domain == "vacuum":
            action = "pause"
    elif state["type"] == "continue":
        description = f"Thiết bị đã tiếp tục"
        if domain == "media_player":
            action = "media_play"
        if domain == "vacuum":
            action = "start"
    else:
        return f"{domain} {state['type']} chức năng chưa được hỗ trợ"

    if arg == "":
        data = {
            "entity_id": entity_id,
        }
    else:
        data = {"entity_id": entity_id, arg: value}
    url = f"{base_url}/api/services/{domain}/{action}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=data, timeout=5)  # Đặt thời gian chờ 5 giây
    logger.bind(tag=TAG).info(
        f"Thiết lập trạng thái:{description},url:{url},mã trả về:{response.status_code}"
    )
    if response.status_code == 200:
        return description
    else:
        return f"Thiết lập thất bại, mã lỗi: {response.status_code}"
