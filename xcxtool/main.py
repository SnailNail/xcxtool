"""Main entry point for xcxtool"""

from plumbum import cli, local, LocalPath

from . import __version__, __doc__ as description
from . import config
from .app import XCXToolApplication, DEBUG, INFO, WARNING


class XCXToolsCLI(XCXToolApplication):
    PROGNAME = "xcxtool"
    DESCRIPTION = description
    VERSION = __version__

    save_location: LocalPath = None

    config_path: LocalPath = cli.SwitchAttr(
        ["--config", "-c"],
        local.path,
        help="Use this file for config instead of the default",
    )
    save_dir: LocalPath = cli.SwitchAttr(
        ["s", "save-dir"],
        argtype=local.path,
        help="Location of save data. Should be a path to a folder containing the gamedata files",
    )

    edition: str = cli.SwitchAttr(
        ["e", "edition"],
        argtype=cli.Set("wiiu", "switch"),
        default="wiiu",
        help="Specify save data is original (WiiU) or Definitive Edition (Switch)",
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
        self.message_level = DEBUG

    def main(self):
        config.load_config(self.config_path)
        if self.save_dir is None:
            save_location = local.path(config.get("xcxtool.save_location"))
            self.debug("Save location from config: %s", save_location)
        else:
            save_location = self.save_dir
            self.debug("Save location from command line: %s", save_location)

        if "st" in save_location.parts:
            self.info("WiiU version detected")
        elif "sts" in save_location.parts:
            self.info("Switch version detected")
            self.edition = "switch"

        if save_location.join("systemdata").exists():
            self.success(f"Saved data found at {save_location}")
            self.save_location= save_location
        else:
            self.warning("Could not find saved data (systemdata not found)")


XCXToolsCLI.subcommand("backup", "xcxtool.backup.BackupSave")
XCXToolsCLI.subcommand("decrypt", "xcxtool.savefiles.main.DecryptSave")
XCXToolsCLI.subcommand("encrypt", "xcxtool.savefiles.main.EncryptSave")
XCXToolsCLI.subcommand("fnav", "xcxtool.probes.FrontierNavTool")
XCXToolsCLI.subcommand("compare", "xcxtool.monitor.CompareSavedata")
XCXToolsCLI.subcommand("monitor", "xcxtool.monitor.MonitorEmu")
# XCXToolsCLI.subcommand("locations", "xcxtool.locations.LocationTool")
