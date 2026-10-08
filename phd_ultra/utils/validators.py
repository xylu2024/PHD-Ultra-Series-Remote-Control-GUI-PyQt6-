# -*- coding: utf-8 -*-
"""
Input validation and unit conversion utilities for PHD Ultra pump parameters.
"""

from decimal import Decimal
from PyQt6 import QtWidgets
from phd_ultra.database.syringes import get_syringe_dict, get_min_max_limit

CONVERSION_DICT = {
    'pl/hr': Decimal(1e-9 / 3600),
    'nl/hr': Decimal(1e-6 / 3600),
    'ul/hr': Decimal(1e-3 / 3600),
    'ml/hr': Decimal(1 / 3600),
    'pl/min': Decimal(1e-9 / 60),
    'nl/min': Decimal(1e-6 / 60),
    'ul/min': Decimal(1e-3 / 60),
    'ml/min': Decimal(1 / 60),
    'pl/s': Decimal(1e-9),
    'nl/s': Decimal(1e-6),
    'ul/s': Decimal(1e-3),
    'ml/s': Decimal(1),
}


def convert_unit(val, from_unit: str, to_unit: str = 'ml/s') -> Decimal:
    """Convert flow rate value between supported units."""
    d_val = Decimal(str(val))
    if from_unit in CONVERSION_DICT and to_unit in CONVERSION_DICT:
        in_ml_s = d_val * CONVERSION_DICT[from_unit]
        return in_ml_s / CONVERSION_DICT[to_unit]
    return d_val



def is_number_and_positive(str_passed) -> bool:
    """Check if input is a valid non-negative number."""
    try:
        number = float(str_passed)
        return number >= 0
    except (ValueError, TypeError):
        return False


def user_input_range_validate(flow_min: str, flow_max: str, param_num, param_unit: str) -> bool:
    """Validate that input flow rate is within allowable min/max limits for selected syringe."""
    try:
        param_num = Decimal(str(param_num))
        param_flow_min = Decimal(flow_min.split()[0])
        unit_flow_min = flow_min.split()[1]
        param_flow_max = Decimal(flow_max.split()[0])
        unit_flow_max = flow_max.split()[1]
    except (IndexError, ValueError, AttributeError):
        return False

    if param_unit in CONVERSION_DICT:
        val_converted = param_num * CONVERSION_DICT[param_unit]
        if unit_flow_min == 'nl/min' and unit_flow_max == 'ml/min':
            min_converted = param_flow_min * Decimal(1e-6 / 60)
            max_converted = param_flow_max * Decimal(1 / 60)
            return min_converted <= val_converted <= max_converted
        elif unit_flow_min == 'pl/min' and unit_flow_max == 'ul/min':
            min_converted = param_flow_min * Decimal(1e-9 / 60)
            max_converted = param_flow_max * Decimal(1e-3 / 60)
            return min_converted <= val_converted <= max_converted
    return False


def set_input_mask(ui, sender_comboBox) -> None:
    """Set input mask for time/volume target input boxes."""
    if sender_comboBox == ui.comboBox_unit_target_1:
        if ui.comboBox_unit_target_1.currentText() == 'h:m:s':
            ui.param_target_1.setInputMask('99:99:99')
        else:
            ui.param_target_1.setInputMask('')
    elif sender_comboBox == ui.comboBox_unit_target_2:
        if ui.comboBox_unit_target_2.currentText() == 'h:m:s':
            ui.param_target_2.setInputMask('99:99:99')
        else:
            ui.param_target_2.setInputMask('')


