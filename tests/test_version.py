from zangar.utils.version import get_version


def test_versions():
    assert get_version((0, 1, 0, "alpha", 0)).startswith("0.1.dev")
    assert get_version((0, 1, 0, "beta", 0)) == "0.1b0"
    assert get_version((0, 1, 0, "final")) == "0.1"
