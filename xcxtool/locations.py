"""Utility for viewing found (or not) locations.

Note that not all locations are catalogued!
"""

from plumbum import cli, LocalPath

from xcxtool.data import locations
from xcxtool.memory_reader import SaveFileReader

FOUND_LOCATIONS_START = 0x032658
FOUND_LOCATIONS_END = 0x03269D


class LocationTool(cli.Application):
    """Utility for viewing found (or not) locations."""
    data: bytes
    found_locations: dict[tuple[int, int], bool]
    locations_by_bit = {(l.offset, l.bit): l for l in locations.locations}

    found = cli.Flag(["-f", "--found"], help="Show found locations", excludes=["not-found"])
    not_found = cli.Flag(["-n", "--not-found"], help="show locations yet to be found", excludes="found")

    @cli.positional(cli.ExistingFile)
    def main(self, file: LocalPath = None):
        self.data = self.load_data(file)
        self.found_locations = get_locations_from_save_data(self.data)

    def load_data(self, from_data: LocalPath = None) -> bytes:
        if not from_data:
            from_data = self.parent.cemu_save_dir.join("gamedata")
        reader = SaveFileReader(from_data)
        return reader.data


def get_locations_from_save_data(save_data: bytes) -> dict[tuple[int, int], bool]:
    found = {}
    for offset in range(FOUND_LOCATIONS_START, FOUND_LOCATIONS_END):
        for power in range(8):
            bit = 2 ** power
            found[(offset, bit)] = bool(save_data[offset] & bit)
    return found
