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
        help="Name of the Cemu process to read data from",
        default="cemu.exe",
    )

    def __init__(self, executable):
        super().__init__(executable)
        self.cemu: pymem.Pymem | None = None

    def main(self):
        print("Running XCXToolCLI.main()")
        config.load_config(self.config_path)
        try:
            self.cemu = self.find_cemu()
        except pymem.exception.ProcessNotFound:
            # Checking errors outside the call so we can exit on error
            print("Could not find cemu process, exiting", file=sys.stderr)
            return 1

    def find_cemu(self) -> pymem.Pymem:
        """Find the cemu process and return a Pymem instance"""
        proc_name = (
            self.cemu_process_name
            if self.cemu_process_name is not None
            else config.config["cemu"]["process_name"]
        )
        cemu = pymem.Pymem(proc_name)
        print(f"Found Cemu at {cemu.base_address:#018x}")
        return cemu


XCXToolsCLI.subcommand("backup", BackupSave)
