"""Research on in-game time in save files.

Uses saves from the very start of the game, immediately after gaining control,
where most time-related functions are disabled (time of day is fixed to night,
weather is fixed to thunderstorms, no FrontierNav ticking away).

There are two addresses that are consistently updated:
  * 0x045d60 (8 bytes) appears to be a timestamp of some kind, related to when
    the game was saved
  * 0x045e40 (4 bytes) appears to correlate with the game timer

Both values increment by something slightly less than a second.

As it turns out, the value at 0x045e40 stores the game timer. It looks like a
standard 4-byte integer, but like so many things in this game is actually
multiple values packed into one using non-standard bit sizes. The lowest six
bits store the number of seconds, the next six bits store the minutes, and the
remaining bits store the number of hours.

The individual values can be extracted either with bitwise operations, or
as below, using integer division and remainders. In cPython, both methods
are about as fast as each other.
"""
import pathlib
from dataclasses import dataclass
import re

import dotenv
import pendulum

from xcxtools import savefiles

env = dotenv.dotenv_values()
timer_saves = pathlib.Path(env["TIMER_SAVE_DATA"])
TIMER_FILENAME_RE = re.compile(r"\w+_(?P<hr>\d)+-(?P<min>\d\d)-(?P<sec>\d\d)_")


@dataclass
class TimerData:
    name: str
    value_1: int
    value_2: int
    mtime: pendulum.DateTime

    def __sub__(self, other) -> "TimerDiff":
        if not isinstance(other, TimerData):
            return NotImplemented
        return TimerDiff(
            self.value_1 - other.value_1,
            self.value_2 - other.value_2,
            self.mtime - other.mtime
        )

    def __str__(self) -> str:
        return f"0x45d60: {self.value_1:,d}, 0x45e40: {self.value_2:,d}, mtime: {self.mtime.to_datetime_string()}"


@dataclass
class TimerDiff:
    value_1: int
    value_2: int
    mtime: pendulum.Period


def get_timer_data(save_file: pathlib.Path) -> TimerData:
    data = save_file.read_bytes()
    if data[0x10:0x14] != b"\x00\x03Wr":
        data, _ = savefiles.decrypt_savedata(data)
    value1 = int.from_bytes(data[0x45d60:0x45d68], "big")
    value2 = int.from_bytes(data[0x45e40:0x45e44], "big")
    mtime = pendulum.from_timestamp(save_file.stat().st_mtime, tz="local")
    return TimerData(save_file.name, value1, value2, mtime)


def diff_timerdata(timers: list[TimerData]) -> list[tuple[str, float, TimerDiff]]:
    diffs = []
    prev = None
    for timer in sorted(timers, key=lambda t: t.mtime):
        if prev is None:
            prev = timer
            continue
        caption = f"{prev.name[13:]} to {timer.name[13:]}"
        game_time = (parse_timer_filename(timer.name) - parse_timer_filename(prev.name)).total_seconds()
        diffs.append((caption, game_time, timer - prev))
        prev = timer
    return diffs


def parse_timer_filename(file_name: str) -> pendulum.Duration | None:
    mo = TIMER_FILENAME_RE.match(file_name)
    if mo is None:
        return
    h, m, s = (int(i) for i in mo.groups())
    return pendulum.duration(hours=h, minutes=m, seconds=s)


def diffs_for_glob(glob: str) -> list[TimerDiff]:
    work_list = [get_timer_data(t) for t in timer_saves.glob(glob)]
    work_list.sort(key=lambda t: t.mtime, reverse=True)
    out_list = []
    prev = None
    for timer in work_list:
        if prev is None:
            prev = timer
            continue
        out_list.append(prev - timer)
        prev = timer
    return out_list


def gamedata_value_to_duration(timer_value: int, as_tuple=False) -> pendulum.Duration | tuple[int, int, int]:
    """Convert the value stored at 0x45e40 in the gamedata save file.

    The value looks like a standard 4-byte integer, but like so many things in
    this game is actually multiple values packed into one. The lowest six bits
    store the number of seconds, the next six bits store the minutes, and the
    remaining bits store the number of hours.

    The individual values can be extracted either with bitwise operations, or
    as here, using integer division and remainders. In cPython, both methods
    are about as fast as each other.
    """
    hours, min_sec = divmod(timer_value, 4096)
    minutes, seconds = divmod(min_sec, 64)
    if as_tuple:
        return hours, minutes, seconds
    return pendulum.duration(hours=hours, minutes=minutes, seconds=seconds)
