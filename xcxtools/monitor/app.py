"""Monitor Cemu process for changes"""
import json
import os

import plumbum
from plumbum import cli
import rich.console
from obsws_python import ReqClient

from xcxtools import memory_reader
from xcxtools.monitor import monitor


_console = rich.console.Console()
rprint = _console.print


class MonitorCemu(cli.Application):
    """Monitor Cemu process memory for changes"""

    CALL_MAIN_IF_NESTED_COMMAND = False

    obs: ReqClient
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
        incs = [range(205952, 233736)]  # first big unknown block
        excs = [
            range(0x0, 0xC620),  # Character & skell data
            range(0xC820, 0xC82C),  # Miranium, credits, tickets
            range(0xC850, 0x32228),  # Inventory,
            range(0x39108, 0x39168),  # BLADE greetings
            range(0x39174, 0x39180),  # BLADE level, points, division
            range(
                0x39540, 0x45D68
            ),  # BLADE Affinity characters, BLADE medals, save time
            range(0x45D71, 0x45E3F),  # Fast travel mysteries (also updates when saving)
            range(0x45E40, 0x45E44),  # Play time
            range(0x480C0, 0x48274),  # FrontierNav layout
            range(0x48AC8, 0x48ACB),  # Field skill levels
        ]
        reader = memory_reader.connect_cemu()
        if reader is None:
            exit(1)
        comp = monitor.Comparator(reader, exclude=excs)
        if self.record:
            self.obs = self._get_obs_client()
            self.obs.start_record()
            comp.monitor_and_record(self.obs, aggregate_runs=False)
        else:
            comp.monitor()
        reader.close()

    def _get_obs_client(self):
        obs = ReqClient(
            host=self.obs_host, port=self.obs_port, password=self.obs_password
        )
        return obs


@MonitorCemu.subcommand("process-json")
class MonitorProcessJson(cli.Application):
    """Process the json data produced when recording gameplay with monitoring"""

    json_path: plumbum.LocalPath

    annotate = cli.Flag(["a", "annotate"], False, excludes=["locations"], help="Annotate changes")
    locations = cli.Flag(["l", "locations"], False, excludes=["annotate"], help="Extract locations")

    @cli.positional(cli.ExistingFile)
    def main(self, json_path: plumbum.LocalPath):
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
        monitor.process_locations_from_monitor_json(self.json_path)

    def do_annotations(self):
        original_stat = self.json_path.stat()
        with open(self.json_path) as f:
            change_data = json.load(f)
        total_changes = len(change_data)

        print(f"Annotating {total_changes} changes.")
        print("Press Ctrl-C to exit without saving, enter Ctrl-Z to save and quit")

        for n, (timestamp, changeset) in enumerate(change_data.items()):
            memory_deltas = [monitor.MemoryDelta(**change) for change in changeset["changes"]]
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
