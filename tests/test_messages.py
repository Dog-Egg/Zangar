from typing import Any

import pytest

import zangar as z
from zangar._messages import DefaultMessages


def test_DefaultMessages():
    class MyDefaultMessages(DefaultMessages):
        def default(self, name: str, value: Any, ctx: dict):
            if name == "field_required":
                return "Required"
            if name == "str_min":
                return f"Min length is {ctx['min']}"
            return super().default(name, value, ctx)

    with MyDefaultMessages():
        with pytest.raises(z.ValidationError) as e:
            z.object({"a": z.field(z.str())}).parse({})
        assert e.value.format_errors() == [{"loc": ["a"], "msgs": ["Required"]}]

        with pytest.raises(z.ValidationError) as e:
            z.str().min(1).parse("")
        assert e.value.format_errors() == [{"msgs": ["Min length is 1"]}]

        with pytest.raises(z.ValidationError) as e:
            z.str().max(1).parse("123")
        assert e.value.format_errors() == [
            {"msgs": ["The maximum length of the string is 1"]}
        ]

        # transform
        with pytest.raises(z.ValidationError) as e:
            z.transform(int).parse("a")
        assert e.value.format_errors() == [
            {"msgs": ["invalid literal for int() with base 10: 'a'"]}
        ]

    with pytest.raises(z.ValidationError) as e:
        z.object({"a": z.field(z.str())}).parse({})
    assert e.value.format_errors() == [
        {"loc": ["a"], "msgs": ["This field is required"]}
    ]
