import datetime
import inspect
from types import SimpleNamespace
from typing import Mapping

import pytest

import zangar as z
from zangar.exceptions import ValidationError


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


class TestStruct:
    def test_field_default(self):
        obj = z.struct(
            {
                "a": z.field(z.str()).optional(default="Tom"),
                "b": z.field(z.str()).optional(default=lambda: "Tom"),
                "c": z.field(z.str()).optional(),
            }
        )
        assert obj.parse({}) == {"a": "Tom", "b": "Tom"}

    def test_field_required(self):
        obj = z.struct(
            {
                "a": z.field(z.str()).required(message="a is required"),
            }
        )
        with pytest.raises(z.ValidationError) as e:
            obj.parse({})
        assert e.value.format_errors() == [{"loc": ["a"], "msgs": ["a is required"]}]

    def test_parse_object(self):
        assert z.struct({"a": z.field(z.str())}).parse(SimpleNamespace(a="Tom")) == {
            "a": "Tom"
        }

    def test_ensure_fields(self):
        schema = z.struct(
            {
                "time_range": z.field(
                    z.struct(
                        {
                            "start_time": z.field(z.datetime(), alias="startTime"),
                            "end_time": z.field(z.datetime(), alias="endTime"),
                        }
                    )
                    .ensure_fields(
                        ["start_time"],
                        lambda o: o["start_time"] < o["end_time"],
                        message="The start time must be younger than the end time",
                    )
                    .ensure_fields(
                        ["end_time"],
                        lambda o: o["end_time"] > o["start_time"],
                        message="The end time must be older than the start time",
                    ),
                )
            }
        )
        with pytest.raises(z.ValidationError) as e:
            schema.parse(
                {
                    "time_range": {
                        "startTime": datetime.datetime(2025, 1, 2),
                        "endTime": datetime.datetime(2025, 1, 1),
                    }
                }
            )
        assert e.value.format_errors() == [
            {
                "loc": ["time_range", "startTime"],
                "msgs": ["The start time must be younger than the end time"],
            },
            {
                "loc": [
                    "time_range",
                    "endTime",
                ],
                "msgs": [
                    "The end time must be older than the start time",
                ],
            },
        ]

        assert schema.parse(
            {
                "time_range": {
                    "startTime": datetime.datetime(2025, 1, 1),
                    "endTime": datetime.datetime(2025, 1, 2),
                }
            }
        ) == {
            "time_range": {
                "start_time": datetime.datetime(2025, 1, 1),
                "end_time": datetime.datetime(2025, 1, 2),
            }
        }

    def test_extend(self):
        obj = z.struct(
            {
                "a": z.field(z.str()),
                "b": z.field(z.str()),
            }
        )
        with pytest.warns(DeprecationWarning):
            assert obj.extend({"c": z.field(z.str())}).parse(
                {"a": "1", "b": "2", "c": "3"}
            ) == {
                "a": "1",
                "b": "2",
                "c": "3",
            }

    @staticmethod
    def __get_required_fields(schema: z.struct):
        return [name for name, field in schema.fields.items() if field._required]

    def test_required_fields(self):
        obj = z.struct(
            {
                "a": z.field(z.str()).optional(),
                "b": z.field(z.str()).optional(),
            }
        )
        assert self.__get_required_fields(obj) == []
        with pytest.warns(DeprecationWarning):
            assert self.__get_required_fields(obj.required_fields()) == ["a", "b"]
            assert self.__get_required_fields(obj.required_fields([])) == []
            assert self.__get_required_fields(obj.required_fields(["a"])) == ["a"]
            assert self.__get_required_fields(obj.required_fields(["a", "b"])) == [
                "a",
                "b",
            ]

        with pytest.raises(ValueError) as e:
            z.required_fields(obj.fields, ["c"])
        assert e.value.args == ("Field 'c' not found in the struct schema",)

    def test_optional_fields(self):
        obj = z.struct(
            {
                "a": z.field(z.str()),
                "b": z.field(z.str()),
            }
        )
        assert self.__get_required_fields(obj) == ["a", "b"]
        with pytest.warns(DeprecationWarning):
            assert self.__get_required_fields(obj.optional_fields()) == []
            assert self.__get_required_fields(obj.optional_fields([])) == ["a", "b"]
            assert self.__get_required_fields(obj.optional_fields(["a"])) == ["b"]
            assert self.__get_required_fields(obj.optional_fields(["a", "b"])) == []

    @staticmethod
    def __get_fields(schema: z.struct):
        return list(schema.fields.keys())

    def test_pick_fields(self):
        obj = z.struct(
            {
                "a": z.str(),
                "b": z.str(),
            }
        )
        with pytest.warns(DeprecationWarning):
            assert self.__get_fields(obj.pick_fields(["a"])) == ["a"]

    def test_omit_fields(self):
        obj = z.struct(
            {
                "a": z.str(),
                "b": z.str(),
            }
        )
        with pytest.warns(DeprecationWarning):
            assert self.__get_fields(obj.omit_fields(["a"])) == ["b"]

    class TestFieldGetter:
        def test_basic(self):
            assert z.struct(
                {
                    "fullname": z.field(
                        z.str(), getter=lambda o: f"{o['firstname']} {o['lastname']}"
                    ),
                }
            ).parse({"firstname": "John", "lastname": "Doe"}) == {
                "fullname": "John Doe"
            }

        def test_getter_raising_exceptions(self):
            input = {"firstname": "John", "lastname": "Doe"}
            schema = z.struct(
                {
                    "firstname": z.str(),
                    "lastname": z.str(),
                    "fullname": z.field(
                        z.str(), getter=lambda o: f"{o['firstname1']} {o['lastname']}"
                    ),
                }
            )
            with pytest.raises(z.ValidationError) as e:
                schema.parse(input)
            assert e.value.format_errors() == [
                {"loc": ["fullname"], "msgs": ["This field is required"]},
            ]

            # with optional fields
            assert z.struct(z.optional_fields(schema.fields)).parse(input) == {
                "firstname": "John",
                "lastname": "Doe",
            }

    class TestFieldMapping:
        def setup_method(self):
            self.fields = z.struct(
                {
                    "a": z.str(),
                    "b": z.str(),
                    "c": z.str(),
                }
            ).fields

        def test_pick(self):
            assert list(self.fields.pick(["a", "b"])) == ["a", "b"]
            with pytest.raises(ValueError) as e:
                self.fields.pick(["d"])
            assert e.value.args == ("Field 'd' not found in the struct schema",)

        def test_omit(self):
            assert list(self.fields.omit(["a", "b"])) == ["c"]
            assert list(self.fields.omit(["a", "b", "c"])) == []
            assert list(self.fields.omit([])) == ["a", "b", "c"]
            with pytest.raises(ValueError) as e:
                self.fields.omit(["d"])
            assert e.value.args == ("Field 'd' not found in the struct schema",)

        def require_names(self, fields: z.FieldMapping):
            return [name for name, field in fields.items() if field._required]

        def test_required(self):
            assert self.require_names(self.fields.required(["a", "b"])) == ["a", "b"]
            assert self.require_names(self.fields.required([])) == []
            assert self.require_names(self.fields.required(["a", "b", "c"])) == [
                "a",
                "b",
                "c",
            ]
            assert self.require_names(self.fields.required()) == [
                "a",
                "b",
                "c",
            ]
            with pytest.raises(ValueError) as e:
                self.fields.required(["d"])
            assert e.value.args == ("Field 'd' not found in the struct schema",)

        def test_optional(self):
            assert self.require_names(self.fields.optional(["a", "c"])) == ["b"]
            assert self.require_names(self.fields.optional([])) == ["a", "b", "c"]
            assert self.require_names(self.fields.optional(["a", "b", "c"])) == []
            assert self.require_names(self.fields.optional()) == []
            with pytest.raises(ValueError) as e:
                self.fields.optional(["d"])
            assert e.value.args == ("Field 'd' not found in the struct schema",)

        def test_create_struct(self):
            """FieldMapping can be used to create a struct."""
            z.struct(
                z.FieldMapping({"a": z.str(), "b": z.str()}).optional().omit(["a"])
            )


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
            {
                "msgs": [
                    "Expected int, received str",
                ],
            },
            {
                "msgs": [
                    "Expected NoneType, received str",
                ],
            },
        ]

        # next transform
        schema = union.transform(lambda _: "string")
        assert schema.parse(None) == "string"
        assert schema.parse(1) == "string"
        with pytest.raises(z.ValidationError) as e:
            schema.parse("string")
        assert e.value.format_errors() == [
            {
                "msgs": [
                    "Expected int, received str",
                ],
            },
            {
                "msgs": [
                    "Expected NoneType, received str",
                ],
            },
        ]

    def test_order(self):
        assert (
            repr(z.str() | z.int() | z.bool()) == "ZangarStr | ZangarInt | ZangarBool"
        )

    def test_parsing_err(self):
        with pytest.raises(z.ValidationError) as e:
            (z.list(z.str()) | z.bool()).parse([1])
        assert e.value.format_errors() == [
            {
                "loc": [0],
                "msgs": ["Expected str, received int"],
            },
            {
                "msgs": [
                    "Expected bool, received list",
                ]
            },
        ]


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
    branch_1 = main.gte(0)
    branch_2 = main.lt(0)

    assert branch_1.parse(0) == 0
    with pytest.raises(z.ValidationError) as e:
        branch_1.parse(-1)
    assert e.value.format_errors() == [
        {"msgs": ["The value should be greater than or equal to 0"]}
    ]

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


