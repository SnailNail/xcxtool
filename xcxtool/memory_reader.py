"""Abstraction for reading XCX memory.

Initial implementation uses Pymem to access Cemu's memory. It may be possible
to use TCP Gecko to read the game running on a real WiiU in the future.
"""
import os
import sys
import typing

import pymem

from xcxtool import savefiles


class MemoryReader(typing.Protocol):

    player_addr: int

    def read_memory(self, offset: int, length: int) -> bytes:
        """Read `length` bytes from `offset`, relative to `self.player`"""


class PymemReader:
    def __init__(self, reader: pymem.Pymem):
        self.pymem = reader
        nagi_addr = reader.pattern_scan_all(b"Nagi.{2804}Lao")
        if nagi_addr is None:
            print("Player data not found", file=sys.stderr)
            raise ValueError("Player data not found")
        self.player_addr = nagi_addr - 0x57c

    def read_memory(self, offset: int, length: int) -> bytes:
        return self.pymem.read_bytes(self.player_addr + offset, length)

    def close(self):
        self.pymem.close_process()


class SaveFileReader:
    """Read data from a XCX save file (gamedata)"""
    def __init__(self, save_file: str | os.PathLike):
        with open(save_file, "rb") as f:
            data = f.read()
        key = savefiles.guess_key(data)
        self.data = savefiles.apply_key(data, key)
        self.player_addr = 0x58

    def read_memory(self, offset: int, length: int) -> bytes:
        start = offset + self.player_addr
        end = start + length
        return self.data[start:end]


def connect_cemu(process_name: str = "cemu.exe") -> PymemReader | None:
    """Connect to a Cemu process"""
    try:
        reader = PymemReader(pymem.Pymem(process_name))
    except pymem.exception.ProcessNotFound:
        print(
            f"Could not find {process_name} process, dynamic file names not available",
            file=sys.stderr,
        )
        return None
    except ValueError as e:
        print(e.args[0])
        return None
    else:
        print(f"Found Cemu at {reader.pymem.base_address:#018x}")
        return reader
