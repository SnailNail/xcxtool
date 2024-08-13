"""Module to generate replacement token values for backup names"""

import struct

import pendulum
import plumbum

from ..memory_reader import MemoryReader
from .. import game_timer


class_map = {
    1: "Drifter",
    2: "Striker",
    3: "Samurai Gunner",
    4: "Duelist",
    5: "Shield Trooper",
    6: "Bastion Warrior",
    7: "Commando",
    8: "Winged Viper",
    9: "Full Metal Jaguar",
    10: "Partisan Eagle",
    11: "Astral Crusader",
    12: "Enforcer",
    13: "Psycorruptor",
    14: "Mastermind",
    15: "Blast Fencer",
    16: "Galactic Knight",
}


def get_datetime() -> dict[str, pendulum.DateTime]:
    return {"datetime": pendulum.now(tz="local")}


def get_mtime(file: plumbum.LocalPath) -> dict[str, pendulum.DateTime]:
    return {"save_date": pendulum.from_timestamp(file.stat().st_mtime, tz="local")}


def get_character_data(reader: MemoryReader) -> dict:
    buffer = reader.read_memory(0, 1404)

    def unpack_value(fmt: str, offset: int):
        val = struct.unpack_from(fmt, buffer, offset)
        if len(val) == 1:
            return val[0]
        return val

    return {
        "player_name": _get_name(buffer),
        "level": unpack_value("B", 0x7a),
        "exp": unpack_value(">I", 0x7c),
        "class": class_map.get(unpack_value("B", 0x128), "Drifter"),
        "class_rank": unpack_value("B", 0x12a),
        "class_exp": unpack_value(">H", 0x12c),
    }


def get_playtime(reader: MemoryReader) -> dict[str, game_timer.GameTimer]:
    playtime_buffer = reader.read_memory(0x45e40 - 0x58, 4)
    playtime = game_timer.unpack_game_timer(playtime_buffer)
    return {"play_time": playtime}


def _get_name(buffer: bytes) -> str:
    name_size: int = struct.unpack_from(">I", buffer, 0x40)[0]
    name_bytes: bytes = struct.unpack_from(f"{name_size}s", buffer)[0]
    return name_bytes.decode("utf-8")