def Quick_mode_param_run(ui, setups_dict_quick_mode: dict) -> dict:
    """Validate flow rate and targets for quick mode."""
    flow_min, flow_max, _ = get_min_max_limit(ui, get_syringe_dict().get(ui.comboBox_syrManu.currentText(), []))

    if setups_dict_quick_mode.get('Run Mode') == 'INF':
        if ui.param_flowRate_1.text() == '' or ui.param_target_1.text() == '':
            setups_dict_quick_mode['Flow Parameter'] = 'None'
        elif user_input_range_validate(flow_min, flow_max, ui.param_flowRate_1.text(), ui.comboBox_unit_frate_1.currentText()):
            setups_dict_quick_mode['Flow Parameter'] = {
                'Frate INF': ui.param_flowRate_1.text() + ' ' + ui.comboBox_unit_frate_1.currentText(),
                'Target INF': ui.param_target_1.text() + ' ' + ui.comboBox_unit_target_1.currentText()
            }
        else:
            setups_dict_quick_mode['Flow Parameter'] = None
            QtWidgets.QMessageBox.information(ui.Run_button_quick, 'Input exceeds allowed range.', f"Valid range: {flow_min} ~ {flow_max}")

    elif setups_dict_quick_mode.get('Run Mode') == 'WD':
        if ui.param_flowRate_1.text() == '' or ui.param_target_1.text() == '':
            setups_dict_quick_mode['Flow Parameter'] = 'None'
        elif user_input_range_validate(flow_min, flow_max, ui.param_flowRate_1.text(), ui.comboBox_unit_frate_1.currentText()):
            setups_dict_quick_mode['Flow Parameter'] = {
                'Frate WD': ui.param_flowRate_1.text() + ' ' + ui.comboBox_unit_frate_1.currentText(),
                'Target WD': ui.param_target_1.text() + ' ' + ui.comboBox_unit_target_1.currentText()
            }
        else:
            setups_dict_quick_mode['Flow Parameter'] = None
            QtWidgets.QMessageBox.information(ui.Run_button_quick, 'Input exceeds allowed range.', f"Valid range: {flow_min} ~ {flow_max}")

    elif setups_dict_quick_mode.get('Run Mode') == 'INF/ WD':
        if ui.param_flowRate_1.text() == '' or ui.param_target_1.text() == '' or ui.param_flowRate_2.text() == '' or ui.param_target_2.text() == '':
            setups_dict_quick_mode['Flow Parameter'] = 'None'
        elif (user_input_range_validate(flow_min, flow_max, ui.param_flowRate_1.text(), ui.comboBox_unit_frate_1.currentText()) and
              user_input_range_validate(flow_min, flow_max, ui.param_flowRate_2.text(), ui.comboBox_unit_frate_2.currentText())):
            setups_dict_quick_mode['Flow Parameter'] = {
                'Frate INF': ui.param_flowRate_1.text() + ' ' + ui.comboBox_unit_frate_1.currentText(),
                'Target INF': ui.param_target_1.text() + ' ' + ui.comboBox_unit_target_1.currentText(),
                'Frate WD': ui.param_flowRate_2.text() + ' ' + ui.comboBox_unit_frate_2.currentText(),
                'Target WD': ui.param_target_2.text() + ' ' + ui.comboBox_unit_target_2.currentText()
            }
        else:
            setups_dict_quick_mode['Flow Parameter'] = None
            QtWidgets.QMessageBox.information(ui.Run_button_quick, 'Input exceeds allowed range.', f"Valid range: {flow_min} ~ {flow_max}")

    elif setups_dict_quick_mode.get('Run Mode') == 'WD/ INF':
        if ui.param_flowRate_1.text() == '' or ui.param_target_1.text() == '' or ui.param_flowRate_2.text() == '' or ui.param_target_2.text() == '':
            setups_dict_quick_mode['Flow Parameter'] = 'None'
        elif (user_input_range_validate(flow_min, flow_max, ui.param_flowRate_1.text(), ui.comboBox_unit_frate_1.currentText()) and
              user_input_range_validate(flow_min, flow_max, ui.param_flowRate_2.text(), ui.comboBox_unit_frate_2.currentText())):
            setups_dict_quick_mode['Flow Parameter'] = {
                'Frate WD': ui.param_flowRate_1.text() + ' ' + ui.comboBox_unit_frate_1.currentText(),
                'Target WD': ui.param_target_1.text() + ' ' + ui.comboBox_unit_target_1.currentText(),
                'Frate INF': ui.param_flowRate_2.text() + ' ' + ui.comboBox_unit_frate_2.currentText(),
                'Target INF': ui.param_target_2.text() + ' ' + ui.comboBox_unit_target_2.currentText()
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


def validate_and_run(ui, read_send_thread, setups_dict_quick_mode: dict, mpl_canvas) -> None:
    """Validate quick mode parameters and start pump execution."""
    from phd_ultra.ui.canvas import clear_graph_text
    Quick_mode_param_run(ui, setups_dict_quick_mode)
    if setups_dict_quick_mode.get('Flow Parameter') not in (None, 'None'):
        clear_graph_text(ui, read_send_thread, mpl_canvas)
        read_send_thread.ser_quick_mode_command_set(ui, setups_dict_quick_mode)
        read_send_thread.send_run_commands()
