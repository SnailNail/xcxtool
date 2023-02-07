#!miscvenv
"""Script to copy and archive the current XCX save file from Cemu.

Archives are stored in the directory the script os called from.


The script uses the following environment variables to configure itself. These
can be set in the real environment, or in a .env file

  * XCX_CEMU_SAVE_PATH should be set to the path of the folder opened when
    selecting "Save directory" from the game's right-click menu in Cemu.
  * XCX_CEMU_USERID should be set to the ID of the user whose save should
    be copied. If there is only one user, this will usually be "80000001"
"""
import configparser
import os
import pathlib

import PySimpleGUI as sg


CONFIG_DEFAULTS = {
    "cemu": {
        "save_path": r"c:\cemu\mlc01\usr\save\00050000\101c4c00",
        "user_id": "80000001",
    },
    "backups": {
        "path": r".\saves",
        "file_name": ""
    }
}


def main():
    config = _load_config()

    save_path = pathlib.Path(config["cemu"]["save_path"]) / pathlib.Path(config["cemu"]["user_id"])
    backup_path = pathlib.Path(config["backups"]["path"])
    sg.popup("Saves will be copied from", f"{save_path}", f"to: {backup_path.resolve()}")


def _load_config(config_file: str = "saves.ini", config_path: str = None) -> configparser.ConfigParser:
    """Load config from the current working directory, or config_path if provided"""
    if config_path is None:
        config_path = os.getcwd()
    config_path = os.path.join(config_path, config_file)

    parser = configparser.ConfigParser()
    parser.read_dict(CONFIG_DEFAULTS, "<defaults>")
    if os.path.exists(config_path):
        with open(config_path) as f:
            parser.read_file(f)
    return parser


if __name__ == '__main__':
    main()
