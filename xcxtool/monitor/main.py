"""Monitor Cemu process for changes"""

import contextlib
import csv
import datetime
import glob
import json
import logging
import os
import re
import sys
import time
from typing import Sequence, Iterable, Generator

from obsws_python import ReqClient
from obsws_python.error import OBSSDKError, OBSSDKRequestError
from plumbum import cli, LocalPath, local

from xcxtool import config, memory_reader
from xcxtool.app import XCXToolApplication, LOGGER_NAME
from xcxtool.monitor import monitor

_log = logging.getLogger(LOGGER_NAME)


def _split_include_exclude(arg: str) -> range:
    split = [int(part, 0) for part in arg.split(",")]
    if len(split) == 1:
        start, end = 0, split[0]
    else:
        start, end = split
    return range(start, end)


class CompareSavedata(XCXToolApplication):
    """Compare gamedata files for changes"""

    DESCRIPTION_MORE = """Performs a simple byte-to-byte comparison of save data and 
    outputs the result to stdout.
    """

    include: list[range] = cli.SwitchAttr(
        ["-i", "--include"],
        _split_include_exclude,
        list=True,
        help="Data file ranges to include in the comparison. Defaults to the whole file",
    )
    exclude: list[range] = cli.SwitchAttr(
        ["-x", "--exclude"],
        _split_include_exclude,
        list=True,
        help="Exclude ranges from the comparison",
    )
    save_directory: LocalPath = cli.SwitchAttr(
        ["-s", "--save-dir"],
        cli.ExistingDirectory,
        excludes=["--before", "--after"],
        help="Override default save data folder",
    )
    before_file: LocalPath = cli.SwitchAttr(
        ["-b", "--before"],
        cli.ExistingFile,
        excludes=["--save-dir"],
        help="Use a specific file as the 'before' state",
    )
    after_file: LocalPath = cli.SwitchAttr(
        ["-a", "--after"],
        cli.ExistingFile,
        excludes=["--save-dir"],
        help="Use a specific file as the 'after' state",
    )
    merge_changes: bool = cli.Flag(
        ["-m", "--merge-results"], help="Merge changes in consecutive memory offsets"
    )

    def main(self):
        if self.parent is None:
            self.error("This app must be run as a subcommand of xcxtool")
            return 2

        self.get_include_and_exclude()
        self.info("Include:", self.include)
        self.info("Exclude:", self.exclude)

        self.get_save_dir()

        before_data = self.get_before_data()
        after_reader = self.get_after()
        if before_data is None or after_reader is None:
            return 2
        named_ranges = monitor.NamedRanges()
        named_ranges.add_from_config(config.get_section("named_ranges"))
        comparator = monitor.Comparator(
            after_reader, self.include, self.exclude, before_data, named_ranges
        )
        if self.merge_changes:
            changes = comparator.aggregate_compare()
        else:
            changes = comparator.compare()
        self.out(changes.format(), highlight=True)

    def get_include_and_exclude(self):
        if not self.include:
            self.include.extend(ranges_from_config("compare.include"))
        if not self.exclude:
            self.exclude.extend(ranges_from_config("compare.exclude"))

    def get_save_dir(self):
        if self.save_directory is not None:
            return self
        if configured := config.get("compare.save_directory"):
            try:
                self.save_directory = cli.ExistingDirectory(configured)
            except ValueError:
                self.warning("Configured save_directory is not a directory")
        self.save_directory = self.parent.cemu_save_dir

    def get_before_data(self) -> bytes | None:
        if self.before_file is None and self.save_directory is not None:
            self.before_file = self.save_directory.join("gamedata_")
        self.success(f"Before: {self.before_file}")
        try:
            before = memory_reader.SaveFileReader(self.before_file)
        except TypeError:  # The encryption key can't be inferred from the data:
            self.error("Before save data could not be read")
        except FileNotFoundError:
            self.error(f"Could not find savedata: {self.before_file}")
        else:
            return before.data
        return

    def get_after(self) -> memory_reader.SaveDataReader | None:
        if self.after_file is None and self.save_directory is not None:
            self.after_file = self.save_directory.join("gamedata")
        self.success(f"After: {self.after_file}")
        try:
            return memory_reader.SaveFileReader(self.after_file)
        except TypeError:
            self.error(f"Could not decrypt save data {self.after_file}")
        except FileNotFoundError:
            self.error(f"Could not find savedata {self.after_file}")
        return


