# XCXTools

A collection of scripts and helpers for playing Xenoblade Chronicles X (XCX) on
the [Cemu emulator]. Most of the utilities are bundled into subcommands of a
single command line tool `xcxtool`. If the project is installed with pip, the
command will be available as an executable, or the utility can also be run as
a module (`python -m xcxtool`)

This project started as a way to partially automate backing up save data, and
most of the utilities operate primarily on save data, but several can also be
used with live data extracted directly from the emulated WiiU memory, via
[PyMem] (on Windows only).

<!-- TOC -->
* [XCXTools](#xcxtools)
  * [Configuration Overview](#configuration-overview)
* [Command reference](#command-reference)
  * [`xcxtool`](#xcxtool)
  * [`xcxtool backup`](#xcxtool-backup)
    * [Configuration](#configuration)
    * [Replacement fields](#replacement-fields)
  * [`xcxtool fnav`](#xcxtool-fnav)
    * [Configuration](#configuration-1)
  * [`xcxtool compare`](#xcxtool-compare)
    * [Configuration](#configuration-2)
<!-- TOC -->

## Configuration Overview

`xcxtool` is intended to be used with a configuration file to define program
settings. By default, `xcxtool` will look for a config file
called `xcxtool.toml`
in the current directory. If a config file isn't found, successive parent
directories are searched and the first found config file is uses. If no
configuration file is found, default values are used.

A custom configuration file can be used with the global `--config` (`-c`)
option.
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

The following options are only available on the command line:

* `--config`, `-c`: Specify a custom configuration file. If the file does not
  exist, only default settings (and command line parameters) will be used,
  automatic search does not take place.

## `xcxtool backup`

Copy the active save data to a custom filename. Requires the
options `xcxtool.nand_root`,
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
  root, persistent ID and region options. This option must be set if any of
  those options are not specified.
* `backup_directory` (`--backup-dir`, `-b`): Directory to backup save data to.
  Defaults to "saves" in the current working directory.
* `file_name` (`--file`, `-f`): The filename for the backup. May contain
  replacement fields as detailed below defaults to `backup-{datetime}` which
  embeds the current date and time.

### Replacement fields

The backup filename may include template values which are replaced by data
extracted from the backed-up save data. In addition, values can be customised
by using Python [string formatting syntax][formatting]: for example, using the
field
`{level:02d}` would be replaced by the player character's level padded to two
digits with zeros.

The following replacement fields are available. Unless otherwise stated, all
character properties refer to the player character:

| Field             | Description                               | Type     |
|-------------------|-------------------------------------------|:---------|
| `{name}`          | The player character's name               | string   |
| `{level}`         | Inner level                               | integer  |
| `{exp}`           | Total experience points                   | integer  |
| `{class}`         | Class type                                | integer  |
| `{class_rank}`    | Class rank/level                          | integer  |
| `{class_exp}`     | Total class experience                    | integer  |
| `{division}`      | Division name                             | string   |
| `{blade_level}`   | BLADE Level (1 - 10)                      | integer  |
| `{play_time}`     | In game play time, formatted as hhh-mm-ss | string   |
| `{save_date}`     | Last save date, formatted as YYYYMMDD     | string   |
| `{save_time}`     | Last save time, formatted as hh-mm-ss     | string   |
| `{date}`          | Current date                              | string   |
| `{time}`          | Current time                              | string   |
| `{save_datetime}` | Last save datetime                        | datetime |
| `{datetime}`      | Current datetime                          | datetime |

## `xcxtool fnav`

Read FrontierNav layout and probe inventory from save data. The primary purpose
of this command is to generate config files for [xenoprobes], or to quickly load
your current probe layout into the excellent [FrontierNav.net] probe simulation.

### Configuration

The following settings should be placed in the `[fnav]` table of the settings
file:

* `sightseeing_spots`: define the number of found sightseeing spots at relevant
  probe sites. See the config file sample for an example (TODO). In the
  future it will be possible to automatically get this information from the
  save data
* `output_directory` (`--output-dir`, `-o`): save xenoprobes output to this
  director (defaults to the current working directory)
* `exclude_probes` (`--exclude-probes` `-x`): Do not include these probe
  types in inventory output. Should be a array of strings in the config file,
  or a comma-separate list on the command line (e.g. `-x M1,R1`)

The following options can only be set on the command line and control the
output of the command:

* `--layout`, `-l`: output probe layout, i.e. a mapping of probe sites to
  probe types (`inventory.csv`). This is the default if no other option mode
  is provided.
* `--inventory`, `-i`: output probe inventory (`inventory.csv`)
* `--sites`, `-s`: output available FrontierNav sites (`sites.csv`). This
  currently uses the `sightseeing_spots` configuration for sightseeing spot
  numbers
* `--frontiernav`, `-j`: output a FrontierNav.net probe inventory URL. If
  navigated to, this URL will set the "current probe layout".

## `xcxtool compare`

Compare two savedata files for differences. By default, this will use the
primary gamedata and backup gamedata_ files in Cemu's nand root, but an
alternative folder can be specified in xcxtool.toml or on the command line.
Command line options can also be used to set specific files as the before
and/or after states.

The comparison is a simple naive byte-to-byte comparison and the output will
be quite verbose if there are significant changes between save states.

An alternative mode for this command is to directly monitor Cemu's process
memory for changes in real time, while optionally recording a gameplay via
OBS Studio. This will produce a simple log of changes in JSON format that
can be processed later.

For gameplay recording, OBS Studio must be installed, configured to record 
Cemu and must have the Websocket interface enabled, and must be running when 
the command is executed. OBS settings for xcxtool are described below.

### Configuration

Settings should be place in the `[compare]` table of xcxtool.toml.

* `save_directory` (`--save-dir`, `-s`): override the default save directory 
  to search for game data (defaults to the save data in Cemu's emulated nand).
* `before_file` (`--before`, `-b`: Use a specific file as the "before" state 
  in the comparison.
* `after_file` (`--after`, `-a`): Use a specific file as the "after" state 
  in the comparison.
* `include` (`--include`, `-i`): Define a subset or subsets of the save file 
  to be included in the comparison. By default the whole file is included, but 
  any value specified here will override the default so only the specified 
  ranges are compared.

  In the config file, this should be an array of arrays, each subarray being 
  a pair of integers. Each pair defines the beginning and end of a range within 
  the save file that  will be compared, relative to the start of the file. For 
  example:

  ```toml
  [compare]
  include = [
    # [start, end],
    [0x30, 0x100],
    [4056, 5098],
  ] 
  ```

  On the command line, the beginning and end values should be supplied as a comma 
  separated pair, the option can be specified multiple times to include multiple
  ranges. For example, the command below is equivalent to the config above:

  ```shell
  xcxtool compare --include 0x30,0x100 -i 4056,5098
  ```

* `exclude` (`--exclude`, `-x`): Define a set of ranges that should be
  excluded from the comparison. Exclusions are applied after inclusions, so
  they can be used to carve out exceptions in larger included ranges. The
  format of the config option and command line arguments is identical to
  `include`.
* `--append-ranges`, `-p`: The normal behaviour of command line arguments, 
  including `--include` and `--exclude`, is to completely replace the 
  equivalent config setting. By setting this flag, any `--include` or 
  `--exclude` arguments will be appended to the configured ranges, rather than 
  replacing them.
* `--monitor-cemu`, `-m` (no config file option): Continuously monitor Cemu 
  memory, 
  rather than comparing save files. In this mode, included/excluded ranges are 
  relative to the start of in-memory save data. This means that the results of 
  save data comparison and memory monitoring are directly comparable. Cemu 
  must already be running and emulating the game when this command is run,
  otherwise it will fail.
* `--record`, `-r`: Simultaneously record gameplay while monitoring using OBS 
  Studio. If `--monitor-cemu` is not set, this option will have no effect. As 
  noted above, OBS Studio must be installed, configured and running and have 
  the websocket server interface enabled.
* `obs_host` (`--obs-host`): Set the hostname of the OBS Websocket. Defaults 
  to `localhost`
* `obs_port` (`--obs-port`): Set the OBS websocket port. Default is 4455
* `obs_password` (`--obs-password`): Set the password to access the OBS 
  websocket interface.

[Cemu emulator]: https://cemu.info

[PyMem]: https://github.com/srounet/Pymem

[TOML]: https://toml.io/en/

[formatting]: https://docs.python.org/3/library/string.html#format-specification-mini-language

[xenoprobes]: https://github.com/minneyar/xenoprobes

[FrontierNav.net]: https://frontiernav.net/explore/xenoblade-chronicles-x
