"""Tests for xcxtools.backup.formatter.ForgivingFormatter"""

import pytest

from xcxtools.backup.formatter import ForgivingFormatter


@pytest.fixture(scope="session")
def formatter():
    return ForgivingFormatter()


def test_missing_keyword_field(formatter):
    assert formatter.format("{missing}") == "{missing}"


def test_missing_positional_field(formatter):
    assert formatter.format("missing {}") == "missing {0}"


def test_missing_indexed_field(formatter):
    assert formatter.format("missing {1}") == "missing {1}"


def test_missing_keyword_with_format_spec(formatter):
    assert formatter.format("{missing:^10}") == "{missing}"


def test_missing_keyword_with_non_str_format_spec(formatter):
    assert formatter.format("{missing:012n}") == "{missing}"


def test_missing_positional_with_format_spec(formatter):
    assert formatter.format("missing {:^10}") == "missing {0}"


def test_missing_indexed_with_format_spec(formatter):
    assert formatter.format("missing {1:^10}") == "missing {1}"


def test_missing_field_with_attribute(formatter):
    assert formatter.format("{missing.attribute}") == "{missing.attribute}"


def test_missing_field_with_brackets(formatter):
    assert formatter.format("{missing[key]}") == "{missing[key]}"