def ranges_from_config(config_key):
    return [range(*pair) for pair in config.get(config_key)]


class MonitorCemu(XCXToolApplication):
    """Monitor Cemu process memory for changes"""

    CALL_MAIN_IF_NESTED_COMMAND = False

    comp: monitor.Comparator
    recording: LocalPath = None

    include: list[range] = cli.SwitchAttr(
        ["-i", "--include"],
        _split_include_exclude,
        list=True,
        help="Data file ranges to include in the comparison. Defaults to the whole file",
    )
    exclude: list[range] = cli.SwitchAttr(
        ["-x", "--exclude"],
        _split_include_exclude,
        list=True,
        help="Exclude ranges from the comparison",
    )
    record: bool = cli.Flag(
        ["r", "record"], False, help="Record gameplay while monitoring"
    )
    merge_changes: bool = cli.Flag(
        ["-m", "--merge-results"], help="Merge changes in consecutive memory offsets"
    )
    write_json: LocalPath = cli.SwitchAttr(
        ["j", "write"],
        local.path,
        help="Write results of the monitoring session to this file as JSON. Note that the "
             "--record function automatically writes a JSON log next to the recording",
    )
    obs_host: str = cli.SwitchAttr(
        ["obs-host"],
        str,
        "localhost",
        group="OBS options",
        help="hostname/IP of OBS websocket",
    )
    obs_port: int = cli.SwitchAttr(
        ["obs-port"], int, 4455, group="OBS options", help="OBS Websocket port"
    )
    obs_password: str = cli.SwitchAttr(
        ["obs-password"], str, group="OBS options", help="OBS websocket password"
    )

    def main(self):
        reader = memory_reader.connect_cemu()
        if reader is None:
            exit(1)
        self.get_include_and_exclude()
        named_ranges = monitor.NamedRanges()
        named_ranges.add_from_config(config.get_section("named_ranges"))
        self.comp = monitor.Comparator(
            reader,
            include=self.include,
            exclude=self.exclude,
            named_ranges=named_ranges,
        )
        try:
            with self.do_recording():
                changes = self.do_monitor(False, self.merge_changes)

        except ConnectionRefusedError as e:
            self.error(
                "[red]Could not connect to OBS Websocket. Is OBS running and correctly configured?[/]"
            )
            self.error(e, rich_highlight=True)
            return 1
        except OBSSDKError as e:
            self.error("[red]Error processing OBS Websocket request[/]")
            self.error(e, rich_highlight=True)
            return 1
        finally:
            reader.close()

        if self.recording is not None:
            json_file = self.recording.with_suffix(".json")
            self.write_output_to_json(changes, json_file)
        elif self.write_json:
            self.write_output_to_json(changes)

    def do_monitor(
        self, quiet: bool, aggregate_runs: bool
    ) -> dict[str, monitor.CompareResult]:

        changes = {}
        monitor_start = datetime.datetime.now()
        monitor_gen = self.comp.monitor(aggregate_runs)
        self.success(f"Started monitor at {monitor_start}")
        try:
            for changeset in monitor_gen:
                if not changeset:
                    continue
                ts = _timedelta_to_hms(changeset.time - monitor_start)
                changes[ts] = changeset
                if quiet:
                    continue
                self.out(f"[bold]{ts}")
                self._print_changes(changeset)

        except KeyboardInterrupt:
            self.success("Caught Ctrl-C, stopping monitor")
            monitor_gen.close()

        return changes

    def get_include_and_exclude(self):
        if not self.include:
            self.include.extend(ranges_from_config("compare.include"))
        if not self.exclude:
            self.exclude.extend(ranges_from_config("compare.exclude"))

    @contextlib.contextmanager
    def do_recording(self) -> Generator[None, None, None]:
        """Set up the OBS client and run monitor-and-record method

        May raise OBSSDKError (or a subclass), ConnectionRefusedError or
        ValueError
        """
        if not self.record:
            yield
            return

        obs = self._get_obs_client()
        old_record_dir = obs.get_record_directory().record_directory
        custom_record_dir = local.path(config.get("compare.recording_dir"))
        try:
            self._set_obs_output_dir(obs, custom_record_dir)
            obs.start_record()
            yield
            recording = obs.stop_record()
        finally:
            self._set_obs_output_dir(obs, old_record_dir)

        self.recording = local.path(recording.output_path)
        self.success(f"Recording saved to {self.recording}")

    def write_output_to_json(self, changes: dict[str, monitor.CompareResult], path: LocalPath = None):
        if path is None:
            path = self.write_json
        with open(path, "w") as f:
            json.dump(changes, f, indent=2)
        self.success(f"Changes written to {path}")

    def _get_obs_client(self):
        obs = ReqClient(
            host=config.get_preferred(self.obs_host, "compare.obs_host"),
            port=config.get_preferred(self.obs_port, "compare.obs_port"),
            password=config.get_preferred(self.obs_password, "compare.obs_password"),
        )
        obs.logger.setLevel(50)
        return obs

    @staticmethod
    def _set_obs_output_dir(client: ReqClient, record_dir: LocalPath, timeout: float = 2.5):
        start = time.monotonic()
        while True:
            try:
                client.set_record_directory(record_dir)
            except OBSSDKRequestError as e:
                if e.code != 500 or (time.monotonic() - start > timeout):
                    raise
                time.sleep(0.2)
            else:
                break

    def _print_changes(self, changeset: monitor.CompareResult):
        for change in changeset.changes:
            self.out(f"  {change}", highlight=True)


