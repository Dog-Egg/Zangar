from dataclasses import asdict, dataclass, field

import zangar as z


def test_dataclass_field_init_false():
    """Test that `init=False` fields are not required."""

    @dataclass
    class User:
        id: int = field(init=False, metadata={"zangar": {"schema": z.int()}})
        name: str = field(metadata={"zangar": {"schema": z.str()}})

        def __post_init__(self):
            self.id = 0

    assert asdict(User(name="Lee")) == {"id": 0, "name": "Lee"}
    assert z.dataclass(User).parse({"name": "Lee"}) == User(name="Lee")
    assert z.dataclass(User).parse({"name": "Lee", "id": 1}) == User(name="Lee")
    assert z.struct(z.dataclass(User).fields).parse(User(name="Lee")) == {
        "id": 0,
        "name": "Lee",
    }
