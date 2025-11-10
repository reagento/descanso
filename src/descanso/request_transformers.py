import itertools
import json
import string
from collections.abc import Callable, Iterator
from inspect import getfullargspec
from typing import Any, get_type_hints

from .client import Dumper
from .request import (
    Field,
    FieldDestintation,
    FileData,
    HttpRequest,
    KeyValue,
    RequestTransformer,
)


def _base_field_name(field_name: str) -> str:
    field_name, *_ = field_name.split(".", 1)
    field_name, *_ = field_name.split("[", 1)
    return field_name


def get_params_from_string(template: str) -> list[str]:
    parsed_format = list(string.Formatter().parse(template))
    return [_base_field_name(x[1]) for x in parsed_format if x[1]]


def get_params_from_callable(
    template: Callable[[dict[str, Any]], Any],
) -> list[str]:
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
        self._field_type = Any
        if template is None:
            self.template = lambda **kwargs: kwargs[request_key]
            self.args = [request_key]
        elif isinstance(template, str):
            self.template = template.format
            self.args = get_params_from_string(template)
        else:
            self.template = template
            self.args = get_params_from_callable(template)
            self._field_type = get_type_hints(template).get("return", Any)
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
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        request_field = getattr(request, self.dest.value)
        data = self.template(
            **{k: v for k, v in data.items() if k in self.args},
        )
        request_field.append((self.request_key, data))
        return request

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"{self.request_key!r}, "
            f"{self._original_template!r}, "
            f"{self.dest!r}"
            f")"
        )


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
            request_key=header,
            template=template,
            dest=FieldDestintation.EXTRA,
        )


class Query(DestTransformer):
    def __init__(self, header: str, template: DataTemplate = None):
        super().__init__(
            request_key=header,
            template=template,
            dest=FieldDestintation.QUERY,
        )

    def transform_request(
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        if self.request_key in data:
            if self._original_template is None:
                data = data.copy()
                hint = next(
                    f.type_hint for f in fields if f.name == self.request_key
                )
                dumper: Dumper = data["self"].request_params_dumper
                data[self.request_key] = dumper.dump(
                    data[self.request_key],
                    hint,
                )
            elif self._field_type is not Any:
                data = data.copy()
                dumper: Dumper = data["self"].request_params_dumper
                data[self.request_key] = dumper.dump(
                    data[self.request_key],
                    self._field_type,
                )

        return super().transform_request(request, fields, data)


class Url(RequestTransformer):
    def __init__(self, template: Callable | str):
        self._original_template = template
        if isinstance(template, str):
            self.template = template.format
            self.args = get_params_from_string(template)
        else:
            self.template = template
            self.args = get_params_from_callable(template)

    def transform_fields(self, fields: list[Field]) -> list[Field]:
        new_fields = []
        for field in fields:
            if field.name in self.args:
                new_fields.append(field.replace_dest(FieldDestintation.URL))
            else:
                new_fields.append(field)
        return new_fields

    def transform_request(
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        request.url = self.template(
            **{k: v for k, v in data.items() if k in self.args},
        )
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self._original_template!r})"


class File(RequestTransformer):
    def __init__(
        self,
        arg: str,
        filefield: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ):
        self.arg = arg
        self.filefield = filefield or arg
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
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        request.files.append(
            (
                self.filefield,
                FileData(
                    filename=self.filename,
                    contents=data[self.arg],
                    content_type=self.content_type,
                ),
            ),
        )
        return request

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"{self.arg!r}, "
            f"{self.filefield!r}, "
            f"{self.filename!r}, "
            f"{self.content_type!r}"
            f")"
        )


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
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        request.body = data[self.arg]
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.arg!r})"


class RetortDump(RequestTransformer):
    def __init__(self, type_hint: Any, dumper: Dumper | None = None) -> None:
        self.type_hint = type_hint
        self.dumper = dumper

    def transform_request(
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        dumper = self.dumper or data["self"].request_body_dumper
        request.body = dumper.dump(request.body, self.type_hint)
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.type_hint!r})"


class JsonDump(RequestTransformer):
    def transform_request(
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
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
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        request.method = self.method
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.method!r})"


class Skip(RequestTransformer):
    def __init__(
        self,
        arg: str,
    ):
        self.arg = arg

    def transform_fields(self, fields: list[Field]) -> list[Field]:
        new_fields = []
        for field in fields:
            if field.name == self.arg:
                new_fields.append(field.replace_dest(FieldDestintation.EXTRA))
            else:
                new_fields.append(field)
        return new_fields


class DelimiterListQuery(RequestTransformer):
    def __init__(self, separator: str = ",") -> None:
        self.separator = separator

    def transform_request(
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        for i, (name, value) in enumerate(request.query_params):
            if isinstance(value, list):
                request.query_params[i] = (
                    name,
                    self.separator.join(map(str, value)),
                )
            elif isinstance(value, dict):
                request.query_params[i] = (
                    name,
                    self.separator.join(
                        itertools.chain.from_iterable(
                            (key, str(single_value))
                            for key, single_value in value.items()
                        ),
                    ),
                )
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.separator!r})"


class DeepObjectQuery(RequestTransformer):
    def transform_request(
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        new_params = []
        for  (name, value) in request.query_params:
            if isinstance(value, list):
                for single_value in value:
                    new_params.append((f"{name}[]", single_value))
            elif isinstance(value, dict):
                for key, single_value in value.items():
                    new_params.append((f"{name}[{key}]", single_value))
            else:
                new_params.append((name, value))
        request.query_params = new_params
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class PhpStyleQuery(RequestTransformer):
    def transform_request(
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        new_params = []
        for (name, value) in request.query_params:
            new_params.extend(self._dump(name, value))
        request.query_params = new_params
        return request

    def _dump(self, prefix: str, data: Any) -> Iterator[KeyValue[str]]:
        if isinstance(data, list):
            for i, value in enumerate(data):
                yield from self._dump(prefix + f"[{i}]", value)
        elif isinstance(data, dict):
            for key, value in data.items():
                yield from self._dump(prefix + f"[{key}]", value)
        else:
            yield prefix, data

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class FormQuery(RequestTransformer):
    def transform_request(
        self,
        request: HttpRequest,
        fields: list[Field],
        data: dict[str, Any],
    ) -> HttpRequest:
        new_params = []
        for name, value in request.query_params:
            if value is None:
                continue
            if isinstance(value, list):
                for single_value in value:
                    new_params.append((f"{name}", single_value))
            elif isinstance(value, dict):
                for key, single_value in value.items():
                    new_params.append((f"{key}", single_value))
            else:
                new_params.append((name, value))
        request.query_params = new_params
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}()"
