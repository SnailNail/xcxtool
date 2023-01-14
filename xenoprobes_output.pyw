#!miscvenvw
"""Script to transform output of Xenoprobes to a standard form to past into
a spreadsheet

Output structure:
    [bunch of setup stuff
    Iteration 1 of x...
    ...
    Probe configuration:
    FN 101 : Mining G1
    FN 102 : ...
    
    FN 201 : ...
    ...
    # Miranium: x
    # Revenue: y
    # Storage: z
    # Ores (x/15)
    #  Arc Sand Ore
    #  ...
    # Best score: n
"""
import io
from typing import Tuple, Mapping

PROBE_SITES = {
    # Primordia
    "FN 101": "None", "FN 102": "None", "FN 103": "None", "FN 104": "None", "FN 105": "None",
    "FN 106": "None", "FN 107": "None", "FN 108": "None", "FN 109": "None", "FN 110": "None",
    "FN 111": "None", "FN 112": "None", "FN 113": "None", "FN 114": "None", "FN 115": "None",
    "FN 116": "None", "FN 117": "None", "FN 118": "None", "FN 119": "None", "FN 120": "None",
    "FN 121": "None",
    # Noctilum
    "FN 201": "None", "FN 202": "None", "FN 203": "None", "FN 204": "None", "FN 205": "None",
    "FN 206": "None", "FN 207": "None", "FN 208": "None", "FN 209": "None", "FN 210": "None",
    "FN 211": "None", "FN 212": "None", "FN 213": "None", "FN 214": "None", "FN 215": "None",
    "FN 216": "None", "FN 217": "None", "FN 218": "None", "FN 219": "None", "FN 220": "None",
    "FN 221": "None", "FN 222": "None", "FN 223": "None", "FN 224": "None", "FN 225": "None",
    # Oblivia
    "FN 301": "None", "FN 302": "None", "FN 303": "None", "FN 304": "None", "FN 305": "None",
    "FN 306": "None", "FN 307": "None", "FN 308": "None", "FN 309": "None", "FN 310": "None",
    "FN 311": "None", "FN 312": "None", "FN 313": "None", "FN 314": "None", "FN 315": "None",
    "FN 316": "None", "FN 317": "None", "FN 318": "None", "FN 319": "None", "FN 320": "None",
    "FN 321": "None", "FN 322": "None",
    # Sylvalum
    "FN 401": "None", "FN 402": "None", "FN 403": "None", "FN 404": "None", "FN 405": "None",
    "FN 406": "None", "FN 407": "None", "FN 408": "None", "FN 409": "None", "FN 410": "None",
    "FN 411": "None", "FN 412": "None", "FN 413": "None", "FN 414": "None", "FN 415": "None",
    "FN 416": "None", "FN 417": "None", "FN 418": "None", "FN 419": "None", "FN 420": "None",
    # Cauldros
    "FN 501": "None", "FN 502": "None", "FN 503": "None", "FN 504": "None", "FN 505": "None",
    "FN 506": "None", "FN 507": "None", "FN 508": "None", "FN 509": "None", "FN 510": "None",
    "FN 511": "None", "FN 512": "None", "FN 513": "None", "FN 514": "None", "FN 515": "None",
    "FN 516": "None",
}

RESOURCES = {
    "Arc Sand Ore": "No",
    "Aurorite": "No",
    "Boiled-Egg Ore": "No",
    "Bonjelium": "No",
    "Cimmerian Cinnabar": "No",
    "Dawnstone": "No",
    "Enduron Lead": "No",
    "Everfreeze Ore": "No",
    "Foucaultium": "No",
    "Infernium": "No",
    "Lionbone Bort": "No",
    "Marine Rutile": "No",
    "Ouroboros Crystal": "No",
    "Parhelion Platinum": "No",
    "White Cometite": "No",
}

META = {
    "Miranium": 0,
    "Revenue": 0,
    "Storage": 0,
    "Best score": 0,
}

TEMPLATE = """\
{miranium}
{revenue}
{storage}
{score}
{ores}
{probes}
"""


def process_input(xprobes_output: str):
    """Iterate the lines of xprobes_output, processing each according to its content"""
    lines = io.StringIO(xprobes_output)
    probes = PROBE_SITES.copy()
    resources = RESOURCES.copy()
    meta = META.copy()
    
    # "Seek" to the probe config lines
    for line in lines:
        if line.startswith("Probe configuration"):
            break

    for line in lines:
        if line.startswith("FN"):
            site, _, probe = split_n_strip(line)
            probes[site] = probe
            continue
        elif line.startswith("#"):
            key, sep, value = split_n_strip(line[1:])
        else:
            continue
        if sep == "":
            resources[key] = "Yes"
            continue
        if value == "":
            continue
        else:
            meta[key] = int(value)

    return {"probes": probes, "resources": resources, "meta": meta}


def split_n_strip(text: str) -> Tuple[str, str, str]:
    """Split a line at a colon and return the parts stripped of whitespace"""
    k, s, v = text.partition(":")
    return k.strip(), s, v.strip()


def format_probes(probes_dict: Mapping[str, str]) -> str:
    """Format the probe sites list"""
    return "\n".join(probes_dict.values())


if __name__ == '__main__':
    import PySimpleGUI as sg
    import pyperclip
    layout = [
        [sg.Text('Paste the output from Xenoprobes here '
                 '(make sure to include the "Probes configuration" line):')],
        [sg.Multiline(key="input")],
        [sg.Button('Copy'), sg.Button('Exit')],
    ]
    window = sg.Window("Xenoprobes output formatter", layout)
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            break
        if event == "Copy":
            data = process_input(values["input"])
            # pprint.pprint(data)
            text = TEMPLATE.format(
                miranium=data['meta']['Miranium'],
                revenue=data['meta']['Revenue'],
                storage=data['meta']['Storage'],
                score=data['meta']['Best score'],
                ores=format_probes(data["probes"]),
                probes=format_probes(data["resources"])
            )
            pyperclip.copy(text)

    window.close()
