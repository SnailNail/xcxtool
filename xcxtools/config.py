"""Configuration module

The app (including subcommands) is intended to be configured through a config
file named xcxtool.ini in the working directory. Settings can be overridden
on the command line. If a setting isn't in the config file or given on the
command line, default values are used.
"""

import configparser
from typing import Any

from plumbum import LocalPath

CONFIG_DEFAULTS = {
    "cemu": {
        "process_name": "cemu.exe"
    },
    "backup": {
        "save_directory": r"C:\cemu\mlc01\usr\save\00050000\101c4d00\user\80000001",
        "backup_directory": r".\saves",
        "file_name": "backup-{datetime}",
    },
    "sightseeing_spots": {
        # Primordia
        "101": 1,
        "103": 1,
        "104": 1,
        "106": 1,
        "110": 1,
        "117": 1,
        # Noctilum
        "213": 1,
        "214": 2,
        "216": 1,
        "220": 1,
        "221": 2,
        "222": 1,
        "223": 1,
        "225": 1,
        # Oblivia
        "306": 1,
        "313": 2,
        "315": 2,
        "317": 1,
        "318": 2,
        "319": 1,
        # Sylvalum
        "404": 1,
        "408": 1,
        "410": 1,
        "413": 1,
        "414": 2,
        "419": 1,
        # Cauldros
        "502": 1,
        "503": 1,
        "505": 2,
        "506": 1,
        "507": 1,
        "508": 1,
        "513": 2,
        "514": 1,
    },
}

_config = configparser.ConfigParser()
_config.read_dict(CONFIG_DEFAULTS)


def load_config(config_path: LocalPath):
    """load configuration from file"""
    if not config_path.exists():
        print("Config file not found")
        return
    print(f"Using config file: {config_path}")
    _config.read(config_path)


def get(config_path: str, default: Any = None) -> Any:
    """Get a config value

    ``config_path`` should be string of the form ``"section.key"``

    if the ``config_path`` is not found, return ``default``
    """
    section, _, key = config_path.partition(".")
    if key == "":
        raise ValueError(f"no config key specified (got {config_path})")

    try:
        return _config[section][key]
    except KeyError:
        return default


def get_preferred(preferred: Any, fallback_config_path: str, sentinel: Any = None) -> Any:
    """Return preferred value.

    If ``preferred`` is the ``sentinel`` value, return the value of
    ``fallback_config_path``.

    ``fallback_config_path`` should be a string of the form ``"section.key"``

    Note ``preferred`` is compared to ``sentinel`` by identity, i.e. :

    >>> if preferred is sentinel:
    >>>     ...

    not by value.
    """
    if preferred is sentinel:
        return get(fallback_config_path)
    return preferred
