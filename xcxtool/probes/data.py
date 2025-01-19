"""Mappings of id numbers to probe metadata

Notes on data sources: Probe data (site ids, types etc) are sourced from the
following data (BDAT) files:
  * common_local_us/FnetVeinList: contains the data for FrontierNav sites, in
    the order they appear in the in-memory array of planted probes.
  * common_local_us/FLD_Location: data on all locations. the ``name`` field of
    FnetVeinList entries is an index in this data file. Note that probe sites
    have a ``Loc_type`` value of 5.
  * common_ms/fieldnamelist_ms: English names of all the in-game locations.
    Referenced by the ``Loc_name`` column in FLD_Location
  * common_local_us/ITM_BeaconList: Probe type data. The probe array data is
    an index into this list.
  * common_ms/ITM_BeaconList_ms: English names of probe types. Reference by
    the ``name`` column in ITM_BeaconList.
"""

from functools import partial
import struct
from typing import NamedTuple

FNAV_SLICE = slice(0x0480C4, 0x04820E)
FNAV_STRUCT = struct.Struct("Bxx" * 110)
PROBE_INVENTORY_SLICE = slice(0x02F0EC, 0x02F59C)
PROBE_INVENTORY_SIZE = 12 * 100
LOCATIONS_SLICE = slice(0x032658, 0x3269c)

_int = partial(int.from_bytes, byteorder="big")


class Probe(NamedTuple):
    type_id: int
    game_name: str
    xenoprobes_name: str
    frontiernav_type: int

    @staticmethod
    def from_id(type_id: int) -> "Probe":
        return _probe_types[type_id]

    def __str__(self):
        return self.game_name


class ProbeSite(NamedTuple):
    id: int
    game_name: str = "skip"
    xenoprobes_name: str = "skip"
    mining_grade: str = "C"
    revenue_grade: str = "C"
    combat_grade: str = "C"
    sightseeing_spots: tuple = tuple()
    ores: tuple[str, ...] = tuple()

    @staticmethod
    def from_id(site_id: int) -> "ProbeSite":
        return _sites_defaults[site_id]

    def __repr__(self):
        return f"ProbeSite({self.id}, {self.game_name}, {self.xenoprobes_name}, {self.sightseeing_spots})"

    def __str__(self):
        return self.game_name

    def __format__(self, format_spec=""):
        if format_spec == "i":
            return str(self.id)
        if format_spec == "g":
            return self.game_name
        if format_spec == "x":
            return self.xenoprobes_name
        if format_spec == "s":
            return str(len(self.sightseeing_spots))
        if format_spec == "xrow":
            # site,mining grade, revenue grade, combat grade, sights
            ores = ""
            if self.ores:
                ores = "," + ",".join(self.ores)
            return "{},{},{},{},{}{}".format(*self[2:6], len(self.sightseeing_spots), ores)


def probe_and_quantity_from_bytes(buffer: bytes) -> tuple[Probe, int]:
    probe_type = _int(buffer[:2]) >> 3
    quantity = (_int(buffer[2:4]) >> 3) & 0x1FF
    return _probe_types[probe_type], quantity


