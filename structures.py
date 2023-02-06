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

        buffer must be exactly cls._struct.size bytes

        If any field is itself a StructureBase subclass, it should be defined
        in cls._struct as a 's' type of the size of the packed structure. The
        field's value will be converted to a StructureBase instance by the
        __post_init__() method
        """
        if len(buffer) != cls._struct.size:
            raise ValueError(f"buffer must be {cls._struct.size} bytes")
        # noinspection PyArgumentList
        return cls(
            *cls._struct.unpack(buffer)
        )

    def __post_init__(self):
        for f in fields(self):
            value = getattr(self, f.name)
            if issubclass(f.type, StructureBase) and isinstance(value, bytes):
                setattr(self, f.name, f.type.from_bytes(value))

    def __bytes__(self):
        for field in fields(self):
            if issubclass(field.type, StructureBase):
                setattr(self, field.name, bytes(getattr(self, field.name)))

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
