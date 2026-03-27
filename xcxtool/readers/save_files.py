"""High-level classes for reading save file data.
"""
import logging
import os
import typing

from xcxtool.app import LOGGER_NAME
from xcxtool.savefiles.encryption import decrypt_save_data, detect_byte_order

_log = logging.getLogger(LOGGER_NAME)


class SaveDataReader(typing.Protocol):

    byte_order: typing.Literal["big", "little"]
    data_start: int

    def read_memory(self, offset: int, length: int) -> bytes:
        """Read `length` bytes from `offset`, relative to `self.data_start`"""


class SaveFileReader:
    """Read data from a XCX save file (gamedata)"""

    def __init__(self, save_file: str | os.PathLike):
        with open(save_file, "rb") as f:
            data = f.read()
        byte_order = detect_byte_order(data)
        if byte_order is None:
            raise ValueError("Could not determine save data byte order")

        self.byte_order = byte_order
        self.data = decrypt_save_data(data, byte_order)
        self.data_start = 0

    def read_memory(self, offset: int, length: int) -> bytes:
        start = offset + self.data_start
        end = start + length
        return self.data[start:end]


