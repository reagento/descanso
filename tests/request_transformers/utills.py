from descanso.request import FieldIn, RequestTransformer


def consumed_fields(
    fields: list[FieldIn],
    transformer: RequestTransformer,
) -> list[str]:
    return [f.name for f in fields if transformer in f.consumed_by]
