from inspect import Parameter, signature
from typing import TypedDict, get_args, get_origin, get_type_hints

try:
    from typing import Unpack
except ImportError:
    Unpack = None


class _ExampleTypedDict(TypedDict):
    pass


TypedDictMeta = type(_ExampleTypedDict)


def unpack_signature(app, obj, bound_method):
    if not bound_method:
        return

    sig = signature(obj)
    hints = get_type_hints(obj)
    new_params = []
    for param in sig.parameters.values():
        hint = hints.get(param.name)
        # Not an Unpack[...] annotation → keep param as-is
        if get_origin(hint) != Unpack:
            new_params.append(param)
            continue
        # Expect Unpack[SomeTypedDict]
        args = get_args(hint)
        if len(args) != 1:
            new_params.append(param)
            continue
        typed_dict_type = args[0]
        if type(typed_dict_type) != TypedDictMeta:
            new_params.append(param)
            continue
        for key, annotation in get_type_hints(typed_dict_type).items():
            new_params.append(
                Parameter(
                    name=key,
                    kind=Parameter.KEYWORD_ONLY,
                    annotation=annotation,
                ),
            )

    obj.__signature__ = sig.replace(parameters=new_params)


def setup(app):
    if Unpack:
        app.connect("autodoc-before-process-signature", unpack_signature)
