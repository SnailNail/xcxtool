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

import struct
from typing import NamedTuple, Optional

FNAV_OFFSET = 0x0480C0
FNAV_STRUCT = struct.Struct("4B" + "Bxx" * 110)
PROBE_INVENTORY_OFFSET = 0x02f0ec


class ProbeSite(NamedTuple):
    id: int
    game_name: str = "skip"
    xenoprobes_name: str = "skip"
    max_sightseeing_spots: int = 0


class Probe(NamedTuple):
    game_name: str
    xenoprobes_name: Optional[str]


sites = {
    4: ProbeSite(0, 'skip', 'skip', 0),
    7: ProbeSite(1, 'FN Site 101', '101', 1),
    10: ProbeSite(2, 'FN Site 102', '102', 0),
    13: ProbeSite(3, 'FN Site 103', '103', 1),
    16: ProbeSite(4, 'FN Site 104', '104', 1),
    19: ProbeSite(5, 'FN Site 106', '106', 1),
    22: ProbeSite(6, 'FN Site 108', '108', 0),
    25: ProbeSite(7, 'FN Site 107', '107', 0),
    28: ProbeSite(8, 'FN Site 109', '109', 0),
    31: ProbeSite(9, 'FN Site 110', '110', 1),
    34: ProbeSite(10, 'FN Site 111', '111', 0),
    37: ProbeSite(11, 'FN Site 112', '112', 0),
    40: ProbeSite(12, 'FN Site 113', '113', 0),
    43: ProbeSite(13, 'FN Site 114', '114', 0),
    46: ProbeSite(14, 'FN Site 115', '115', 0),
    49: ProbeSite(15, 'FN Site 116', '116', 0),
    52: ProbeSite(16, 'FN Site 117', '117', 1),
    55: ProbeSite(17, 'FN Site 118', '118', 0),
    58: ProbeSite(18, 'FN Site 119', '119', 0),
    61: ProbeSite(19, 'FN Site 120', '120', 0),
    64: ProbeSite(20, 'FN Site 121', '121', 0),
    67: ProbeSite(21, 'FN Site 105', '105', 0),
    70: ProbeSite(22, 'FN Site 201', '201', 0),
    73: ProbeSite(23, 'FN Site 202', '202', 0),
    76: ProbeSite(24, 'FN Site 203', '203', 0),
    79: ProbeSite(25, 'FN Site 204', '204', 0),
    82: ProbeSite(26, 'FN Site 205', '205', 0),
    85: ProbeSite(27, 'FN Site 206', '206', 0),
    88: ProbeSite(28, 'FN Site 207', '207', 0),
    91: ProbeSite(29, 'FN Site 208', '208', 0),
    94: ProbeSite(30, 'FN Site 209', '209', 0),
    97: ProbeSite(31, 'FN Site 210', '210', 0),
    100: ProbeSite(32, 'FN Site 211', '211', 0),
    103: ProbeSite(33, 'FN Site 212', '212', 0),
    106: ProbeSite(34, 'FN Site 213', '213', 1),
    109: ProbeSite(35, 'FN Site 214', '214', 2),
    112: ProbeSite(36, 'FN Site 215', '215', 0),
    115: ProbeSite(37, 'FN Site 216', '216', 1),
    118: ProbeSite(38, 'FN Site 217', '217', 0),
    121: ProbeSite(39, 'FN Site 218', '218', 0),
    124: ProbeSite(40, 'FN Site 219', '219', 0),
    127: ProbeSite(41, 'FN Site 220', '220', 1),
    130: ProbeSite(42, 'FN Site 221', '221', 2),
    133: ProbeSite(43, 'FN Site 222', '222', 1),
    136: ProbeSite(44, 'FN Site 223', '223', 1),
    139: ProbeSite(45, 'FN Site 224', '224', 0),
    142: ProbeSite(46, 'FN Site 225', '225', 1),
    145: ProbeSite(47, 'skip', 'skip', 0),
    148: ProbeSite(48, 'skip', 'skip', 0),
    151: ProbeSite(49, 'FN Site 301', '301', 0),
    154: ProbeSite(50, 'FN Site 302', '302', 0),
    157: ProbeSite(51, 'FN Site 303', '303', 0),
    160: ProbeSite(52, 'FN Site 304', '304', 0),
    163: ProbeSite(53, 'FN Site 305', '305', 0),
    166: ProbeSite(54, 'FN Site 306', '306', 1),
    169: ProbeSite(55, 'FN Site 307', '307', 0),
    172: ProbeSite(56, 'FN Site 308', '308', 0),
    175: ProbeSite(57, 'FN Site 309', '309', 0),
    178: ProbeSite(58, 'FN Site 310', '310', 0),
    181: ProbeSite(59, 'FN Site 311', '311', 0),
    184: ProbeSite(60, 'FN Site 312', '312', 0),
    187: ProbeSite(61, 'FN Site 313', '313', 2),
    190: ProbeSite(62, 'FN Site 314', '314', 0),
    193: ProbeSite(63, 'FN Site 315', '315', 2),
    196: ProbeSite(64, 'FN Site 316', '316', 0),
    199: ProbeSite(65, 'FN Site 317', '317', 1),
    202: ProbeSite(66, 'FN Site 318', '318', 2),
    205: ProbeSite(67, 'FN Site 320', '320', 0),
    208: ProbeSite(68, 'FN Site 321', '321', 0),
    211: ProbeSite(69, 'FN Site 319', '319', 1),
    214: ProbeSite(70, 'FN Site 322', '322', 0),
    217: ProbeSite(71, 'skip', 'skip', 0),
    220: ProbeSite(72, 'skip', 'skip', 0),
    223: ProbeSite(73, 'skip', 'skip', 0),
    226: ProbeSite(74, 'FN Site 401', '401', 0),
    229: ProbeSite(75, 'FN Site 402', '402', 0),
    232: ProbeSite(76, 'FN Site 403', '403', 0),
    235: ProbeSite(77, 'FN Site 404', '404', 1),
    238: ProbeSite(78, 'FN Site 405', '405', 0),
    241: ProbeSite(79, 'FN Site 406', '406', 0),
    244: ProbeSite(80, 'FN Site 407', '407', 0),
    247: ProbeSite(81, 'FN Site 408', '408', 1),
    250: ProbeSite(82, 'FN Site 409', '409', 0),
    253: ProbeSite(83, 'FN Site 410', '410', 1),
    256: ProbeSite(84, 'FN Site 411', '411', 0),
    259: ProbeSite(85, 'FN Site 412', '412', 0),
    262: ProbeSite(86, 'FN Site 413', '413', 1),
    265: ProbeSite(87, 'FN Site 414', '414', 2),
    268: ProbeSite(88, 'FN Site 415', '415', 0),
    271: ProbeSite(89, 'FN Site 416', '416', 0),
    274: ProbeSite(90, 'FN Site 417', '417', 0),
    277: ProbeSite(91, 'FN Site 418', '418', 0),
    280: ProbeSite(92, 'FN Site 419', '419', 1),
    283: ProbeSite(93, 'FN Site 420', '420', 0),
    286: ProbeSite(94, 'FN Site 501', '501', 0),
    289: ProbeSite(95, 'FN Site 502', '502', 1),
    292: ProbeSite(96, 'FN Site 503', '503', 1),
    295: ProbeSite(97, 'FN Site 504', '504', 0),
    298: ProbeSite(98, 'FN Site 505', '505', 2),
    301: ProbeSite(99, 'FN Site 506', '506', 1),
    304: ProbeSite(100, 'FN Site 507', '507', 1),
    307: ProbeSite(101, 'FN Site 508', '508', 1),
    310: ProbeSite(102, 'FN Site 509', '509', 0),
    313: ProbeSite(103, 'FN Site 510', '510', 0),
    316: ProbeSite(104, 'FN Site 511', '511', 0),
    319: ProbeSite(105, 'FN Site 512', '512', 0),
    322: ProbeSite(106, 'FN Site 513', '513', 2),
    325: ProbeSite(107, 'FN Site 514', '514', 1),
    328: ProbeSite(108, 'FN Site 515', '515', 0),
    331: ProbeSite(109, 'FN Site 516', '516', 0)
}

