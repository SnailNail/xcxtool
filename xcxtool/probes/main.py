"""Subcommand for getting probe data from a save file"""

import webbrowser
from collections import Counter

from plumbum import cli, local, LocalPath

from xcxtool import config
from xcxtool.app import XCXToolApplication
from xcxtool.probes import data
from xcxtool.savefiles.encryption import decrypt_save_data


class FrontierNavTool(XCXToolApplication):
    """Utility to get FrontierNav probe inventory and layout

    By default, this will write a sites.csv and inventory.csv to the current working
    directory using the layout in the configures save data. A custom save file can be
    passed as an argument.
    """

    inventory: Counter[data.Probe]
    sites: dict[data.ProbeSite, data.Probe]
    spots: set[int]
    _exclude: set[str] = set()

    include_sites = cli.Flag(
        ["-s", "--sites"], help="Include sites in output", group="Output data"
    )
    include_inventory = cli.Flag(
        ["-i", "--inventory"],
        help="Include probe inventory in output",
        group="Output data",
    )
    include_layout = cli.Flag(
        ["-l", "--layout"], help="Include probe layout in output", group="Output data"
    )
    output_dir = cli.SwitchAttr(
        ["-o", "--output-dir"],
        argtype=cli.ExistingDirectory,
        help="Write files to this directory",
        group="Output control",
    )
    print = cli.Flag(
        ["-p", "--print"],
        help="Print output to console instead of writing to files",
        group="Output control",
    )
    tee = cli.Flag(
        ["-t", "--tee"],
        help="Print the command output to the console and write to files.",
        group="Output control",
    )
    frontiernav = cli.Flag(
        ["-j", "--frontiernav"],
        help="Attempt to open the current probe layout in the FrontierNav.net probe simulation",
        group="Output data",
    )

    @cli.positional(cli.ExistingFile)
    def main(self, target: LocalPath = None):
        if self.parent is None:
            self.error("This application must be run as a subcommand of xcxtool")
            return 2

        savedata = self.get_save_data(target)
        if savedata is None:
            return 2
        self.inventory = get_probe_inventory(savedata[data.PROBE_INVENTORY_SLICE])
        self.sites = get_installed_probes(savedata[data.FNAV_SLICE])
        self.spots = get_sightseeing_spots(savedata[data.LOCATIONS_SLICE])

        if not any((self.include_inventory, self.include_sites, self.include_layout, self.frontiernav)):
            self.include_inventory = True
            self.include_sites = True

        if self.include_inventory:
            self.do_output(self.format_xenoprobes_inventory(), "inventory.csv")
        if self.include_sites:
            self.do_output(self.format_xenoprobes_sites(), "sites.csv")
        if self.include_layout:
            self.do_output(self.format_xenoprobes_setup(), "layout.csv")
        if self.frontiernav:
            self.do_frontiernav()

    @cli.switch(["-x", "--exclude"], str, argname="PROBES", group="Input")
    def exclude(self, exclude_set: str):
        """Exclude probe types from Xenoprobes inventory, e.g. "-x M1,R1\" """
        self._exclude = split_exclude(exclude_set)

    def get_save_data(self, target: LocalPath | None) -> bytes | None:
        """Get save data.

        If a save file is specified on the command line, get that. Otherwise,
        look for a save file in the configured MLC path.
        """
        if target is not None:
            return get_save_data_from_file(target)
        if self.parent.cemu_save_dir is not None:
            return get_save_data_from_file(self.parent.cemu_save_dir.join("gamedata"))
        self.error(
            "No save data found, please specify a gamedata file, or configure Cemu"
            "settings.",
        )

    def format_xenoprobes_inventory(self) -> str:
        """Build a xenoprobes inventory as a string"""
        line_fmt = "{enabled}{type},{quantity}\n"
        inventory = "# inventory.csv\n"

        for probe, quantity in self.inventory.items():
            if not probe.xenoprobes_name:
                continue
            enabled = self._include_in_inventory(probe)
            inventory += line_fmt.format(
                enabled=enabled, type=probe.xenoprobes_name, quantity=quantity
            )

        return inventory

    def format_xenoprobes_sites(self) -> str:
        """Build a xenoprobes sites.csv as a string"""
        sites = "# sites.csv\n"
        for site, probe in sorted(
            self.sites.items(), key=lambda t: t[0].xenoprobes_name
        ):
            if site.game_name == "skip":
                continue
            sites += self._format_site_row(site, probe)

        return sites

    def format_xenoprobes_setup(self) -> str:
        """Build a xenoprobes-1.x layout.csv as a string.

        This can be used with the --setup argument to show the output of a given
        probe layout
        """
        layout = "# layout.csv\n"
        for site, probe in self.sites.items():
            if site.game_name == "skip":
                continue
            layout += f"{site.xenoprobes_name},{probe.xenoprobes_name}\n"

        return layout

    def do_output(self, file_data: str, file_name: str):
        if self.print or self.tee:
            self.out(file_data)
        if not self.print or self.tee:
            out_dir = self.get_output_dir()
            out_file = out_dir / file_name
            out_file.write(file_data, "utf8")

    def get_output_dir(self) -> LocalPath:
        if self.output_dir:
            return self.output_dir
        config_setting = config.get("fnav.output_dir")
        try:
            return cli.ExistingDirectory(config_setting)
        except ValueError:
            self.warning("Configured output_dir does not exist, writing to current directory")
            return local.path(".")

    def format_frontiernav_url(self) -> str:
        base_url = "https://frontiernav.net/wiki/xenoblade-chronicles-x/visualisations/maps/probe-guides/My%20Current%20Layout?map="
        probe_layout = [f"{site.xenoprobes_name}-{probe.frontiernav_type}" for site, probe in self.sites.items()]
        return base_url + "~".join(probe_layout)

    def do_frontiernav(self) -> None:
        url = self.format_frontiernav_url()
        if self.print or self.tee:
            self.out("# Frontiernav URL")
            self.out(url)
        if not self.print or self.tee:
            webbrowser.open_new_tab(url)

    def _include_in_inventory(self, probe: data.Probe) -> str:
        if probe.xenoprobes_name in self._exclude:
            return "# "
        return ""

    def _format_site_row(self, site: data.ProbeSite, probe: data.Probe) -> str:
        line_fmt = "{locked}{site:xrow}\n"
        locked = "#" if probe.type_id == 254 else ""

        found_spots = tuple(self._get_spots_for_site(site))
        if found_spots != site.sightseeing_spots:
            site = site._replace(sightseeing_spots=found_spots)

        return line_fmt.format(locked=locked, site=site)

    def _get_spots_for_site(self, site: data.ProbeSite) -> list[int]:
        found_spots = [s for s in site.sightseeing_spots if s in self.spots]
        configured_spots: int = config.get("fnav.sightseeing_spots").get(
            site.xenoprobes_name, -1
        )
        if configured_spots > len(site.sightseeing_spots):
            configured_spots = len(site.sightseeing_spots)

        if configured_spots > -1:
            return list(range(configured_spots))
        return found_spots


def get_save_data_from_file(file_path: LocalPath) -> bytes:
    """Helper function to get save data"""
    if file_path.stat().st_size != 359984:
        raise ValueError("Savefile should be exactly 359,984 bytes")
    # noinspection PyTypeChecker
    raw_data: bytes = file_path.read(mode="rb")
    return decrypt_save_data(raw_data)


def get_save_data_from_backup_folder() -> bytes:
    """Get save data from the backup folder config"""
    folder = local.path(config.get("backup.save_directory"))
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


def get_sightseeing_spots(locations_buffer: bytes) -> set[int]:
    """Get a set of location IDs for found sightseeing spots."""
    spots = set()
    for location_id, offset, bit in data.sightseeing_spots:
        if locations_buffer[offset] & bit:
            spots.add(location_id)

    return spots


def split_exclude(exclude_arg: str) -> set[str]:
    return {p.strip().upper() for p in exclude_arg.split(",")}
