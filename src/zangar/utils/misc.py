import typing


def merge_meta(m1: dict, m2: dict):
    o1 = m1.pop("oas", None)
    o2 = m2.pop("oas", None)
    if o1 is not None and o2 is not None:

        def oas(obj: dict):
            assign_oas(obj, o1)
            assign_oas(obj, o2)

    else:
        oas = o1 or o2
    return {**m1, **m2, "oas": oas}


def assign_oas(
    target: dict, source: typing.Union[dict, typing.Callable[[dict], None]]
) -> dict:
    if isinstance(source, dict):
        target.update(source)
    else:
        source(target)
    return target
