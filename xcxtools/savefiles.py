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

import plumbum
from plumbum import cli, local

SAVEDATA_PLAYER_OFFSET = -0x58
SAVEDATA_SIZE = 359984

# Late game, post-Lifehold Core, lots of things found (Quinn)
SAVE_LATE_GAME = r"G:\Emulation\WiiU\cemu\mlc01\usr\save\00050000\101c4c00\user\80000002\st\game\gamedata"
# Early game, approx Chapter 3 finished (Obadiah)
SAVE_EARLY_GAME = r"G:\Emulation\WiiU\cemu\mlc01\usr\save\00050000\101c4c00\user\80000003\st\game\gamedata"


class DecryptSave(cli.Application):
    """Decrypt save data"""
    dump_key = cli.Flag(["-k", "--dump-key"], help="Dump decryption key")

    @cli.positional(cli.ExistingFile)
    def main(self, savefile: plumbum.LocalPath):
        print(f"Decrypting {savefile}")
        data = savefile.read(None, "rb")
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

        if self.dump_key:
            of_key_name = savefile.name + "_key"
            of_key = savefile.parent / of_key_name
            print(f"Writing key to {of_key}")
            of_key.write(key, None, "wb")


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
