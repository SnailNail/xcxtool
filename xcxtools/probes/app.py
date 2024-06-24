"""Subcommand for getting probe data from a save file"""

from collections import Counter

import plumbum
from plumbum import cli, LocalPath

from xcxtools import savefiles, config
from xcxtools.probes import data


class FrontierNavTool(cli.Application):

    def main(self, target: cli.ExistingFile = None):
        if target is None:
            print(f"Using config file")


def get_save_data_from_file(file_path: LocalPath) -> bytes:
    """Helper function to get save data"""
    if file_path.stat().st_size != 359984:
        raise ValueError("Savefile should be exactly 359,984 bytes")
    # noinspection PyTypeChecker
    raw_data: bytes = file_path.read(mode="b")
    key = savefiles.guess_key(raw_data)
    return savefiles.apply_key(raw_data, key)


def get_save_data_from_backup_folder() -> bytes:
    """Get save data from the backup folder config"""
    folder = plumbum.local.path(config.get("backup.save_directory"))
    save_file = folder.join("st", "game", "gamedata")
    return get_save_data_from_file(save_file)


def get_probe_inventory(probe_inventory_buffer: bytes) -> Counter[data.Probe]:
    """Returns a Counter object representing the probe inventory."""
    if len(probe_inventory_buffer) != 1200:
        raise ValueError(
            f"buffer must be exactly 1200 bytes, got {len(probe_inventory_buffer):,} bytes"
        )
    probes_inventory = Counter()
    for offset in range(0, 1200, 12):
        chunk = probe_inventory_buffer[offset : offset + 12]
        if chunk[2] != 0x80:
            continue
        probe, quantity = data.probe_and_quantity_from_bytes(chunk)
        probes_inventory[probe] += quantity

    return probes_inventory


def get_installed_probes(probe_sites_buffer: bytes) -> dict[data.ProbeSite, data.Probe]:
    """Get probes installed at all FrontierNav sites"""
    if len(probe_sites_buffer) < 330:
        raise ValueError(
            f"buffer must be at least 330 bytes, got {len(probe_sites_buffer):,} bytes"
        )
    installed = data.FNAV_STRUCT.unpack_from(probe_sites_buffer)
    sites = {}
    for index, installed_type in enumerate(installed):
        sites[data.ProbeSite.from_id(index)] = data.Probe.from_id(installed_type)
    return sites
