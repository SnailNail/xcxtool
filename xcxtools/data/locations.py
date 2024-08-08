"""Records and theories for location data in save files"""

from typing import NamedTuple


class Location(NamedTuple):
    offset: int
    bit: int
    name: str
    location_id: int
    location_type: int
    worth: int = 0
    fspot: int = 0

    def __repr__(self):
        return (f'Location({self.offset:#08x}, {self.bit:#04x}, "{self.name}", {self.location_id}, '
                f'{self.location_type}, {self.worth}, {self.fspot})')


locations = [
    Location(0x03265C, 0x01, "Biahno Grassland", 53, 4, 3384),
    # Location(0x03265C, 0x02, "Drop Shaft", 54, 1, 3385),
    # Location(0x03265C, 0x04, "Silent Mire", 55, 1, 3386),
    # Location(0x03265C, 0x08, "Seaswept Base", 56, 4, 3387),
    # Location(0x03265C, 0x10, "Wonderment Bluff", 57, 2, 3388),
    # Location(0x03265C, 0x20, "Sickle RockRise", 58, 1, 3389),
    # Location(0x03265C, 0x40, "Roof Rock", 59, 1, 3390),
    # Location(0x03265C, 0x80, "Janpath Lake", 60, 1, 3391),
    Location(0x03265D, 0x01, "Green Threshold", 45, 4, 3376),
    Location(0x03265D, 0x02, "Headwater Cavern", 46, 4, 3377),
    # Location(0x03265D, 0x04, "* Headwater Summit", 47, 1, None),
    # Location(0x03265D, 0x08, "* Headwater Cliff", 48, 3, None),
    # Location(0x03265D, 0x10, "* Biahno Water Purification Plant", 49, 1, None),
    Location(0x03265D, 0x20, "Biahno Lake", 50, 4, 3381),
    # Location(0x03265D, 0x40, "* Fallshorn Isle", 51, 1, None),
    Location(0x03265D, 0x80, "Grieving Plains", 52, 1, 3383),
    Location(0x03265E, 0x01, "Stickstone Rise", 37, 4, 3368),
    # Location(0x03265E, 0x02, "* ", 38, 4, 3369,),
    # Location(0x03265E, 0x04, "* ", 39, 4, 3370,),
    Location(0x03265E, 0x08, "Unicorn Rock,", 40, 4, 3371),
    # Location(0x03265E, 0x10, "* ", 41, 4, 3372,),
    # Location(0x03265E, 0x20, "* ", 42, 4, 3373,),
    # Location(0x03265E, 0x30, "* ", 43, 4, 3374,),
    # Location(0x03265E, 0x80, "* ", 44, 4, 3375,),
    Location(0x03265F, 0x40, "Greater Gemini Bridge", 35, 1, 3366),
    Location(0x032660, 0x02, "FN Site 102", 86, 5, 3417),
    Location(0x032660, 0x04, "FN Site 103", 87, 5, 3418),
    Location(0x032661, 0x02, "Shadow Rise", 78, 1, 3409),
    Location(0x032661, 0x08, "Starfall Basin", 80, 1, 3411),
    Location(0x032668, 0x20, "Nopon Braidbridge", 154, 1, 0, 0),
    Location(0x032668, 0x40, "Skybound Coil Tree", 155, 1, 0, 0),
    Location(0x03266b, 0x10, "Nopon Highroad", 129, 4, 0, 0),
    Location(0x03266b, 0x40, "Decapotamon Vista", 131, 3, 2000, 0),
    Location(0x03266b, 0x80, "Decapotamon", 132, 4, 0, 0),
    Location(0x03266f, 0x40, "Canopied Nightwood", 163, 4, 0, 0),
    Location(0x032689, 0x10, "Canopied Nightwood BC", 404, 4, 0, 0),
    Location(0x032689, 0x20, "Decapotamon BC", 405, 4, 0, 0),
    Location(0x03268A, 0x01, "Shadow Beach BC", 392, 4, 3720),
    Location(0x03268A, 0x08, "Biahno Grassland BC", 395, 4, 3723),
    Location(0x03268B, 0x80, "Shadow Rise BC", 391, 4, 3719),
]
