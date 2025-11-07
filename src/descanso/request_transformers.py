import json
import re
import string
from inspect import getfullargspec
from typing import Callable, Any, List, Protocol

from .request import (
    RequestTransformer,
    FileData,
    Field,
    FieldDestintation,
    HttpRequest,
)


def _base_field_name(field_name: str) -> str:
    field_name, *_ = field_name.split(".", 1)
    field_name, *_ = field_name.split("[", 1)
    return field_name


def get_params_from_string(template: str) -> List[str]:
    parsed_format = list(string.Formatter().parse(template))
    return [_base_field_name(x[1]) for x in parsed_format if x[1]]


def get_params_from_callable(
    template: Callable[[dict[str, Any]], Any],
) -> List[str]:
    url_template_func_arg_spec = getfullargspec(template)
    return url_template_func_arg_spec.args


DataTemplate = Callable[[dict[str, Any]], Any] | str | None


class DestTransformer(RequestTransformer):
    def __init__(
        self,
        request_key: str,
        template: DataTemplate,
        dest: FieldDestintation,
    ) -> None:
        self._original_template = template
        if template is None:
            self.template = f"{{{request_key}}}".format
            self.args = [request_key]
        elif isinstance(template, str):
            self.template = template.format
            self.args = get_params_from_string(template)
        else:
            self.template = template
            self.args = get_params_from_callable(template)
        self.request_key = request_key
        self.dest = dest

    def transform_fields(self, fields: list[Field]) -> list[Field]:
        new_fields = []
        for field in fields:
            if field.name in self.args:
                new_fields.append(field.replace_dest(self.dest))
            else:
                new_fields.append(field)
        return new_fields

    def transform_request(
        self, request: HttpRequest, fields: dict[str, Any]
    ) -> HttpRequest:
        request_field = getattr(request, self.dest.value)
        data = self.template(
            **{k: v for k, v in fields.items() if k in self.args}
        )
        request_field.append((self.request_key, data))
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.request_key!r}, {self._original_template!r}, {self.dest!r})"


class Header(DestTransformer):
    def __init__(self, header: str, template: DataTemplate = None):
        super().__init__(
            request_key=header,
            template=template,
            dest=FieldDestintation.HEADER,
        )


class Extra(DestTransformer):
    def __init__(self, header: str, template: DataTemplate = None):
        super().__init__(
            request_key=header, template=template, dest=FieldDestintation.EXTRA
        )


class Query(DestTransformer):
    def __init__(self, header: str, template: DataTemplate = None):
        super().__init__(
            request_key=header, template=template, dest=FieldDestintation.QUERY
        )


class Url(RequestTransformer):
    def __init__(self, template: Callable | str):
        self._original_template = template
        if isinstance(template, str):
            self.template = template.format
            self.args = get_params_from_string(template)
        else:
            self.template = template
            self.args = get_params_from_callable(template)

    def transform_request(
        self,
        request: HttpRequest,
        fields: dict[str, Any],
    ) -> HttpRequest:
        request.url = self.template(
            **{k: v for k, v in fields.items() if k in self.args}
        )
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self._original_template!r})"


class File(RequestTransformer):
    def __init__(
        self,
        arg: str,
        filefield: str,
        filename: str | None = None,
        content_type: str | None = None,
    ):
        self.arg = arg
        self.filefield = filefield
        self.filename = filename
        self.content_type = content_type

    def transform_fields(self, fields: list[Field]) -> list[Field]:
        new_fields = []
        for field in fields:
            if field.name == self.arg:
                new_fields.append(field.replace_dest(FieldDestintation.FILE))
            else:
                new_fields.append(field)
        return new_fields

    def transform_request(
        self, request: HttpRequest, fields: dict[str, Any]
    ) -> HttpRequest:
        request.files.append(
            (
                self.filefield,
                FileData(
                    filename=self.filename,
                    contents=fields[self.arg],
                    content_type=self.content_type,
                ),
            )
        )
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.arg!r}, {self.filefield!r}, {self.filename!r}, {self.content_type!r})"


class Body(RequestTransformer):
    def __init__(self, arg: str):
        self.arg = arg

    def transform_fields(self, fields: list[Field]) -> list[Field]:
        new_fields = []
        for field in fields:
            if field.name == self.arg:
                new_fields.append(field.replace_dest(FieldDestintation.BODY))
            else:
                new_fields.append(field)
        return new_fields

    def transform_request(
        self, request: HttpRequest, fields: dict[str, Any]
    ) -> HttpRequest:
        request.body = fields[self.arg]
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.arg!r})"


class DumperProtocol(Protocol):
    def dump(self, data: Any, class_: Any = None) -> Any:
        raise NotImplementedError


class RetortDump(RequestTransformer):
    def __init__(self, type_hint: Any) -> None:
        self.type_hint = type_hint

    def transform_request(
        self, request: HttpRequest, fields: dict[str, Any]
    ) -> HttpRequest:
        factory: DumperProtocol = fields["self"].request_body_factory
        request.body = factory.dump(request.body, self.type_hint)
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.type_hint!r})"


class JsonDump(RequestTransformer):
    def transform_request(
        self, request: HttpRequest, fields: dict[str, Any]
    ) -> HttpRequest:
        request.body = json.dumps(request.body)
        request.headers.append(("Content-Type", "application/json"))
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class Method(RequestTransformer):
    def __init__(self, method: str) -> None:
        self.method = method

    def transform_request(
        self, request: HttpRequest, fields: dict[str, Any]
    ) -> HttpRequest:
        request.method = self.method
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.method!r})"
