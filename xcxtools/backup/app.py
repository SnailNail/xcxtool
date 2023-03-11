"""Backup Cemu save file"""
import shutil

import plumbum
from plumbum import local, cli

from .. import config


_archive_formats = (f[0] for f in shutil.get_archive_formats())


class BackupSave(cli.Application):
    """Copy/backups Cemu save files.

    See xcxtool --help for global options
    """

    backup_dir: plumbum.LocalPath = cli.SwitchAttr(
        ["-d", "--backup-dir"],
        argtype=cli.ExistingDirectory,
        help=f"Backups will be saved to this directory; default is '{config.get('backup.path')}'",
    )
    backup_name: str = cli.SwitchAttr(
        ["-f", "--file"],
        help=f"Name for the backup file (without extension); default is '{config.get('backup.file_name')}'",
    )
    save_dir: plumbum.LocalPath = cli.SwitchAttr(
        ["-s", "--save-dir"],
        argtype=cli.ExistingDirectory,
        help="Directory containing XCX save files in the st/game subdirectory",
    )
    archive_format: str = cli.SwitchAttr(
        ["-a", "--archive-format"],
        argtype=cli.Set(*_archive_formats),
        help=f"Archive format for the backup; default is '{config.get('backup.archive_format')}'",
    )

    def __init__(self, executable):
        super().__init__(executable)
        self._help_names_run = False

    def main(self):
        if result := self.pre_flight_checks() is not None:
            return result
        print("running BackupSave.main()")

    def pre_flight_checks(self) -> int | None:
        """Various checks before running main() proper"""
        if self._help_names_run:
            return 0
        if not any((self._check_parent(), self._check_paths())):
            return 2
        return

    def _check_paths(self) -> bool:
        self.save_dir = local.path(config.get_preferred(self.save_dir, "cemu.save_path"))
        self.backup_dir = local.path(config.get_preferred(self.backup_dir, "backup.path"))
        if not (self.save_dir / "st").exists():
            print(f"Cemu save directory not found: {self.save_dir / 'st'}")
            return False
        if not self.backup_dir.exists():
            print(f"Backup directory not found: {self.backup_dir}")
            return False
        print(f"Copying save files from {self.save_dir}\nto {self.backup_dir}")
        return True

    def _check_parent(self) -> bool:
        if self.parent:
            return True
        print("This utility must be run via the main xcxtools application")
        return False

    @cli.switch(["--help-names"])
    def help_names(self):
        """Print available replacement tokens for --backup-path and --file"""
        preamble = ("The --backup-dir and --file arguments can contain replacement fields "
                    "e.g, 'fixed_{player_name}_also_fixed'. The available fields are "
                    "listed below. Note that for most of these fields to work, the game "
                    "must be emulated and running in Cemu.\n"
                    "\n"
                    "If a field cannot be replaced, the program will exit with an error\n"
                    "\n"
                    "Python's formatting mini-language can be used to customise the appearance "
                    "of replacement fields. The type of each replacement field is indicated "
                    "below, and the appropriate formatting codes can be used.")
        token_descriptions = {
            "{player_name}": "Name of the player character (str)",
            "{level}": "Inner level of the player character (int)",
            "{exp}": "Total inner experience points for player character (int)",
            "{class}": "Player's combat class (str)",
            "{class_level}": "Player's class level (int)",
            "{class_rank}": "Player's class rank (int)",
            "{class_exp}": "Total class exp of the player (int)",
            "{play_time}": "Total playtime as seen on the main menu. "
                           "The main menu must be open for this to be accurate; "
                           "if the menu is not open the last displayed values will be used "
                           "(pendulum.duration)",
            "{save_date}": "Last modified date/time of the gamedata save file (pendulum.datetime)",
            "{date}": "Current (calendar) date/time (pendulum.datetime)",
        }
        print(preamble)
        for token, description in token_descriptions.items():
            print(f"  {token:14} {description}")
        self._help_names_run = True
