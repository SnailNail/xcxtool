"""Main entry point for xcxtools"""
import sys

import pymem
from plumbum import cli
import plumbum

from . import VERSION
from . import config
from .backup import BackupSave
from .savefiles import DecryptSave, EncryptSave
from .probes import FrontierNavTool


class XCXToolsCLI(cli.Application):
    PROGNAME = "xcxtool"
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

    def main(self):
        config.load_config(self.config_path)


XCXToolsCLI.subcommand("backup", BackupSave)
XCXToolsCLI.subcommand("decrypt", DecryptSave)
XCXToolsCLI.subcommand("encrypt", EncryptSave)
XCXToolsCLI.subcommand("fnav", FrontierNavTool)