class TestDatetime:
    def test_is_aware(self):
        assert (
            z.datetime()
            .is_aware()
            .parse(datetime.datetime.now(tz=datetime.timezone.utc))
        )
        with pytest.raises(z.ValidationError) as e:
            z.datetime().is_aware().parse(datetime.datetime.now())
        assert e.value.format_errors() == [{"msgs": ["The datetime should be aware"]}]

    def test_is_naive(self):
        assert z.datetime().is_naive().parse(datetime.datetime.now())
        with pytest.raises(z.ValidationError) as e:
            z.datetime().is_naive().parse(
                datetime.datetime.now(tz=datetime.timezone.utc)
            )
        assert e.value.format_errors() == [{"msgs": ["The datetime should be naive"]}]

    def test_to_datetime(self):
        dt = datetime.datetime.now()
        assert z.to.datetime().parse(dt) is dt


def test_meta_checking():
    with pytest.raises(ValueError) as e:
        z.int(meta={"type": "integer"})
    assert e.value.args == ("Invalid meta key: type",)


@pytest.mark.parametrize(
    "cls",
    [
        z.any,
        z.bool,
        z.int,
        z.float,
        z.str,
        z.to.datetime,
        z.to.list,
        z.to.str,
        z.dataclass,
        z.struct,
    ],
)
def test_is_class(cls):
    assert issubclass(cls, z.Schema)


