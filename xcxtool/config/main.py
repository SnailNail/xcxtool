"""Main config module functions"""

import sys
from typing import Any

if sys.version_info >= (3, 11):
    # noinspection PyUnresolvedReferences
    import tomllib
else:
    # noinspection PyPackageRequirements,SpellCheckingInspection
    import tomli as tomllib

from plumbum import local, LocalPath

from xcxtool.config.defaults import CONFIG_DEFAULTS


__all__ = ["load_config", "get", "get_preferred", "get_section"]

_config = {}


def load_config(config_file: LocalPath = None):
    if config_file is None:
        config_file = find_config()
    if config_file is None or not config_file.exists():
        print("Config file not found", file=sys.stderr)
        return
    print(f"Using config file: {config_file}", file=sys.stderr)
    with open(config_file, "rb") as f:
        new_config = tomllib.load(f)
        _config.update(new_config)


def find_config(config_file_name: str = "xcxtool.toml") -> LocalPath | None:
    """Search for the default config file name in the current directory and
    any parent directory.

    Returns the first config file found as a LocalPath, or None
    """
    cwd = local.path(config_file_name)

    for candidate in (p / config_file_name for p in cwd.parents):
        if candidate.exists():
            return candidate

    return None


def get(config_path: str, default: Any = None) -> Any:
    """Get a config value.

    config_path should be a string of the form "table.key"

    If the config_path is not found, return default.
    """
    table, _, key = config_path.partition(".")
    if key == "":
        raise ValueError(f"no config key specified (got {config_path})")
    try:
        result = _config[table][key]
    except KeyError:
        result = CONFIG_DEFAULTS.get(table).get(key)
    if result is None:
        return default
    return result


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


def get_section(section: str) -> dict[str, Any] | None:
    """Get a whole config section"""
    try:
        return _config[section]
    except KeyError:
        return CONFIG_DEFAULTS.get(section)
