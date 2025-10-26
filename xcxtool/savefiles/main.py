"""xcxtool applications for encrypting and decrypting save data files."""

import os
from typing import Literal

from plumbum import cli, LocalPath

from xcxtool.app import XCXToolApplication
from .encryption import (
    decrypt_save_data,
    get_initial_key_position,
    encrypt_save_data,
    detect_byte_order,
)
from .checksum import fix_checksum, verify_checksum, verify_data_size

ByteOrder = Literal["big", "little"]


class DecryptSave(XCXToolApplication):
    """Decrypt save data"""

    def __init__(self, executable):
        super().__init__(executable)
        self.endian: ByteOrder = "big"

    @cli.positional(cli.ExistingFile)
    def main(self, savefile: LocalPath):
        self.success(f"Decrypting [bold]{savefile}[/bold]")
        # noinspection PyTypeChecker
        data: bytes = savefile.read(None, "rb")

        byte_order = detect_byte_order(data)
        if byte_order is None:
            self.error("Could not detect byte order of save data")
            return 1
        self.success(f"Detected {'DE' if byte_order == 'little' else 'OG'} game version")

        key_position = get_initial_key_position(data, byte_order)
        self.success(f"Initial key position: [green]{key_position}[/]")

        decrypted = decrypt_save_data(data, byte_order)
        of_name = savefile.name + "_decrypted"
        of: LocalPath = savefile.parent / of_name

        self.success(f"Writing decrypted data to [green]{of}[/green]")
        of.write(decrypted, None, "wb")
        copy_mtime(savefile, of)
        return 0


class EncryptSave(XCXToolApplication):
    """Encrypt save data"""

    fix_checksum: bool = cli.Flag(["--fix-checksum"], help="Verify checksum and write new checksum if data has changed")
    byte_order: ByteOrder

    def __init__(self, executable) -> None:
        super().__init__(executable)

    @cli.positional(cli.ExistingFile)
    def main(self, decrypted_data: LocalPath):
        # noinspection PyTypeChecker
        data: bytes = decrypted_data.read(None, "rb")

        one_value = data[4:8]
        if one_value == b"\x01\x00\x00\x00":
            self.byte_order = "little"
        elif one_value == b"\x00\x00\x00\x01":
            self.byte_order = "big"
        else:
            self.error("Could not determine byte order (invalid or encrypted header data)")
            return 1

        if self.fix_checksum:
            try:
                data = self.do_fix_checksum(data)
            except ValueError:
                self.error("Data is already encrypted or invalid header data")
                return 1

        # noinspection PyTypeChecker
        encrypted = encrypt_save_data(data, self.byte_order)
        of_name = decrypted_data.name + "_encrypted"
        of = decrypted_data.parent / of_name

        self.success(f"Writing encrypted data to [green]{of}[/green]")
        of.write(encrypted, None, mode="wb")
        copy_mtime(decrypted_data, of)
        return 0

    def do_fix_checksum(self, save_data: bytes) -> bytes:
        """Check header and write new checksum value.

        Returns data unchanged if the checksum is correct or data size does
        not match the header value.

        Raises ValueError if the data is not decrypted.
        """
        if not verify_data_size(save_data, self.byte_order):
            self.warning(f"Data size not correct")
            return save_data
        if verify_checksum(save_data, self.byte_order):
            self.success(f"Checksum OK")
            return save_data
        self.success("Data has been changed, calculating new checksum")

        return fix_checksum(save_data, self.byte_order)


def copy_mtime(src: LocalPath, dest: LocalPath) -> None:
    """Copy the modified date from src to dest."""
    src_stat = src.stat()
    dest_stat = dest.stat()
    os.utime(dest, (dest_stat.st_atime, src_stat.st_mtime))
