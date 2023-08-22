"""Research on in-game time in save files.

Uses saves from the very start of the game, immediately after gaining control,
where most time-related functions are disabled (time of day is fixed to night,
weather is fixed to thunderstorms, no FrontierNav ticking away).

There are two addresses that are consistently updated:
  * 0x045d64 (4 bytes) records the timestamp of the time the game was saved
  * 0x045e40 (4 bytes) records the game timer

Both the timestamp and timer values are packed integer values. The timestamp
is comprised of six bits for the year (since 2000), nine bits for the number
of days into the year and the time of the save (hours, minutes and seconds in
5, 6 and 6 bits respectively)

The timer value records the time since the game starts in hours (20 bits),
minutes (6 bits) and seconds (six) bits.

The values can be unpacked using either integer division and modulo operations
(as in the unpack_game_timer() function below) or using bitwise
operations (as in the unpack_save_timestamp() function), there is negligible
performance difference between the two in CPython.
"""
import typing

import pendulum


SAVE_TIMESTAMP_OFFSET = 0x45d64
SAVE_TIMESTAMP_EPOCH = pendulum.datetime(2000, 1, 1)
GAME_TIMER_OFFSET = 0x45e40


class GameTimer(typing.NamedTuple):
    hours: int
    minutes: int
    seconds: int

    def as_duration(self) -> pendulum.Duration:
        return pendulum.duration(
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
        )


class SavedTime(typing.NamedTuple):
    year: int
    days: int
    hours: int
    minutes: int
    seconds: int

    def as_datetime(self) -> pendulum.DateTime:
        return SAVE_TIMESTAMP_EPOCH.add(
            years=self.year,
            days=self.days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
        )


def unpack_game_timer(timer_value: int | bytes) -> GameTimer:
    """Convert the value stored at 0x45e40 in the gamedata save file.

    The value looks like a standard 4-byte integer, but like so many things in
    this game is actually multiple values packed into one. The lowest six bits
    store the number of seconds, the next six bits store the minutes, and the
    remaining bits store the number of hours.

    The individual values can be extracted either with bitwise operations, or
    as here, using integer division and remainders. In cPython, both methods
    are about as fast as each other.
    """
    if isinstance(timer_value, bytes):
        timer_value = int.from_bytes(timer_value, "big")
    hours, min_sec = divmod(timer_value, 4096)
    minutes, seconds = divmod(min_sec, 64)
    return GameTimer(hours, minutes, seconds)


def unpack_save_timestamp(data: int | bytes) -> SavedTime:
    """Convert the value stored at 0x45d64 in the gamedata file.

    This value stores the timestamp of the last save, stored as five integers
    packed into 32 bits as below:

    YYYYYYDD DDDDDDDH HHHHMMMM MMSSSSSS

    where YYYYYY are the years since 2000, DDDDDDDDD are the days since the
    start of the year, HHHHH are the hours, MMMMMM are the minutes and SSSSSS
    are the seconds of the save time.
    """
    if isinstance(data, bytes):
        data = int.from_bytes(data, "big")
    year = data >> 26
    days = (data >> 17) & 511
    hours = (data >> 12) & 31
    mins = (data >> 6) & 63
    secs = data & 63
    return SavedTime(year, days, hours, mins, secs)
