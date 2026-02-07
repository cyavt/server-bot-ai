"""Bộ xử lý điểm cuối MCP"""

import json
import asyncio
import re
import websockets
from config.logger import setup_logging
from .mcp_endpoint_client import MCPEndpointClient

TAG = __name__
logger = setup_logging()


async def connect_mcp_endpoint(mcp_endpoint_url: str, conn=None) -> MCPEndpointClient:
    """Kết nối đến điểm cuối MCP"""
    if not mcp_endpoint_url or "你的" in mcp_endpoint_url or mcp_endpoint_url == "null":
        return None

    try:
        websocket = await websockets.connect(mcp_endpoint_url)

        mcp_client = MCPEndpointClient(conn)
        mcp_client.set_websocket(websocket)

        # Khởi động trình lắng nghe tin nhắn
        asyncio.create_task(_message_listener(mcp_client))

        # Gửi tin nhắn khởi tạo
        await send_mcp_endpoint_initialize(mcp_client)

        # Gửi thông báo hoàn tất khởi tạo
        await send_mcp_endpoint_notification(mcp_client, "notifications/initialized")

        # Lấy danh sách công cụ
        await send_mcp_endpoint_tools_list(mcp_client)

        logger.bind(tag=TAG).info("Kết nối điểm cuối MCP thành công")
        return mcp_client

    except Exception as e:
        logger.bind(tag=TAG).error(f"Kết nối điểm cuối MCP thất bại: {e}")
        return None


async def _message_listener(mcp_client: MCPEndpointClient):
    """Lắng nghe tin nhắn điểm cuối MCP"""
    try:
        async for message in mcp_client.websocket:
            await handle_mcp_endpoint_message(mcp_client, message)
    except websockets.exceptions.ConnectionClosed:
        logger.bind(tag=TAG).info("Kết nối điểm cuối MCP đã đóng")
    except Exception as e:
        logger.bind(tag=TAG).error(f"Lỗi trình lắng nghe tin nhắn điểm cuối MCP: {e}")
    finally:
        await mcp_client.set_ready(False)


