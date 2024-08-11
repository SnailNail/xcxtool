"""Monitor Cemu process for changes"""
import plumbum
from plumbum import cli
from obsws_python import ReqClient

from xcxtools import memory_reader
from xcxtools.monitor import monitor


class MonitorCemu(cli.Application):
    """Monitor Cemu process memory for changes"""

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
            range(0x45D71, 0x45E18),  # Fast travel mysteries
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

    @cli.positional(cli.ExistingFile)
    def main(self, json_path: plumbum.LocalPath):
        monitor.process_locations_from_monitor_json(json_path)
