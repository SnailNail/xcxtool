"""Backup Cemu save file"""
from typing import Mapping

import plumbum
from plumbum import cli

from . import config


class BackupSave(cli.Application):

    def main(self):
        save_path = config.config["cemu"]["save_path"]
        user_id = config.config["cemu"]["user_id"]

        save_path = plumbum.local.path(save_path, "user", user_id)
        if save_path.exists():
            print(f"Copying save from {save_path}")
        else:
            print(f"Save path does not exist: {save_path}")

