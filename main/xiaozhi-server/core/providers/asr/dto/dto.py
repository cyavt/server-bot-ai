from enum import Enum
from typing import Union, Optional


class InterfaceType(Enum):
    # Loại giao diện
    STREAM = "STREAM"  # Giao diện streaming
    NON_STREAM = "NON_STREAM"  # Giao diện không streaming
    LOCAL = "LOCAL"  # Dịch vụ local
