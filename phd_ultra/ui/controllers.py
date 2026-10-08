# -*- coding: utf-8 -*-
"""UI controller and event handling logic for PHD Ultra Remote Control GUI."""

import logging
from PyQt6 import QtCore, QtGui, QtWidgets

from phd_ultra.database.syringes import Get_syringe_dict
from phd_ultra.utils.validators import user_input_range_validate, is_number_and_positive
from phd_ultra.utils.method_io import (
    renumber_steps,
    export_user_defined_methods,
    import_user_defined_methods,
)
import resources_rc

logger = logging.getLogger("logger2")

STEP_GUIDE_CONFIG = {
    "Constant": ["Format: INF|WD, rate, units, target(t/v)", "const_param.png"],
    "Ramp": ["Format: INF|WD, rate r<sub>start</sub>, rate r<sub>end</sub>, target t", "ramp_param.png"],
    "Stepped": ["Format: INF|WD, rate [r<sub>1</sub>, r<sub>2</sub>], target [t, steps]", "stepped_param.png"],
    "Pulse": ["Format: INF|WD, rate [r<sub>1</sub>, r<sub>2</sub>], [v<sub>1</sub>, v<sub>2</sub>]| [t<sub>1</sub>, t<sub>2</sub>], pulses", "pulse_param.png"],
    "Bolus": ["Format: target t, target v", "bolus_param.png"],
    "Concentration": ["Format: weight, rate, concentration[%], Dose|time lag", "concentration_param.png"],
    "Gradient": ["Format: total rate, [addr.1-[%], addr.2-[%]...] , time|steps", "gradient_param.png"],
    "Autofill": ["Format: INF/WD| WD/INF, [r<sub>1</sub>, r<sub>2</sub>], v per Cyc, total v/ Cyc", "autofill_param.png"],
}


def on_button_clicked(button, tab, ui, setups_dict_quick_mode: dict) -> dict:
    """Handle radio button selection for Quick Mode run mode."""
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


def init_combox_syrSize(ui, setups_dict_quick_mode: dict):
    """Initialize syringe selection combo boxes."""
    ui.comboBox_syrManu.clear()
    ui.comboBox_syrSize.clear()
    ui.comboBox_syrManu.currentTextChanged.connect(
        lambda: update_combox_syrSize(ui.comboBox_syrManu.currentText(), setups_dict_quick_mode, ui)
    )
    ui.comboBox_syrManu.currentTextChanged.connect(
        lambda: get_min_max_limit(ui, Get_syringe_dict().get(ui.comboBox_syrManu.currentText(), []))
    )
    ui.comboBox_syrManu.currentTextChanged.connect(lambda: force_level_recommendation(ui))


def update_combox_syrSize(text: str, setups_dict_quick_mode: dict, ui):
    """Update available sizes when syringe manufacturer changes."""
    selected_values = Get_syringe_dict().get(text, [])
    list_items = [sublist[0] for sublist in selected_values]
    ui.comboBox_syrSize.clear()
    ui.comboBox_syrSize.addItems(list_items)
    setups_dict_quick_mode['Syringe Info'] = {'Selected Syringe': ui.comboBox_syrSize.currentText()}
    ui.comboBox_syrSize.currentTextChanged.connect(lambda: get_min_max_limit(ui, selected_values))
    ui.comboBox_syrSize.currentTextChanged.connect(lambda: clear_previous_limit(ui))
    ui.comboBox_syrSize.currentTextChanged.connect(lambda: force_level_recommendation(ui))


def clear_previous_limit(ui):
    """Clear flow rate input fields."""
    ui.param_flowRate_1.setText('')
    ui.param_flowRate_2.setText('')


def get_min_max_limit(ui, selected_values: list):
    """Retrieve min/max flow rate limits and recommended force level for selected syringe."""
    matching_sublist = None
    for sublist in selected_values:
        if ui.comboBox_syrSize.currentText() == sublist[0]:
            matching_sublist = sublist
            break

    if matching_sublist:
        list_lower_limit = matching_sublist[1]
        list_upper_limit = matching_sublist[2]
        max_force_level = matching_sublist[3]
        if list_lower_limit and list_upper_limit and max_force_level is not None:
            try:
                ui.forceLimit_Slider.setValue(int(max_force_level))
            except (ValueError, TypeError):
                pass
            return list_lower_limit, list_upper_limit, max_force_level
    return None, None, None


