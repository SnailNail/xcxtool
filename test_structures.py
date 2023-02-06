"""Tests for structures.py"""
from dataclasses import dataclass
from struct import Struct
from typing import ClassVar

from structures import StructureBase


@dataclass
class Simple(StructureBase):
    _struct: ClassVar = Struct(">I")
    one: int


@dataclass
class Nested(StructureBase):
    _struct: ClassVar = Struct(">I4s")
    two: int
    sub: Simple


def test_simple_direct_construction():
    assert Simple(1)


def test_simple_construction_from_bytes():
    assert Simple.from_bytes(b'\x00\x00\x00\x01').one == 1


def test_simple_packing_to_bytes():
    buffer = b'\x00\x00\x00\x01'
    assert bytes(Simple(1)) == buffer


def test_nested_direct_construction():
    assert Nested(2, Simple(1))


def test_nested_construction_from_bytes():
    buffer = b'\x00\x00\x00\x02\x00\x00\x00\x01'
    nested = Nested.from_bytes(buffer)
    assert nested.two == 2
    assert isinstance(nested.sub, Simple)
    assert nested.sub.one == 1


def test_nested_packing_to_bytes():
    buffer = b'\x00\x00\x00\x02\x00\x00\x00\x01'
    assert bytes(Nested(2, Simple(1))) == buffer
