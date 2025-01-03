from types import SimpleNamespace

import pytest

import zangar as z


def test_schema():
    name_to_greeting = (
        z.transform(lambda s: s.title())
        .ensure(lambda s: len(s) > 3, message="Name must be at least 4 characters long")
        .transform(lambda s: f"Hello {s}")
        .ensure(lambda s: "!" not in s, message="Name must not contain !")
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
        z.str()
        .ensure(lambda s: len(s) >= 8, message="密码至少需要8位")
        .ensure(lambda s: "!" not in s, message="密码不能包含感叹号")
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


class TestObject:
    def test_field_default(self):
        obj = z.object(
            {
                "a": z.field(z.str()).optional(default="Tom"),
                "b": z.field(z.str()).optional(default=lambda: "Tom"),
                "c": z.field(z.str()).optional(),
            }
        )
        assert obj.parse({}) == {"a": "Tom", "b": "Tom"}

    def test_field_required(self):
        obj = z.object(
            {
                "a": z.field(z.str()).required(message="a is required"),
            }
        )
        with pytest.raises(z.ValidationError) as e:
            obj.parse({})
        assert e.value.format_errors() == [{"loc": ["a"], "msgs": ["a is required"]}]

    def test_parse_object(self):
        assert z.object({"a": z.field(z.str())}).parse(SimpleNamespace(a="Tom")) == {
            "a": "Tom"
        }


class TestList:
    def test_parse_wrong_type(self):
        with pytest.raises(z.ValidationError) as e:
            z.list(z.int()).parse(1)  # type: ignore
        assert e.value.format_errors() == [{"msgs": ["Expected list, received int"]}]

    def test_inner_parsing(self):
        """List 需要先对内部数据进行解析"""
        assert (
            z.list(z.transform(int))
            .ensure(lambda x: all(i > 0 for i in x))
            .parse(["1", "2"])
        )


class TestUnion:

    def test_parse(self):
        union = z.int() | z.none()

        assert union.parse(None) is None
        assert union.parse(1) == 1
        with pytest.raises(z.ValidationError) as e:
            union.parse("string")
        assert e.value.format_errors() == [
            {"msgs": ["Expected int, received str", "Expected NoneType, received str"]},
        ]

        # next transform
        schema = union.transform(lambda _: "string")
        assert schema.parse(None) == "string"
        assert schema.parse(1) == "string"
        with pytest.raises(z.ValidationError) as e:
            schema.parse("string")
        assert e.value.format_errors() == [
            {"msgs": ["Expected int, received str", "Expected NoneType, received str"]},
        ]

    def test_order(self):
        assert repr(z.str() | z.int() | z.bool()) == "String | Integer | Boolean"


class TestNumber:
    def test_methods(self):
        my_int = z.int().gt(0).lte(100)

        with pytest.raises(z.ValidationError) as e:
            my_int.parse(-1)
        assert e.value.format_errors() == [
            {"msgs": ["The value should be greater than 0"]}
        ]

        with pytest.raises(z.ValidationError) as e:
            my_int.parse(101)
        assert e.value.format_errors() == [
            {"msgs": ["The value should be less than or equal to 100"]}
        ]

        assert my_int.parse(50) == 50


def test_branch():
    main = z.int()
    branch_1 = main.gt(0)
    branch_2 = main.lt(0)

    assert branch_1.parse(1) == 1
    with pytest.raises(z.ValidationError) as e:
        branch_1.parse(0)
    assert e.value.format_errors() == [{"msgs": ["The value should be greater than 0"]}]

    assert branch_2.parse(-1) == -1
    with pytest.raises(z.ValidationError) as e:
        branch_2.parse(0)
    assert e.value.format_errors() == [{"msgs": ["The value should be less than 0"]}]


class TestConversions:
    def test_list(self):
        assert z.to.list().parse((1, 2, 3)) == [1, 2, 3]

        with pytest.raises(z.ValidationError) as e:
            z.to.list().parse(1)
        assert e.value.format_errors() == [
            {"msgs": ["Cannot convert the value 1 to list"]}
        ]