def test_ValidationError():
    peer1 = z.ValidationError()
    peer1._set_child_err(0, z.ValidationError("err1"))

    peer2 = z.ValidationError()
    peer2._set_child_err(0, z.ValidationError("err2"))

    error = z.ValidationError()
    error._set_peer_err(peer1)
    error._set_peer_err(peer2)
    assert error.format_errors() == [
        {"loc": [0], "msgs": ["err1", "err2"]},
    ]


class TestMappingStruct:
    def test_field_alias(self):
        schema = z.mstruct(
            {
                "username": z.field(z.str(), alias="name"),
            },
            unknown="include",
        )
        assert schema.parse({"name": "john", "email": "john@example.com"}) == {
            "username": "john",
            "email": "john@example.com",
        }


class TestDataclass:
    def test_missing_metadata(self):
        from dataclasses import dataclass, field

        @dataclass
        class C:
            a: str = field(default="test")

        with pytest.raises(RuntimeError) as e:
            z.dataclass(C)
        assert e.value.args == ("Need to add 'zangar' metadata to the 'a' field",)


def test_isinstance():
    schema = z.isinstance(int)
    assert schema.parse(1) == 1

    with pytest.raises(z.ValidationError) as e:
        schema.parse("string")
    assert e.value.format_errors() == [
        {
            "msgs": [
                "Expected int, received str",
            ]
        }
    ]


def test_relay():
    assert z.str().relay(z.to.int()).parse("1") == 1


def test_break_on_failure():
    schema = (
        z.int()
        .ensure(
            lambda x: x > 0,
            break_on_failure=True,
            message="The value should be greater than 0",
        )
        .ensure(lambda x: x < 10)
    )
    with pytest.raises(z.ValidationError) as e:
        schema.parse(-1)
    assert e.value.format_errors() == [{"msgs": ["The value should be greater than 0"]}]

    schema = (
        z.int()
        .ensure(
            lambda x: x > 0,
            message="The value should be greater than 0",
        )
        .ensure(lambda x: x > 10)
    )
    with pytest.raises(z.ValidationError) as e:
        schema.parse(-1)
    assert e.value.format_errors() == [
        {"msgs": ["The value should be greater than 0", "Invalid value"]}
    ]


class TestZangarToInt:
    def test_bigint(self):
        n = 2**63 - 1
        assert z.to.int().lte(n).parse(n) == n
        assert z.to.int().lte(n).parse(str(n)) == n
