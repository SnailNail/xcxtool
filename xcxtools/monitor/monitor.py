"""Un-integrated tools for watching memory"""

import dataclasses
import json
import time
from pathlib import Path
from typing import Any

import obsws_python
import pendulum

from xcxtools.memory_reader import MemoryReader
from xcxtools.data import locations


_locations_by_name: dict[str, locations.Location] = {}


@dataclasses.dataclass
class MemoryDelta:
    offset: int = 0
    before: list[int] = dataclasses.field(default_factory=list)
    after: list[int] = dataclasses.field(default_factory=list)

    def __bool__(self):
        return any((self.offset, self.before, self.after))

    def __str__(self):
        return self.to_str()

    def to_str(self, address_format="#08x", value_format="#04x"):
        if len(self.before) == 1:
            before_str = format(self.before[0], value_format)
            after_str = format(self.after[0], value_format)
        else:
            before_str = [format(i, value_format) for i in self.before]
            after_str = [format(i, value_format) for i in self.after]
        return f"{self.offset:{address_format}}: {before_str} -> {after_str}"

    def append(self, new_before, new_after):
        self.before.append(new_before)
        self.after.append(new_after)

    @property
    def next_offset(self) -> int:
        return self.offset + len(self.after)


@dataclasses.dataclass
class CompareResult:
    time: pendulum.datetime
    changes: list[MemoryDelta]

    def format(
        self, datefmt: str = "%x %X", addrfmt: str = "#08x", valuefmt: str = "#04x"
    ) -> str:
        out = f"{self.time:{datefmt}}\n"
        for c in self.changes:
            out += f"  {c.offset:{addrfmt}}: {[format(i, valuefmt) for i in c.before]} -> {[format(i, valuefmt) for i in c.after]}\n"
        return out

    def to_json(self):
        return {
            "datetime": str(self.time),
            "comment": "",
            "changes": [dataclasses.asdict(change) for change in self.changes],
        }

    def __bool__(self) -> bool:
        return bool(self.changes)


class Comparator:
    data_size = 359_984

    def __init__(
        self,
        reader: PymemReader,
        include: list[range] = None,
        exclude: list[range] = None,
        initial_data: bytes = None,
    ):
        reader.player_addr -= 0x58
        self.reader = reader
        self.includes = include if include is not None else [range(0, self.data_size)]
        self.excludes = exclude if exclude is not None else []
        if initial_data is None:
            self.initial = reader.read_memory(0, self.data_size)
        self.previous = self.initial

    def compare(self) -> CompareResult:
        now = pendulum.now("local")
        mem = self._read()
        deltas = []
        for offset, (before, after) in enumerate(zip(self.previous, mem)):
            if before != after and self._valid_offset(offset):
                deltas.append(MemoryDelta(offset, [before], [after]))
        self.previous = mem
        return CompareResult(now, deltas)

    def aggregate_compare(self) -> CompareResult:
        """WIP"""
        new_mem = self._read()
        deltas = []
        current_run = None
        now = pendulum.now()

        for offset, (before, after) in enumerate(zip(self.previous, new_mem)):
            if not self._valid_offset(offset) or before == after:
                continue
            if current_run is None:
                current_run = MemoryDelta(offset, [before], [after])
            elif offset == current_run.next_offset:
                current_run.append(before, after)
            else:
                deltas.append(current_run)
                current_run = MemoryDelta(offset, [before], [after])

        if current_run is not None:
            deltas.append(current_run)

        self.previous = new_mem
        return CompareResult(now, deltas)

    def monitor(
        self, interval: float = 1.0, *, quiet: bool = False, aggregate_runs: bool = True
    ):
        """Continuously compare memory states and interval seconds.

        If quiet is True, no output will be printed, only a dictionary of changes
        will be returned

        If aggregate_runs is True, changes in continuous memory blocks will be
        aggregated into a single result
        """
        if interval < 0.5:
            raise ValueError("interval should be greater than 0.5 seconds")
        return self._monitor(interval, quiet=quiet, aggregate_runs=aggregate_runs)

    def _monitor(self, interval: float, *, quiet: bool, aggregate_runs: bool):
        if aggregate_runs:
            compare_func = self.aggregate_compare
        else:
            compare_func = self.compare

        monitor_start = pendulum.now()
        last = monitor_start.timestamp()
        print(f"Started monitor at {monitor_start}")
        changes = {}
        should_continue = True

        try:
            while should_continue:
                delta = compare_func()
                if delta:
                    timedelta = delta.time - monitor_start
                    hours, rest = divmod(timedelta.total_seconds(), 3600)
                    minutes, seconds = divmod(rest, 60)
                    ts = f"{int(hours)}:{int(minutes):02d}:{seconds:05.2f}"
                    if not quiet:
                        print(ts)
                        for change in delta.changes:
                            print(f"  {change}")
                    changes[ts] = delta.to_json()
                current = delta.time.timestamp()
                since_last = current - last
                if since_last >= interval:
                    continue
                next_in = interval - since_last
                last = current
                time.sleep(next_in)
        except KeyboardInterrupt:
            print("Caught Ctrl-C, stopping monitor")

        return changes

    def monitor_and_record(
        self,
        obs: obsws_python.ReqClient,
        interval: float = 1.0,
        *,
        quiet: bool = False,
        aggregate_runs: bool = True,
    ):
        """Monitor changes in and record with OBS.

        A JSON file will be stored next to the recorded video. The JSON file
        will contain details of the changes, keyed to timestamps that should
        approximately be synchronised with the video.

        The obs parameter must be a connected obsws client object, and OBS must
        be installed, running and configured to record Cemu.
        """
        obs.start_record()
        changes = self.monitor(interval, quiet=quiet, aggregate_runs=aggregate_runs)
        response = obs.stop_record()

        vid_file = Path(response.output_path)
        json_file = vid_file.with_suffix(".json")
        with json_file.open("w") as f:
            json.dump(changes, f, indent=2)
        print(f"Changes and video saved to {vid_file.parent}")

    def _read(self) -> bytes:
        return self.reader.read_memory(0, self.data_size)

    def _valid_offset(self, offset: int) -> bool:
        if not any(offset in r for r in self.includes):
            return False
        if any(offset in r for r in self.excludes):
            return False
        return True


