"""Backup Cemu save file"""
import shutil
import sys

from plumbum import cli, local, LocalPath

from .. import config, memory_reader
from . import tokens, formatter
from ..app import XCXToolApplication


_archive_formats = (f[0] for f in shutil.get_archive_formats())


class BackupSave(XCXToolApplication):
    """Copy/backups Cemu save files.

    See xcxtool --help for global options
    """

    backup_dir: LocalPath = cli.SwitchAttr(
        ["-b", "--backup-dir"],
        argtype=LocalPath,
        help="Backups will be saved to this directory",
    )
    backup_name: str = cli.SwitchAttr(
        ["-f", "--file"],
        help="Name for the backup file (without extension)",
    )
    save_dir: LocalPath = cli.SwitchAttr(
        ["-s", "--save-dir"],
        argtype=cli.ExistingDirectory,
        help="Custom save data path. Must contain save files in the st/game subdirectory",
    )
    dry_run: bool = cli.Flag(["--dry-run"], help="Do not create the archive, just print its name")
    gamedata: LocalPath = None

    def main(self):
        if self.parent is None:
            self.error("This utility must be run via the main xcxtool application")
            return 2

        if self.backup_name is None:
            self.backup_name = config.get("backup.file_name")

        backup_path = self.get_backup_path()
        if backup_path is None:
            return 2

        save_path = self.get_save_path()
        if save_path is None:
            self.error("[red]No save data path specified[/red]")
            return 2

        self.gamedata = save_path.join("st", "game", "gamedata")
        if not self.gamedata.exists():
            self.error(f"[red]No save data found in {save_path}")
            return 2

        reader = memory_reader.SaveFileReader(self.gamedata)
        field_values = self.get_tokens(reader)
        archive_name = formatter.ForgivingFormatter().format(self.backup_name, **field_values)

        self.do_backup(archive_name, backup_path, save_path)

    def get_backup_path(self) -> LocalPath | None:
        if self.backup_dir is not None:
            return self.backup_dir

        backup_dir = local.path(config.get("backup.backup_directory"))
        if not backup_dir.exists():
            self.error(f"[red]Backup directory not found (got '{self.backup_dir}')")
            return
        if not backup_dir.is_dir():
            self.error(f"[red]Backup path is not a directory (got '{self.backup_dir}')")
            return
        return backup_dir

    def get_save_path(self) -> LocalPath | None:
        if self.save_dir is not None:
            return self.save_dir

        if configured := config.get("backup.save_directory"):
            return local.path(configured)

        if self.parent.cemu_save_dir is not None:
            return self.parent.cemu_save_dir.parents[1]

    def get_tokens(self, gamedata_reader: memory_reader.SaveDataReader) -> dict:
        field_values = {}
        field_values.update(tokens.get_datetime())
        field_values.update(tokens.get_mtime(self.gamedata))

        field_values.update(tokens.get_character_data(gamedata_reader))
        field_values.update(tokens.get_playtime(gamedata_reader))
        return field_values

    def do_backup(self, backup_name: str, backup_dir: LocalPath, save_dir: LocalPath):
        self.success(f"Backing up from: [green]{save_dir}[/green]\n"
               f"to: [green]{backup_dir}[/green]\n"
               f"With filename [green]{backup_name}.zip[/green]")
        base_name = backup_dir / backup_name
        if not self.dry_run:
            shutil.make_archive(
                base_name, "zip", save_dir, "st/game", dry_run=self.dry_run
            )

    @cli.switch("--help-tokens", help="Show available replacement tokens")
    def help_names(self):
        """Print available replacement tokens for --backup-path and --file"""
        preamble = ("The --backup-dir and --file arguments can contain replacement fields "
                    "e.g, 'fixed_{player_name}_also_fixed'. The available fields are "
                    "listed below.\n"
                    "\n"
                    "If a field cannot be replaced, it will be left in the name as-is.\n"
                    "\n"
                    "Python's formatting mini-language can be used to customise the appearance "
                    "of replacement fields. The type of each replacement field is indicated "
                    "below, and the appropriate formatting codes can be used. If a field name"
                    "is not recognized, any formatting codes will be removed from the output.")
        token_descriptions = {
            "{name}": "Name of the player character (str)",
            "{level}": "Inner level of the player character (int)",
            "{exp}": "Total inner experience points for player character (int)",
            "{class}": "Player's combat class (str)",
            "{class_rank}": "Player's class rank (int)",
            "{class_exp}": "Total class exp of the player (int)",
            "{division}": "Player character's Division (str)",
            "{blade_level}": "Player's BLADE level (int)",
            "{play_time}": "Total playtime (as seen on the main menu) (str)",
            "{save_date}": "In-game save date of the gamedata save file as YYYYMMDD (str)",
            "{save_time": "In-game save time as hh-mm-ss (str)",
            "{date}": "Current (calendar) date as YYYYMMDD (str)",
            "{time": "Current time as hh-mm-ss (str)",
            "{save_datetime}": "In-game save date and time (datetime.datetime)",
            "{datetime}": "Current date and time (datetime.datetime)",
            "{mtime}": "Last modified date and time of the save data file (datetime.datetime)",
        }
        self.out(preamble)
        for token, description in token_descriptions.items():
            self.out(f"  [bold]{token:16}[/bold] {description}")
        sys.exit()
