# Gamedata

This document is an incomplete description of the main gamedata save file for 
Xenoblade Chronicles X. Addresses and offsets are given relative to the start 
of the file unless otherwise specified

## Preamble
`0x10 - 0x58`

Immediately following the header at 0x10, there is a 4-byte integer with the 
value 218,499 (0x00035772), or 219,035 (0x9b570300) for XCX DE. This is 
followed a sixty-four byte string buffer containing the player character's name.