def set_max_min_flow_rate(ui, sender_button):
    """Set maximum or minimum allowable flow rate into input fields."""
    flow_min, flow_max, _ = get_min_max_limit(ui, Get_syringe_dict().get(ui.comboBox_syrManu.currentText(), []))
    if not flow_min or not flow_max:
        return

    param_flow_min, unit_flow_min = flow_min.split()[0], flow_min.split()[1]
    param_flow_max, unit_flow_max = flow_max.split()[0], flow_max.split()[1]

    if sender_button == ui.flow_lower_button_1:
        ui.param_flowRate_1.setText(param_flow_min)
        if ui.comboBox_unit_frate_1.findText(unit_flow_min) != -1:
            ui.comboBox_unit_frate_1.setCurrentText(unit_flow_min)
    elif sender_button == ui.flow_lower_button_2:
        ui.param_flowRate_2.setText(param_flow_min)
        if ui.comboBox_unit_frate_2.findText(unit_flow_min) != -1:
            ui.comboBox_unit_frate_2.setCurrentText(unit_flow_min)
    elif sender_button == ui.flow_upper_button_1:
        ui.param_flowRate_1.setText(param_flow_max)
        if ui.comboBox_unit_frate_1.findText(unit_flow_max) != -1:
            ui.comboBox_unit_frate_1.setCurrentText(unit_flow_max)
    elif sender_button == ui.flow_upper_button_2:
        ui.param_flowRate_2.setText(param_flow_max)
        if ui.comboBox_unit_frate_2.findText(unit_flow_max) != -1:
            ui.comboBox_unit_frate_2.setCurrentText(unit_flow_max)


def force_level_recommendation(ui, force_level=None):
    """Display recommended force level tooltip."""
    selected_values = Get_syringe_dict().get(ui.comboBox_syrManu.currentText(), [])
    matching_sublist = None
    for sublist in selected_values:
        if ui.comboBox_syrSize.currentText() == sublist[0]:
            matching_sublist = sublist
            break

    if matching_sublist:
        force_level = matching_sublist[3]

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
                "<font color='#646464' style='max-width:200px; white-space:nowrap;'>"
                "No maximum force limit recommended.</font>"
            )
            return None


def update_combox_syr_enabled(ui, setups_dict_quick_mode: dict):
    """Toggle predefined syringe selector vs custom syringe geometry."""
    if ui.syr_param_enter.text().strip():
        setups_dict_quick_mode['Syringe Info'] = {'Selected Syringe': ui.syr_param_enter.text().strip()}
        ui.comboBox_syrManu.setEnabled(False)
        ui.comboBox_syrSize.setEnabled(False)
    else:
        setups_dict_quick_mode['Syringe Info'] = {'Selected Syringe': ui.comboBox_syrSize.currentText()}
        ui.comboBox_syrManu.setEnabled(True)
        ui.comboBox_syrSize.setEnabled(True)
    return setups_dict_quick_mode


