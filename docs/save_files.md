# Save File Information

This file documents the common format of Xenoblade Chronicles X (XCX) save 
files, based on my own research. It is not a complete description of the save 
file by any stretch. For the most part, information has been gathered by 
playing the game and seeing what changes. 

The information-gathering process is helped by the fact that the game loads all
save data into memory at boot and writes to it as the game is played. This 
makes it possible to monitor changes in real time using something like 
CheatEngine, or pymem with some custom scripts.

Much of what is below will broadly apply to save files for the 
Definitive Edition of the game, but precise locations, offsets and data
structures are quite different.

## Save data files
Xenoblade Chronicles X stores saved data across several data files. The 
original WiiU version only allows one save slot, and keeps backups of the 
last-saved version of each data file. The backups have the same name as the live
file with and underscore appended.

The Switch DE version of the game has three save slots and does not seem to 
keep backups.

  * `gamedata`: This is the main save data file. It contains all the character 
    data, skell, weapon and item inventories, and most of the game state.
    * XCX DE has three gamedata files named `gamedata01`, `gamedata02` and 
      `gamedata03`, corresponding to the three manual save slots. There is 
      also an autosave named `gamedataa`. As far as I can tell these are all 
      full save files with the same format. gamedata is the only file that has 
      multiple versions on DE, other data and settings are shared between save 
      slots
  * `socialdata`: This file stores achievements and possibly other data.
  * `systemdata`: stores the various game, camera and system settings.
  * `avatarmakedata`: stores the player character avatars that are saved during 
    character creation or using Yardley's lifepod.

In addition to the above, the Definitive Edition has four `*.tmb` files with the 
same name as the gamedata files. These are the thumbnail screenshots that are 
displayed in the load and save data screens.

## Encryption
Each data file is encrypted using a simple [XOR cipher] with a 512 byte key. 
The key is applied repeatedly without variation over the entire length of the 
file (including the 16 byte header). Since the key repeats every 512 bytes and 
the gamedata file is both much larger and sparsely populated, it is trivial to
determine the key from this file as there are several regions where the raw 
key is exposed.

The same key is used for all the data files saved at the same time, and is
different for files saved at different times. It is my guess that the second 4 
bytes of the header is used by the game to somehow determine the encryption 
key for a given save file.

## Save data file format
Data is stored in a binary format (really, several binary formats in the case 
of the gamedata file). Multi-byte values are stored with the same endianess as 
the game's system, so big-endian on the WiiU version and little-endian on the 
Switch version.

Each file has a 16-byte header consisting of four 4-byte integers. The first 
and third values of the header are different for every save file and seem to 
be some kind of checksum value that validates the rest of the data file. The 
second value is always 1, and the fourth value is the size of the following
data (i.e. the file size - 16 bytes for the header).

The data following the header can be pretty much anything, and the structure is 
different for each of the save data files.


[XOR cipher]: https://en.wikipedia.org/wiki/XOR_cipher