async def handle_mcp_endpoint_message(mcp_client: MCPEndpointClient, message: str):
    """Xử lý tin nhắn điểm cuối MCP"""
    try:
        payload = json.loads(message)
        logger.bind(tag=TAG).debug(f"Nhận tin nhắn điểm cuối MCP: {payload}")

        if not isinstance(payload, dict):
            logger.bind(tag=TAG).error("Định dạng tin nhắn điểm cuối MCP sai")
            return

        # Xử lý kết quả
        if "result" in payload:
            result = payload["result"]
            # Lấy ID tin nhắn an toàn, nếu là None thì dùng 0
            msg_id_raw = payload.get("id")
            msg_id = int(msg_id_raw) if msg_id_raw is not None else 0

            # Kiểm tra phản hồi gọi công cụ trước
            if msg_id in mcp_client.call_results:
                logger.bind(tag=TAG).debug(
                    f"Nhận phản hồi gọi công cụ, ID: {msg_id}, kết quả: {result}"
                )
                await mcp_client.resolve_call_result(msg_id, result)
                return

            if msg_id == 1:  # mcpInitializeID
                logger.bind(tag=TAG).debug("Nhận phản hồi khởi tạo điểm cuối MCP")
                if result is not None and isinstance(result, dict):
                    server_info = result.get("serverInfo")
                    if isinstance(server_info, dict):
                        name = server_info.get("name")
                        version = server_info.get("version")
                        logger.bind(tag=TAG).info(
                            f"Thông tin máy chủ điểm cuối MCP: name={name}, version={version}"
                        )
                else:
                    logger.bind(tag=TAG).warning(
                        "Kết quả phản hồi khởi tạo điểm cuối MCP trống hoặc định dạng sai"
                    )
                return

            elif msg_id == 2:  # mcpToolsListID
                logger.bind(tag=TAG).debug("Nhận phản hồi danh sách công cụ điểm cuối MCP")
                if (
                    result is not None
                    and isinstance(result, dict)
                    and "tools" in result
                ):
                    tools_data = result["tools"]
                    if not isinstance(tools_data, list):
                        logger.bind(tag=TAG).error("Định dạng danh sách công cụ sai")
                        return

                    logger.bind(tag=TAG).info(
                        f"Số lượng công cụ được hỗ trợ bởi điểm cuối MCP: {len(tools_data)}"
                    )

                    for i, tool in enumerate(tools_data):
                        if not isinstance(tool, dict):
                            continue

                        name = tool.get("name", "")
                        description = tool.get("description", "")
                        input_schema = {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        }

                        if "inputSchema" in tool and isinstance(
                            tool["inputSchema"], dict
                        ):
                            schema = tool["inputSchema"]
                            input_schema["type"] = schema.get("type", "object")
                            input_schema["properties"] = schema.get("properties", {})
                            input_schema["required"] = [
                                s
                                for s in schema.get("required", [])
                                if isinstance(s, str)
                            ]

                        new_tool = {
                            "name": name,
                            "description": description,
                            "inputSchema": input_schema,
                        }
                        await mcp_client.add_tool(new_tool)
                        logger.bind(tag=TAG).debug(f"Công cụ điểm cuối MCP #{i+1}: {name}")

                    # Thay thế tên công cụ trong tất cả mô tả công cụ
                    for tool_data in mcp_client.tools.values():
                        if "description" in tool_data:
                            description = tool_data["description"]
                            # Duyệt tất cả tên công cụ để thay thế
                            for (
                                sanitized_name,
                                original_name,
                            ) in mcp_client.name_mapping.items():
                                description = description.replace(
                                    original_name, sanitized_name
                                )
                            tool_data["description"] = description

                    next_cursor = (
                        result.get("nextCursor", "") if result is not None else ""
                    )
                    if next_cursor:
                        logger.bind(tag=TAG).info(
                            f"Có thêm công cụ, nextCursor: {next_cursor}"
                        )
                        await send_mcp_endpoint_tools_list_continue(
                            mcp_client, next_cursor
                        )
                    else:
                        await mcp_client.set_ready(True)
                        logger.bind(tag=TAG).info(
                            "Đã lấy tất cả công cụ điểm cuối MCP, client sẵn sàng"
                        )

                        # Làm mới bộ nhớ đệm công cụ, đảm bảo công cụ điểm cuối MCP được bao gồm trong danh sách hàm
                        if (
                            hasattr(mcp_client, "conn")
                            and mcp_client.conn
                            and hasattr(mcp_client.conn, "func_handler")
                            and mcp_client.conn.func_handler
                        ):
                            mcp_client.conn.func_handler.tool_manager.refresh_tools()
                            mcp_client.conn.func_handler.current_support_functions()

                        logger.bind(tag=TAG).info(
                            f"Hoàn tất lấy công cụ điểm cuối MCP, tổng cộng {len(mcp_client.tools)} công cụ"
                        )
                else:
                    logger.bind(tag=TAG).warning(
                        "Kết quả phản hồi danh sách công cụ điểm cuối MCP trống hoặc định dạng sai"
                    )
                return

        # Xử lý gọi phương thức (yêu cầu từ điểm cuối)
        elif "method" in payload:
            method = payload["method"]
            logger.bind(tag=TAG).info(f"Nhận yêu cầu điểm cuối MCP: {method}")

        elif "error" in payload:
            error_data = payload["error"]
            error_msg = error_data.get("message", "Lỗi không xác định")
            logger.bind(tag=TAG).error(f"Nhận phản hồi lỗi điểm cuối MCP: {error_msg}")

            # Lấy ID tin nhắn an toàn, nếu là None thì dùng 0
            msg_id_raw = payload.get("id")
            msg_id = int(msg_id_raw) if msg_id_raw is not None else 0

            if msg_id in mcp_client.call_results:
                await mcp_client.reject_call_result(
                    msg_id, Exception(f"Lỗi điểm cuối MCP: {error_msg}")
                )

    except json.JSONDecodeError as e:
        logger.bind(tag=TAG).error(f"Phân tích JSON tin nhắn điểm cuối MCP thất bại: {e}")
    except Exception as e:
        logger.bind(tag=TAG).error(f"Lỗi khi xử lý tin nhắn điểm cuối MCP: {e}")
        import traceback

        logger.bind(tag=TAG).error(f"Chi tiết lỗi: {traceback.format_exc()}")


async def send_mcp_endpoint_initialize(mcp_client: MCPEndpointClient):
    """Gửi tin nhắn khởi tạo điểm cuối MCP"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,  # mcpInitializeID
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {},
            },
            "clientInfo": {
                "name": "XiaozhiMCPEndpointClient",
                "version": "1.0.0",
            },
        },
    }
    message = json.dumps(payload)
    logger.bind(tag=TAG).info("Gửi tin nhắn khởi tạo điểm cuối MCP")
    await mcp_client.send_message(message)


async def send_mcp_endpoint_notification(mcp_client: MCPEndpointClient, method: str):
    """Gửi tin nhắn thông báo điểm cuối MCP"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": {},
    }
    message = json.dumps(payload)
    logger.bind(tag=TAG).debug(f"Gửi thông báo điểm cuối MCP: {method}")
    await mcp_client.send_message(message)


async def send_mcp_endpoint_tools_list(mcp_client: MCPEndpointClient):
    """Gửi yêu cầu danh sách công cụ điểm cuối MCP"""
    payload = {
        "jsonrpc": "2.0",
        "id": 2,  # mcpToolsListID
        "method": "tools/list",
    }
    message = json.dumps(payload)
    logger.bind(tag=TAG).debug("Gửi yêu cầu danh sách công cụ điểm cuối MCP")
    await mcp_client.send_message(message)