def process_locations_from_monitor_json(json_path: str) -> list[locations.Location]:
    with open(json_path) as f:
        data = json.load(f)
    found = 0
    no_match = 0
    matched = []
    for delta in data.values():
        if not delta["comment"].lower().startswith("location:"):
            continue
        found += 1
        location = match_json_to_location(delta)
        if location is None:
            no_match += 1
            continue
        matched.append(location)
    return matched


def match_json_to_location(monitor_delta: dict[str, Any]) -> locations.Location | None:
    """Get a location from"""
    if not _locations_by_name:
        _locations_by_name.update((loc.name, loc) for loc in locations.locations)

    *_, loc_name = monitor_delta["comment"].partition(":")
    location = _locations_by_name.get(loc_name)
    if location is None:
        print(f"Could not match name: {loc_name}")
        return None

    changes = monitor_delta["changes"]
    if isinstance(changes, dict):
        offset, before, after = _get_changes_from_json_v1(changes)
    else:
        offset, before, after = _get_changes_from_json_v2(changes)

    bit = after - before
    if bit <= 0:
        print(f"Invalid data change ({before:#04x} -> {after:#04x}")
    return location._replace(offset=offset, bit=bit)


def _get_changes_from_json_v2(changes: list[dict]) -> tuple:
    if len(changes) > 1:
        change = _get_change_from_user(changes)
    else:
        change = changes[0]

    return change["offset"], change["before"], change["after"]


def _get_change_from_user(changes: list[dict]) -> dict:
    for n, change in enumerate(changes):
        print(f" {n+1:>4d}: {change['offset']:#08x}")
    prompt = f"Multiple offsets in change,please select one (1 - {len(changes)}): "
    choice = -1
    while choice < 1 or choice > len(changes):
        try:
            choice = int(input(prompt))
        except ValueError:
            continue
    return changes[choice - 1]


def _get_changes_from_json_v1(changes: dict[str, dict]) -> tuple[int, int, int]:
    offsets = list(changes)
    if len(offsets) > 1:
        offset = _get_offset_from_user(offsets)
    else:
        offset = int(offsets[0])
    before, after = changes[str(offset)]
    return offset, before, after


def _get_offset_from_user(offsets: list[str]) -> int:
    for n, offset in enumerate(offsets):
        print(f" {n + 1:>4d}: {int(offset):#08x}")
    prompt = f"Multiple offsets in change, please select one (1 - {len(offsets)}): "
    choice = -1
    while choice < 1 or choice > len(offsets):
        try:
            choice = int(input(prompt))
        except ValueError:
            continue
    return int(offsets[choice - 1])
