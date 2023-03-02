"""Backup Cemu save file"""
import shutil

import plumbum
from plumbum import cli

from .config import config


_archive_formats = (f[0] for f in shutil.get_archive_formats())


class BackupSave(cli.Application):
    """Copy/backups Cemu save files.

    See xcxtool --help for global options
    """

    backup_dir: plumbum.LocalPath = cli.SwitchAttr(
        ["-d", "--backup-dir"],
        argtype=cli.ExistingDirectory,
        help=f"Backups will be saved to this directory; default is '{config['backup']['path']}'",
    )
    backup_name: str = cli.SwitchAttr(
        ["-f", "--file"],
        help=f"Name for the backup file (without extension); default is '{config['backup']['file_name']}'",
    )
    save_dir: plumbum.LocalPath = cli.SwitchAttr(
        ["-s", "--save-dir"],
        argtype=cli.ExistingDirectory,
        help="Directory containing XCX save files in the st/game subdirectory",
    )
    archive_format: str = cli.SwitchAttr(
        ["-a", "--archive-format"],
        argtype=cli.Set(*_archive_formats),
        help=f"Archive format for the backup; default is '{config['backup']['archive_format']}'",
    )

    def main(self):
        save_dir = self.save_dir if self.save_dir else config["cemu"]["save_path"]
        backup_dir = self.backup_dir if self.backup_dir else config["backup"]["path"]

        save_dir = plumbum.local.path(save_dir)
        backup_dir = plumbum.local.path(backup_dir)
        if save_dir.exists():
            print(f"Copying save from {save_dir}")
        else:
            print(f"Save path does not exist: {save_dir}")
        print(f"to: {backup_dir}")

    @cli.switch(["--help-names"])
    def help_names(self):
        """Print available replacement tokens for --backup-path and --file"""
