The functions in the ``xcxtool.data.load_json`` module are used to help 
generate the data files in the other ``xcxtool.data.*`` modules. The 
functions rely on JSON data dumps certain tables from the ``common_local_us.bdat``
and ``common_ms.bdat`` data files being available in this folder.

These dumps are not included in the Git repository, so you will need to extract 
them from the game data yourself if you want to use the load_data functions. 
The tool used to convert BDAT tables to JSON was [XbTool]; other tools may 
not produce the same expected JSON structure.

The as a minimum, the following tables need to be dumped:

### ``common_local_us.bdat``
  * FLD_Location
  * FnetVeinList
  * ITM_BeaconList

### ``common_ms.bdat``
  * fieldnamelist_ms
  * FNT_VeinList_ms
  * ITM_BeaconList_ms

[xbtool]: <https://github.com/AlexCSDev/XbTool>