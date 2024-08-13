"""Test cases for the xcxtools.config._FallbackDict class"""

import pytest
import xcxtools.config.main
from xcxtools.config import get, get_preferred


# patch the config object
xcxtools.config.main._config = {
    "s1": {
        "case_1": "Case1",
        "case_d": "Case2",
    },
    "s2": {"s2Case": "value"},
}


def test_get():
    assert get("s1.case_1") == "Case1"


def test_get_default():
    assert get("s1.case_3", "default") == "default"


def test_no_section_raises():
    with pytest.raises(ValueError):
        get("no_key")


def test_get_preferred_truthy_value():
    assert get_preferred("preferred", "s1.case_1") == "preferred"


def test_get_preferred_falsy_value():
    assert get_preferred("", "s1.case_1") == ""


def test_get_preferred_fallback_with_none_value():
    assert get_preferred(None, "s1.case_1") == "Case1"


def test_get_preferred_none_value_with_sentinel():
    assert get_preferred(None, "s1.case_1", object()) is None
