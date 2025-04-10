# Gamedata

This document is an incomplete description of the main gamedata save file for 
Xenoblade Chronicles X. Addresses and offsets are given relative to the start 
of the file unless otherwise specified

<!-- TOC -->
* [Gamedata](#gamedata)
  * [Preamble](#preamble)
  * [Player Character data](#player-character-data)
  * [Scout character data](#scout-character-data)
  * [Skell data](#skell-data)
  * [Player class progression](#player-class-progression)
  * [Currencies](#currencies)
  * [Party composition](#party-composition)
  * [Inventory](#inventory)
  * [Found locations](#found-locations)
  * [BLADE state](#blade-state)
  * [Affinity players](#affinity-players)
  * [FrontierNav timers](#frontiernav-timers)
  * [Probe placements](#probe-placements)
  * [Field Skills](#field-skills)
  * [Holofigures](#holofigures)
  * [Engineer Augments (Weapon and Armour) menu state](#engineer-augments-weapon-and-armour-menu-state)
  * [Engineer Augments (Skell Weapon, armour and frame) menu state](#engineer-augments-skell-weapon-armour-and-frame-menu-state)
  * [Enemy index](#enemy-index)
  * [Info](#info)
  * [Arms manufacturer state](#arms-manufacturer-state)
<!-- TOC -->

## Preamble
`0x10 - 0x57`, 4 + 68 = 72 bytes

Immediately following the header at 0x10, there is a 4-byte integer with the 
value 218,499 (0x00035772), or 219,035 (0x9b570300) for XCX DE. This is 
followed a sixty-four byte string buffer containing the player character's name.

## Player Character data
`0x58 - 0x688b`, 19 × 1,440 = 26,676 bytes

Each playable character is represented by a 1,404 byte structure which holds 
the common character specific data:
* Name
* Appearance
* Level
* Experience
* Equipment and fashion gear
* Soul voices
* HP
* BP
* Arts and Skills levels
* Affinity points and affinity level (non avatar characters only)
* Assigned skell

## Scout character data
`0x6890 - 0x6eef`, 3 × 544 = 1,632 bytes

If the player has recruited any scouts into their party, the scout characters 
will be stored here. Scout characters are represent by a smaller version of 
the character structure. Since the WiiU online service shut down I haven't 
had access to scouts to analyze, but from what I can see structure records 
at least the following fields:
* Display name
* Appearance
* Equipment and fashion gear
* Public greeting
* Personal greeting
* Personal name

## Skell data
`0x6ef0 - 0xC16f`, 60 × 372 = 22,320 bytes

Records skells that the player owns. The Ares 90 is just another skell in 
this list, its properties come from the game's data files not its 
representation in the save data. Known properties:
* Name
* Equipped gear (including the frame)
* Appearance (colours)
* HP
* Index in the skell list
* Remaining insurance
* State (destroyed)
* Finsh (matte or not)

## Player class progression
`0xc620` - `0xc81d`, 17 × 30 = 510 bytes

Since the player can be any of 16 classes, each with its own level of 
progression, and the player's character data only has room for the 
particular assigned class, the game needs to store the player's progression 
in other classes somewhere, and this is that somewhere.

Each member of this array records the rank, class exp, assigned arts and 
assigned skills for a particular class (the same data structure is used in 
the character struct to record the assigned class). The member's index in 
the array corresponds to a row in the CHR_ClassInfo BDAT table, with the 
first (index 0) being a dummy or null member.

## Currencies
`0xc820` - `0xc82b`, 3 × 4 = 12 bytes

These three integers keep track of the three currencies that player 
can spend in shops: credits, miranium and reward tickets.

## Party composition
`0xc82c` - `0xc84b`, 4 × 8 = 32 bytes

Describes the composition and order of the current party. Each 8-byte 
structure describes the character type (player avatar, other main character 
or scout), the index into the relevant array for that character, and the skell 
assigned to the character.

## Inventory
`0xc850` - `0x3247f` (154,672 bytes)

The player's inventory takes up almost half the save file. It consists of 13 
fixed size arrays holding either equipment type structures (24 bytes each) 
or item type structures (12 bytes each):
* Skell armour (999 × 24 = 23,976 bytes)
* Skell weapons (999 × 24 bytes)
* Ground armour (999 × 24 bytes)
* Melee weapons (999 × 24 bytes)
* Ranged weapons (999 × 24 bytes)
* Augments (999 × 12 = 11,988 bytes)
* Materials (800 × 12 = 9,600 bytes)
* Probes (100 × 12 = 1,200 bytes)
* Collectables (300 × 12 = 3600 bytes)
* Important items (50 × 24 = 6,000 bytes)
* \[unknown items\] (50 × 24 = 1,200 bytes)
* Precious resources (50 × 12 = 600 bytes)
* Consumables (battle items) (50 × 12 = 600 bytes)

## Found locations
`0x32658 - 0x3269d` (70 bytes)

Annoying bitfields

## BLADE state
`0x39108 - 0x3917f` (120 bytes)
Public & personal greeting, BLADE points, BLADE level

## Affinity players
`0x39540` - `0x45d3f`, 100 * 512 = 51,200 bytes

## FrontierNav timers
`0x480c0` - `0x480c3`

## Probe placements
`0x480c4` - `0x48273`, 144 × 3 = 432 bytes

## Field Skills
`0x48ac8 - 0x48aca`, 3 bytes

## Holofigures
`0x48ad0 - 0x 48eb7`, 1000 bytes

Correlates with ITM_FigList

## Engineer Augments (Weapon and Armour) menu state
`0x4c6d4 - 0x4d527`, 3668 bytes

Correlates with BTL_ItemSkill_inner

## Engineer Augments (Skell Weapon, armour and frame) menu state
`0x4d674 - 0xe2a1`, 3118 bytes

Correlates with BTL_ItemSkill_doll

## Enemy index
`0x4e614 - 0x527e3`, 12 × 1,404 = 16,848 bytes

Completion, number slain, defeated by. Correlates with BTL_EnBook

## Info
`0x572c0 - 0x57bdf`. 4 × 584 = 2,336 bytes

Four-byte integers for some reason, 1 = new, 2 = seen. Correlates to 
ITM_InfoList

## Arms manufacturer state
`0x57db0 - 0x57e2f`, 8 × 16 = 128 bytes

Level, research points, pending research points, level completion percent?
