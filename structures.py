"""Dataclasses for in-memory structures"""
from dataclasses import dataclass, astuple, fields
from struct import Struct
from typing import ClassVar


@dataclass
class StructureBase:
    """Base class of Structure dataclasses

    Override the _struct ClassVar in subclasses to customise the structure
    """
    _struct: ClassVar[Struct]

    @classmethod
    def from_bytes(cls, buffer: bytes):
        """Alternative constructor for creating from bytes.

        buffer must be exactly cls._struct.size bytes"""
        if len(buffer) != cls._struct.size:
            raise ValueError(f"buffer must be {cls._struct.size} bytes")
        return cls(
            *cls._struct.unpack(buffer)
        )

    def __bytes__(self):
        return self._struct.pack(*astuple(self))

    def __len__(self):
        return self._struct.size


@dataclass
class Appearance(StructureBase):
    _struct: ClassVar = Struct(">HHH BBBB HHI HHHH HHHH 2x ffff")
    face: int
    hair_style: int
    hair_addon: int
    moles: int
    freckles: int
    cheeks: int
    scars: int
    face_paint: int
    eye_style: int
    gender: int
    voice: int
    skin_tone: int
    lips: int
    eye_shadow: int
    eye_color_1: int
    eye_color_2: int
    hair_color_1: int
    hair_color_2: int
    height: float
    chest_depth: float
    chest_height: float
    chest_width: float
