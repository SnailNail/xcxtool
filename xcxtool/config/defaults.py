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
    },
}
