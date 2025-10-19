"""xcxtool applications for encrypting and decrypting save data files."""

import os
from typing import Literal

from plumbum import cli, LocalPath

from xcxtool.app import XCXToolApplication
from .encryption import decrypt_save_data, get_initial_key_position, transform, encrypt_save_data


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

        key_position = get_initial_key_position(data, self.endian)
        self.success(f"Initial key position: [green]{key_position}[/]")

        decrypted = decrypt_save_data(data, self.endian)
        of_name = savefile.name + "_decrypted"
        of: LocalPath = savefile.parent / of_name

        self.success(f"Writing decrypted data to [green]{of}[/green]")
        of.write(decrypted, None, "wb")
        copy_mtime(savefile, of)

    @cli.switch(["--de"])
    def definitive_edition(self):
        """Pass this flag if save files are from the Definitive Edition of the game"""
        self.endian = "little"


class EncryptSave(XCXToolApplication):
    """Encrypt save data"""

    def __init__(self, executable) -> None:
        super().__init__(executable)
        self.endian: ByteOrder = "big"

    @cli.positional(cli.ExistingFile)
    def main(self, decrypted_data: LocalPath):

        data = decrypted_data.read(None, "rb")
        # noinspection PyTypeChecker
        encrypted = encrypt_save_data(data, self.endian)
        of_name = decrypted_data.name + "_encrypted"
        of = decrypted_data.parent / of_name

        self.success(f"Writing encrypted data to [green]{of}[/green]")
        of.write(encrypted, None, mode="wb")
        copy_mtime(decrypted_data, of)

    @cli.switch(["--de"])
    def definitive_edition(self):
        """Pass this flag if save files are from the Definitive Edition of the game"""
        self.endian = "little"


def copy_mtime(src: LocalPath, dest: LocalPath) -> None:
    """Copy the modified date from src to dest."""
    src_stat = src.stat()
    dest_stat = dest.stat()
    os.utime(dest, (dest_stat.st_atime, src_stat.st_mtime))
