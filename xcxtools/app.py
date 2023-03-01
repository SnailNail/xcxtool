"""Main entry point for xcxtools"""
import sys

import pymem
from plumbum import cli
import plumbum

from . import VERSION
from . import config
from .backup_save import BackupSave


class XCXToolsCLI(cli.Application):
    PROGNAME = "xcxtools"
    DESCRIPTION = "Utilities for playing Xenoblade Chronicles X on Cemu"
    VERSION = VERSION

    config_path: plumbum.LocalPath = cli.SwitchAttr(
        "--config-path",
        plumbum.local.path,
        help="Use this file for config instead of the default",
        default=plumbum.local.path("xcxtools.ini"),
    )
    cemu_process_name: str = cli.SwitchAttr(
        "--cemu-process-name",
        help="Name of the Cemu process to read data from; the default is cemu.exe",
    )

    def __init__(self, executable):
        super().__init__(executable)
        self.cemu: pymem.Pymem | None = None

    def main(self):
        print("Running XCXToolCLI.main()")
        config.load_config(self.config_path)
        self.find_cemu()

    def find_cemu(self) -> None:
        """Find the cemu process, warn if not found"""
        proc_name = (
            self.cemu_process_name
            if self.cemu_process_name is not None
            else config.config["cemu"]["process_name"]
        )
        try:
            self.cemu = pymem.Pymem(proc_name)
        except pymem.exception.ProcessNotFound:
            print(
                f"Could not find {proc_name} process, dynamic file names not available",
                file=sys.stderr,
            )
        else:
            print(f"Found Cemu at {self.cemu.base_address:#018x}")


XCXToolsCLI.subcommand("backup", BackupSave)
