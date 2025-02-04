from __future__ import annotations

import datetime
import typing
from dataclasses import dataclass

import pytest

import zangar as z
from zangar._core import Union
from zangar.dataclass import resolve_complex_type


class C:
    simple: str
    a: typing.Union[str, None]
    b: typing.Optional[str]
    c: typing.Union[str, int]
    d: typing.List[str]
    e: typing.List[typing.Union[str, int]]
    f: typing.List


def test_complex_type():
    hints = typing.get_type_hints(C)
    assert resolve_complex_type(hints["simple"]) == None
    assert resolve_complex_type(hints["a"]) == (Union, (str, type(None)))
    assert resolve_complex_type(hints["b"]) == (Union, (str, type(None)))
    assert resolve_complex_type(hints["c"]) == (Union, (str, int))
    assert resolve_complex_type(hints["d"]) == (z.list, (str,))
    assert resolve_complex_type(hints["e"]) == (
        z.list,
        (typing.Union[str, int],),
    )
    assert resolve_complex_type(hints["f"]) == (z.list, ())


class TestFieldDecorator:
    def test_field_decorator(self):
        @dataclass
        class C:
            f: str

            @z.dc.field_assisted("f")
            @staticmethod
            def f_field(schema: z.Schema[str]):
                return schema.transform(lambda x: x.upper())

        assert z.dataclass(C).parse({"f": "hello"}) == C(f="HELLO")

    def test_error(self):
        with pytest.raises(ValueError) as e:

            class C:
                @z.dc.field_assisted("f")
                def f_field(self, schema):
                    return schema  # pragma: no cover

        assert e.value.args == (
            "@dc.field_assisted must decorate a class method or a static method",
        )

    def test_field_not_found(self):
        @dataclass
        class C:
            @z.dc.field_assisted("f")
            @classmethod
            def f_field(cls, schema):
                return schema  # pragma: no cover

        with pytest.raises(RuntimeError) as e:
            z.dataclass(C)
        assert e.value.args == ("Field 'f' is not found",)

    def test_field_already_decorated(self):
        @dataclass
        class C:
            f: int

            @z.dc.field_assisted("f")
            @classmethod
            def f_field(cls, schema):
                return schema  # pragma: no cover

            @z.dc.field_assisted("f")
            @classmethod
            def f_field2(cls, schema):
                return schema  # pragma: no cover

        with pytest.raises(RuntimeError) as e:
            z.dataclass(C)
        assert e.value.args == ("Field 'f' is already decorated",)


class TestEnsureFieldsDecorator:
    def test_ensure_fields_decorator(self):
        @dataclass
        class C:
            start_time: datetime.datetime
            end_time: datetime.datetime

            @z.dc.ensure_fields(
                ["end_time"], message="start_time must be less than end_time"
            )
            def ensure_fields(self):
                return self.start_time < self.end_time

        # incorrect
        with pytest.raises(z.ValidationError) as e:
            z.dataclass(C).parse(
                {
                    "start_time": datetime.datetime(2022, 1, 2),
                    "end_time": datetime.datetime(2022, 1, 2),
                }
            )
        assert e.value.format_errors() == [
            {
                "loc": ["end_time"],
                "msgs": ["start_time must be less than end_time"],
            }
        ]

        # correct
        assert z.dataclass(C).parse(
            {
                "start_time": datetime.datetime(2022, 1, 2),
                "end_time": datetime.datetime(2022, 1, 3),
            }
        ) == C(datetime.datetime(2022, 1, 2), datetime.datetime(2022, 1, 3))

    def test_error(self):
        with pytest.raises(ValueError) as e:

            class C:
                @z.dc.ensure_fields(["f"])
                @classmethod
                def f_field(cls):
                    return True  # pragma: no cover

        assert e.value.args == ("@dc.ensire_fields must decorate a instance method",)


def test_decorators_in_inheritance():
    """测试装饰器在继承过程中是否生效"""

    @dataclass
    class OnlyUsername:
        username: str

        @z.dc.field_assisted("username")
        @classmethod
        def _username_field(cls, schema: z.Schema[str]):
            return schema.ensure(
                lambda x: "!" not in x, message="username cannot contain !"
            )

    @dataclass
    class User(OnlyUsername):
        password: str

    # incorrect
    with pytest.raises(z.ValidationError) as e:
        z.dataclass(User).parse({"username": "john!", "password": "123"})
    assert e.value.format_errors() == [
        {
            "loc": ["username"],
            "msgs": ["username cannot contain !"],
        }
    ]

    # correct
    assert z.dataclass(User).parse({"username": "john", "password": "123"}) == User(
        username="john", password="123"
    )
