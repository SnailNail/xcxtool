"""Abstraction for reading XCX memory.

Initial implementation uses Pymem to access Cemu's memory. It may be possible
to use TCP Gecko to read the game running on a real WiiU in the future.
"""

import logging
import os
import sys
import typing

import pymem

from xcxtool import savefiles
from xcxtool.app import LOGGER_NAME, SUCCESS

_log = logging.getLogger(LOGGER_NAME)


class SaveDataReader(typing.Protocol):

    data_start: int

    def read_memory(self, offset: int, length: int) -> bytes:
        """Read `length` bytes from `offset`, relative to `self.data_start`"""


class PymemReader:
    def __init__(
        self,
        reader: pymem.Pymem,
        anchor_pattern: bytes = b"Nagi.{2804}Lao",
        anchor_offset: int = -0x5D4,
    ):
        self.pymem = reader
        anchor_addr = reader.pattern_scan_all(anchor_pattern)
        if anchor_addr is None:
            _log.error("Anchor pattern not found")
            raise ValueError("Save data not found")
        self.data_start = anchor_addr + anchor_offset

    def read_memory(self, offset: int, length: int) -> bytes:
        return self.pymem.read_bytes(self.data_start + offset, length)

    def close(self):
        self.pymem.close_process()


class SaveFileReader:
    """Read data from a XCX save file (gamedata)"""

    def __init__(self, save_file: str | os.PathLike):
        with open(save_file, "rb") as f:
            data = f.read()
        self.data = savefiles.decrypt_save_data(data)
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
