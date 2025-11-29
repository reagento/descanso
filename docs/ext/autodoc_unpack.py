from inspect import Parameter, signature
from typing import TypedDict, Unpack, get_args, get_origin, get_type_hints


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
        if get_origin(hint) != Unpack:
            new_params.append(param)
            continue
        subargs = get_args(hint)[0]
        if type(subargs) != TypedDictMeta:
            new_params.append(param)
            continue
        subargs_hints = get_type_hints(subargs)
        for key, value in subargs_hints.items():
            new_params.append(
                Parameter(
                    name=key,
                    kind=Parameter.KEYWORD_ONLY,
                    annotation=value,
                ),
            )
            hints[key] = value

    obj.__signature__ = sig.replace(parameters=new_params)


def setup(app):
    app.connect("autodoc-before-process-signature", unpack_signature)
