# -*- coding: utf-8 -*-
"""Backward-compatibility facade for phd_ultra package.

This module re-exports components from phd_ultra so that existing code
referencing `functions.<symbol>` continues to work seamlessly with modern,
thread-safe, and modular implementations.
"""

from phd_ultra.core.serial_worker import (
    CheckSerialThread,
    ReadSendPort,
    receive_dict,
    disconnect_from_port_call,
    update_connection_status,
    detect_ports,
    show_port_setup_dialog,
    show_user_defined_dialog,
)

from phd_ultra.ui.canvas import GraphicalMplCanvas
from phd_ultra.ui.tray import MySysTrayWidget
from phd_ultra.ui.theme import switch_theme_qdarktheme, apply_dark_theme, apply_light_theme
from phd_ultra.ui.dialogs import (
    StepsDialogChildWindow,
    PortSetupChildWindow,
    StepGuideChildWindow,
)
from phd_ultra.ui.controllers import (
    on_button_clicked,
    init_combox_syrSize,
    update_combox_syrSize,
    clear_previous_limit,
    get_min_max_limit,
    set_max_min_flow_rate,
    force_level_recommendation,
    update_combox_syr_enabled,
    Quick_mode_param_run,
    validate_and_run,
    set_input_mask,
    add_to_list,
    delete_selected_item,
    update_item_numbers,
    update_setups_dict_custom,
    edit_item_parameter,
    print_setups_dict_custom,
    clear_graph_text,
    fast_btn_timer_start,
    fast_btn_timer_stop,
    rwd_btn_timer_start,
    rwd_btn_timer_stop,
    reset_all_config,
    progress_display,
    display_progress_on_statusBar,
    return_receive_status,
    STEP_GUIDE_CONFIG as label_path_StepGuide_dict,
)

from phd_ultra.database.syringes import (
    Get_syringe_dict,
    SYRINGE_DATA,
    LIMIT_FORCE_LEVEL_DICT,
)

from phd_ultra.utils.validators import (
    is_number_and_positive,
    user_input_range_validate,
    convert_unit,
)

from phd_ultra.utils.method_io import (
    renumber_steps,
    export_user_defined_methods,
    import_user_defined_methods,
)

__all__ = [
    "CheckSerialThread",
    "ReadSendPort",
    "receive_dict",
    "disconnect_from_port_call",
    "update_connection_status",
    "detect_ports",
    "show_port_setup_dialog",
    "show_user_defined_dialog",
    "GraphicalMplCanvas",
    "MySysTrayWidget",
    "switch_theme_qdarktheme",
    "apply_dark_theme",
    "apply_light_theme",
    "StepsDialogChildWindow",
    "PortSetupChildWindow",
    "StepGuideChildWindow",
    "on_button_clicked",
    "init_combox_syrSize",
    "update_combox_syrSize",
    "clear_previous_limit",
    "get_min_max_limit",
    "set_max_min_flow_rate",
    "force_level_recommendation",
    "update_combox_syr_enabled",
    "Quick_mode_param_run",
    "validate_and_run",
    "set_input_mask",
    "add_to_list",
    "delete_selected_item",
    "update_item_numbers",
    "update_setups_dict_custom",
    "edit_item_parameter",
    "print_setups_dict_custom",
    "clear_graph_text",
    "fast_btn_timer_start",
    "fast_btn_timer_stop",
    "rwd_btn_timer_start",
    "rwd_btn_timer_stop",
    "reset_all_config",
    "progress_display",
    "display_progress_on_statusBar",
    "return_receive_status",
    "label_path_StepGuide_dict",
    "Get_syringe_dict",
    "SYRINGE_DATA",
    "LIMIT_FORCE_LEVEL_DICT",
    "is_number_and_positive",
    "user_input_range_validate",
    "convert_unit",
    "renumber_steps",
    "export_user_defined_methods",
    "import_user_defined_methods",
]
