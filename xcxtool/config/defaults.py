"""Default configuration values/config schema"""
CONFIG_DEFAULTS = {
    "xcxtool": {
        "cemu_process_name": "cemu.exe",
        "nand_root": "",
        "persistent_id": "80000001",
        "region": "EUR"
    },
    "backup": {
        "save_directory": r"",
        "backup_directory": r".\saves",
        "file_name": "backup-{datetime}",
    },
    "fnav": {
        "output_dir": ".",
        "sightseeing_spots": {
            # Primordia
            "101": -1,  # max = 1
            "103": -1,  # max = 1
            "104": -1,  # max = 1
            "106": -1,  # max = 1
            "110": -1,  # max = 1
            "117": -1,  # max = 1
            # Noctilum
            "213": -1,  # max = 1
            "214": -1,  # max = 2
            "216": -1,  # max = 1
            "220": -1,  # max = 1
            "221": -1,  # max = 2
            "222": -1,  # max = 1
            "223": -1,  # max = 1
            "225": -1,  # max = 1
            # Oblivia
            "306": -1,  # max = 1
            "313": -1,  # max = 2
            "315": -1,  # max = 2
            "317": -1,  # max = 1
            "318": -1,  # max = 2
            "319": -1,  # max = 1
            # Sylvalum
            "404": -1,  # max = 1
            "408": -1,  # max = 1
            "410": -1,  # max = 1
            "413": -1,  # max = 1
            "414": -1,  # max = 2
            "419": -1,  # max = 1
            # Cauldros
            "502": -1,  # max = 1
            "503": -1,  # max = 1
            "505": -1,  # max = 2
            "506": -1,  # max = 1
            "507": -1,  # max = 1
            "508": -1,  # max = 1
            "513": -1,  # max = 2
            "514": -1,  # max = 1
        },

    },
    "compare": {
        "include": [
            [0x10, 0x5e710],
        ],
        "exclude": [],
        "obs_port": 4455,
        "obs_host": "localhost",
        "obs_password": "",
        "recording_dir": "."
    },
    "named_ranges": {
        "gamedata": [0x10, 0x5e710],
        "player Characters": [0x58, 0x688c],
        "scouted characters": [0x6890, 0x6ef0],
        "skells": [0x6ef0, 0xc620],
        "player class records": [0xc20, 0xc81e],
        "currencies": [0xc820, 0xc82c],
        "party configuration": [0xc82c, 0xc84c],
        "inventory": [0xc850, 0x32480],
        "inventory (skell armour)": [0xc850, 0x125f8],
        "inventory (skell weapons)": [0x125f8, 0x183a0],
        "inventory (ground armour)": [0x183a0, 0x1e148],
        "inventory (melee weapons)": [0x1e148, 0x23ef0],
        "inventory (ranged weapons)": [0x23ef0, 0x29c98],
        "inventory (augments)": [0x29c98, 0x2cb6c],
        "inventory (materials)": [0x2cb6c, 0x2f0ec],
        "inventory (data probes)": [0x2f0ec, 0x2f59c],
        "inventory (collectables)": [0x2f59c, 0x303ac],
        "inventory (important items)": [0x303ac, 0x31b1c],
        "inventory (unknown)": [0x31b20, 0x31fd0],
        "inventory (precious resources)": [0x31fd0, 0x32228],
        "inventory (consumables)": [0x32228, 0x32480],
        "main game state (assumed)": [0x32480, 0x39108],
        "found locations": [0x32658, 0x3269e],
        "BLADE info": [0x39108, 0x39180],
        "affinity characters": [0x39540, 0x45d40],
        "blade medals": [0x45d60, 0x45d64],
        "last save time": [0x45d64, 0x45d68],
        "last landmark": [0x45e14, 0x45e18],
        "play timer": [0x45e40, 0x45e44],
        "FrontierNav timers": [0x480c0, 0x480c4],
        "FrontierNav probe placement": [0x480c4, 0x48274],
        "field_skills": [0x48ac8, 0x48aca],
        "holofigure collection (assumed)": [0x48ad0, 0x48eb8],
        "schematics collection (assumed)": [0x4b724, 0x4b7d4],
        "enemy index": [0x4e614, 0x569b4],
    },
}
