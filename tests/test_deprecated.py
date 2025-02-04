import linecache

import pytest

import zangar as z


def test_dc_field():
    with pytest.warns(DeprecationWarning) as w:

        @z.dc.field("f")
        @classmethod
        def method(cls, schema):
            return schema  # pragma: no cover

    assert linecache.getline(w[0].filename, w[0].lineno).strip() == '@z.dc.field("f")'


def test_zangar_schema_in_metadata():
    ## Customize the field schema

    from dataclasses import dataclass, field

    @dataclass
    class InventoryItem:
        """Class for keeping track of an item in inventory."""

        name: str
        unit_price: float = field(metadata={"zangar_schema": z.transform(float)})
        quantity_on_hand: int = 0

    with pytest.warns(DeprecationWarning) as w:
        assert z.dataclass(InventoryItem).parse(
            {"name": "necklace", "unit_price": "12.50"}
        ) == InventoryItem(name="necklace", unit_price=12.5, quantity_on_hand=0)
    assert "assert z.dataclass(InventoryItem).parse(" in linecache.getline(
        w[0].filename, w[0].lineno
    )