_probe_types = {
    1: Probe(1, "Basic Probe", "BA", 1),
    2: Probe(2, "Mining Probe G1", "M1", 2),
    3: Probe(3, "Mining Probe G2", "M2", 3),
    4: Probe(4, "Mining Probe G3", "M3", 4),
    5: Probe(5, "Mining Probe G4", "M4", 5),
    6: Probe(6, "Mining Probe G5", "M5", 6),
    7: Probe(7, "Mining Probe G6", "M6", 7),
    8: Probe(8, "Mining Probe G7", "M7", 8),
    9: Probe(9, "Mining Probe G8", "M8", 9),
    10: Probe(10, "Mining Probe G9", "M9", 10),
    11: Probe(11, "Mining Probe G10", "M10", 11),
    14: Probe(14, "Research Probe G1", "R1", 12),
    15: Probe(15, "Research Probe G2", "R2", 13),
    16: Probe(16, "Research Probe G3", "R3", 14),
    17: Probe(17, "Research Probe G4", "R4", 15),
    18: Probe(18, "Research Probe G5", "R5", 16),
    19: Probe(19, "Research Probe G6", "R6", 17),
    22: Probe(22, "Booster Probe G1", "B1", 18),
    23: Probe(23, "Booster Probe G2", "B2", 19),
    26: Probe(26, "Storage Probe", "S", 20),
    29: Probe(29, "Duplicator Probe", "D", 21),
    30: Probe(30, "Fuel Recovery Probe", "FR", 22),
    31: Probe(31, "Melee Attack Probe", "MA", 22),
    32: Probe(32, "Ranged Attack Probe", "RA", 22),
    33: Probe(33, "EZ Debuff Probe", "ED", 22),
    34: Probe(34, "Attribute Resistance Probe", "AR", 22),
    254: Probe(254, "[LOCKED]", "XX", 0),
}

