"""Main entry point for xcxtools"""
from configparser import ConfigParser
from typing import Mapping

from plumbum import cli
import plumbum

from . import VERSION
from . import config


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
        default="cemu.exe"
    )

    def main(self):
        print("Running XCXToolCLI.main()")
        config.load_config(self.config_path)
