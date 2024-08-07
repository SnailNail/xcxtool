"""Un-integrated tools for watching memory"""

import dataclasses
import json
import os
import time
from pathlib import Path

import dotenv
import obsws_python
import pendulum

from .memory_reader import PymemReader, connect_cemu


dotenv.load_dotenv()


@dataclasses.dataclass
class CompareResult:
    time: pendulum.datetime
    changes: dict[int, tuple[int, int]]

    def format(self, datefmt: str = "%x %X", addrfmt: str = "#08x", valuefmt: str = "#04x") -> str:
        out = f"{self.time:{datefmt}}\n"
        for addr, (before, after) in self.changes.items():
            out += f"  {addr:{addrfmt}}: {before:{valuefmt}} -> {after:{valuefmt}}\n"
        return out

    def to_json(self):
        return {
            "datetime": str(self.time),
            "changes": self.changes,
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
                deltas[offset] = pair
        self.previous = mem
        return CompareResult(now, deltas)

    def monitor(self, interval: float = 1.0):
        if interval < 0.5:
            raise ValueError("interval should be greater than 0.5 seconds")
        return self._monitor(interval)

    def _monitor(self, interval: float, *, quiet: bool = False):
        monitor_start = pendulum.now()
        last = monitor_start.timestamp()
        print(f"Started monitor at {monitor_start}")
        changes = {}

        try:
            while True:
                delta = self.compare()
                if delta:
                    timedelta = delta.time - monitor_start
                    hours, rest = divmod(timedelta.total_seconds(), 3600)
                    minutes, seconds = divmod(rest, 60)
                    ts = f"{int(hours)}:{int(minutes):02d}:{seconds:05.2f}"
                    if not quiet:
                        print(ts)
                        for addr, (before, after) in delta.changes.items():
                            print(f"  {addr:#08x}: {before:#04x} -> {after:#04x}")
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
        finally:
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
            obs = obsws_python.ReqClient(host=obs_host, port=obs_port, password=obs_pass, timeout=3)
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


if __name__ == '__main__':
    incs = [range(205952, 233736)]  # first big unknown block
    excs = [
        range(0x0, 0xc620),  # Character & skell data
        range(0xc820, 0xc82c),  # Miranium, credits, tickets
        range(0xc850, 0x32228),  # Inventory,
        range(0x39108, 0x39168),  # BLADE greetings
        range(0x39174, 0x39180),  # BLADE level, points, division
        range(0x39540, 0x45d68),  # BLADE Affinity characters, BLADE medals, save time
        range(0x45e40, 0x45244),  # Play time
        range(0x480c0, 0x48274),  # FrontierNav layout
        range(0x48ac8, 0x48acb),  # Field skill levels
    ]
    reader = connect_cemu()
    if reader is None:
        exit(1)
    comp = Comparator(reader, exclude=excs)
    comp.monitor_and_record()
