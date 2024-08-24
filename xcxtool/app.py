"""Main entry point for xcxtool"""

from plumbum import cli
import plumbum

from . import VERSION
from . import config
from .backup import BackupSave
from .savefiles import DecryptSave, EncryptSave
from .monitor import MonitorCemu
from .probes import FrontierNavTool


class XCXToolsCLI(cli.Application):
    PROGNAME = "xcxtool"
    DESCRIPTION = "Utilities for playing Xenoblade Chronicles X on Cemu"
    VERSION = VERSION
    _REGION_PARTS = {
        "EUR": "101c4c00",
        "USA": "101c4d00",
        "JPN": "10116100",
    }
    cemu_save_dir: plumbum.LocalPath = None

    config_path: plumbum.LocalPath = cli.SwitchAttr(
        ["--config", "-c"],
        plumbum.local.path,
        help="Use this file for config instead of the default",
    )
    cemu_process_name: str = cli.SwitchAttr(
        ["--cemu-process-name"],
        help="Name of the Cemu process to read data from; the default is cemu.exe",
    )
    cemu_nand_root: plumbum.LocalPath = cli.SwitchAttr(
        ["--cemu-nand-root"],
        cli.ExistingDirectory,
        help="Path to Cemu's emulated NAND",
    )
    cemu_account_id: str = cli.SwitchAttr(
        ["--cemu-account-id"],
        str,
        help="The PersistentID of the WiiU account in Cemu",
    )
    region: str = cli.SwitchAttr(
        ["--region"],
        cli.Set(*_REGION_PARTS),
        help="Region of the emulated game (determines save path)",
    )

    def main(self):
        config.load_config(self.config_path)
        nand_root = config.get_preferred(self.cemu_nand_root, "xcxtool.nand_root")
        if not nand_root:
            return
        region = config.get_preferred(self.region, "xcxtool.region")
        region_part = self._REGION_PARTS[region.upper()]
        persistent_id = config.get_preferred(
            self.cemu_account_id, "xcxtool.persistent_id"
        )
        cemu_save_dir = plumbum.local.path(
            nand_root,
            "usr/save/00050000",
            region_part,
            "user",
            persistent_id,
            "st/game",
        )
        if cemu_save_dir.exists():
            print(f"Saved data found at {cemu_save_dir}")
            self.cemu_save_dir = cemu_save_dir


XCXToolsCLI.subcommand("backup", BackupSave)
XCXToolsCLI.subcommand("decrypt", DecryptSave)
XCXToolsCLI.subcommand("encrypt", EncryptSave)
XCXToolsCLI.subcommand("fnav", FrontierNavTool)
XCXToolsCLI.subcommand("monitor", MonitorCemu)
