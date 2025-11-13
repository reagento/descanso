from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    IO,
    Any,
    Protocol,
    TypeAlias,
    TypeVar,
    runtime_checkable,
)

T = TypeVar("T")
KeyValue: TypeAlias = tuple[str, T]
KeyValueList: TypeAlias = list[KeyValue[T]]


@dataclass
class FileData:
    contents: str | IO | None
    content_type: str | None = None
    filename: str | None = None


@dataclass
class HttpRequest:
    body: Any = None
    files: KeyValueList[FileData] = field(default_factory=list)
    query_params: KeyValueList[Any] = field(default_factory=list)
    headers: KeyValueList[str | bytes] = field(default_factory=list)
    extras: KeyValueList[Any] = field(default_factory=list)
    url: str = ""
    method: str = "GET"


class FieldDestintation(Enum):
    URL = "url"
    HEADER = "headers"
    BODY = "body"
    FILE = "files"
    QUERY = "query_params"
    EXTRA = "extras"
    UNDEFINED = "undefined"


@dataclass
class FieldIn:
    name: str
    type_hint: Any
    consumed_by: list["RequestTransformer"]


@dataclass
class FieldOut:
    name: str | None
    dest: FieldDestintation
    type_hint: Any


@runtime_checkable
class RequestTransformer(Protocol):
    def transform_fields(
        self,
        fields_in: Sequence[FieldIn],
    ) -> Sequence[FieldOut]:
        return []

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        return request
