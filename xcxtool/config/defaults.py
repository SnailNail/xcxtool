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
        "sightseeing_spots": {
            # Primordia
            "101": 0,  # max = 1
            "103": 0,  # max = 1
            "104": 0,  # max = 1
            "106": 0,  # max = 1
            "110": 0,  # max = 1
            "117": 0,  # max = 1
            # Noctilum
            "213": 0,  # max = 1
            "214": 0,  # max = 2
            "216": 0,  # max = 1
            "220": 0,  # max = 1
            "221": 0,  # max = 2
            "222": 0,  # max = 1
            "223": 0,  # max = 1
            "225": 0,  # max = 1
            # Oblivia
            "306": 0,  # max = 1
            "313": 0,  # max = 2
            "315": 0,  # max = 2
            "317": 0,  # max = 1
            "318": 0,  # max = 2
            "319": 0,  # max = 1
            # Sylvalum
            "404": 0,  # max = 1
            "408": 0,  # max = 1
            "410": 0,  # max = 1
            "413": 0,  # max = 1
            "414": 0,  # max = 2
            "419": 0,  # max = 1
            # Cauldros
            "502": 0,  # max = 1
            "503": 0,  # max = 1
            "505": 0,  # max = 2
            "506": 0,  # max = 1
            "507": 0,  # max = 1
            "508": 0,  # max = 1
            "513": 0,  # max = 2
            "514": 0,  # max = 1
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
    },
}
