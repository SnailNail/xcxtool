# XCXTools

A collection of scripts and helpers for playing Xenoblade Chronicles X (XCX) on
the [Cemu emulator]. Most of the utilities are bundled into subcommands of a
single command line tool `xcxtool`. If the project is installed with pip, the
command will be available as an executable, or the utility can also be run as
a module (`python -m xcxtool`)

This project started as a way to partially automate backing up save data, and
most of the utilities operate primarily on save data, but most can also be used
with live data extracted directly from the emulated WiiU memory, via [PyMem]
(on Windows only).


## Configuration
`xcxtool` is intended to be used with a configuration file to define program
settings. By default, `xcxtool` will look for a config file called `xcxtool.toml`
in the current directory. If a config file isn't found, successive parent 
directories are searched and the first found config file is uses. If no
configuration file is found, default values are used.

A custom configuration file can be used with the global `--config` (`-c`) option.
Most options can also be configured on the command line, in which case they will
override the default or config file value.

The config file is in [TOML] format. Each section, or table, contains options
for subcommand named by the section.

# Command reference

## `xcxtool`

The bare `xcxtool` command has minimal functionality, but it does host some
global configuration that applies to all subcommands. Configuration options
are stored in the `[xcxtool]` table of the config file. In the list below, 
configuration key is shown first, followed by the command-line option
equivalent(s).

  * `cemu_process` (`--cemu-process-name`): The name of the cemu process, if 
    different from the default `cemu.exe`.
  * `nand_root` (`--cemu-nand-root`): location of the emulated NAND root, 
     typically the `mlc0` directory in Cemu's installation directory.
  * `persistent_id` (`--cemu-account-id`): The PersistentID of the Cemu account,
     defaults to `"80000001"`.
  * `region` (`--region`): The region of the emulated ROM, the value must be
    one of `EUR`, `USA` or `JAP`. Defaults to `EUR`.

## `xcxtool backup`
Copy the active save data to a custom filename. Requires the options `xcxtool.nand_root`,
`xcxtool.region` and `xcxtool.persistent_id` options to be set, unless a custom
save directory is explicitly set.

File names can contain any number of fields, which are replace with values
extracted from the save data. For example, a filename template could be 
`backup {player_name} Level {level}`, and the resulting filename might be
`backup MyCharacter Level 34.zip`.

### Configuration
Specific configuration options should be put in the `[backup]` table.

* `save_directory` (`--save-dir`, `-s`): Directory to backup save data from.
  The default is to use the Cemu save data folder, constructed from the NAND
  root, persitent ID and region options, but this option must be set if any of
  those options are not specified
* `backup_directory` (`--backup-dir`, `-b`): Directory to backup save data to.
  Defaults to "saves" in the current working directory.
* `file_name` (`--file`, `-f`): The filename for the backup. May contain
  replacement fields as detailed below defaults to "backup-{datetime}" which
  embeds the current date and time.


[Cemu emulator]: https://cemu.info
[PyMem]: https://github.com/srounet/Pymem
[TOML]: https://toml.io/en/