def Quick_mode_param_run(ui, setups_dict_quick_mode: dict):
    """Validate Quick Mode inputs and populate configuration dictionary."""
    flow_min, flow_max, _ = get_min_max_limit(ui, Get_syringe_dict().get(ui.comboBox_syrManu.currentText(), []))
    run_mode = setups_dict_quick_mode.get('Run Mode')

    if run_mode == 'INF':
        if not ui.param_flowRate_1.text() or not ui.param_target_1.text():
            setups_dict_quick_mode['Flow Parameter'] = 'None'
        elif user_input_range_validate(flow_min, flow_max, ui.param_flowRate_1.text(), ui.comboBox_unit_frate_1.currentText()):
            setups_dict_quick_mode['Flow Parameter'] = {
                'Frate INF': f"{ui.param_flowRate_1.text()} {ui.comboBox_unit_frate_1.currentText()}",
                'Target INF': f"{ui.param_target_1.text()} {ui.comboBox_unit_target_1.currentText()}"
            }
        else:
            setups_dict_quick_mode['Flow Parameter'] = None
            QtWidgets.QMessageBox.information(ui.Run_button_quick, 'Input exceeds allowed range.', f"Valid range: {flow_min} ~ {flow_max}")

    elif run_mode == 'WD':
        if not ui.param_flowRate_1.text() or not ui.param_target_1.text():
            setups_dict_quick_mode['Flow Parameter'] = 'None'
        elif user_input_range_validate(flow_min, flow_max, ui.param_flowRate_1.text(), ui.comboBox_unit_frate_1.currentText()):
            setups_dict_quick_mode['Flow Parameter'] = {
                'Frate WD': f"{ui.param_flowRate_1.text()} {ui.comboBox_unit_frate_1.currentText()}",
                'Target WD': f"{ui.param_target_1.text()} {ui.comboBox_unit_target_1.currentText()}"
            }
        else:
            setups_dict_quick_mode['Flow Parameter'] = None
            QtWidgets.QMessageBox.information(ui.Run_button_quick, 'Input exceeds allowed range.', f"Valid range: {flow_min} ~ {flow_max}")

    elif run_mode == 'INF/ WD':
        if not (ui.param_flowRate_1.text() and ui.param_target_1.text() and ui.param_flowRate_2.text() and ui.param_target_2.text()):
            setups_dict_quick_mode['Flow Parameter'] = 'None'
        elif user_input_range_validate(flow_min, flow_max, ui.param_flowRate_1.text(), ui.comboBox_unit_frate_1.currentText()) and \
             user_input_range_validate(flow_min, flow_max, ui.param_flowRate_2.text(), ui.comboBox_unit_frate_2.currentText()):
            setups_dict_quick_mode['Flow Parameter'] = {
                'Frate INF': f"{ui.param_flowRate_1.text()} {ui.comboBox_unit_frate_1.currentText()}",
                'Target INF': f"{ui.param_target_1.text()} {ui.comboBox_unit_target_1.currentText()}",
                'Frate WD': f"{ui.param_flowRate_2.text()} {ui.comboBox_unit_frate_2.currentText()}",
                'Target WD': f"{ui.param_target_2.text()} {ui.comboBox_unit_target_2.currentText()}"
            }
        else:
            setups_dict_quick_mode['Flow Parameter'] = None
            QtWidgets.QMessageBox.information(ui.Run_button_quick, 'Input exceeds allowed range.', f"Valid range: {flow_min} ~ {flow_max}")

    elif run_mode == 'WD/ INF':
        if not (ui.param_flowRate_1.text() and ui.param_target_1.text() and ui.param_flowRate_2.text() and ui.param_target_2.text()):
            setups_dict_quick_mode['Flow Parameter'] = 'None'
        elif user_input_range_validate(flow_min, flow_max, ui.param_flowRate_1.text(), ui.comboBox_unit_frate_1.currentText()) and \
             user_input_range_validate(flow_min, flow_max, ui.param_flowRate_2.text(), ui.comboBox_unit_frate_2.currentText()):
            setups_dict_quick_mode['Flow Parameter'] = {
                'Frate WD': f"{ui.param_flowRate_1.text()} {ui.comboBox_unit_frate_1.currentText()}",
                'Target WD': f"{ui.param_target_1.text()} {ui.comboBox_unit_target_2.currentText()}",
                'Frate INF': f"{ui.param_flowRate_2.text()} {ui.comboBox_unit_frate_2.currentText()}",
                'Target INF': f"{ui.param_target_2.text()} {ui.comboBox_unit_target_1.currentText()}"
            }
        else:
            setups_dict_quick_mode['Flow Parameter'] = None
            QtWidgets.QMessageBox.information(ui.Run_button_quick, 'Input exceeds allowed range.', f"Valid range: {flow_min} ~ {flow_max}")

    if setups_dict_quick_mode.get('Run Mode') == 'Custom method':
        QtWidgets.QMessageBox.information(ui.RadioButtonGroup, 'Wrong run mode specified.', 'Run button is only for Quick Mode available.')
    elif setups_dict_quick_mode.get('Run Mode') is None:
        QtWidgets.QMessageBox.information(ui.RadioButtonGroup, 'Input Error.', 'Please specify a run mode for Quick Mode!')
    elif setups_dict_quick_mode.get('Flow Parameter') == 'None':
        QtWidgets.QMessageBox.information(ui.groupBox_param_enter, 'Input Error.', 'Flow parameters needed for the selected run mode.')
    else:
        return setups_dict_quick_mode


def validate_and_run(ui, read_send_thread, setups_dict_quick_mode: dict, mpl_canvas):
    """Validate parameters and start pump run."""
    Quick_mode_param_run(ui, setups_dict_quick_mode)
    if setups_dict_quick_mode.get('Flow Parameter') not in (None, 'None'):
        clear_graph_text(ui, read_send_thread, mpl_canvas)
        read_send_thread.ser_quick_mode_command_set(ui, setups_dict_quick_mode)
        read_send_thread.send_run_commands()


def set_input_mask(ui, sender_comboBox):
    """Set time input mask if time unit format is h:m:s."""
    if sender_comboBox == ui.comboBox_unit_target_1:
        ui.param_target_1.setInputMask('99:99:99' if ui.comboBox_unit_target_1.currentText() == 'h:m:s' else '')
    elif sender_comboBox == ui.comboBox_unit_target_2:
        ui.param_target_2.setInputMask('99:99:99' if ui.comboBox_unit_target_2.currentText() == 'h:m:s' else '')


def _get_item_index(list_widget, item):
    """Get the count of duplicate step types and the relative index of selected item."""
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


def add_to_list(item_text, item_icon, setups_dict_custom: dict, ui_list_widget):
    """Add selected step to custom method list."""
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


def delete_selected_item(list_widget, setups_dict_custom: dict, del_btn):
    """Delete the selected step from list widget and configurations."""
    selected_item = list_widget.currentItem()
    if selected_item:
        row = list_widget.row(selected_item)
        key = selected_item.text().split(".")[1].strip()
        update_item_numbers(list_widget, setups_dict_custom, del_btn)
        update_setups_dict_custom(list_widget, setups_dict_custom, selected_item, key)
        list_widget.takeItem(row)


