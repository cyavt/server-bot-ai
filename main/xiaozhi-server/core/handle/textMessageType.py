from enum import Enum


class TextMessageType(Enum):
    """Liệt kê loại tin nhắn"""
    HELLO = "hello"
    ABORT = "abort"
    LISTEN = "listen"
    IOT = "iot"
    MCP = "mcp"
    SERVER = "server"
    PING = "ping"
