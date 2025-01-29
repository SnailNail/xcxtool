"""Monitor Cemu process for changes"""

import json
import os
import sys

from plumbum import cli, LocalPath
import rich.console
from obsws_python import ReqClient

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
            reader, include=self.include, exclude=self.exclude, named_ranges=named_ranges
        )
        if self.record:
            self.obs = self._get_obs_client()
            self.obs.start_record()
            comp.monitor_and_record(self.obs, aggregate_runs=False)
        else:
            comp.monitor()
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


@MonitorCemu.subcommand("process-json")
class MonitorProcessJson(cli.Application):
    """Process the json data produced when recording gameplay with monitoring"""

    json_path: LocalPath
    named_ranges: monitor.NamedRanges

    annotate = cli.Flag(
        ["a", "annotate"], False, excludes=["locations"], help="Annotate changes"
    )
    locations = cli.Flag(
        ["l", "locations"], False, excludes=["annotate"], help="Extract locations"
    )
    decimal = cli.Flag(
        ["d", "decimal"], False, excludes=["annotate"], help="Print decimal offsets & bits"
    )

    @cli.positional(cli.ExistingFile)
    def main(self, json_path: LocalPath):
        try:
            self.json_path = json_path
            if self.locations:
                self.do_locations()
            elif self.annotate:
                self.do_annotations()
            else:
                print("Re-run with one of '--locations' or '--annotate'")
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

        for n, (timestamp, changeset) in enumerate(change_data.items()):
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