async def send_mcp_endpoint_tools_list_continue(
    mcp_client: MCPEndpointClient, cursor: str
):
    """Gửi yêu cầu danh sách công cụ điểm cuối MCP có cursor"""
    payload = {
        "jsonrpc": "2.0",
        "id": 2,  # mcpToolsListID (cùng ID cho phần tiếp theo)
        "method": "tools/list",
        "params": {"cursor": cursor},
    }
    message = json.dumps(payload)
    logger.bind(tag=TAG).info(f"Gửi yêu cầu danh sách công cụ điểm cuối MCP có cursor: {cursor}")
    await mcp_client.send_message(message)


async def call_mcp_endpoint_tool(
    mcp_client: MCPEndpointClient, tool_name: str, args: str = "{}", timeout: int = 30
):
    """
    Gọi công cụ điểm cuối MCP được chỉ định và chờ phản hồi
    """
    if not await mcp_client.is_ready():
        raise RuntimeError("Client điểm cuối MCP chưa sẵn sàng")

    if not mcp_client.has_tool(tool_name):
        raise ValueError(f"Công cụ {tool_name} không tồn tại")

    tool_call_id = await mcp_client.get_next_id()
    result_future = asyncio.Future()
    await mcp_client.register_call_result_future(tool_call_id, result_future)

    # Xử lý tham số
    try:
        if isinstance(args, str):
            # Đảm bảo chuỗi là JSON hợp lệ
            if not args.strip():
                arguments = {}
            else:
                try:
                    # Thử phân tích trực tiếp
                    arguments = json.loads(args)
                except json.JSONDecodeError:
                    # Nếu phân tích thất bại, thử hợp nhất nhiều đối tượng JSON
                    try:
                        # Sử dụng biểu thức chính quy để khớp tất cả đối tượng JSON
                        json_objects = re.findall(r"\{[^{}]*\}", args)
                        if len(json_objects) > 1:
                            # Hợp nhất tất cả đối tượng JSON
                            merged_dict = {}
                            for json_str in json_objects:
                                try:
                                    obj = json.loads(json_str)
                                    if isinstance(obj, dict):
                                        merged_dict.update(obj)
                                except json.JSONDecodeError:
                                    continue
                            if merged_dict:
                                arguments = merged_dict
                            else:
                                raise ValueError(f"Không thể phân tích bất kỳ đối tượng JSON hợp lệ nào: {args}")
                        else:
                            raise ValueError(f"Phân tích JSON tham số thất bại: {args}")
                    except Exception as e:
                        logger.bind(tag=TAG).error(
                            f"Phân tích JSON tham số thất bại: {str(e)}, tham số gốc: {args}"
                        )
                        raise ValueError(f"Phân tích JSON tham số thất bại: {str(e)}")
        elif isinstance(args, dict):
            arguments = args
        else:
            raise ValueError(f"Loại tham số sai, mong đợi chuỗi hoặc từ điển, loại thực tế: {type(args)}")

        # Đảm bảo tham số là kiểu từ điển
        if not isinstance(arguments, dict):
            raise ValueError(f"Tham số phải là kiểu từ điển, loại thực tế: {type(arguments)}")

    except Exception as e:
        if not isinstance(e, ValueError):
            raise ValueError(f"Xử lý tham số thất bại: {str(e)}")
        raise e

    actual_name = mcp_client.name_mapping.get(tool_name, tool_name)
    payload = {
        "jsonrpc": "2.0",
        "id": tool_call_id,
        "method": "tools/call",
        "params": {"name": actual_name, "arguments": arguments},
    }

    message = json.dumps(payload)
    logger.bind(tag=TAG).info(
        f"Gửi yêu cầu gọi công cụ điểm cuối MCP: {actual_name}，tham số: {json.dumps(arguments, ensure_ascii=False)}"
    )
    await mcp_client.send_message(message)

    try:
        # Chờ phản hồi hoặc hết thời gian chờ
        raw_result = await asyncio.wait_for(result_future, timeout=timeout)
        logger.bind(tag=TAG).info(
            f"Gọi công cụ điểm cuối MCP {actual_name} thành công, kết quả gốc: {raw_result}"
        )

        if isinstance(raw_result, dict):
            if raw_result.get("isError") is True:
                error_msg = raw_result.get(
                    "error", "Gọi công cụ trả về lỗi, nhưng không cung cấp thông tin lỗi cụ thể"
                )
                raise RuntimeError(f"Lỗi gọi công cụ: {error_msg}")

            content = raw_result.get("content")
            if isinstance(content, list) and len(content) > 0:
                if isinstance(content[0], dict) and "text" in content[0]:
                    # Trả về trực tiếp nội dung văn bản, không phân tích JSON
                    return content[0]["text"]
        # Nếu kết quả không phải định dạng mong đợi, chuyển đổi thành chuỗi
        return str(raw_result)
    except asyncio.TimeoutError:
        await mcp_client.cleanup_call_result(tool_call_id)
        raise TimeoutError("Yêu cầu gọi công cụ hết thời gian chờ")
    except Exception as e:
        await mcp_client.cleanup_call_result(tool_call_id)
        raise e
