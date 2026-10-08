# -*- coding: utf-8 -*-
"""
Custom method step management, parameter editing, JSON import/export routines.
"""

import datetime
import json
import os
import sys

from PyQt6 import QtCore, QtGui, QtWidgets
from phd_ultra.core.commands import (
    ICON_DICT,
    IMPORT_DICT_RENAME,
    LABEL_PATH_STEP_GUIDE_DICT,
)
from phd_ultra.config.logging import logger_info_console_file


def on_button_clicked(button, tab, ui, setups_dict_quick_mode: dict) -> dict:
    """Handle operation mode radio buttons switching."""
    setups_dict_quick_mode['Flow Parameter'] = ''
    setups_dict_quick_mode['Run Mode'] = ''
    tabs_name = ['Infusion', 'Withdraw', 'Param1', 'Param2']
    val = button.property('value')

    if val == 'INF':
        tab.setTabText(0, tabs_name[0])
        tab.setTabText(1, tabs_name[3])
        tab.setTabEnabled(0, True)
        tab.setTabEnabled(1, False)
        setups_dict_quick_mode['Run Mode'] = 'INF'
    elif val == 'WD':
        tab.setTabText(0, tabs_name[1])
        tab.setTabText(1, tabs_name[3])
        tab.setTabEnabled(0, True)
        tab.setTabEnabled(1, False)
        setups_dict_quick_mode['Run Mode'] = 'WD'
    elif val == 'INF/ WD':
        tab.setTabText(1, tabs_name[1])
        tab.setTabText(0, tabs_name[0])
        tab.setTabEnabled(1, True)
        tab.setTabEnabled(0, True)
        setups_dict_quick_mode['Run Mode'] = 'INF/ WD'
    elif val == 'WD/ INF':
        tab.setTabText(1, tabs_name[0])
        tab.setTabText(0, tabs_name[1])
        tab.setTabEnabled(1, True)
        tab.setTabEnabled(0, True)
        setups_dict_quick_mode['Run Mode'] = 'WD/ INF'
    else:
        tab.setTabText(0, tabs_name[2])
        tab.setTabText(1, tabs_name[3])
        tab.setTabEnabled(0, False)
        tab.setTabEnabled(1, False)
        setups_dict_quick_mode['Run Mode'] = 'Custom method'

    return setups_dict_quick_mode


def _get_item_index(list_widget, item):
    """Find index of item within duplicate items of the same type."""
    items = []
    item_text = item.text().split(".")[1].strip().split()[0]
    for index in range(list_widget.count()):
        item_index = list_widget.model().index(index, 0)
        item_rep = list_widget.itemFromIndex(item_index)
        item_rep_short = item_rep.text().split(".")[1].strip().split()[0]
        if item and item_rep_short == item_text:
            items.append(item_rep)
    selected_item_index = items.index(list_widget.currentItem())
    return len(items), selected_item_index


def add_to_list(item_text: str, item_icon, setups_dict_custom: dict, ui_list_widget) -> None:
    """Add a new method step to QListWidget and state dictionary."""
    count = ui_list_widget.count() + 1
    item = QtWidgets.QListWidgetItem()
    item.setIcon(QtGui.QIcon(item_icon))
    item.setText(f"{count}. {item_text}")

    item_short = item_text.split()[0]
    if item_short in setups_dict_custom:
        suffix = 1
        while f"{item_short}_{suffix}" in setups_dict_custom:
            suffix += 1
        item_short = f"{item_short}_{suffix}"
    setups_dict_custom[item_short] = ''
    ui_list_widget.addItem(item)


def delete_selected_item(list_widget, setups_dict_custom: dict, del_btn) -> None:
    """Delete selected step from QListWidget and state dictionary."""
    selected_item = list_widget.currentItem()
    if selected_item:
        row = list_widget.row(selected_item)
        key = selected_item.text().split(".")[1].strip()
        update_item_numbers(list_widget, setups_dict_custom, del_btn)
        update_setups_dict_custom(list_widget, setups_dict_custom, selected_item, key)
        list_widget.takeItem(row)


def update_item_numbers(list_widget, setups_dict_custom: dict, del_btn) -> None:
    """Renumber list widget items after deletion."""
    for i in range(list_widget.count()):
        item = list_widget.item(i)
        item.setText(f"{i + 1}. {item.text()[3:]}")
    del_btn.disconnect()
    del_btn.clicked.connect(lambda: delete_selected_item(list_widget, setups_dict_custom, del_btn))


def update_setups_dict_custom(list_widget, setups_dict_custom: dict, item, key_to_remove: str = None) -> None:
    """Update internal dictionary after step deletion."""
    len_items_same, selected_item_index = _get_item_index(list_widget, item)
    if not key_to_remove:
        return
    key_short = key_to_remove.split()[0]
    if len_items_same == 1 or (len_items_same > 1 and selected_item_index == 0):
        setups_dict_custom.pop(key_short, None)
    else:
        setups_dict_custom.pop(f"{key_short}_{selected_item_index}", None)