def update_item_numbers(list_widget, setups_dict_custom: dict, del_btn):
    """Renumber list widget items sequentially."""
    for i in range(list_widget.count()):
        item = list_widget.item(i)
        item.setText(f"{i + 1}. {item.text()[3:]}")
    try:
        del_btn.disconnect()
    except Exception:
        pass
    del_btn.clicked.connect(lambda: delete_selected_item(list_widget, setups_dict_custom, del_btn))


def update_setups_dict_custom(list_widget, setups_dict_custom: dict, item, key_to_remove=None):
    """Update custom method steps dictionary after step deletion."""
    len_items_same, selected_item_index = _get_item_index(list_widget, item)
    key_to_remove = key_to_remove.split()[0] if key_to_remove else ''
    if key_to_remove:
        if len_items_same == 1 or (len_items_same > 1 and selected_item_index == 0):
            setups_dict_custom.pop(key_to_remove, None)
        else:
            setups_dict_custom.pop(f"{key_to_remove}_{selected_item_index}", None)


def edit_item_parameter(list_widget, ui_step_guide, setups_dict_custom: dict, item):
    """Open step parameter dialog on double-click and store input."""
    item_text = item.text().split(".")[1].strip().split()[0]
    len_items_same, current_index = _get_item_index(list_widget, item)

    if len_items_same == 1 or (len_items_same > 1 and current_index == 0):
        default_value = setups_dict_custom.get(item_text, '')
    else:
        default_value = setups_dict_custom.get(f"{item_text}_{current_index}", '')
    ui_step_guide.lineEdit.setText(default_value if default_value else '')

    for label_path_key, label_path_value in STEP_GUIDE_CONFIG.items():
        if label_path_key in item_text:
            img_resource_step_guide = f":guide_/{label_path_value[1]}"
            ui_step_guide.pixmap = QtGui.QPixmap(img_resource_step_guide)
            ui_step_guide.image_label.setPixmap(ui_step_guide.pixmap)
            ui_step_guide.image_label.setScaledContents(True)
            ui_step_guide.layout.addWidget(ui_step_guide.image_label)
            ui_step_guide.label.setText(label_path_value[0])
            ui_step_guide.groupBox.setTitle(label_path_key)
            ui_step_guide.exec()
            break

    if ui_step_guide.buttonBox.accepted:
        item_parameter = ui_step_guide.lineEdit.text().strip()
        if len_items_same == 1 or (len_items_same > 1 and current_index == 0):
            setups_dict_custom[item_text] = item_parameter
        else:
            setups_dict_custom[f"{item_text}_{current_index}"] = item_parameter


def print_setups_dict_custom(setups_dict_custom: dict) -> dict:
    """Renumber and log custom method configuration."""
    renumbered = renumber_steps(setups_dict_custom)
    logger.info(renumbered)
    return renumbered


def clear_graph_text(ui, read_send_thread, mpl_canvas):
    """Clear real-time plot and terminal displays."""
    ui.Response_from_pump.setText('')
    ui.commands_sent.setText('')
    read_send_thread.initialize_class_var()
    if hasattr(ui, 'actionDark') and ui.actionDark.isChecked():
        mpl_canvas.initialize_graph(axis_label_color='white')
    else:
        mpl_canvas.initialize_graph(axis_label_color='black')
    read_send_thread.clear_from_button(ui)


def fast_btn_timer_start(timer):
    timer.start(200)


def fast_btn_timer_stop(timer):
    timer.stop()


def rwd_btn_timer_start(timer):
    timer.start(200)


def rwd_btn_timer_stop(timer):
    timer.stop()


def reset_all_config(ui):
    """Reset quick mode radio button options."""
    ui.radioButton_1.setChecked(False)
    ui.radioButton_2.setChecked(False)
    ui.radioButton_3.setChecked(False)
    ui.radioButton_4.setChecked(False)
    ui.radioButton_5.setChecked(False)


def progress_display(ui, progress_str: str):
    """Update running mode label and progress bar from formatted progress string."""
    try:
        parts = progress_str.split(':')
        sequence_mode = parts[0].strip()
        progress_percent = int(parts[1].strip())
        ui.running_mode.setText(sequence_mode)
        ui.progress_bar_running.setValue(progress_percent)
    except Exception:
        pass


def display_progress_on_statusBar(ui, label_str, value_str):
    """Update status bar label and progress percentage."""
    if label_str and value_str is not None:
        try:
            ui.running_mode.setText(str(label_str))
            ui.progress_bar_running.setValue(int(value_str))
        except (ValueError, TypeError):
            pass


def return_receive_status(receive_status, send_data_to_port=None):
    """Return serial receive status."""
    return receive_status

