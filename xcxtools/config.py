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

_config = configparser.ConfigParser()
_config.read_dict(CONFIG_DEFAULTS)


def load_config(config_path: LocalPath):
    """load configuration from file"""
    print(f"Using config file: {config_path}")
    if not config_path.exists():
        print("Config file not found")
        return
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