_sites_defaults = {
    0: ProbeSite(0, "skip", "skip", "C", "C", "C", ()),
    1: ProbeSite(1, "FN Site 101", "101", "C", "S", "S", (34,)),
    2: ProbeSite(2, "FN Site 102", "102", "C", "F", "B", ()),
    3: ProbeSite(3, "FN Site 103", "103", "C", "E", "A", (57,)),
    4: ProbeSite(4, "FN Site 104", "104", "C", "S", "B", (48,)),
    5: ProbeSite(5, "FN Site 106", "106", "B", "E", "B", (41,), ("Arc Sand Ore",)),
    6: ProbeSite(6, "FN Site 108", "108", "C", "F", "B", (), ("Aurorite", "Arc Sand Ore", "Foucaultium"),),
    7: ProbeSite(7, "FN Site 107", "107", "A", "F", "B", ()),
    8: ProbeSite(8, "FN Site 109", "109", "C", "D", "B", (), ("Foucaultium", "Dawnstone", "Lionbone Bort"),),
    9: ProbeSite(9, "FN Site 110", "110", "C", "E", "B", (74,), ("Aurorite", "Arc Sand Ore", "White Cometite", "Dawnstone"),),
    10: ProbeSite(10, "FN Site 111", "111", "C", "F", "B", (), ("Foucaultium",)),
    11: ProbeSite(11, "FN Site 112", "112", "A", "F", "A", ()),
    12: ProbeSite(12, "FN Site 113", "113", "C", "C", "B", ()),
    13: ProbeSite(13, "FN Site 114", "114", "C", "E", "B", ()),
    14: ProbeSite(14, "FN Site 115", "115", "C", "D", "B", (), ("Arc Sand Ore", "White Cometite", "Lionbone Bort"),),
    15: ProbeSite(15, "FN Site 116", "116", "A", "D", "B", ()),
    16: ProbeSite(16, "FN Site 117", "117", "A", "D", "A", (81,)),
    17: ProbeSite(17, "FN Site 118", "118", "C", "E", "B", (), ("Aurorite", "White Cometite", "Dawnstone"),),
    18: ProbeSite(18, "FN Site 119", "119", "C", "E", "B", ()),
    19: ProbeSite(19, "FN Site 120", "120", "B", "B", "B", ()),
    20: ProbeSite(20, "FN Site 121", "121", "A", "E", "B", ()),
    21: ProbeSite(21, "FN Site 105", "105", "A", "F", "B", ()),
    22: ProbeSite(22, "FN Site 201", "201", "C", "B", "S", ()),
    23: ProbeSite(23, "FN Site 202", "202", "C", "C", "B", (), ("Cimmerian Cinnabar", "Everfreeze Ore")),
    24: ProbeSite(24, "FN Site 203", "203", "C", "A", "B", (), ("Cimmerian Cinnabar",)),
    25: ProbeSite(25, "FN Site 204", "204", "A", "C", "B", ()),
    26: ProbeSite(26, "FN Site 205", "205", "A", "F", "B", ()),
    27: ProbeSite(27, "FN Site 206", "206", "B", "A", "S", ()),
    28: ProbeSite(28, "FN Site 207", "207", "C", "C", "B", (), ("Infernium", "White Cometite", "Cimmerian Cinnabar", "Foucaultium"),),
    29: ProbeSite(29, "FN Site 208", "208", "B", "D", "B", (), ("Foucaultium",)),
    30: ProbeSite(30, "FN Site 209", "209", "C", "F", "B", ()),
    31: ProbeSite(31, "FN Site 210", "210", "B", "D", "B", ()),
    32: ProbeSite(32, "FN Site 211", "211", "A", "D", "B", ()),
    33: ProbeSite(33, "FN Site 212", "212", "B", "E", "B", (), ("Aurorite", "Enduron Lead", "White Cometite"),),
    34: ProbeSite(34, "FN Site 213", "213", "C", "S", "B", (162,)),
    35: ProbeSite(35, "FN Site 214", "214", "C", "D", "B", (229, 241)),
    36: ProbeSite(36, "FN Site 215", "215", "C", "D", "B", (), ("Aurorite", "Enduron Lead", "Everfreeze Ore"),),
    37: ProbeSite(37, "FN Site 216", "216", "C", "A", "A", (133,)),
    38: ProbeSite(38, "FN Site 217", "217", "C", "C", "B", (), ("Aurorite", "Infernium", "Cimmerian Cinnabar"),),
    39: ProbeSite(39, "FN Site 218", "218", "C", "E", "B", (), ("Aurorite", "Enduron Lead", "White Cometite"),),
    40: ProbeSite(40, "FN Site 219", "219", "C", "E", "B", (), ("Enduron Lead", "White Cometite")),
    41: ProbeSite(41, "FN Site 220", "220", "C", "C", "A", (126,), ("Infernium", "Everfreeze Ore")),
    42: ProbeSite(42, "FN Site 221", "221", "C", "E", "B", (118, 112)),
    43: ProbeSite(43, "FN Site 222", "222", "C", "D", "B", (153,)),
    44: ProbeSite(44, "FN Site 223", "223", "C", "F", "B", (168,)),
    45: ProbeSite(45, "FN Site 224", "224", "C", "A", "B", ()),
    46: ProbeSite(46, "FN Site 225", "225", "C", "A", "B", (131,)),
    47: ProbeSite(47, "skip", "skip", "C", "C", "C", ()),
    48: ProbeSite(48, "skip", "skip", "C", "C", "C", ()),
    49: ProbeSite(49, "FN Site 301", "301", "B", "D", "B", (), ("Infernium", "Arc Sand Ore", "Lionbone Bort"),),
    50: ProbeSite(50, "FN Site 302", "302", "C", "E", "B", ()),
    51: ProbeSite(51, "FN Site 303", "303", "C", "E", "B", (), ("Aurorite", "White Cometite")),
    52: ProbeSite(52, "FN Site 304", "304", "B", "A", "S", ()),
    53: ProbeSite(53, "FN Site 305", "305", "C", "E", "B", (), ("Aurorite", "Arc Sand Ore", "Enduron Lead"),),
    54: ProbeSite(54, "FN Site 306", "306", "C", "D", "B", (211,)),
    55: ProbeSite(55, "FN Site 307", "307", "C", "B", "B", (), ("Infernium", "Arc Sand Ore", "Enduron Lead", "White Cometite"),),
    56: ProbeSite(56, "FN Site 308", "308", "B", "C", "A", (), ("Ouroboros Crystal",)),
    57: ProbeSite(57, "FN Site 309", "309", "C", "C", "B", (), ("Enduron Lead", "Ouroboros Crystal"),),
    58: ProbeSite(58, "FN Site 310", "310", "C", "A", "B", ()),
    59: ProbeSite(59, "FN Site 311", "311", "C", "B", "B", ()),
    60: ProbeSite(60, "FN Site 312", "312", "C", "D", "B", (), ("Infernium", "Boiled-Egg Ore", "Lionbone Bort"),),
    61: ProbeSite(61, "FN Site 313", "313", "C", "E", "A", (235, 206)),
    62: ProbeSite(62, "FN Site 314", "314", "C", "B", "S", ()),
    63: ProbeSite(63, "FN Site 315", "315", "A", "S", "B", (229, 241)),
    64: ProbeSite(64, "FN Site 316", "316", "C", "D", "B", ()),
    65: ProbeSite(65, "FN Site 317", "317", "C", "A", "B", (205,)),
    66: ProbeSite(66, "FN Site 318", "318", "C", "B", "B", (201, 210), ("Boiled-Egg Ore", "White Cometite", "Lionbone Bort"),),
    67: ProbeSite(67, "FN Site 320", "320", "C", "B", "B", (), ("Aurorite", "Ouroboros Crystal")),
    68: ProbeSite(68, "FN Site 321", "321", "A", "D", "A", ()),
    69: ProbeSite(69, "FN Site 319", "319", "C", "D", "B", (233,), ("Infernium", "Boiled-Egg Ore")),
    70: ProbeSite(70, "FN Site 322", "322", "A", "A", "B", ()),
    71: ProbeSite(71, "skip", "skip", "C", "C", "C", ()),
    72: ProbeSite(72, "skip", "skip", "C", "C", "C", ()),
    73: ProbeSite(73, "skip", "skip", "C", "C", "C", ()),
    74: ProbeSite(74, "FN Site 401", "401", "C", "B", "B", (), ("Parhelion Platinum", "Marine Rutile"),),
    75: ProbeSite(75, "FN Site 402", "402", "A", "B", "B", ()),
    76: ProbeSite(76, "FN Site 403", "403", "A", "C", "S", ()),
    77: ProbeSite(77, "FN Site 404", "404", "B", "S", "S", (309,)),
    78: ProbeSite(78, "FN Site 405", "405", "A", "E", "A", (), ("Arc Sand Ore",)),
    79: ProbeSite(79, "FN Site 406", "406", "C", "B", "B", ()),
    80: ProbeSite(80, "FN Site 407", "407", "A", "B", "B", ()),
    81: ProbeSite(81, "FN Site 408", "408", "B", "D", "B", (312, ), ("Aurorite", "Arc Sand Ore", "Everfreeze Ore"),),
    82: ProbeSite(82, "FN Site 409", "409", "B", "S", "B", ()),
    83: ProbeSite(83, "FN Site 410", "410", "C", "S", "B", (308,)),
    84: ProbeSite(84, "FN Site 411", "411", "A", "A", "S", ()),
    85: ProbeSite(85, "FN Site 412", "412", "A", "B", "A", ()),
    86: ProbeSite(86, "FN Site 413", "413", "C", "A", "B", (276,)),
    87: ProbeSite(87, "FN Site 414", "414", "C", "B", "B", (303, 313), ("Parhelion Platinum", "Marine Rutile"),),
    88: ProbeSite(88, "FN Site 415", "415", "C", "S", "B", ()),
    89: ProbeSite(89, "FN Site 416", "416", "C", "B", "B", ()),
    90: ProbeSite(90, "FN Site 417", "417", "B", "D", "B", (), ("Everfreeze Ore", "Boiled-Egg Ore")),
    91: ProbeSite(91, "FN Site 418", "418", "C", "C", "B", (), ("Parhelion Platinum", "Arc Sand Ore", "Everfreeze Ore", "Boiled-Egg Ore", "Marine Rutile",),),
    92: ProbeSite(92, "FN Site 419", "419", "C", "S", "S", (305,)),
    93: ProbeSite(93, "FN Site 420", "420", "B", "C", "B", (), ("Everfreeze Ore",)),
    94: ProbeSite(94, "FN Site 501", "501", "B", "F", "B", (), ("Arc Sand Ore",)),
    95: ProbeSite(95, "FN Site 502", "502", "A", "C", "B", (336,), ("Bonjelium",)),
    96: ProbeSite(96, "FN Site 503", "503", "C", "D", "B", (339,), ("Enduron Lead",)),
    97: ProbeSite(97, "FN Site 504", "504", "C", "C", "B", (), ("Arc Sand Ore", "Enduron Lead", "Marine Rutile", "Bonjelium"),),
    98: ProbeSite(98, "FN Site 505", "505", "C", "B", "B", (341, 364)),
    99: ProbeSite(99, "FN Site 506", "506", "C", "B", "B", (345,), ("Bonjelium", "Arc Sand Ore")),
    100: ProbeSite(100, "FN Site 507", "507", "C", "A", "B", (346,), ("Bonjelium",)),
    101: ProbeSite(101, "FN Site 508", "508", "A", "B", "S", (347,), ("Enduron Lead", "Marine Rutile")),
    102: ProbeSite(102, "FN Site 509", "509", "A", "A", "A", ()),
    103: ProbeSite(103, "FN Site 510", "510", "C", "B", "B", (), ("Bonjelium",)),
    104: ProbeSite(104, "FN Site 511", "511", "A", "C", "A", (), ("Bonjelium",)),
    105: ProbeSite(105, "FN Site 512", "512", "C", "A", "S", ()),
    106: ProbeSite(106, "FN Site 513", "513", "C", "A", "B", (358, 360)),
    107: ProbeSite(107, "FN Site 514", "514", "C", "A", "B", (356,)),
    108: ProbeSite(108, "FN Site 515", "515", "C", "B", "S", ()),
    109: ProbeSite(109, "FN Site 516", "516", "B", "E", "B", ()),
}


