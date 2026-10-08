# -*- coding: utf-8 -*-
"""
Syringe library and specification helpers for Harvard Apparatus PHD Ultra.
"""

from PyQt6 import QtCore, QtGui, QtWidgets
from phd_ultra.core.commands import load_commands_json
from phd_ultra.config.logging import logger_debug_console

_SYRINGE_CACHE = None


def get_syringe_dict() -> dict:
    """
    Parse and return the syringe catalog dictionary from commands.json.
    Caches the parsed result in memory.
    """
    global _SYRINGE_CACHE
    if _SYRINGE_CACHE is not None:
        return _SYRINGE_CACHE

    commands = load_commands_json()
    syringe_list = commands.get("Syringe list", {})
    syringe_dic = {}

    for syrm_info in syringe_list.values():
        if "description" in syrm_info and "size" in syrm_info:
            syringe_dic[syrm_info["description"]] = list(syrm_info["size"].values())

    _SYRINGE_CACHE = syringe_dic
    return _SYRINGE_CACHE


# Backward-compatible alias
Get_syringe_dict = get_syringe_dict
SYRINGE_DATA = get_syringe_dict()
LIMIT_FORCE_LEVEL_DICT = {}



def init_combox_syrSize(ui, setups_dict_quick_mode: dict) -> None:
    """Initialize syringe manufacturer and size combo boxes."""
    ui.comboBox_syrManu.clear()
    ui.comboBox_syrSize.clear()
    ui.comboBox_syrManu.currentTextChanged.connect(
        lambda: update_combox_syrSize(ui.comboBox_syrManu.currentText(), setups_dict_quick_mode, ui)
    )
    ui.comboBox_syrManu.currentTextChanged.connect(
        lambda: get_min_max_limit(ui, get_syringe_dict().get(ui.comboBox_syrManu.currentText(), []))
    )
    ui.comboBox_syrManu.currentTextChanged.connect(lambda: force_level_recommendation(ui))


def update_combox_syrSize(text: str, setups_dict_quick_mode: dict, ui) -> None:
    """Update size combo box when manufacturer changes."""
    selected_values = get_syringe_dict().get(text, [])
    list_items = [sublist[0] for sublist in selected_values]
    ui.comboBox_syrSize.clear()
    ui.comboBox_syrSize.addItems(list_items)
    setups_dict_quick_mode['Syringe Info'] = {'Selected Syringe': ui.comboBox_syrSize.currentText()}

    ui.comboBox_syrSize.currentTextChanged.connect(lambda: get_min_max_limit(ui, selected_values))
    ui.comboBox_syrSize.currentTextChanged.connect(lambda: clear_previous_limit(ui))
    ui.comboBox_syrSize.currentTextChanged.connect(lambda: force_level_recommendation(ui))


def clear_previous_limit(ui) -> None:
    """Clear flow rate input boxes."""
    ui.param_flowRate_1.setText('')
    ui.param_flowRate_2.setText('')


def get_min_max_limit(ui, selected_values: list):
    """Return the lower, upper flow limit and recommended force level for selected syringe."""
    matching_sublist = None
    for sublist in selected_values:
        if ui.comboBox_syrSize.currentText() == sublist[0]:
            matching_sublist = sublist
            break

    if matching_sublist is not None:
        list_lower_limit = matching_sublist[1]
        list_upper_limit = matching_sublist[2]
        max_force_level = matching_sublist[3]
    else:
        list_lower_limit = None
        list_upper_limit = None
        max_force_level = None

    if list_lower_limit and list_upper_limit and max_force_level:
        ui.forceLimit_Slider.setValue(int(max_force_level))
        return list_lower_limit, list_upper_limit, max_force_level
    return None, None, None


def set_max_min_flow_rate(ui, sender_button) -> None:
    """Set min or max flow rate into input fields based on sender button."""
    flow_min, flow_max, force_level = get_min_max_limit(
        ui, get_syringe_dict().get(ui.comboBox_syrManu.currentText(), [])
    )
    if not flow_min or not flow_max:
        return

    param_flow_min, unit_flow_min = flow_min.split()[0], flow_min.split()[1]
    param_flow_max, unit_flow_max = flow_max.split()[0], flow_max.split()[1]

    if sender_button == ui.flow_lower_button_1:
        if ui.comboBox_syrSize:
            ui.param_flowRate_1.setText(param_flow_min)
            if ui.comboBox_unit_frate_1.findText(unit_flow_min) != -1:
                ui.comboBox_unit_frate_1.setCurrentText(unit_flow_min)
    elif sender_button == ui.flow_lower_button_2:
        if ui.comboBox_syrSize:
            ui.param_flowRate_2.setText(param_flow_min)
            if ui.comboBox_unit_frate_2.findText(unit_flow_min) != -1:
                ui.comboBox_unit_frate_2.setCurrentText(unit_flow_min)
    elif sender_button == ui.flow_upper_button_1:
        if ui.comboBox_syrSize:
            ui.param_flowRate_1.setText(param_flow_max)
            if ui.comboBox_unit_frate_1.findText(unit_flow_max) != -1:
                ui.comboBox_unit_frate_1.setCurrentText(unit_flow_max)
    elif sender_button == ui.flow_upper_button_2:
        if ui.comboBox_syrSize:
            ui.param_flowRate_2.setText(param_flow_max)
            if ui.comboBox_unit_frate_2.findText(unit_flow_max) != -1:
                ui.comboBox_unit_frate_2.setCurrentText(unit_flow_max)


def force_level_recommendation(ui, force_level=None):
    """Display recommended force level tooltip."""
    matching_sublist = None
    selected_values = get_syringe_dict().get(ui.comboBox_syrManu.currentText(), [])
    for sublist in selected_values:
        if ui.comboBox_syrSize.currentText() == sublist[0]:
            matching_sublist = sublist
            break
    if matching_sublist:
        force_level = matching_sublist[3]
    else:
        force_level = None

    QtWidgets.QToolTip.setFont(QtGui.QFont('Open Sans Medium', 10))
    if ui.comboBox_syrSize.isEnabled():
        if isinstance(force_level, (int, float)):
            ui.comboBox_syrSize.setToolTip(
                f"<font color='#646464' style='max-width:200px; white-space:nowrap;'>"
                f"Recommended force level: {force_level} %</font>"
            )
            return force_level
        else:
            ui.comboBox_syrSize.setToolTip(
                f"<font color='#646464' style='max-width:200px; white-space:nowrap;'>"
                f"No maximum force limit recommended.</font>"
            )
            return None


def update_combox_syr_enabled(ui, setups_dict_quick_mode: dict) -> dict:
    """Toggle between preset syringe catalog and custom syringe dimension input."""
    if ui.syr_param_enter.text() != '':
        setups_dict_quick_mode['Syringe Info'] = {'Selected Syringe': ui.syr_param_enter.text()}
        ui.comboBox_syrManu.setEnabled(False)
        ui.comboBox_syrSize.setEnabled(False)
    else:
        setups_dict_quick_mode['Syringe Info'] = {'Selected Syringe': ui.comboBox_syrSize.currentText()}
        ui.comboBox_syrManu.setEnabled(True)
        ui.comboBox_syrSize.setEnabled(True)
    return setups_dict_quick_mode
