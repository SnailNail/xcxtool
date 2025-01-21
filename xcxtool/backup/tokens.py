"""Module to generate replacement token values for backup names"""

import struct

import pendulum
from plumbum import LocalPath

from ..memory_reader import SaveDataReader
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
division_map = {
    0: "none",
    1: "Pathfinders",
    2: "Interceptors",
    3: "Harriers",
    4: "Reclaimers",
    5: "Curators",
    6: "Prospectors",
    7: "Outfitters",
    8: "Mediators",
}


def get_datetime() -> dict[str, pendulum.DateTime]:
    now = pendulum.now("local")
    return {
        "date": format(now, "%Y%m%d"),
        "time": format(now, "%H-%M-%S"),
        "datetime": now,
    }


def get_mtime(file: LocalPath) -> dict[str, pendulum.DateTime]:
    return {"save_date": pendulum.from_timestamp(file.stat().st_mtime, tz="local")}


def get_character_data(reader: SaveDataReader) -> dict:
    buffer = reader.read_memory(88, 1404)

    def unpack_value(fmt: str, offset: int):
        val = struct.unpack_from(fmt, buffer, offset)
        if len(val) == 1:
            return val[0]
        return val

    blade_level, division = struct.unpack_from(
        ">2I",
        reader.read_memory(0x39178, 8),
    )

    return {
        "name": _get_name(buffer),
        "level": unpack_value("B", 0x7a),
        "exp": unpack_value(">I", 0x7c),
        "class": class_map.get(unpack_value("B", 0x128), "Drifter"),
        "class_rank": unpack_value("B", 0x12a),
        "class_exp": unpack_value(">H", 0x12c),
        "division": division_map.get(division, "none"),
        "blade_level": blade_level,
    }


def get_playtime(reader: SaveDataReader) -> dict[str, str | pendulum.DateTime]:
    playtime_buffer = reader.read_memory(0x45e40, 4)
    playtime = game_timer.unpack_game_timer(playtime_buffer)
    savetime_buffer = reader.read_memory(0x45d64, 4)
    savetime = game_timer.unpack_save_timestamp(savetime_buffer).as_datetime()
    return {
        "play_time": f"{playtime.hours:03d}-{playtime.minutes:02d}-{playtime.seconds:02d}",
        "save_date": format(savetime, "%Y%m%d"),
        "save_time": format(savetime, "%H-%M-%S"),
        "save_datetime": savetime,
    }


def _get_name(buffer: bytes) -> str:
    name_size: int = struct.unpack_from(">I", buffer, 0x40)[0]
    name_bytes: bytes = struct.unpack_from(f"{name_size}s", buffer)[0]
    return name_bytes.decode("utf-8")
