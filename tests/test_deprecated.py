import pytest

import zangar as z


@pytest.fixture(autouse=True, scope="function")
def expect_deprecation_warnings():
    with pytest.warns(DeprecationWarning):
        yield


def test_deprecated_object():
    z.object({})
