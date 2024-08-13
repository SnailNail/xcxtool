import functools
import json
from os.path import dirname, abspath, join

try:
    _this_dir = dirname(abspath(__file__))
except NameError:
    print("This module should not be run as a script")
    raise


_jjoin = functools.partial(join, _this_dir, "json")


def load_fld_location(get_names: bool = True) -> list[dict]:
    with open(_jjoin("FLD_Location.json")) as f:
        data = json.load(f)
    if get_names:
        names = _load_textlist("fieldnamelist_ms")
        for location in data:
            name_id = location["Loc_name"]
            location["Loc_name"] = names[name_id]
    return data


def load_fnetveinlist(get_names: bool = True) -> list[dict]:
    with open(_jjoin("FnetVeinList.json")) as f:
        data = json.load(f)
    if get_names:
        locations = {loc["id"]: loc["Loc_name"] for loc in load_fld_location()}
        for site in data:
            name_id = site["name"]
            location = locations.get(name_id)
            if location is None:
                site["name"] = "0"
            site["name"] = location
    return data


def load_itm_beaconlist(get_names: bool = True):
    with open(_jjoin("ITM_BeaconList.json")) as f:
        data = json.load(f)
    if get_names:
        names = _load_textlist("ITM_BeaconList_ms")
        for probe in data:
            probe["Name"] = names[probe["Name"]]
            probe["Caption"] = names[probe["Caption"]]
    return data


def _load_textlist(textlist_file) -> dict[int, str]:
    """Load textlist_file.json

    Returns a dictionary mapping ids to strings
    """
    with open(_jjoin(f"{textlist_file}.json")) as f:
        data = json.load(f)
    return {d["id"]: d["name"] for d in data}