def edit_item_parameter(list_widget, ui_step_guide, setups_dict_custom: dict, item) -> None:
    """Open parameter guide dialog on double click to edit step parameters."""
    item_text = item.text().split(".")[1].strip().split()[0]
    len_items_same, current_index = _get_item_index(list_widget, item)

    if len_items_same == 1 or (len_items_same > 1 and current_index == 0):
        default_val = setups_dict_custom.get(item_text, '')
    else:
        default_val = setups_dict_custom.get(f"{item_text}_{current_index}", '')

    ui_step_guide.lineEdit.setText(default_val if default_val is not None else '')

    for label_path_key, label_path_value in LABEL_PATH_STEP_GUIDE_DICT.items():
        if label_path_key in item_text:
            img_resource = f":guide_/{label_path_value[1]}"
            ui_step_guide.pixmap = QtGui.QPixmap(img_resource)
            ui_step_guide.image_label.setPixmap(ui_step_guide.pixmap)
            ui_step_guide.image_label.setScaledContents(True)
            ui_step_guide.layout.addWidget(ui_step_guide.image_label)
            ui_step_guide.label.setText(label_path_value[0])
            ui_step_guide.groupBox.setTitle(label_path_key)
            ui_step_guide.exec()
            break

    if ui_step_guide.buttonBox.accepted:
        param = ui_step_guide.lineEdit.text().strip()
        if len_items_same == 1 or (len_items_same > 1 and current_index == 0):
            setups_dict_custom[item_text] = param
        else:
            setups_dict_custom[f"{item_text}_{current_index}"] = param


def print_setups_dict_custom(setups_dict_custom: dict) -> dict:
    """Normalize and format sequential keys in custom setup dictionary."""
    sorted_dict = {
        k: v for k, v in sorted(setups_dict_custom.items(), key=lambda item: list(setups_dict_custom.keys()).index(item[0]))
    }
    new_dict = {}
    counter_dict = {}
    for key in sorted_dict:
        prefix = key.split("_")[0]
        if prefix not in new_dict:
            new_dict[prefix] = sorted_dict[key]
            counter_dict[prefix] = 0
        else:
            counter_dict[prefix] += 1
            new_dict[f"{prefix}_{counter_dict[prefix]}"] = sorted_dict[key]

    logger_info_console_file.info(f"Custom setups: {new_dict}")
    return new_dict


# Alias for modern naming
renumber_steps = print_setups_dict_custom


def import_user_defined_methods(list_widget, setups_dict_custom: dict) -> dict:
    """Load user-defined steps JSON configuration from file."""
    setups_dict_custom.clear()
    file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
        list_widget, "Import User Defined Methods", "UserDefinedMethods", "JSON files (*.json)"
    )
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                imported_dict = json.load(f)
            if isinstance(imported_dict, dict):
                imported_dict = print_setups_dict_custom(imported_dict)
                for key, value in imported_dict.items():
                    setups_dict_custom[key] = value
                update_list_widget(list_widget, setups_dict_custom)
                return setups_dict_custom
        except Exception as e:
            QtWidgets.QMessageBox.information(list_widget, 'Invalid import', str(e))
            logger_info_console_file.error(f"Import error: {e}")
    return setups_dict_custom


def update_list_widget(list_widget, setups_dict_custom: dict) -> None:
    """Repopulate QListWidget after importing custom steps."""
    list_widget.model().removeRows(0, list_widget.model().rowCount())
    for i, (key, value) in enumerate(setups_dict_custom.items()):
        icon_path = f":/icon_/{list(ICON_DICT.keys())[0]}"
        for icon_name, key_str in ICON_DICT.items():
            if key_str in key:
                icon_path = f":/icon_/{icon_name}"
                break
        key_list_widget = key.split("_")[0]
        label_text = IMPORT_DICT_RENAME.get(key_list_widget, key_list_widget)
        item = QtWidgets.QListWidgetItem(QtGui.QIcon(icon_path), f"{i + 1}. {label_text}")
        list_widget.addItem(item)


def export_user_defined_methods(ui, setups_dict_custom: dict) -> None:
    """Export current custom steps dictionary to timestamped JSON file."""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    save_path = os.path.join(base_path, "UserDefinedMethods")
    os.makedirs(save_path, exist_ok=True)

    current_time = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    filename = f"Method_{current_time}.json"
    filepath = os.path.join(save_path, filename)

    if setups_dict_custom:
        print_setups_dict_custom(setups_dict_custom)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(setups_dict_custom, f, indent=4)

            msgBox = QtWidgets.QMessageBox(ui.userDefined_Export)
            msgBox.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
            msgBox.setWindowTitle('Information')
            msgBox.setText("Custom method has been successfully exported.")
            icon_msgBox = QtGui.QPixmap(":green_tick_/green_tick.png").scaled(
                32, 32, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation
            )
            msgBox.setIconPixmap(icon_msgBox)
            msgBox.setDetailedText(f"File: {filename}\r\nPath: {filepath}.")
            msgBox.setDefaultButton(msgBox.StandardButton.Ok)
            msgBox.exec()
        except Exception as e:
            logger_info_console_file.error(f"Export error: {e}")


def reset_all_config(ui) -> None:
    """Reset radio buttons in main window."""
    ui.radioButton_1.setChecked(False)
    ui.radioButton_2.setChecked(False)
    ui.radioButton_3.setChecked(False)
    ui.radioButton_4.setChecked(False)
    ui.radioButton_5.setChecked(False)


def fast_btn_timer_start(timer):
    timer.start(200)


def fast_btn_timer_stop(timer):
    timer.stop()


def rwd_btn_timer_start(timer):
    timer.start(200)


def rwd_btn_timer_stop(timer):
    timer.stop()
