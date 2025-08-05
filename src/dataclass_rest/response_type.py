from enum import Enum
from typing import Literal

class ResponseType(Enum):
    JSON = "json"
    TEXT = "text"
    BYTES = "bytes"
    NO_CONTENT = "no_content"

ResponseTypeLiteral = Literal["json", "text", "bytes", "no_content"]