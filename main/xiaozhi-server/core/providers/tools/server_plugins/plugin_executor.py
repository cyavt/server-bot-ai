"""Trình thực thi công cụ plugin phía máy chủ"""

from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from ..base import ToolType, ToolDefinition, ToolExecutor
from plugins_func.register import all_function_registry, Action, ActionResponse


class ServerPluginExecutor(ToolExecutor):
    """Trình thực thi công cụ plugin phía máy chủ"""

    def __init__(self, conn: "ConnectionHandler"):
        self.conn = conn
        self.config = conn.config

    async def execute(
        self, conn: "ConnectionHandler", tool_name: str, arguments: Dict[str, Any]
    ) -> ActionResponse:
        """Thực thi công cụ plugin phía máy chủ"""
        func_item = all_function_registry.get(tool_name)
        if not func_item:
            return ActionResponse(
                action=Action.NOTFOUND, response=f"Hàm plugin {tool_name} không tồn tại"
            )

        try:
            # Quyết định cách gọi dựa trên loại công cụ
            if hasattr(func_item, "type"):
                func_type = func_item.type
                if func_type.code in [4, 5]:  # SYSTEM_CTL, IOT_CTL (cần tham số conn)
                    result = func_item.func(conn, **arguments)
                elif func_type.code == 2:  # WAIT
                    result = func_item.func(**arguments)
                elif func_type.code == 3:  # CHANGE_SYS_PROMPT
                    result = func_item.func(conn, **arguments)
                else:
                    result = func_item.func(**arguments)
            else:
                # Mặc định không truyền tham số conn
                result = func_item.func(**arguments)

            return result

        except Exception as e:
            return ActionResponse(
                action=Action.ERROR,
                response=str(e),
            )

    def get_tools(self) -> Dict[str, ToolDefinition]:
        """Lấy tất cả công cụ plugin phía máy chủ đã đăng ký"""
        tools = {}

        # Lấy các hàm cần thiết
        necessary_functions = ["handle_exit_intent", "get_lunar"]

        # Lấy các hàm từ cấu hình
        config_functions = self.config["Intent"][
            self.config["selected_module"]["Intent"]
        ].get("functions", [])

        # Chuyển đổi thành danh sách
        if not isinstance(config_functions, list):
            try:
                config_functions = list(config_functions)
            except TypeError:
                config_functions = []

        # Hợp nhất tất cả các hàm cần thiết
        all_required_functions = list(set(necessary_functions + config_functions))

        for func_name in all_required_functions:
            func_item = all_function_registry.get(func_name)
            if func_item:
                # Lấy mô tả từ đăng ký hàm
                fun_description = (
                    self.config.get("plugins", {})
                    .get(func_name, {})
                    .get("description", "")
                )
                if fun_description is not None and len(fun_description) > 0:
                    if "function" in func_item.description and isinstance(
                        func_item.description["function"], dict
                    ):
                        func_item.description["function"][
                            "description"
                        ] = fun_description
                tools[func_name] = ToolDefinition(
                    name=func_name,
                    description=func_item.description,
                    tool_type=ToolType.SERVER_PLUGIN,
                )

        return tools

    def has_tool(self, tool_name: str) -> bool:
        """Kiểm tra xem có công cụ plugin phía máy chủ được chỉ định không"""
        return tool_name in all_function_registry
