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
import os
import pathlib
import sys

import dotenv
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
    dotenv.load_dotenv()
    cemu_save_path, cemu_user_id = _check_env()

    save_path = pathlib.Path(cemu_save_path) / pathlib.Path(cemu_user_id)
    sg.popup("Saves will be copied from", f"{save_path}", f"to: {os.getcwd()}")


def _check_env() -> tuple[str, str]:
    env_hint = f"Environment variables can be configured in a .env file in {os.getcwd()}"
    save_path = os.getenv("XCX_CEMU_SAVE_PATH")
    user = os.getenv("XCX_CEMU_USER_ID")
    if save_path is None:
        sg.popup_error("The CEMU_SAVE_PATH environment variable must be set", env_hint)
        sys.exit(1)

    if user is None:
        sg.popup("The XCX_CEMU_USER_ID environment is not set, assuming '80000001'", env_hint)
        user = "80000001"
    return save_path, user


if __name__ == '__main__':
    main()
