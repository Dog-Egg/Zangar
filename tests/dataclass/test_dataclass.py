from __future__ import annotations

import datetime
import typing
from dataclasses import dataclass

import pytest

import zangar as z
from zangar._core import Union
from zangar.dataclass import Converter


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
    assert Converter().resolve_complex_type(hints["simple"]) == None
    assert Converter().resolve_complex_type(hints["a"]) == (Union, (str, type(None)))
    assert Converter().resolve_complex_type(hints["b"]) == (Union, (str, type(None)))
    assert Converter().resolve_complex_type(hints["c"]) == (Union, (str, int))
    assert Converter().resolve_complex_type(hints["d"]) == (z.list, (str,))
    assert Converter().resolve_complex_type(hints["e"]) == (
        z.list,
        (typing.Union[str, int],),
    )
    assert Converter().resolve_complex_type(hints["f"]) == (z.list, ())


def test_zangar_schema_in_metadata():
    ## Customize the field schema

    from dataclasses import field

    @dataclass
    class InventoryItem:
        """Class for keeping track of an item in inventory."""

        name: str
        unit_price: float = field(metadata={"zangar_schema": z.transform(float)})
        quantity_on_hand: int = 0

    assert z.dataclass(InventoryItem).parse(
        {"name": "necklace", "unit_price": "12.50"}
    ) == InventoryItem(name="necklace", unit_price=12.5, quantity_on_hand=0)


class TestFieldDecorator:
    def test_field_decorator(self):
        @dataclass
        class C:
            f: str

            @z.dc.field("f")
            @staticmethod
            def f_field(schema: z.Schema[str]):
                return schema.transform(lambda x: x.upper())

        assert z.dataclass(C).parse({"f": "hello"}) == C(f="HELLO")

    def test_error(self):
        with pytest.raises(ValueError) as e:

            class C:
                @z.dc.field("f")
                def f_field(self, schema):
                    return schema  # pragma: no cover

        assert e.value.args == (
            "@dc.field must decorate a class method or a static method",
        )


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
