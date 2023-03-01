"""Backup Cemu save file"""
import plumbum
from plumbum import cli

from .config import CONFIG_DEFAULTS, config


class BackupSave(cli.Application):
    backup_dir: cli.ExistingDirectory = cli.SwitchAttr(
        ["-d", "--backup-dir"],
        help=f"Backups will be saved to this directory; default is '{CONFIG_DEFAULTS['backup']['path']}'",
    )
    backup_name: str = cli.SwitchAttr(
        ["-f", "--file"],
        help=f"Name for the backup file; default is '{CONFIG_DEFAULTS['backup']['file_name']}'",
    )
    save_dir: cli.ExistingDirectory = cli.SwitchAttr(
        ["-s", "--save-dir"],
        help="XCX save directory. Can be found by selecting 'Save directory' from the "
             "game's context menu in Cemu's game list",
    )
    user_id: str = cli.SwitchAttr(
        ["-u", "--user-id"],
        help=f"Cemu/WiiU user account ID; default is '{CONFIG_DEFAULTS['cemu']['user_id']}'",
    )

    def main(self):
        save_path = config["cemu"]["save_path"]
        user_id = config["cemu"]["user_id"]

        save_path = plumbum.local.path(save_path, "user", user_id)
        if save_path.exists():
            print(f"Copying save from {save_path}")
        else:
            print(f"Save path does not exist: {save_path}")

    @cli.switch(["--help-names"])
    def help_names(self):
        """Print available replacement tokens for --backup-path and --file"""
