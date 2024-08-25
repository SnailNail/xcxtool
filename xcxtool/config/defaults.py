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
    "sightseeing_spots": {
        # Primordia
        "101": 1,
        "103": 1,
        "104": 1,
        "106": 1,
        "110": 1,
        "117": 1,
        # Noctilum
        "213": 1,
        "214": 2,
        "216": 1,
        "220": 1,
        "221": 2,
        "222": 1,
        "223": 1,
        "225": 1,
        # Oblivia
        "306": 1,
        "313": 2,
        "315": 2,
        "317": 1,
        "318": 2,
        "319": 1,
        # Sylvalum
        "404": 1,
        "408": 1,
        "410": 1,
        "413": 1,
        "414": 2,
        "419": 1,
        # Cauldros
        "502": 1,
        "503": 1,
        "505": 2,
        "506": 1,
        "507": 1,
        "508": 1,
        "513": 2,
        "514": 1,
    },
    "compare": {
        "include": [
            [0x10, 0x5e710],
        ],
        "exclude": [],
        "obs_port": 4455,
        "obs_host": "localhost",
        "obs_password": "",
    },
}
