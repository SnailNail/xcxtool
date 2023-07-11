"""Research on in-game time in save files.

Uses saves from the very start of the game, immediately after gaining control,
where most time-related functions are disabled (time of day is fixed to night,
weather is fixed to thunderstorms, no FrontierNav ticking away).

There are two addresses that are consistently updated:
  * 0x045d60 (8 bytes) appears to be a timestamp of some kind, related to when
    the game was saved
  * 0x045e40 (4 bytes) appears to correlate with the game timer

Both values increment by something slightly less than a second

One of the XCX provides a function for setting the time. It's never worked
for me, but it provides an interesting mapping of game times to some kind o tick:
    >>> ct_times = {
    ... "midnight": 0,
    ... "3:00 am": 12000,
    ... "6:00 am": 24000,
    ... "9:00 am": 36900,
    ... "12:00 pm": 49000,
    ... "3:00 pm": 61400,
    ... "6:00 pm": 73700,
    ... "9:00 pm": 86000,
    ... }

I'm not sure where in the code this is used, but it does imply some non-linear
mapping between game ticks and time units.
"""
import pathlib
from dataclasses import dataclass

import dotenv
import pendulum

from xcxtools import savefiles

env = dotenv.dotenv_values()

timer_saves = pathlib.Path(env["TIMER_SAVE_DATA"])


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
    value1 = int.from_bytes(data[0x45d60:0x45d68], "big")
    value2 = int.from_bytes(data[0x45e40:0x45e44], "big")
    mtime = pendulum.from_timestamp(save_file.stat().st_mtime, tz="local")
    return TimerData(save_file.name, value1, value2, mtime)


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
