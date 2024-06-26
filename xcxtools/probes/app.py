"""Subcommand for getting probe data from a save file"""

from collections import Counter

import plumbum
from plumbum import cli, LocalPath

from xcxtools import savefiles, config
from xcxtools.probes import data


class FrontierNavTool(cli.Application):
    """Utility to get FrontierNav probe inventory and layout

    By default, this will dump the information into a Xenoprobes inventory format,
    which can be copied or redirected to a file. Specific probe types can be excluded
    from the inventory using the -x option
    """

    inventory: Counter[data.Probe]
    sites: dict[data.ProbeSite, data.Probe]
    _exclude: set = set()

    include_sites = cli.Flag(["-s", "--include-sites"], help="Include sites in output")
    include_inventory = cli.Flag(
        ["-i", "--include-inventory"], help="Include probe inventory in output"
    )

    def main(self, target: cli.ExistingFile = None):
        if target is None:
            savedata = get_save_data_from_backup_folder()
        else:
            savedata = get_save_data_from_file(target)
        self.inventory = get_probe_inventory(savedata[data.PROBE_INVENTORY_SLICE])
        self.sites = get_installed_probes(savedata[data.FNAV_SLICE])

        if self.include_inventory:
            print(self.format_xenoprobes_inventory())
        if self.include_sites:
            print(self.format_xenoprobes_sites())

    @cli.switch(["-x", "--exclude"], str, argname="PROBES")
    def exclude(self, exclude_set: str):
        """Exclude probe types from Xenoprobes inventory, e.g. "-x M1,R1\""""
        self._exclude = split_exclude(exclude_set)

    def format_xenoprobes_inventory(self) -> str:
        """Build a xenoprobes inventory as a string"""
        line_fmt = "{enabled}{type},{quantity}\n"
        inventory = "# inventory.csv\n"

        for probe, quantity in self.inventory.items():
            if not probe.xenoprobes_name:
                continue
            enabled = self._include_in_inventory(probe)
            inventory += line_fmt.format(enabled=enabled, type=probe.xenoprobes_name, quantity=quantity)

        return inventory

    def format_xenoprobes_sites(self) -> str:
        """Build a xenoprobes sites.csv as a string"""
        sites = "# sites.csv\n"
        for site, probe in sorted(self.sites.items(), key=lambda t: t[0].xenoprobes_name):
            if site.game_name == "skip":
                continue
            sites += self._format_site_row(site, probe)

        return sites

    def _include_in_inventory(self, probe: data.Probe) -> str:
        if probe.xenoprobes_name in self._exclude:
            return "# "
        return ""

    def _format_site_row(self, site: data.ProbeSite, probe: data.Probe) -> str:
        line_fmt = "{locked}{site:xrow}\n"
        locked = "#" if probe.type_id == 255 else ""

        found_spots = int(config.get(f"sightseeing_spots.{site.xenoprobes_name}", 0))
        if found_spots < site.max_sightseeing_spots:
            site = site._replace(max_sightseeing_spots=found_spots)

        return line_fmt.format(locked=locked, site=site)


def get_save_data_from_file(file_path: LocalPath) -> bytes:
    """Helper function to get save data"""
    if file_path.stat().st_size != 359984:
        raise ValueError("Savefile should be exactly 359,984 bytes")
    # noinspection PyTypeChecker
    raw_data: bytes = file_path.read(mode="rb")
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

    sorted_inventory = Counter({k: n for k, n in sorted(probes_inventory.items())})
    return sorted_inventory


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


def split_exclude(exclude_arg: str) -> set[str]:
    return {p.strip().upper() for p in exclude_arg.split(",")}
