from zangar.exceptions import ValidationError


def test_basic():
    e1 = ValidationError("m1")
    e2 = ValidationError("m2")

    assert e1.format_errors() == [{"msgs": ["m1"]}]
    assert (e1 & e2).format_errors() == [{"msgs": ["m1", "m2"]}]
    assert (e1 | e2).format_errors() == [{"msgs": ["m1"]}, {"msgs": ["m2"]}]


def test_and_operations():
    e = ValidationError()
    e = e & ValidationError("m1")
    assert e.format_errors() == [{"msgs": ["m1"]}]
    e = e & ValidationError("m2")
    assert e.format_errors() == [{"msgs": ["m1", "m2"]}]


def test_or_operations():
    e = ValidationError()
    e = e | ValidationError("m1")
    assert e.format_errors() == [{"msgs": ["m1"]}]
    e = e | ValidationError("m2")
    assert e.format_errors() == [{"msgs": ["m1"]}, {"msgs": ["m2"]}]


def test_sub():
    e = ValidationError()
    e._set_sub_error("k1", ValidationError("m1"))
    e._set_sub_error("k2", ValidationError("m2"))
    assert e.format_errors() == [
        {"loc": ["k1"], "msgs": ["m1"]},
        {"loc": ["k2"], "msgs": ["m2"]},
    ]


def test_sub2():
    e = ValidationError()
    e._set_sub_error("k1", ValidationError("m1") & ValidationError("m2"))
    e._set_sub_error("k2", ValidationError("m3") | ValidationError("m4"))

    assert e.format_errors() == [
        {"loc": ["k1"], "msgs": ["m1", "m2"]},
        {"loc": ["k2"], "msgs": ["m3"]},
        {"loc": ["k2"], "msgs": ["m4"]},
    ]


def test_sub3():
    e = ValidationError()
    e1 = ValidationError()
    e1._set_sub_error("k1", ValidationError("m1"))
    e1._set_sub_error("k2", ValidationError("m2"))
    e = e & e1
    assert e.format_errors() == [
        {"loc": ["k1"], "msgs": ["m1"]},
        {"loc": ["k2"], "msgs": ["m2"]},
    ]


def test_deep_sub():
    e = ValidationError()
    e1 = ValidationError()
    e2 = ValidationError()
    e2._set_sub_error("k2", ValidationError("m2"))
    e1._set_sub_error("k1", e2)
    e = e & e1
    assert e.format_errors() == [
        {"loc": ["k1", "k2"], "msgs": ["m2"]},
    ]
