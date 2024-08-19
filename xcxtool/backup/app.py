"""Backup Cemu save file"""
import shutil
import sys

import plumbum
from plumbum import local, cli
from rich import print as rprint

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
    backup_name: str = cli.SwitchAttr(
        ["-f", "--file"],
        help=f"Name for the backup file (without extension)",
    )
    save_dir: plumbum.LocalPath = cli.SwitchAttr(
        ["-s", "--save-dir"],
        argtype=cli.ExistingDirectory,
        help="Custom save data path. Must contain save files in the st/game subdirectory",
    )
    dry_run: bool = cli.Flag(["--dry-run"], help="Do not create the archive, just print its name")
    gamedata: plumbum.LocalPath = None

    def main(self):
        if self.parent is None:
            print("This utility must be run via the main xcxtool application", file=sys.stderr)
            return 2

        backup_path = self.get_backup_path()
        if backup_path is None:
            return 2

        save_path = self.get_save_path()
        if save_path is None:
            rprint("[red]No save data path specified[/red]", file=sys.stderr)
            return 2

        save_data_path = save_path.join("st", "game", "gamedata")
        if not save_data_path.exists():
            rprint(f"[red]No save data found in {save_path}", file=sys.stderr)
            return 2

        reader = memory_reader.SaveFileReader(save_data_path)
        field_values = self.get_tokens(reader)
        archive_name = formatter.ForgivingFormatter().format(self.backup_name, **field_values)

        self.do_backup(archive_name, backup_path, save_path)

    def get_backup_path(self) -> plumbum.LocalPath | None:
        if self.backup_dir is None:
            return self.backup_dir

        backup_dir = plumbum.local.path(config.get("backup.backup_directory"))
        if not self.backup_dir.exists():
            rprint(f"[red]Backup directory not found (got '{self.backup_dir}')")
            return
        if not self.backup_dir.is_dir():
            rprint(f"[red]Backup path is not a directory (got '{self.backup_dir}')")
            return
        return backup_dir

    def get_save_path(self) -> plumbum.LocalPath | None:
        if self.save_dir is not None:
            return self.save_dir

        if configured := config.get("backup.save_directory") is not None:
            return plumbum.local.path(configured)

        if self.parent.cemu_save_dir is not None:
            return self.parent.cemu_save_dir.parents[-1]

    def get_tokens(self, gamedata_reader: memory_reader.MemoryReader) -> dict:
        field_values = {}
        field_values.update(tokens.get_datetime())
        field_values.update(tokens.get_mtime(self.gamedata))

        field_values.update(tokens.get_character_data(gamedata_reader))
        field_values.update(tokens.get_playtime(gamedata_reader))
        return field_values

    def do_backup(self, backup_name: str, backup_dir: plumbum.LocalPath, save_dir: plumbum.LocalPath):
        rprint(f"Backing up from: [green]{self.save_dir}[/green]\n"
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
            "{class_rank}": "Player's class rank (int)",
            "{class_exp}": "Total class exp of the player (int)",
            "{play_time}": "Total playtime as seen on the main menu. "
                           "The main menu must be open for this to be accurate; "
                           "if the menu is not open the last displayed values will be used "
                           "(str)",
            "{save_date}": "Last modified date/time of the gamedata save file (pendulum.datetime)",
            "{date}": "Current (calendar) date/time (pendulum.datetime)",
        }
        print(preamble)
        for token, description in token_descriptions.items():
            rprint(f"  {token:14} {description}")
        sys.exit()

