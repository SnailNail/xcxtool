"""Main entry point for xcxtools"""

from plumbum import cli
import plumbum
from . import VERSION


class XCXToolsCLI(cli.Application):
    PROGNAME = "xcxtools"
    DESCRIPTION = "Utilities for playing Xenoblade Chronicles X on Cemu"
    VERSION = VERSION
    config_path = cli.SwitchAttr(
        "--config-path",
        plumbum.local.path,
        help="Use this file for config instead of the default",
        default=plumbum.local.path("xcxtools.ini"),
    )
    cemu_process_name = cli.SwitchAttr(
        "--cemu-process-name",
        help="Name of the Cemu process to read data from",
        default="cemu.exe"
    )

    def main(self):
        print("Running XCXToolCLI.main()")
        print(f"Using config at {self.config_path}")
        print(
            f"Config file exists"
            if self.config_path.exists()
            else "Config file does not exist"
        )
