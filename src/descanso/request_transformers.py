import itertools
import json
import string
from collections.abc import Callable, Iterator, Sequence
from inspect import getfullargspec
from typing import Any, get_type_hints

from .client import Dumper
from .request import (
    BaseRequestTransformer,
    FieldDestination,
    FieldIn,
    FieldOut,
    FileData,
    HttpRequest,
    KeyValue,
)


def _base_field_name(field_name: str) -> str:
    field_name, *_ = field_name.split(".", 1)
    field_name, *_ = field_name.split("[", 1)
    return field_name


def get_params_from_string(template: str) -> list[str]:
    parsed_format = list(string.Formatter().parse(template))
    return [_base_field_name(x[1]) for x in parsed_format if x[1]]


def get_params_from_callable(
    template: Callable[..., Any],
) -> list[str]:
    url_template_func_arg_spec = getfullargspec(template)
    return url_template_func_arg_spec.args


DataTemplate = Callable[..., Any] | str | None


class DestTransformer(BaseRequestTransformer):
    def __init__(
        self,
        name_out: str,
        template: DataTemplate,
        dest: FieldDestination,
    ) -> None:
        self.name_out = name_out
        self.dest = dest
        self.original_template = template
        self.type_hint = Any
        if template is None:
            self.template = lambda **kwargs: kwargs[name_out]
            self.args = [name_out]
            self.type_hint = Any
        elif isinstance(template, str):
            self.template = template.format
            self.args = get_params_from_string(template)
            self.type_hint = str
        else:
            self.template = template
            self.args = get_params_from_callable(template)
            self.type_hint = get_type_hints(template).get("return", Any)

    def transform_fields(
        self,
        fields: Sequence[FieldIn],
    ) -> Sequence[FieldOut]:
        type_hint = self.type_hint
        for field in fields:
            if field.name in self.args:
                field.consumed_by.append(self)
                if self.original_template is None:
                    type_hint = field.type_hint
        return [
            FieldOut(
                name=self.name_out,
                dest=self.dest,
                type_hint=type_hint,
            ),
        ]

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        request_field = getattr(request, self.dest.value)
        data = self.template(
            **{k: v for k, v in data.items() if k in self.args},
        )
        request_field.append((self.name_out, data))
        return request

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"{self.name_out!r}, "
            f"{self.original_template!r}, "
            f"{self.dest!r}"
            f")"
        )


class Header(DestTransformer):
    def __init__(self, header: str, template: DataTemplate = None):
        super().__init__(
            name_out=header,
            template=template,
            dest=FieldDestination.HEADER,
        )


class Extra(DestTransformer):
    def __init__(self, header: str, template: DataTemplate = None):
        super().__init__(
            name_out=header,
            template=template,
            dest=FieldDestination.EXTRA,
        )


class Query(DestTransformer):
    def __init__(self, name_out: str, template: DataTemplate = None):
        super().__init__(
            name_out=name_out,
            template=template,
            dest=FieldDestination.QUERY,
        )


class Url(BaseRequestTransformer):
    def __init__(self, template: Callable | str):
        self._field_out = FieldOut(
            name=None,
            dest=FieldDestination.URL,
            type_hint=str,
        )
        self._original_template = template
        if isinstance(template, str):
            self.template = template.format
            self.args = get_params_from_string(template)
        else:
            self.template = template
            self.args = get_params_from_callable(template)

    def transform_fields(
        self,
        fields: Sequence[FieldIn],
    ) -> Sequence[FieldOut]:
        for field in fields:
            if field.name in self.args:
                field.consumed_by.append(self)
        return [self._field_out]

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        request.url = self.template(
            **{k: v for k, v in data.items() if k in self.args},
        )
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self._original_template!r})"


class File(BaseRequestTransformer):
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

    def transform_fields(
        self,
        fields: Sequence[FieldIn],
    ) -> Sequence[FieldOut]:
        for field in fields:
            if field.name == self.arg:
                field.consumed_by.append(self)
                return [
                    FieldOut(
                        name=self.filefield,
                        dest=FieldDestination.FILE,
                        type_hint=field.type_hint,
                    ),
                ]
        return []

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
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


class Body(BaseRequestTransformer):
    def __init__(self, arg: str):
        self.arg = arg

    def transform_fields(
        self,
        fields: Sequence[FieldIn],
    ) -> Sequence[FieldOut]:
        for field in fields:
            if field.name == self.arg:
                field.consumed_by.append(self)
                return [
                    FieldOut(
                        name=None,
                        dest=FieldDestination.BODY,
                        type_hint=field.type_hint,
                    ),
                ]
        return []

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        if self.arg not in data:
            return request
        request.body = data[self.arg]
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.arg!r})"


class BodyModelDump(BaseRequestTransformer):
    def __init__(self, dumper: Dumper) -> None:
        self.dumper = dumper

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        type_hint = next(
            (
                f.type_hint
                for f in fields_out
                if f.dest == FieldDestination.BODY
            ),
            Any,
        )
        request.body = self.dumper.dump(request.body, type_hint)
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.dumper!r})"


class QueryModelDump(BaseRequestTransformer):
    def __init__(self, dumper: Dumper) -> None:
        self.dumper = dumper

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        types = {
            f.name: f.type_hint
            for f in fields_out
            if f.dest == FieldDestination.QUERY
        }
        request.query_params = [
            (name, self.dumper.dump(value, types.get(name, Any)))
            for name, value in request.query_params
        ]
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.dumper!r})"


class JsonDump(BaseRequestTransformer):
    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        request.body = json.dumps(request.body)
        request.headers.append(("Content-Type", "application/json"))
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class Method(BaseRequestTransformer):
    def __init__(self, method: str) -> None:
        self.method = method

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        request.method = self.method
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.method!r})"


class Skip(BaseRequestTransformer):
    def __init__(
        self,
        arg: str | None = None,
    ):
        self.arg = arg

    def transform_fields(
        self,
        fields: Sequence[FieldIn],
    ) -> Sequence[FieldOut]:
        if not self.arg:
            return []
        for field in fields:
            if field.name == self.arg:
                field.consumed_by.append(self)
        return []


class DelimiterQuery(BaseRequestTransformer):
    def __init__(self, separator: str = ",") -> None:
        self.separator = separator

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
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


class DeepObjectQuery(BaseRequestTransformer):
    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        new_params = []
        for name, value in request.query_params:
            if isinstance(value, list):
                for single_value in value:
                    new_params.append((f"{name}[]", str(single_value)))
            elif isinstance(value, dict):
                for key, single_value in value.items():
                    new_params.append((f"{name}[{key}]", str(single_value)))
            else:
                new_params.append((name, str(value)))
        request.query_params = new_params
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class PhpStyleQuery(BaseRequestTransformer):
    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        new_params = []
        for name, value in request.query_params:
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
            yield prefix, str(data)

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class FormQuery(BaseRequestTransformer):
    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        new_params = []
        for name, value in request.query_params:
            if value is None:
                continue
            if isinstance(value, list):
                for single_value in value:
                    new_params.append((f"{name}", str(single_value)))
            elif isinstance(value, dict):
                for key, single_value in value.items():
                    new_params.append((f"{key}", str(single_value)))
            else:
                new_params.append((name, str(value)))
        request.query_params = new_params
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}()"
