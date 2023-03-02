"""Configuration module

The app (including subcommands) is intended to be configured through a config
file named xcxtool.ini in the working directory. Settings can be overridden
on the command line. If a setting isn't in the config file or given on the
command line, default values are used.
"""

import configparser
import os

from plumbum import LocalPath

CONFIG_DEFAULTS = {
    "cemu": {
        "save_path": r"C:\cemu\mlc01\usr\save\00050000\101c4d00\user\80000001",
        "process_name": "cemu.exe"
    },
    "backup": {
        "path": r".\saves",
        "file_name": "backup-{datetime}",
        "archive_format": "zip",
    },
    "sightseeing_spots": {
        # Primordia
        "FN101": 1,
        "FN103": 1,
        "FN104": 1,
        "FN106": 1,
        "FN110": 1,
        "FN117": 1,
        # Noctilum
        "FN213": 1,
        "FN214": 2,
        "FN216": 1,
        "FN220": 1,
        "FN221": 2,
        "FN222": 1,
        "FN223": 1,
        "FN225": 1,
        # Oblivia
        "FN306": 1,
        "FN313": 2,
        "FN315": 2,
        "FN317": 1,
        "FN318": 2,
        "FN319": 1,
        # Sylvalum
        "FN404": 1,
        "FN408": 1,
        "FN410": 1,
        "FN413": 1,
        "FN414": 2,
        "FN419": 1,
        # Cauldros
        "FN502": 1,
        "FN503": 1,
        "FN505": 2,
        "FN506": 1,
        "FN507": 1,
        "FN508": 1,
        "FN513": 2,
        "FN514": 1,
    },
}

config = configparser.ConfigParser()
config.read_dict(CONFIG_DEFAULTS)


def load_config(config_path: LocalPath):
    """load configuration from file"""
    print(f"Using config file: {config_path}")
    if not config_path.exists():
        print("Config file not found")
        return
    config.read(config_path)
