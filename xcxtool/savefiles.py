"""Experiments with XCX save files.

XCX save files are fairly inscrutable beasts, being on first glance not much
more than random data. However, inspection with a binary visualiser tool such
as Sharkdp's Binocle[1] it becomes clear there is some structure. The files
seem to be a dump of the game's memory, overlaid (XOR'd?) with some obfuscatory
data.

The obfuscating data, which I'll call the key from now on, seems to be 512
bytes long. It appears to the same for different save file types generated at
the same time (e.g. gamedata and socialdata files) but different for the same
type of save files generated at different times.

[1]: https://github.com/sharkdp/binocle
"""

import collections
import os

from plumbum import cli, LocalPath

from xcxtool.app import XCXToolApplication

SAVEDATA_PLAYER_OFFSET = -0x58
SAVEDATA_SIZE = 359984

# Late game, post-Lifehold Core, lots of things found (Quinn)
SAVE_LATE_GAME = r"G:\Emulation\WiiU\cemu\mlc01\usr\save\00050000\101c4c00\user\80000002\st\game\gamedata"
# Early game, approx Chapter 3 finished (Obadiah)
SAVE_EARLY_GAME = r"G:\Emulation\WiiU\cemu\mlc01\usr\save\00050000\101c4c00\user\80000003\st\game\gamedata"


class DecryptSave(XCXToolApplication):
    """Decrypt save data"""

    dump_key = cli.Flag(["-d", "--dump-key"], help="Dump decryption key")

    def __init__(self, executable):
        super().__init__(executable)
        self.key_data = None

    @cli.positional(cli.ExistingFile)
    def main(self, savefile: LocalPath):
        self.success(f"Decrypting [bold]{savefile}[/bold]")
        data = savefile.read(None, "rb")

        if self.key_data is not None:
            if len(self.key_data) != 512:
                self.error("[bold red]KEY_FILE must be exactly 512 bytes[/bold red]")
                return 1
            self.success(f"Using key [green]{self.key_data[0:32].hex()}...[/green]")
            # noinspection PyTypeChecker

        else:
            # noinspection PyTypeChecker
            self.key_data = guess_key(data)
            if self.key_data is None:
                self.error("[bold red]could not determine encryption key[/bold red]")
                return 1
            self.success(f"Found key: [green]{self.key_data[0:32].hex()}...[/green]")

        # noinspection PyTypeChecker
        decrypted = apply_key(data, self.key_data)
        of_name = savefile.name + "_decrypted"
        of: LocalPath = savefile.parent / of_name

        self.success(f"Writing decrypted data to [green]{of}[/green]")
        of.write(decrypted, None, "wb")
        copy_mtime(savefile, of)

        if self.dump_key:
            of_key_name = savefile.name + "_key"
            of_key = savefile.parent / of_key_name
            self.success(f"Writing key to [green]{of_key}[green]")
            of_key.write(self.key_data, None, "wb")
            copy_mtime(savefile, of_key)

    @cli.switch(["-k", "--key"], cli.ExistingFile)
    def key(self, key_file: LocalPath):
        """Use KEY_File to decode save data. KEY_FILE must be exactly 512 bytes"""
        self.key_data = key_file.read(None, "rb")


class EncryptSave(XCXToolApplication):
    """Encrypt save data"""

    def __init__(self, executable) -> None:
        super().__init__(executable)
        self.key_data = None

    @cli.positional(cli.ExistingFile)
    def main(self, decrypted_data: LocalPath):
        if len(self.key_data) != 512:
            self.error("[bold red]KEY_FILE must be exactly 512 bytes[/bold red]")
            return 1

        self.success(f"Using key [green]{self.key_data[0:32].hex()}...[/green]")
        data = decrypted_data.read(None, "rb")
        # noinspection PyTypeChecker
        encrypted = apply_key(data, self.key_data)
        of_name = decrypted_data.name + "_encrypted"
        of = decrypted_data.parent / of_name

        self.success(f"Writing encrypted data to [green]{of}[/green]")
        of.write(encrypted, None, mode="wb")
        copy_mtime(decrypted_data, of)

    @cli.switch(["-k", "--key"], cli.ExistingFile, "KEY_FILE", mandatory=True)
    def key(self, key_file: LocalPath):
        """Key to use to encrypt the save data. Must be a file of size 512 bytes"""
        self.key_data = key_file.read(None, "rb")


def guess_key(savedata: bytes) -> bytes | None:
    """Try to guess a savefile's key.

    Compares key-size chunks until three in a row are the same
    """
    rows = collections.deque([b"", b"", b""], 3)
    for offset in range(0, len(savedata), 512):
        chunk = savedata[offset : offset + 512]
        rows.append(chunk)
        if len(set(rows)) == 1:
            return chunk
    return


def apply_key(data: bytes, key: bytes) -> bytes:
    decrypted = b""
    for offset in range(0, len(data), 512):
        decrypted += _decrypt(data[offset : offset + 512], key)
    return decrypted


def _decrypt(cipher: bytes, key: bytes):
    return bytes(a ^ b for a, b in zip(cipher, key))


def copy_mtime(src: LocalPath, dest: LocalPath) -> None:
    """Copy the modified date from src to dest."""
    src_stat = src.stat()
    dest_stat = dest.stat()
    os.utime(dest, (dest_stat.st_atime, src_stat.st_mtime))
