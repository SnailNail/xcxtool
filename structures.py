"""Dataclasses for in-memory structures"""
from dataclasses import dataclass, astuple, fields
from struct import calcsize, pack, unpack_from
from typing import ClassVar


@dataclass
class StructureBase:
    """Base class of Structure dataclasses

    Override the _struct ClassVar in subclasses to customise the structure
    """
    _struct: ClassVar[str]

    @classmethod
    def from_bytes(cls, buffer: bytes, offset: int = 0):
        """Alternative constructor for creating from bytes.

        buffer must be at least (calcsize(cls._struct) + offset) bytes

        If any field is itself a StructureBase subclass, it should be defined
        in cls._struct as a 's' type of the size of the packed structure. The
        field's value will be converted to a StructureBase instance by the
        __post_init__() method
        """
        size = calcsize(cls._struct)
        if len(buffer) < (size - offset):
            raise ValueError(f"buffer must be at least {size} bytes")
        # noinspection PyArgumentList
        return cls(
            *unpack_from(cls._struct, buffer, offset)
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

        return pack(self._struct, *astuple(self))

    def __len__(self):
        return calcsize(self._struct)


@dataclass
class Appearance(StructureBase):
    _struct: ClassVar = ">HHH BBBB HHI HHHH HHHH 2x ffff"
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