sightseeing_spots = [
    # (location_id, offset, bit)
    (57, 0x000004, 0x10),
    (48, 0x000005, 0x08),
    (41, 0x000006, 0x10),
    (34, 0x000007, 0x20),
    (81, 0x000009, 0x10),
    (74, 0x00000a, 0x20),
    (118, 0x00000c, 0x02),
    (112, 0x00000d, 0x08),
    (153, 0x000010, 0x10),
    (147, 0x000011, 0x40),
    (133, 0x000012, 0x01),
    (126, 0x000013, 0x02),
    (131, 0x000013, 0x40),
    (162, 0x000017, 0x20),
    (210, 0x000019, 0x04),
    (211, 0x000019, 0x08),
    (201, 0x00001a, 0x02),
    (205, 0x00001a, 0x20),
    (206, 0x00001a, 0x40),
    (241, 0x00001d, 0x02),
    (233, 0x00001e, 0x02),
    (235, 0x00001e, 0x08),
    (229, 0x00001f, 0x20),
    (276, 0x000021, 0x10),
    (312, 0x000024, 0x01),
    (313, 0x000024, 0x02),
    (308, 0x000025, 0x10),
    (309, 0x000025, 0x20),
    (303, 0x000026, 0x80),
    (305, 0x000025, 0x02),
    (345, 0x000028, 0x02),
    (350, 0x000028, 0x40),
    (336, 0x000029, 0x01),
    (339, 0x000029, 0x08),
    (341, 0x000029, 0x20),
    (360, 0x00002e, 0x01),
    (364, 0x00002e, 0x10),
    (356, 0x00002f, 0x10),
    (358, 0x00002f, 0x40),
    (167, 0x00003b, 0x01),
    (168, 0x00003b, 0x02),
    (347, 0x000028, 0x08),
]
