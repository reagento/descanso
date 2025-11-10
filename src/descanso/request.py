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
class Field:
    name: str
    type_hint: Any
    dest: FieldDestintation

    def replace_dest(self, dest: FieldDestintation) -> "Field":
        return Field(
            name=self.name,
            type_hint=self.type_hint,
            dest=dest,
        )


@runtime_checkable
class RequestTransformer(Protocol):
    def transform_fields(self, fields: list[Field]) -> list[Field]:
        return fields

    def transform_request(
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        return request
