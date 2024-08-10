"""Un-integrated tools for watching memory"""

import dataclasses
import json
import os
import time
from pathlib import Path
from typing import Any

import dotenv
import obsws_python
import pendulum

from .memory_reader import PymemReader, connect_cemu
from .data import locations


dotenv.load_dotenv()


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
    changes: dict[int, MemoryDelta]

    def format(
        self, datefmt: str = "%x %X", addrfmt: str = "#08x", valuefmt: str = "#04x"
    ) -> str:
        out = f"{self.time:{datefmt}}\n"
        for addr, d in self.changes.items():
            out += f"  {addr:{addrfmt}}: {[format(i, valuefmt) for i in d.before]} -> {[format(i, valuefmt) for i in d.after]}\n"
        return out

    def to_json(self):
        return {
            "datetime": str(self.time),
            "comment": "",
            "changes": {
                offset: dataclasses.asdict(delta)
                for offset, delta in self.changes.items()
            },
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
        deltas = {}
        for offset, pair in enumerate(zip(self.previous, mem)):
            if pair[0] != pair[1] and self._valid_offset(offset):
                deltas[offset] = MemoryDelta(offset, [pair[0]], [pair[1]])
        self.previous = mem
        return CompareResult(now, deltas)

    def aggregate_compare(self) -> CompareResult:
        """WIP"""
        new_mem = self._read()
        deltas = {}
        current_run = None
        now = pendulum.now()

        for offset, (before, after) in enumerate(zip(self.previous, new_mem)):
            if not self._valid_offset(offset) or before == after:
                continue
            if current_run is None:
                current_run = MemoryDelta(offset, before, after)
            if offset == current_run.next_offset:
                current_run.append(before, after)
            else:
                deltas[current_run.offset] = current_run
                current_run = MemoryDelta(offset, [before], [after])

        if current_run is not None:
            deltas[current_run.offset] = current_run

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
                        for addr, d in delta.changes.items():
                            print(f"  {d}")
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

    def monitor_and_record(self, interval: float = 1.0):
        """Monitor changes in and record with OBS.

        A JSON file will be stored next to the recorded video. The JSON file
        will contain details of the changes, keyed to timestamps that should
        approximately be synchronised with the video.

        OBS must be installed, running and set-up to record otherwise this
        function will fail, perhaps unpredictably. OBS Websocket parameters
        are read from the OBS_WEBSOCKET_{HOST|PORT|PASSWORD} environment
        variables, or a .env file in the dotenv search path
        """
        obs_host = os.getenv("OBS_WEBSOCKET_HOST", "localhost")
        obs_port = int(os.getenv("OBS_WEBSOCKET_PORT", 4455))
        obs_pass = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
        try:
            obs = obsws_python.ReqClient(
                host=obs_host, port=obs_port, password=obs_pass, timeout=3
            )
        except Exception as e:
            print("Could not connect to OBS Websocket")
            print(e)
            return
        obs.start_record()
        changes = self.monitor(interval)
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

    offsets = list(monitor_delta["changes"])
    if len(offsets) > 1:
        offset = _get_offset_from_user(offsets)
    else:
        offset = int(offsets[0])

    before, after = monitor_delta["changes"][str(offset)]
    bit = after - before
    if bit <= 0:
        print(f"Invalid data change ({before:#04x} -> {after:#04x}")
    return location._replace(offset=offset, bit=bit)


def _get_offset_from_user(offsets: list[int]) -> int:
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


if __name__ == "__main__":
    incs = [range(205952, 233736)]  # first big unknown block
    excs = [
        range(0x0, 0xC620),  # Character & skell data
        range(0xC820, 0xC82C),  # Miranium, credits, tickets
        range(0xC850, 0x32228),  # Inventory,
        range(0x39108, 0x39168),  # BLADE greetings
        range(0x39174, 0x39180),  # BLADE level, points, division
        range(0x39540, 0x45D68),  # BLADE Affinity characters, BLADE medals, save time
        # range(0x45d71, 0x45e18),  # Fast travel mysteries
        range(0x45E40, 0x45E44),  # Play time
        range(0x480C0, 0x48274),  # FrontierNav layout
        range(0x48AC8, 0x48ACB),  # Field skill levels
    ]
    reader = connect_cemu()
    if reader is None:
        exit(1)
    comp = Comparator(reader, exclude=excs)
    # comp.monitor_and_record()
    comp.monitor()
