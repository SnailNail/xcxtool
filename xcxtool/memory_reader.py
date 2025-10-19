"""Abstraction for reading XCX memory.

Initial implementation uses Pymem to access Cemu's memory. It may be possible
to use TCP Gecko to read the game running on a real WiiU in the future.
"""

import abc
import logging
import os
import typing

import pymem

from xcxtool.app import LOGGER_NAME, SUCCESS
from xcxtool.savefiles.encryption import decrypt_save_data, detect_byte_order

_log = logging.getLogger(LOGGER_NAME)


class SaveDataReader(typing.Protocol):

    data_start: int

    def read_memory(self, offset: int, length: int) -> bytes:
        """Read `length` bytes from `offset`, relative to `self.data_start`"""


class PymemReaderBase(abc.ABC):

    def __init__(self, reader: pymem.Pymem):
        self.pymem = reader
        self.data_start = self.search()

    def close(self):
        self.pymem.close_process()

    def read_memory(self, offset: int, length: int) -> bytes:
        """Read `length` byts from address `offset` in process memory"""
        return self.pymem.read_bytes(self.data_start + offset, length)

    @abc.abstractmethod
    def search(self) -> int:
        """Return a memory address of save data in process memory.

        This function should return an address that is equivalent to the start
        of a gamedata file. That is, self.read_memory(address, length) should
        return the same result as SaveFileReader.read_memory(address, length).
        """


class PymemReader(PymemReaderBase):
    def __init__(
        self,
        reader: pymem.Pymem,
        anchor_pattern: bytes = b"Nagi.{2804}Lao",
        anchor_offset: int = -0x5D4,
    ):
        self.anchor_pattern = anchor_pattern
        self.anchor_offset = anchor_offset
        super().__init__(reader)

    def search(self) -> int:
        anchor_addr = self.pymem.pattern_scan_all(self.anchor_pattern)
        if anchor_addr is None:
            _log.error("Anchor pattern not found")
            raise ValueError("Save data not found")
        return anchor_addr + self.anchor_offset

    def read_memory(self, offset: int, length: int) -> bytes:
        return self.pymem.read_bytes(self.data_start + offset, length)


class PymemReaderDE(PymemReaderBase):
    """Class for reading Definitive Edition save data from emulator memory"""

    def __init__(
        self,
        reader: pymem.Pymem,
        anchor_pattern: bytes = b"Nagi.{4076}Lao",
        anchor_to_start: int = -2128,
        next_pattern=b"rW\x03\x00",
        anchor_to_next=694704,
    ):
        self.anchor_pattern = anchor_pattern
        self.anchor_offset = anchor_to_start
        self.next_pattern = next_pattern
        self.anchor_to_next = anchor_to_next
        super().__init__(reader)

    def search(self) -> int:
        candidate_addresses = self.pymem.pattern_scan_all(
            self.anchor_pattern, return_multiple=True
        )
        anchor_address = None
        for address in candidate_addresses:
            if (
                self.pymem.read_bytes(
                    address + self.anchor_to_next, len(self.next_pattern)
                )
                == self.next_pattern
            ):
                anchor_address = address
                break
        if anchor_address is None:
            _log.error("Save data not found")
            raise ValueError("Save data not found")
        return anchor_address + self.anchor_offset


class SaveFileReader:
    """Read data from a XCX save file (gamedata)"""

    def __init__(self, save_file: str | os.PathLike):
        with open(save_file, "rb") as f:
            data = f.read()
        byte_order = detect_byte_order(data)
        if byte_order is None:
            raise ValueError("Could not determine save data byte order")

        self.data = decrypt_save_data(data, byte_order)
        self.data_start = 0

    def read_memory(self, offset: int, length: int) -> bytes:
        start = offset + self.data_start
        end = start + length
        return self.data[start:end]


def connect_cemu(process_name: str = "cemu.exe") -> PymemReader | None:
    """Connect to a Cemu process"""
    try:
        reader = PymemReader(pymem.Pymem(process_name))
    except pymem.exception.ProcessNotFound:
        _log.warning(
            f"Could not find {process_name} process, dynamic file names not available"
        )
        return None
    except ValueError as e:
        _log.error(e.args[0])
        return None
    else:
        _log.log(SUCCESS, f"Found Cemu at {reader.pymem.base_address:#018x}")
        return reader


def connect_emulator(process_name: str, definitive_edition: bool = False) -> PymemReaderBase | None:
    """Connect to emulator running the WiiU or Switch version"""
    try:
        connection = pymem.Pymem(process_name)
    except pymem.exception.ProcessNotFound:
        _log.error(f"Could not find {process_name} process ")
        return None
    _log.log(SUCCESS, f"Found {process_name} at {connection.base_address:#018x}")
    if definitive_edition:
        reader_class = PymemReaderDE
    else:
        reader_class = PymemReader
    try:
        reader = reader_class(connection)
    except ValueError:
        return None
    _log.log(SUCCESS, f"save data found at offset {reader.data_start:#018x}")
    return reader