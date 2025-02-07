"""Monitor Cemu process for changes"""

import csv
import json
import os
import re
import sys

import rich.console
from obsws_python import ReqClient
from obsws_python.error import OBSSDKError
from plumbum import cli, LocalPath

from xcxtool import config, memory_reader
from xcxtool.monitor import monitor

_console = rich.console.Console()
rprint = _console.print


def _split_include_exclude(arg: str) -> range:
    split = [int(part, 0) for part in arg.split(",")]
    if len(split) == 1:
        start, end = 0, split[0]
    else:
        start, end = split
    return range(start, end)


class CompareSavedata(cli.Application):
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
            print("This app must be run as a subcommand of xcxtool")
            return 2

        self.get_include_and_exclude()
        print("Include:", self.include)
        print("Exclude:", self.exclude)

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
        print(changes.format())

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
                print("Configured save_directory is not a directory")
        self.save_directory = self.parent.cemu_save_dir

    def get_before_data(self) -> bytes | None:
        if self.before_file is None and self.save_directory is not None:
            self.before_file = self.save_directory.join("gamedata_")
        print("Before:", self.before_file)
        try:
            before = memory_reader.SaveFileReader(self.before_file)
        except TypeError:  # The encryption key can't be inferred from the data:
            print("Before save data could not be read", file=sys.stderr)
        except FileNotFoundError:
            print("Could not find savedata", self.before_file, file=sys.stderr)
        else:
            return before.data
        return

    def get_after(self) -> memory_reader.SaveDataReader | None:
        if self.after_file is None and self.save_directory is not None:
            self.after_file = self.save_directory.join("gamedata")
        print("After:", self.after_file)
        try:
            return memory_reader.SaveFileReader(self.after_file)
        except TypeError:
            print("Could not decrypt save data", self.after_file, file=sys.stderr)
        except FileNotFoundError:
            print("Could not find savedata", self.before_file, file=sys.stderr)
        return


def ranges_from_config(config_key):
    return [range(*pair) for pair in config.get(config_key)]


class MonitorCemu(cli.Application):
    """Monitor Cemu process memory for changes"""

    CALL_MAIN_IF_NESTED_COMMAND = False

    obs: ReqClient

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
        comp = monitor.Comparator(
            reader,
            include=self.include,
            exclude=self.exclude,
            named_ranges=named_ranges,
        )
        if self.record:
            try:
                self._record(comp)
            except ConnectionRefusedError as e:
                rprint(
                    "[red]Could not connect to OBS Websocket. Is OBS running and correctly configured?[/]"
                )
                rprint(e)
                return 1
            except OBSSDKError as e:
                rprint("[red]Error processing OBS Websocket request[/]")
                rprint(e)
                return 1
        else:
            comp.monitor(aggregate_runs=self.merge_changes)
        reader.close()

    def get_include_and_exclude(self):
        if not self.include:
            self.include.extend(ranges_from_config("compare.include"))
        if not self.exclude:
            self.exclude.extend(ranges_from_config("compare.exclude"))

    def _get_obs_client(self):
        obs = ReqClient(
            host=config.get_preferred(self.obs_host, "compare.obs_host"),
            port=config.get_preferred(self.obs_port, "compare.obs_port"),
            password=config.get_preferred(self.obs_password, "compare.obs_password"),
        )
        return obs

    def _record(self, comparator: monitor.Comparator) -> None:
        """Set up the OBS client and run monitor-and-record method

        May raise OBSSDKError (or a subclass), ConnectionRefusedError or
        ValueError
        """
        obs = self._get_obs_client()
        old_record_dir = obs.get_record_directory().record_directory
        custom_record_dir = config.get("compare.recording_dir")
        try:
            if custom_record_dir:
                obs.set_record_directory(custom_record_dir)
            comparator.monitor_and_record(aggregate_runs=self.merge_changes)
        finally:
            obs.set_record_directory(old_record_dir)


