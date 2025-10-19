"""Main entry point for xcxtool"""

import logging

from platformdirs import user_config_path
from plumbum import cli, local, LocalPath

from . import __version__, __doc__ as description
from . import config
from .app import XCXToolApplication, INFO, WARNING


class XCXToolsCLI(XCXToolApplication):
    PROGNAME = "xcxtool"
    DESCRIPTION = description
    VERSION = __version__
    _REGION_PARTS = {
        "EUR": "101c4c00",
        "USA": "101c4d00",
        "JPN": "10116100",
    }
    cemu_save_dir: LocalPath = None

    config_path: LocalPath = cli.SwitchAttr(
        ["--config", "-c"],
        local.path,
        help="Use this file for config instead of the default",
    )
    cemu_process_name: str = cli.SwitchAttr(
        ["--cemu-process-name"],
        help="Name of the Cemu process to read data from; the default is cemu.exe",
    )
    cemu_nand_root: LocalPath = cli.SwitchAttr(
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

    @cli.switch(["v", "verbose"], excludes=["quiet", "debug"])
    def verbose(self):
        """Display more informational output"""
        self.message_level = INFO

    @cli.switch(["q", "quiet"], excludes=["verbose", "debug"])
    def quiet(self):
        """Supress informational output (warnings and errors will still be shown)"""
        self.message_level = WARNING

    @cli.switch(["debug"], excludes=["verbose", "quiet"])
    def _debug(self):
        """Show debug output"""
        self.message_level = logging.DEBUG

    def main(self):
        config.load_config(self.config_path)
        nand_root = config.get_preferred(self.cemu_nand_root, "xcxtool.nand_root")
        if not nand_root:
            nand_root = user_config_path("Cemu", False, roaming=True) / "mlc01"
        region = config.get_preferred(self.region, "xcxtool.region")
        region_part = self._REGION_PARTS[region.upper()]
        persistent_id = config.get_preferred(
            self.cemu_account_id, "xcxtool.persistent_id"
        )
        cemu_save_dir = local.path(
            nand_root,
            "usr/save/00050000",
            region_part,
            "user",
            persistent_id,
            "st/game",
        )
        if cemu_save_dir.exists():
            self.info(f"Saved data found at {cemu_save_dir}")
            self.cemu_save_dir = cemu_save_dir
        else:
            self.warning("Could not find saved data (Cemu NAND not found)")


XCXToolsCLI.subcommand("backup", "xcxtool.backup.BackupSave")
XCXToolsCLI.subcommand("decrypt", "xcxtool.savefiles.main.DecryptSave")
XCXToolsCLI.subcommand("encrypt", "xcxtool.savefiles.main.EncryptSave")
XCXToolsCLI.subcommand("fnav", "xcxtool.probes.FrontierNavTool")
XCXToolsCLI.subcommand("compare", "xcxtool.monitor.CompareSavedata")
XCXToolsCLI.subcommand("monitor", "xcxtool.monitor.MonitorEmu")
XCXToolsCLI.subcommand("locations", "xcxtool.locations.LocationTool")