def _timedelta_to_hms(delta: datetime.timedelta) -> str:
    hours, rest = divmod(delta.total_seconds(), 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{int(hours)}:{int(minutes):02d}:{seconds:06.3f}"


@MonitorCemu.subcommand("process-json")
class MonitorProcessJson(XCXToolApplication):
    """Process the json data produced when recording gameplay with monitoring"""

    json_path: LocalPath
    csv_path: LocalPath | None
    named_ranges: monitor.NamedRanges

    annotate = cli.Flag(
        ["a", "annotate"],
        False,
        excludes=["locations", "csv"],
        group="Actions",
        help="Annotate changes",
    )
    locations = cli.Flag(
        ["l", "locations"],
        False,
        excludes=["annotate", "csv"],
        group="Actions",
        help="Extract locations",
    )
    csv = cli.Flag(
        ["c", "csv"],
        default=False,
        excludes=["annotate", "locations"],
        group="Actions",
        help="Convert to a CSV file",
    )
    decimal = cli.Flag(
        ["d", "decimal"],
        False,
        requires=["locations"],
        help="Print decimal offsets & bits",
    )
    append_csv = cli.Flag(
        ["append"],
        requires=["csv"],
        help="Append CSV output to the specified file, instead of overwriting it",
    )

    @cli.positional(cli.ExistingFile)
    def main(self, json_path: LocalPath, csv_path: LocalPath = None):
        if not json_path.is_file():
            self.error("json_path must be a JSON file")
            return 2
        try:
            self.json_path = json_path
            self.csv_path = csv_path
            if self.locations:
                self.do_locations()
            elif self.annotate:
                return self.do_annotations()
            elif self.csv:
                return self.to_csv()
            else:
                self.error("Re-run with one of '--locations', '--annotate' or '--csv'")
                return 2
        except KeyboardInterrupt:
            self.out("Caught Ctrl-C, exiting (no changes will be saved)")

    def do_locations(self):
        locations = monitor.process_locations_from_monitor_json(self.json_path)
        max_len = 10
        if self.decimal:
            max_len = max(len(l.name) for l in locations)
        else:
            self.out("new_locations = [")
        for location in sorted(locations, key=lambda l: l.location_id):
            if self.decimal:
                self.out(
                    f"{location.name:{max_len}}  {location.location_id:>4d}: {location.offset} {location.bit:3d}"
                )
            else:
                self.out(f"    {location},")
        if not self.decimal:
            self.out("]")

    def do_annotations(self):
        original_stat = self.json_path.stat()
        change_data = _load_json(self.json_path)
        if change_data is None:
            return 1
        total_changes = len(change_data)

        self.out(f"Annotating {total_changes} changes.", highlight=True)
        self.out(
            "Press [bold]Ctrl-C[/] to exit without saving, enter [bold]Ctrl-Z[/] to save and quit"
        )

        for n, (timestamp, changeset) in enumerate(change_data.items(), 1):
            memory_deltas = [
                monitor.MemoryDelta(**change) for change in changeset["changes"]
            ]
            self.out(
                f"[bold green]{timestamp}", f"({n}/{total_changes})", highlight=True
            )
            for delta in memory_deltas:
                self.out(f"  {delta}", highlight=True)
            if current_comment := changeset.get("comment"):
                self.out(f"[bold]Comment:[/] {current_comment}")
            try:
                comment = self.output_console.input(
                    "Annotation ([bold]enter[/] to keep current): "
                )
            except EOFError:
                self.out("Caught Ctrl-Z, saving and exiting")
                break
            if comment:
                changeset["comment"] = comment

        with open(self.json_path, "w") as f:
            # noinspection PyTypeChecker
            json.dump(change_data, f, indent=2)
        os.utime(self.json_path, (original_stat.st_atime, original_stat.st_mtime))

    def to_csv(self):
        data = _load_json(self.json_path)
        if data is None:
            return 1
        rows = []
        for time, changeset in data.items():
            rows.extend(self._changeset_to_rows(time, changeset))
        if self.csv_path is None:
            self._csv_to_stdout(rows)
            return
        try:
            self._csv_to_file(rows)
        except (OSError, csv.Error) as e:
            self.error("Error writing csv file:")
            self.error(e)
            return 1

    def _changeset_to_rows(self, time: str, changeset: dict) -> list[dict]:
        rows = []
        filename = self.json_path.relative_to(local.cwd)
        for change in changeset["changes"]:
            rows.append(
                {
                    "filename": filename,
                    "time": time,
                    "offset": change["offset"],
                    "before": change["before"][0],
                    "after": change["after"][0],
                    "name": change.get("name", ""),
                    "comment": changeset["comment"],
                }
            )
        return rows

    def _csv_to_file(self, rows: list[dict]):
        mode = "a" if self.append_csv else "w"
        with open(self.csv_path, mode, newline="") as csv_h:
            # noinspection PyTypeChecker
            writer = csv.DictWriter(csv_h, list(rows[0]))
            if not self.append_csv:
                writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _csv_to_stdout(rows: list[dict]):
        if sys.platform == "win32":
            writer = csv.DictWriter(sys.stdout, rows[0], lineterminator="\n")
        else:
            writer = csv.DictWriter(sys.stdout, rows[0])
        writer.writeheader()
        writer.writerows(rows)


@MonitorCemu.subcommand("grep")
class MonitorSearchJson(XCXToolApplication):
    """Search monitor JSON output for patterns.

    By default, PATTERN is treated as a regular expression and is searched for in
    comments. if `-s`|`--simple` is specified, PATTERN is treated as a simple string
    and matched accordingly

    If `-o`|`--offset` is passed, matches will be limited to changes at that offset. As
    well as a plain number, a range can be specified as `start,stop` or as a named
    range.
    """

    _flags: re.RegexFlag = re.IGNORECASE
    offsets: list[range] = []
    pattern: re.Pattern

    simple_search: bool = cli.Flag(
        ["s", "simple"],
        help="Do a simple string search, do not match regular expressions",
    )
    exact_match: bool = cli.Flag(
        ["e", "exact"], help="PATTERN must match the entire comment, not just a subset"
    )

    # noinspection PyPep8Naming
    def main(self, PATTERN: str, *SEARCH_PATHS: str):
        self.pattern = re.compile(PATTERN, self._flags)
        for search_path in _expand_globs(SEARCH_PATHS):
            data = _load_json(search_path)
            if data is None:
                continue
            matches = self.regex_search(data)
            if matches:
                self.print_matches(data, matches, search_path)

    @cli.switch(["c", "case-sensitive"])
    def match_case(self):
        """Do a case-sensitive search"""
        self._flags ^ re.IGNORECASE

    @cli.switch(["o", "offset"], str, list=True)
    def offset(self, offsets: list[str]):
        """Limit matches to changes at the specified offsets or range of offsets"""
        self.offsets = [parse_offset_ranges(o) for o in offsets]

    def regex_search(self, data: dict[str, dict]) -> dict[str, re.Match]:
        matches = {}
        for ts, changeset in data.items():
            if not self.in_offsets(
                [change["offset"] for change in changeset["changes"]]
            ):
                continue
            if self.exact_match:
                match = self.pattern.fullmatch(changeset["comment"])
            else:
                match = self.pattern.search(changeset["comment"])
            if match:
                matches[ts] = match
        return matches

    def print_matches(
        self,
        data: dict[str, dict],
        matches: dict[str, re.Match],
        search_path: LocalPath = None,
    ) -> None:
        indent = ""
        if search_path is not None:
            self.out(
                f"[bold green]{search_path.relative_to(local.cwd)}[/] ({len(matches)} matches):",
                highlight=True,
            )
            indent = "  "
        for ts, match in matches.items():
            changes = data[ts]
            deltas = [
                monitor.MemoryDelta(**delta)
                for delta in changes["changes"]
                if self.in_offsets(delta["offset"])
            ]
            comment = rich_highlight(
                changes["comment"], match.start(), match.end(), "[bold red]"
            )
            self.out(indent + ts, comment)
            for delta in deltas:
                self.out(f"{indent}  {delta}")

    def in_offsets(self, values: int | Iterable[int]) -> bool:
        if not self.offsets:
            return True
        if isinstance(values, int):
            values = [values]
        for value in values:
            return any(value in r for r in self.offsets)
        return False


def parse_offset_ranges(range_input: str) -> range:
    """Convert strings to ranges for the MonitorSearchJson offsets options"""
    named_ranges = config.get_section("named_ranges")
    try:
        single_int = int(range_input, 0)
    except ValueError:
        pass
    else:
        return range(single_int, single_int + 1)
    try:
        return range(*named_ranges[range_input])
    except KeyError:
        pass
    start, _, stop = range_input.partition(",")
    return range(int(start, 0), int(stop, 0))


def rich_highlight(string: str, start: int, end: int, style: str = "[green]") -> str:
    if start == end:
        return string
    return string[:start] + style + string[start:end] + "[/]" + string[end:]


def _expand_globs(args: Sequence[str]) -> list[LocalPath]:
    new_args = []
    if not args:
        args = ["."]
    for arg in args:
        expanded = glob.glob(arg)
        for path_str in expanded:
            path = local.path(path_str)
            if path.is_dir():
                new_args.extend(path.glob("*.json"))
                continue
            if path.suffix.lower() == ".json":
                new_args.append(path)
    return new_args


def _load_json(path: LocalPath) -> dict | None:
    try:
        with open(path, "r") as j:
            return json.load(j)
    except (json.JSONDecodeError, OSError) as e:
        _log.error(f"Error reading JSON file {path}")
        _log.error(e)
    return None