probe_types = {
    1: Probe(game_name='Basic Probe', xenoprobes_name=''),
    2: Probe(game_name='Mining Probe G1', xenoprobes_name='M1'),
    3: Probe(game_name='Mining Probe G2', xenoprobes_name='M2'),
    4: Probe(game_name='Mining Probe G3', xenoprobes_name='M3'),
    5: Probe(game_name='Mining Probe G4', xenoprobes_name='M4'),
    6: Probe(game_name='Mining Probe G5', xenoprobes_name='M5'),
    7: Probe(game_name='Mining Probe G6', xenoprobes_name='M6'),
    8: Probe(game_name='Mining Probe G7', xenoprobes_name='M7'),
    9: Probe(game_name='Mining Probe G8', xenoprobes_name='M8'),
    10: Probe(game_name='Mining Probe G9', xenoprobes_name='M9'),
    11: Probe(game_name='Mining Probe G10', xenoprobes_name='M10'),
    14: Probe(game_name='Research Probe G1', xenoprobes_name='R1'),
    15: Probe(game_name='Research Probe G2', xenoprobes_name='R2'),
    16: Probe(game_name='Research Probe G3', xenoprobes_name='R3'),
    17: Probe(game_name='Research Probe G4', xenoprobes_name='R4'),
    18: Probe(game_name='Research Probe G5', xenoprobes_name='R5'),
    19: Probe(game_name='Research Probe G6', xenoprobes_name='R6'),
    22: Probe(game_name='Booster Probe G1', xenoprobes_name='B1'),
    23: Probe(game_name='Booster Probe G2', xenoprobes_name='B2'),
    26: Probe(game_name='Storage Probe', xenoprobes_name='S'),
    29: Probe(game_name='Duplicator Probe', xenoprobes_name='D'),
    30: Probe(game_name='Fuel Recovery Probe', xenoprobes_name=''),
    31: Probe(game_name='Melee Attack Probe', xenoprobes_name=''),
    32: Probe(game_name='Ranged Attack Probe', xenoprobes_name=''),
    33: Probe(game_name='EZ Debuff Probe', xenoprobes_name=''),
    34: Probe(game_name='Attribute Resistance Probe', xenoprobes_name='')
}
