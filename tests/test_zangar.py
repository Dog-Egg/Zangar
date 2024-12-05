import datetime
from types import SimpleNamespace

import pytest

import zangar as z


def test_relationship_to_refinements():
    name_to_greeting = (
        z.String()
        .transform(lambda s: s.title())
        .refine(lambda s: len(s) > 3, message="Name must be at least 4 characters long")
        .transform(lambda s: f"Hello {s}")
        .refine(lambda s: "!" not in s, message="Name must not contain !")
    )

    with pytest.raises(z.ValidationError) as e:
        name_to_greeting.parse("jo")
    assert e.value.format_errors() == [
        {"msgs": ["Name must be at least 4 characters long"]}
    ]

    with pytest.raises(z.ValidationError) as e:
        name_to_greeting.parse("john!")
    assert e.value.format_errors() == [{"msgs": ["Name must not contain !"]}]

    assert name_to_greeting.parse("john") == "Hello John"


def test_multiple_error_messages():
    password = (
        z.String()
        .refine(lambda s: len(s) >= 8, message="密码至少需要8位")
        .refine(lambda s: "!" not in s, message="密码不能包含感叹号")
    )

    with pytest.raises(z.ValidationError) as e:
        password.parse("1234!")
    assert e.value.format_errors() == [
        {
            "msgs": [
                "密码至少需要8位",
                "密码不能包含感叹号",
            ],
        },
    ]


class TestSchema:
    def test_nullable_and_nonnullable(self):
        with pytest.raises(z.ValidationError) as e:
            z.String().parse(None)
        assert e.value.format_errors() == [{"msgs": ["This value is not nullable"]}]

        with pytest.raises(z.ValidationError) as e:
            z.String().nonnullable(message="不可为空").parse(None)
        assert e.value.format_errors() == [{"msgs": ["不可为空"]}]


class TestObject:
    def test_field_default(self):
        obj = z.Object(
            {
                "a": z.Field(z.String()).optional(default="Tom"),
                "b": z.Field(z.String()).optional(default=lambda: "Tom"),
                "c": z.Field(z.String()).optional(),
            }
        )
        assert obj.parse({}) == {"a": "Tom", "b": "Tom"}

    def test_field_required(self):
        obj = z.Object(
            {
                "a": z.Field(z.String()).required(message="a is required"),
            }
        )
        with pytest.raises(z.ValidationError) as e:
            obj.parse({})
        assert e.value.format_errors() == [{"msgs": ["a is required"]}]

    def test_parse_object(self):
        assert z.Object({"a": z.Field(z.String())}).parse(SimpleNamespace(a="Tom")) == {
            "a": "Tom"
        }


def test_Integer():
    with pytest.raises(z.ValidationError):
        z.Integer().parse("1.1")
