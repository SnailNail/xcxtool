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

import plumbum
from plumbum import cli

SAVEDATA_PLAYER_OFFSET = -0x58
SAVEDATA_SIZE = 359984

# Late game, post-Lifehold Core, lots of things found (Quinn)
SAVE_LATE_GAME = r"G:\Emulation\WiiU\cemu\mlc01\usr\save\00050000\101c4c00\user\80000002\st\game\gamedata"
# Early game, approx Chapter 3 finished (Obadiah)
SAVE_EARLY_GAME = r"G:\Emulation\WiiU\cemu\mlc01\usr\save\00050000\101c4c00\user\80000003\st\game\gamedata"


class DecryptSave(cli.Application):
    """Decrypt save data"""
    dump_key = cli.Flag(["-k", "--dump-key"], help="Dump decryption key")

    def __init__(self, executable):
        super().__init__(executable)
        self.key_data = None

    @cli.positional(cli.ExistingFile)
    def main(self, savefile: plumbum.LocalPath):
        print(f"Decrypting {savefile}")
        data = savefile.read(None, "rb")
        if self.key_data is not None:
            if len(self.key_data) != 512:
                print("KEY_FILE must be exactly 512 bytes")
                return 1
            print(f"Using key {self.key_data[0:32].hex()}...")
            decrypted, key = decrypt_savedata(data, self.key_data)
        else:
            try:
                decrypted, key = decrypt_savedata(data)
            except ValueError:
                print(f"could not determine encryption key")
                return 1
            print(f"Found key: {key[0:32].hex()}...")
        of_name = savefile.name + "_decrypted"
        of: plumbum.LocalPath = savefile.parent / of_name

        print(f"Writing decrypted data to {of}")
        of.write(decrypted, None, "wb")
        copy_mtime(savefile, of)

        if self.dump_key:
            of_key_name = savefile.name + "_key"
            of_key = savefile.parent / of_key_name
            print(f"Writing key to {of_key}")
            of_key.write(key, None, "wb")
            copy_mtime(savefile, of_key)

    @cli.switch(["-u", "--use-key"], cli.ExistingFile)
    def use_key(self, key_file: plumbum.LocalPath):
        """Use KEY_File to decode savedata. KEY_FILE must be exactly 512 bytes"""
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


def decrypt_savedata(data: bytes, use_key: bytes | None = None) -> tuple[bytes, bytes]:
    decrypted = b""
    if use_key is None:
        key = guess_key(data)
    else:
        key = use_key
    if key is None:
        raise ValueError("Could not determine key")
    for offset in range(0, len(data), 512):
        decrypted += _decrypt(data[offset: offset + 512], key)
    return decrypted, key


def _decrypt(cipher: bytes, key: bytes):
    return bytes(a ^ b for a, b in zip(cipher, key))


def copy_mtime(src: plumbum.LocalPath, dest: plumbum.LocalPath) -> None:
    """Copy the modified date from src to dest."""
    src_stat = src.stat()
    dest_stat = dest.stat()
    os.utime(dest, (dest_stat.st_atime, src_stat.st_mtime))
