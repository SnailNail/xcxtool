import functools
import json
from os.path import dirname, exists, abspath, join

try:
    _this_dir = dirname(abspath(__file__))
except NameError:
    print("This module should not be run as a script")
    raise


_data_dir_join = functools.partial(join, _this_dir, "json")
_text_dir_join = _data_dir_join


def load_fld_location(get_names: bool = True) -> list[dict]:
    if get_names:
        get_names = "fieldnamelist_ms"
    return load_with_text_field("FLD_Location", get_names, "Loc_name")


def load_fnetveinlist(get_names: bool = True) -> list[dict]:
    data = load_with_text_field("FnetVeinList")
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
    data = load_with_text_field("ITM_BeaconList")
    if get_names:
        names = load_textlist("ITM_BeaconList_ms")
        for probe in data:
            probe["Name"] = names[probe["Name"]]
            probe["Caption"] = names[probe["Caption"]]
    return data


def load_with_text_field(
    data_table: str, text_table: str = "", text_field: str = "Name"
) -> list[dict]:
    """Generic function to load a JSON dump and replace text fields"""
    with open(_data_dir_join(f"{data_table}.json")) as f:
        data = json.load(f)
    if text_table:
        names = load_textlist(text_table)
        for item in data:
            item[text_field] = names[item[text_field]]
    return data


def load_textlist(textlist_file) -> dict[int, str]:
    """Load textlist_file.json

    Returns a dictionary mapping ids to strings
    """
    with open(_text_dir_join(f"{textlist_file}.json")) as f:
        data = json.load(f)
    return {d["id"]: d["name"] for d in data}


def set_data_dir(data_path: str):
    global _data_dir_join
    if exists(data_path):
        _data_dir_join = functools.partial(join, data_path)


def set_text_dir(data_path: str):
    global _text_dir_join
    if exists(data_path):
        _text_dir_join = functools.partial(join, data_path)

