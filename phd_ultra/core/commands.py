# -*- coding: utf-8 -*-
"""
Harvard Apparatus PHD Ultra Serial Commands and Protocol Definitions.
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMMANDS_JSON_PATH = os.path.join(BASE_DIR, "json", "commands.json")


def load_commands_json() -> dict:
    """Load the commands database JSON file."""
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = BASE_DIR

    path = os.path.join(base_path, "json", "commands.json")
    if not os.path.exists(path):
        # Fallback to current directory
        path = "json/commands.json"

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


ICON_DICT = {
    "const_icon.png": "Constant",
    "ramp_icon.png": "Ramp",
    "stepped_icon.png": "Stepped",
    "pulse_icon.png": "Pulse",
    "bolus_icon.png": "Bolus",
    "concentration_icon.png": "Concentration",
    "gradient_icon.png": "Gradient",
    "autofill_icon.png": "Autofill",
}

LABEL_PATH_STEP_GUIDE_DICT = {
    "Constant": ["Format: INF|WD, rate, units, target(t/v)", "const_param.png"],
    "Ramp": ["Format: INF|WD, rate r<sub>start</sub>, rate r<sub>end</sub>, target t", "ramp_param.png"],
    "Stepped": ["Format: INF|WD, rate [r<sub>1</sub>, r<sub>2</sub>], target [t, steps]", "stepped_param.png"],
    "Pulse": ["Format: INF|WD, rate [r<sub>1</sub>, r<sub>2</sub>], [v<sub>1</sub>, v<sub>2</sub>]| [t<sub>1</sub>, t<sub>2</sub>], pulses", "pulse_param.png"],
    "Bolus": ["Format: target t, target v", "bolus_param.png"],
    "Concentration": ["Format: weight, rate, concentration[%], Dose|time lag", "concentration_param.png"],
    "Gradient": ["Format: total rate, [addr.1-[%], addr.2-[%]...] , time|steps", "gradient_param.png"],
    "Autofill": ["Format: INF/WD| WD/INF, [r<sub>1</sub>, r<sub>2</sub>], v per Cyc, total v/ Cyc", "autofill_param.png"],
}

LABEL_STEP_GUIDE_DICT = {
    "Constant": "Format: INF|WD, rate, units",
    "Ramp": "Format: INF|WD, rate [r<sub>1</sub>, r<sub>2</sub>], target t",
    "Stepped": "Format: INF|WD, rate [r<sub>1</sub>, r<sub>2</sub>], target [t, steps]",
    "Pulse": "Format: INF|WD, rate [r<sub>1</sub>, r<sub>2</sub>], [v<sub>1</sub>, v<sub>2</sub>]| [t<sub>1</sub>, t<sub>2</sub>], pulses",
    "Bolus": "Format: target t, target v",
    "Concentration": "Format: weight, rate, concentration[%], Dose|time lag",
    "Gradient": "Format: total rate, [addr.1-[%], addr.2-[%]...] , time|steps",
    "Autofill": "Format: INF/WD| WD/INF, [r<sub>1</sub>, r<sub>2</sub>], v per Cyc, total v/ Cyc",
}

IMPORT_DICT_RENAME = {
    "Constant": "Constant rate",
    "Ramp": "Ramp rate",
    "Stepped": "Stepped rate",
    "Pulse": "Pulse flow",
    "Bolus": "Bolus delivery",
    "Concentration": "Concentration delivery",
    "Gradient": "Gradient",
    "Autofill": "Autofill",
}