@MonitorCemu.subcommand("process-json")
class MonitorProcessJson(cli.Application):
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
        try:
            self.json_path = json_path
            self.csv_path = csv_path
            if self.locations:
                self.do_locations()
            elif self.annotate:
                self.do_annotations()
            elif self.csv:
                self.to_csv()
            else:
                print("Re-run with one of '--locations', '--annotate' or '--csv'")
        except KeyboardInterrupt:
            print("Caught Ctrl-C, exiting (no changes will be saved)")

    def do_locations(self):
        locations = monitor.process_locations_from_monitor_json(self.json_path)
        max_len = 10
        if self.decimal:
            max_len = max(len(l.name) for l in locations)
        else:
            print("new_locations = [")
        for location in sorted(locations, key=lambda l: l.location_id):
            if self.decimal:
                print(
                    f"{location.name:{max_len}}  {location.location_id:>4d}: {location.offset} {location.bit:3d}"
                )
            else:
                print(f"    {location},")
        if not self.decimal:
            print("]")

    def do_annotations(self):
        original_stat = self.json_path.stat()
        with open(self.json_path) as f:
            change_data = json.load(f)
        total_changes = len(change_data)

        print(f"Annotating {total_changes} changes.")
        print("Press Ctrl-C to exit without saving, enter Ctrl-Z to save and quit")

        for n, (timestamp, changeset) in enumerate(change_data.items(), 1):
            memory_deltas = [
                monitor.MemoryDelta(**change) for change in changeset["changes"]
            ]
            rprint(f"[bold green]{timestamp}", f"({n}/{total_changes})")
            for delta in memory_deltas:
                rprint(f"  {delta}")
            if current_comment := changeset.get("comment"):
                rprint(f"[bold]Comment:[/] {current_comment}")
            try:
                comment = input("Annotation (enter to keep current): ")
            except EOFError:
                print("Caught Ctrl-Z, saving and exiting")
                break
            if comment:
                changeset["comment"] = comment

        with open(self.json_path, "w") as f:
            json.dump(change_data, f, indent=2)
        os.utime(self.json_path, (original_stat.st_atime, original_stat.st_mtime))

    def to_csv(self):
        with open(self.json_path) as f:
            data = json.load(f)
        rows = []
        for time, changeset in data.items():
            rows.extend(self._changeset_to_rows(time, changeset))
        if self.csv_path is None:
            self._csv_to_stdout(rows)
        else:
            self._csv_to_file(rows)

    @staticmethod
    def _changeset_to_rows(time: str, changeset: dict) -> list[dict]:
        rows = []
        for change in changeset["changes"]:
            rows.append(
                {
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
class MonitorSearchJson(cli.Application):
    """Search monitor JSON output for patterns.

    By default, PATTERN is treated as a regular expression and is searched for in
    comments. if `-s`|`--simple` is specified, PATTERN is treated as a simple string
    and matched accordingly

    If `-o`|`--offset` is passed, matches will be limited to changes at that offset. As
    well as a plain number, a range can be specified as `start,stop` or as a named
    range.
    """

    _flags: re.RegexFlag = re.IGNORECASE
    pattern: re.Pattern
    data: dict[str, dict]
    matches: dict[str, re.Match]
    offsets: list[range] = []

    simple_search: bool = cli.Flag(
        ["s", "simple"],
        help="Do a simple string search, do not match regular expressions",
    )
    exact_match: bool = cli.Flag(
        ["e", "exact"], help="PATTERN must match the entire comment, not just a subset"
    )

    # noinspection PyPep8Naming
    def main(self, PATTERN: str, SEARCH_PATH: cli.ExistingFile):
        self.pattern = re.compile(PATTERN, self._flags)
        with open(SEARCH_PATH) as f:
            self.data = json.load(f)
        self.regex_search()
        self.print_matches()

    @cli.switch(["c", "case-sensitive"])
    def match_case(self):
        """Do a case-sensitive search"""
        self._flags ^ re.IGNORECASE

    @cli.switch(["o", "offset"], list=True)
    def offset(self, offsets: list[str]):
        """Limit matches to changes at the specified offsets or range of offsets"""
        self.offsets = [parse_offset_ranges(o) for o in offsets]

    def regex_search(self):
        self.matches = {}
        for ts, changeset in self.data.items():
            if self.exact_match:
                match = self.pattern.fullmatch(changeset["comment"])
            else:
                match = self.pattern.search(changeset["comment"])
            if match:
                self.matches[ts] = match

    def print_matches(self):
        for ts, match in self.matches.items():
            changes = self.data[ts]
            deltas = [
                monitor.MemoryDelta(**delta)
                for delta in changes["changes"]
                if self.in_offsets(delta["offset"])
            ]
            comment = rich_highlight(changes["comment"], match.start(), match.end())
            rprint(ts, comment)
            for delta in deltas:
                rprint(f"  {delta}")

    def in_offsets(self, value: int) -> bool:
        if not self.offsets:
            return True
        return any(value in r for r in self.offsets)


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
