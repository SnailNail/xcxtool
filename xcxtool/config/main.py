"""Main config module functions"""

import sys
from collections import ChainMap
from typing import Any

if sys.version_info >= (3, 11):
    # noinspection PyUnresolvedReferences
    import tomllib
else:
    # noinspection PyPackageRequirements,SpellCheckingInspection
    import tomli as tomllib

from plumbum import LocalPath

from xcxtool.config.defaults import CONFIG_DEFAULTS


__all__ = ["load_config", "get", "get_preferred"]

_config = ChainMap(CONFIG_DEFAULTS)


def load_config(config_file_path: LocalPath):
    if not config_file_path.exists():
        print("Config file not found")
        return
    print(f"Using config file: {config_file_path}")
    with open(config_file_path, "rb") as f:
        new_config = tomllib.load(f)
        _config.maps.insert(0, new_config)


def get(config_path: str, default: Any = None) -> Any:
    """Get a config value.

    config_path should be a string of the form "table.key"

    If the config_path is not found, return default.
    """
    table, _, key = config_path.partition(".")
    if key == "":
        raise ValueError(f"no config key specified (got {config_path})")

    try:
        return _config[table][key]
    except KeyError:
        return default


def get_preferred(
    preferred: Any, fallback_config_path: str, sentinel: Any = None
) -> Any:
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
