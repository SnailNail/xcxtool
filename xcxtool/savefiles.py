"""Applications and functions to decrypt (and encrypt) save files.

The decryption/encryption functions are based on lincoln-lm's gist[1]

[1]: https://gist.github.com/lincoln-lm/aa09cd89ff338ac5ee0404942d528154
"""

import collections
import os
import random
import struct
from typing import Literal

from plumbum import cli, LocalPath

from xcxtool.app import XCXToolApplication


XOR_KEY = (
    33088,
    12288,
    33089,
    12289,
    33090,
    12290,
    33091,
    65292,
    33092,
    65294,
    33093,
    12539,
    33094,
    65306,
    33095,
    65307,
    33096,
    65311,
    33097,
    65281,
    33098,
    12443,
    33099,
    12444,
    33100,
    180,
    33101,
    65344,
    33102,
    168,
    33103,
    65342,
    33104,
    65507,
    33105,
    65343,
    33106,
    12541,
    33107,
    12542,
    33108,
    12445,
    33109,
    12446,
    33110,
    12291,
    33111,
    20189,
    33112,
    12293,
    33113,
    12294,
    33114,
    12295,
    33115,
    12540,
    33116,
    8213,
    33117,
    8208,
    33118,
    65295,
    33119,
    92,
    33120,
    12316,
    33121,
    8214,
    33122,
    65372,
    33123,
    8230,
    33124,
    8229,
    33125,
    8216,
    33126,
    8217,
    33127,
    8220,
    33128,
    8221,
    33129,
    65288,
    33130,
    65289,
    33131,
    12308,
    33132,
    12309,
    33133,
    65339,
    33134,
    65341,
    33135,
    65371,
    33136,
    65373,
    33137,
    12296,
    33138,
    12297,
    33139,
    12298,
    33140,
    12299,
    33141,
    12300,
    33142,
    12301,
    33143,
    12302,
    33144,
    12303,
    33145,
    12304,
    33146,
    12305,
    33147,
    65291,
    33148,
    8722,
    33149,
    177,
    33150,
    215,
    33152,
    247,
    33153,
    65309,
    33154,
    8800,
    33155,
    65308,
    33156,
    65310,
    33157,
    8806,
    33158,
    8807,
    33159,
    8734,
    33160,
    8756,
    33161,
    9794,
    33162,
    9792,
    33163,
    176,
    33164,
    8242,
    33165,
    8243,
    33166,
    8451,
    33167,
    65509,
    33168,
    65284,
    33169,
    162,
    33170,
    163,
    33171,
    65285,
    33172,
    65283,
    33173,
    65286,
    33174,
    65290,
    33175,
    65312,
    33176,
    167,
    33177,
    9734,
    33178,
    9733,
    33179,
    9675,
    33180,
    9679,
    33181,
    9678,
    33182,
    9671,
    33183,
    9670,
    33184,
    9633,
    33185,
    9632,
    33186,
    9651,
    33187,
    9650,
    33188,
    9661,
    33189,
    9660,
    33190,
    8251,
    33191,
    12306,
    33192,
    8594,
    33193,
    8592,
    33194,
    8593,
    33195,
    8595,
    33196,
    12307,
    33208,
    8712,
    33209,
    8715,
    33210,
    8838,
    33211,
    8839,
    33212,
    8834,
    33213,
    8835,
    33214,
    8746,
    33215,
    8745,
    33224,
    8743,
    33225,
    8744,
    33226,
    172,
    33227,
    8658,
    33228,
    8660,
    33229,
    8704,
    33230,
    8707,
    33242,
    8736,
    33243,
    8869,
    33244,
    8978,
    33245,
    8706,
    33246,
    8711,
)


class DecryptSave(XCXToolApplication):
    """Decrypt save data"""

    def __init__(self, executable):
        super().__init__(executable)
        self.endian: Literal["big", "little"] = "big"
        self.struct_fmt = ">256H"

    @cli.positional(cli.ExistingFile)
    def main(self, savefile: LocalPath):
        self.success(f"Decrypting [bold]{savefile}[/bold]")
        # noinspection PyTypeChecker
        data: bytes = savefile.read(None, "rb")

        key_position = get_initial_key_position(data, self.endian)
        self.success(f"Initial key position: [green]{key_position}[/]")

        decrypted = transform(data, struct.pack(self.struct_fmt, *XOR_KEY), key_position)
        of_name = savefile.name + "_decrypted"
        of: LocalPath = savefile.parent / of_name

        self.success(f"Writing decrypted data to [green]{of}[/green]")
        of.write(decrypted, None, "wb")
        copy_mtime(savefile, of)

    @cli.switch(["--de"])
    def definitive_edition(self):
        """Pass this flag if save files are from the Definitive Edition of the game"""
        self.endian = "little"
        self.struct_fmt = "<256H"


class EncryptSave(XCXToolApplication):
    """Encrypt save data"""

    def __init__(self, executable) -> None:
        super().__init__(executable)
        self.endian = "big"
        self.struct_fmt = ">256H"

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
        self.struct_fmt = "<256H"


def get_initial_key_position(
    save_data: bytes, endian: Literal["big", "little"] = "big"
) -> int:
    return int.from_bytes(save_data[0:4], endian) & 0x1FF


def transform(save_data: bytes, key: bytes, key_position: int) -> bytes:
    """Encrypt or decrypt save_data with key.

    Since encryption is symmetrical, this can encrypt and decrypt save data
    """
    decrypted = []
    for data_index, byte in enumerate(save_data[4:]):
        byte ^= data_index & 0xFF
        byte ^= key[key_position] ^ 0xFF
        decrypted.append(byte)
        key_position = (key_position + 1) % 512
    return save_data[0:4] + bytes(decrypted)


def decrypt_save_data(data: bytes, endian: Literal["big", "little"] = "big") -> bytes:
    """Decrypt encrypted save data and return plain bytes"""
    key_position = get_initial_key_position(data, endian)
    if endian == "little":
        fmt = "<256H"
    else:
        fmt = ">256H"
    key = struct.pack(fmt, XOR_KEY)
    return transform(data, key, key_position)


def encrypt_save_data(data: bytes, endian: Literal["big", "little"] = "big", key_position: int | None = None) -> bytes:
    """Encrypt save data.

    Specify endian = "big" if encrypting save data for the WiiU edition of the
    game, and "little" for the Switch Definitive Edition version.

    If key_position is not specified it will be read from the save data
    header. If an integer between 0 and 511 is provided it will be used as the
    initial key value. If key_value is -1 (or any negative number) a random
    initial value will be used
    """
    if endian == "little":
        fmt = "<256H"
    else:
        fmt = ">256H"
    key = struct.pack(fmt, XOR_KEY)

    if key_position is None:
        key_position = get_initial_key_position(data, endian)
    elif key_position < 0:
        key_position = random.randint(0, 511)
    key_position = key_position % 512

    encrypted = transform(data, key, key_position)
    random_value = int.from_bytes(random.randbytes(4), endian)
    encryption_info = (random_value & 0xfffffe00) | key_position

    return encryption_info.to_bytes(4, endian) + encrypted[4:]


def copy_mtime(src: LocalPath, dest: LocalPath) -> None:
    """Copy the modified date from src to dest."""
    src_stat = src.stat()
    dest_stat = dest.stat()
    os.utime(dest, (dest_stat.st_atime, src_stat.st_mtime))
