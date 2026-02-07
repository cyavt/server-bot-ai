"""Trình quản lý MCP phía máy chủ"""

import asyncio
import os
import json
from typing import Dict, Any, List

from mcp.types import LoggingMessageNotificationParams

from config.config_loader import get_project_dir
from config.logger import setup_logging
from .mcp_client import ServerMCPClient

TAG = __name__
logger = setup_logging()


class ServerMCPManager:
    """Trình quản lý tập trung cho nhiều dịch vụ MCP phía máy chủ"""

    def __init__(self, conn) -> None:
        """Khởi tạo trình quản lý MCP"""
        self.conn = conn
        self.config_path = get_project_dir() + "data/.mcp_server_settings.json"
        if not os.path.exists(self.config_path):
            self.config_path = ""
            logger.bind(tag=TAG).warning(
                f"Vui lòng kiểm tra file cấu hình dịch vụ mcp: data/.mcp_server_settings.json"
            )
        self.clients: Dict[str, ServerMCPClient] = {}
        self.tools = []
        self._init_lock = asyncio.Lock()

    def load_config(self) -> Dict[str, Any]:
        """Tải cấu hình dịch vụ MCP"""
        if len(self.config_path) == 0:
            return {}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("mcpServers", {})
        except Exception as e:
            logger.bind(tag=TAG).error(
                f"Error loading MCP config from {self.config_path}: {e}"
            )
            return {}

    async def _init_server(self, name: str, srv_config: Dict[str, Any]):
        """Khởi tạo một dịch vụ MCP đơn lẻ"""
        # Kiểm tra cấu hình có placeholder chưa được thay thế không
        if "command" in srv_config:
            args = srv_config.get("args", [])
            if any("YOUR_" in str(arg) or "your_" in str(arg).lower() for arg in args):
                logger.bind(tag=TAG).warning(
                    f"Bỏ qua máy chủ MCP {name}: Cấu hình chứa placeholder chưa được thay thế (YOUR_*). "
                    f"Vui lòng cập nhật file data/.mcp_server_settings.json với cấu hình thực tế."
                )
                return
            
            # Kiểm tra command có hợp lệ không
            command = srv_config.get("command")
            if not command or command.strip() == "":
                logger.bind(tag=TAG).warning(
                    f"Bỏ qua máy chủ MCP {name}: Command không được chỉ định hoặc rỗng."
                )
                return
        
        if "url" in srv_config:
            url = srv_config.get("url", "")
            if "YOUR_" in url or "your_" in url.lower() or "localhost" in url.lower():
                # Kiểm tra xem có phải là placeholder không
                if "YOUR_" in url or url == "http://localhost:8080/sse" or url == "http://localhost:8000/mcp":
                    logger.bind(tag=TAG).warning(
                        f"Bỏ qua máy chủ MCP {name}: URL chứa placeholder hoặc localhost chưa được cấu hình đúng. "
                        f"URL hiện tại: {url}. Vui lòng cập nhật file data/.mcp_server_settings.json với URL thực tế."
                    )
                    return
        
        client = None
        try:
            # Khởi tạo client MCP phía máy chủ
            logger.bind(tag=TAG).info(f"Khởi tạo client MCP phía máy chủ: {name}")
            client = ServerMCPClient(srv_config)
            # Đặt thời gian chờ là 10 giây
            await asyncio.wait_for(client.initialize(logging_callback=self.logging_callback), timeout=10)

            # Sử dụng khóa để bảo vệ việc sửa đổi trạng thái dùng chung
            async with self._init_lock:
                self.clients[name] = client
                client_tools = client.get_available_tools()
                self.tools.extend(client_tools)

        except asyncio.TimeoutError:
            logger.bind(tag=TAG).warning(
                f"Không thể khởi tạo máy chủ MCP {name}: Hết thời gian chờ. "
                f"Vui lòng kiểm tra cấu hình và đảm bảo máy chủ MCP đang chạy."
            )
            if client:
                await client.cleanup()
        except ValueError as e:
            # Lỗi validation hoặc command không tìm thấy
            error_msg = str(e)
            if "validation error" in error_msg.lower() or "không tìm thấy" in error_msg.lower():
                logger.bind(tag=TAG).warning(
                    f"Bỏ qua máy chủ MCP {name}: {error_msg}. "
                    f"Vui lòng kiểm tra cấu hình trong file data/.mcp_server_settings.json."
                )
            else:
                logger.bind(tag=TAG).error(
                    f"Không thể khởi tạo máy chủ MCP {name}: {error_msg}"
                )
            if client:
                await client.cleanup()
        except Exception as e:
            error_msg = str(e)
            # Kiểm tra xem có phải lỗi validation không
            if "validation error" in error_msg.lower():
                logger.bind(tag=TAG).warning(
                    f"Bỏ qua máy chủ MCP {name}: Lỗi validation cấu hình. "
                    f"Chi tiết: {error_msg}. Vui lòng kiểm tra file data/.mcp_server_settings.json."
                )
            # Kiểm tra xem có phải lỗi kết nối không
            elif "ConnectTimeout" in error_msg or "Connection" in error_msg:
                logger.bind(tag=TAG).warning(
                    f"Không thể kết nối đến máy chủ MCP {name}: {error_msg}. "
                    f"Vui lòng kiểm tra URL và đảm bảo máy chủ MCP đang chạy."
                )
            else:
                logger.bind(tag=TAG).error(
                    f"Không thể khởi tạo máy chủ MCP {name}: {error_msg}"
                )
            if client:
                await client.cleanup()

    async def initialize_servers(self) -> None:
        """Khởi tạo tất cả các dịch vụ MCP"""
        config = self.load_config()
        tasks = []
        for name, srv_config in config.items():
            if not srv_config.get("command") and not srv_config.get("url"):
                logger.bind(tag=TAG).warning(
                    f"Bỏ qua máy chủ {name}: không chỉ định command hoặc url"
                )
                continue
            
            tasks.append(self._init_server(name, srv_config))
        
        if tasks:
            await asyncio.gather(*tasks)

        # Xuất danh sách công cụ MCP phía máy chủ hiện được hỗ trợ
        if hasattr(self.conn, "func_handler") and self.conn.func_handler:
            # Làm mới bộ đệm công cụ để đảm bảo công cụ MCP phía máy chủ được tải đúng cách
            if hasattr(self.conn.func_handler, "tool_manager"):
                self.conn.func_handler.tool_manager.refresh_tools()
            self.conn.func_handler.current_support_functions()

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Lấy định nghĩa function công cụ của tất cả các dịch vụ"""
        return self.tools

    def is_mcp_tool(self, tool_name: str) -> bool:
        """Kiểm tra xem có phải là công cụ MCP không"""
        for tool in self.tools:
            if (
                tool.get("function") is not None
                and tool["function"].get("name") == tool_name
            ):
                return True
        return False

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Thực thi gọi công cụ, sẽ thử kết nối lại khi thất bại"""
        logger.bind(tag=TAG).info(f"Thực thi công cụ MCP phía máy chủ {tool_name}, tham số: {arguments}")

        max_retries = 3  # Số lần thử lại tối đa
        retry_interval = 2  # Khoảng thời gian giữa các lần thử (giây)

        # Tìm client tương ứng
        client_name = None
        target_client = None
        for name, client in self.clients.items():
            if client.has_tool(tool_name):
                client_name = name
                target_client = client
                break

        if not target_client:
            raise ValueError(f"Công cụ {tool_name} không được tìm thấy trong bất kỳ dịch vụ MCP nào")

        # Gọi công cụ với cơ chế thử lại
        for attempt in range(max_retries):
            try:
                return await target_client.call_tool(tool_name, arguments, progress_callback=self.progress_callback)
            except Exception as e:
                # Ném ngoại lệ trực tiếp khi lần thử cuối cùng thất bại
                if attempt == max_retries - 1:
                    raise

                logger.bind(tag=TAG).warning(
                    f"Thực thi công cụ {tool_name} thất bại (thử {attempt+1}/{max_retries}): {e}"
                )

                # Thử kết nối lại
                logger.bind(tag=TAG).info(
                    f"Thử kết nối lại client MCP {client_name} trước khi thử lại"
                )
                try:
                    # Đóng kết nối cũ
                    await target_client.cleanup()

                    # Khởi tạo lại client
                    config = self.load_config()
                    if client_name in config:
                        client = ServerMCPClient(config[client_name])
                        await client.initialize(logging_callback=self.logging_callback)
                        self.clients[client_name] = client
                        target_client = client
                        logger.bind(tag=TAG).info(
                            f"Kết nối lại client MCP thành công: {client_name}"
                        )
                    else:
                        logger.bind(tag=TAG).error(
                            f"Không thể kết nối lại client MCP {client_name}: không tìm thấy cấu hình"
                        )
                except Exception as reconnect_error:
                    logger.bind(tag=TAG).error(
                        f"Kết nối lại client MCP {client_name} thất bại: {reconnect_error}"
                    )

                # Chờ một khoảng thời gian trước khi thử lại
                await asyncio.sleep(retry_interval)

    async def cleanup_all(self) -> None:
        """Đóng tất cả các client MCP"""
        for name, client in list(self.clients.items()):
            try:
                if hasattr(client, "cleanup"):
                    await asyncio.wait_for(client.cleanup(), timeout=20)
                logger.bind(tag=TAG).info(f"Client MCP phía máy chủ đã đóng: {name}")
            except (asyncio.TimeoutError, Exception) as e:
                logger.bind(tag=TAG).error(f"Xảy ra lỗi khi đóng client MCP phía máy chủ {name}: {e}")
        self.clients.clear()

    # Phương thức callback tùy chọn

    async def logging_callback(self, params: LoggingMessageNotificationParams):
        logger.bind(tag=TAG).info(f"[Server Log - {params.level.upper()}] {params.data}")

    async def progress_callback(self, progress: float, total: float | None, message: str | None) -> None:
        logger.bind(tag=TAG).info(f"[Progress {progress}/{total}]: {message}")