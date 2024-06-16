"""Backup Cemu save file"""
import shutil

import plumbum
from plumbum import local, cli

from .. import config, memory_reader
from . import tokens, formatter


_archive_formats = (f[0] for f in shutil.get_archive_formats())


class BackupSave(cli.Application):
    """Copy/backups Cemu save files.

    See xcxtool --help for global options
    """

    backup_dir: plumbum.LocalPath = cli.SwitchAttr(
        ["-b", "--backup-dir"],
        argtype=plumbum.LocalPath,
        help=f"Backups will be saved to this directory",
    )
    create_backup_dir: bool = cli.Flag(
        ["-c", "--create"],
        help="Try to create backup-dir if it doesn't exist",
    )
    backup_name: str = cli.SwitchAttr(
        ["-f", "--file"],
        help=f"Name for the backup file (without extension)",
    )
    help_tokens: bool = cli.Flag("--help-tokens", help="Show available replacement tokens")
    save_dir: plumbum.LocalPath = cli.SwitchAttr(
        ["-s", "--save-dir"],
        argtype=cli.ExistingDirectory,
        help="Directory containing XCX save files in the st/game subdirectory",
    )
    dry_run: bool = cli.Flag(["--dry-run"], help="Do not create the archive, just print its name")
    gamedata: plumbum.LocalPath = None

    def main(self):
        if self._help_names():
            return
        if result := self.pre_flight_checks() is not None:
            return result
        if self.backup_name is None:
            self.backup_name = config.get("backup.file_name")

        field_values = {}
        field_values.update(tokens.get_datetime())

        field_values.update(tokens.get_mtime(self.gamedata))

        gamedata_reader = memory_reader.SaveFileReader(self.gamedata)
        print("*** gamedata: ", self.gamedata)
        field_values.update(tokens.get_character_data(gamedata_reader))
        field_values.update(tokens.get_playtime(gamedata_reader))

        archive_name = formatter.ForgivingFormatter().vformat(self.backup_name, (), field_values)
        print(f"Backing up from: {self.save_dir}")
        print(f"to: {self.backup_dir}")
        print(f"With filename {archive_name}.zip")
        base_name = self.backup_dir / archive_name
        if not self.dry_run:
            shutil.make_archive(
                base_name, "zip", self.save_dir, "st/game", dry_run=self.dry_run
            )

    def pre_flight_checks(self) -> int | None:
        """Various checks before running main() proper"""
        if not any((self._check_parent(), self._check_save_path(), self._check_backup_path())):
            return 2
        return

    def _check_save_path(self) -> bool:
        if self.save_dir is None:
            self.save_dir = local.path(config.get("cemu.save_path"))
        gamedata = self.save_dir.join("st", "game", "gamedata")
        if not gamedata.exists():
            print(f"Could not find gamedata in {self.save_dir}")
            return False
        self.gamedata = gamedata
        return True

    def _check_backup_path(self) -> bool:
        if self.backup_dir is None:
            self.backup_dir = local.path(config.get("backup.path"))
        if self.backup_dir.exists():
            return True
        if self.create_backup_dir:
            return self.backup_dir.mkdir()
        return False

    def _check_parent(self) -> bool:
        if self.parent:
            return True
        print("This utility must be run via the main xcxtools application")
        return False

    def _help_names(self):
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
                           "(str)",
            "{save_date}": "Last modified date/time of the gamedata save file (pendulum.datetime)",
            "{date}": "Current (calendar) date/time (pendulum.datetime)",
        }
        if self.help_tokens:
            print(preamble)
            for token, description in token_descriptions.items():
                print(f"  {token:14} {description}")
            return True
        return False
