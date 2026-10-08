# -*- coding: utf-8 -*-
########################################################################################################################
########################## Developer: Xueyong Lu @ Institut für Verfahrens- und Umwelttechnik ##########################
##########################         Professur für Transportprozesse an Grenzflächen            ##########################
##########################              Helmholtz-Zentrum Dresden-Rossendorf                  ##########################
##########################                     Dresden, 13.04.2023                            ##########################
########################################################################################################################
import sys
import logging.config

from PyQt6 import QtCore, QtGui, QtWidgets
import global_hotkeys as hotkey
import resources_rc

from settings import settings_log
import functions
from functions import (
    GraphicalMplCanvas,
    StepsDialogChildWindow,
    PortSetupChildWindow,
    StepGuideChildWindow,
)
from RemoteControl_main_UI import Ui_MainWindow

logging.config.dictConfig(settings_log.LOGGING_DIC)
logger_info_console_file = logging.getLogger('logger2')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.serial_port = None
        self.setups_dict_custom = {}
        self.setups_dict_quick_mode = {
            'Run Mode': None,
            'Syringe Info': '',
            'Flow Parameter': None
        }

        self.ui_main = Ui_MainWindow()
        self.ui_main.setupUi(self)

        style_resource = QtCore.QFile(':/qss_/origin_style.qss')
        if style_resource.open(QtCore.QIODevice.OpenModeFlag.ReadOnly):
            self.style_sheet = style_resource.readAll().data().decode()
            style_resource.close()
        else:
            self.style_sheet = ""

        self.app_instance = QtWidgets.QApplication.instance()

        self.mpl_canvas = GraphicalMplCanvas(parent=self)
        self.layout_canvas = QtWidgets.QGridLayout(self.ui_main.frame_graphical_display)
        self.layout_canvas.addWidget(self.mpl_canvas)

        self.double_validator = QtGui.QDoubleValidator()
        self.double_validator.setBottom(0)
        self.double_validator.setDecimals(5)

        self.int_validator = QtGui.QIntValidator()
        self.int_validator.setBottom(0)
        self.int_validator.setTop(99)

        self.actionGroup = QtGui.QActionGroup(self)
        self.actionGroup.addAction(self.ui_main.actionNo_line_feed)
        self.actionGroup.addAction(self.ui_main.action_carrige_return)
        self.actionGroup.addAction(self.ui_main.action_line_feed)
        self.actionGroup.addAction(self.ui_main.action_CR_LF)

        self.decodingGroup = QtGui.QActionGroup(self)
        self.decodingGroup.addAction(self.ui_main.actionASCII)
        self.decodingGroup.addAction(self.ui_main.actionUTF_8)

        self.themGroup = QtGui.QActionGroup(self)
        self.themGroup.addAction(self.ui_main.actionLight)
        self.themGroup.addAction(self.ui_main.actionDark)
        self.themGroup.addAction(self.ui_main.actionDefaultTheme)

        self.ui_main.actionReset.triggered.connect(lambda: functions.reset_all_config(self.ui_main))

        self.ui_main.actionLight.triggered.connect(
            lambda: functions.switch_theme_qdarktheme(
                self.ui_main, self.ui_child_steps_dialog, self.mpl_canvas, self.sender(),
                app=self.app_instance, style_sheet=None
            )
        )
        self.ui_main.actionDark.triggered.connect(
            lambda: functions.switch_theme_qdarktheme(
                self.ui_main, self.ui_child_steps_dialog, self.mpl_canvas, self.sender(),
                app=self.app_instance, style_sheet=None
            )
        )
        self.ui_main.actionDefaultTheme.triggered.connect(
            lambda: functions.switch_theme_qdarktheme(
                self.ui_main, self.ui_child_steps_dialog, self.mpl_canvas, self.sender(),
                app=self.app_instance, style_sheet=self.style_sheet
            )
        )

        self.ui_main.main_layout.setContentsMargins(0, 0, 0, 0)

        self.timer_fast_move = QtCore.QTimer()
        self.timer_rewind = QtCore.QTimer()
        self.timer_ui_update = QtCore.QTimer()

        icon_upper = QtGui.QIcon()
        icon_upper.addPixmap(QtGui.QPixmap(":upper_lower_icon_/upper_limit_icon.png"), QtGui.QIcon.Mode.Active,
                             QtGui.QIcon.State.On)
        self.ui_main.flow_upper_button_1.setIcon(icon_upper)
        self.ui_main.flow_upper_button_1.setIconSize(QtCore.QSize(12, 20))
        self.ui_main.flow_upper_button_2.setIcon(icon_upper)
        self.ui_main.flow_upper_button_2.setIconSize(QtCore.QSize(12, 20))

        icon_lower = QtGui.QIcon()
        icon_lower.addPixmap(QtGui.QPixmap(":upper_lower_icon_/lower_limit_icon.png"), QtGui.QIcon.Mode.Active,
                             QtGui.QIcon.State.On)
        self.ui_main.flow_lower_button_1.setIcon(icon_lower)
        self.ui_main.flow_lower_button_1.setIconSize(QtCore.QSize(12, 20))
        self.ui_main.flow_lower_button_2.setIcon(icon_lower)
        self.ui_main.flow_lower_button_2.setIconSize(QtCore.QSize(12, 20))

        self.check_serial_thread = functions.CheckSerialThread(self.ui_main, self)
        self.read_send_thread = functions.ReadSendPort(
            check_serial_thread=self.check_serial_thread,
            ui_main=self.ui_main,
            parent=self
        )

        self.hotkey_stop_pump = [
            [["control", "g"], None, self.read_send_thread.stop_pump_button],
        ]
        try:
            hotkey.register_hotkeys(self.hotkey_stop_pump)
            hotkey.start_checking_hotkeys()
        except Exception as e:
            logger_info_console_file.warning(f"Could not initialize global stop hotkey: {e}")

        self.ui_main.status_label = QtWidgets.QLabel()
        self.ui_main.status_label.setText('  Waiting for the serial port to open.')
        self.ui_main.status_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.ui_main.status_label.setStyleSheet('color: grey')

        self.spacer_status_label = QtWidgets.QWidget()
        self.spacer_status_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.ui_main.statusbar.addWidget(self.ui_main.status_label, 0)
        self.check_serial_thread.CONNECTION_STATUS_CHANGED.connect(
            lambda status: functions.update_connection_status(self.ui_main, status)
        )

        self.ui_main.port_button_stop.clicked.connect(
            lambda: functions.disconnect_from_port_call(
                self.check_serial_thread, auto_reconnect=False, _pause_thread=True
            )
        )

        self.ui_main.statusbar.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        self.ui_main.statusbar.setStyleSheet("QStatusBar::item { border: none; }")

        self.ui_main.running_mode = QtWidgets.QLabel()
        self.ui_main.running_mode.setStyleSheet(
            "QLabel { background-color : none; color : grey; qproperty-alignment: 'AlignCenter'; padding: 0px; margin: 0px; }"
        )
        self.ui_main.statusbar.addPermanentWidget(self.ui_main.running_mode, 1)

        self.ui_main.progress_bar_running = QtWidgets.QProgressBar()
        self.ui_main.statusbar.addPermanentWidget(self.ui_main.progress_bar_running, 2)
        self.ui_main.progress_bar_running.setStyleSheet("QProgressBar { text-align: center; }")
        self.ui_main.progress_bar_running.setMinimum(0)
        self.ui_main.progress_bar_running.setMaximum(100)
        self.ui_main.progress_bar_running.setValue(0)

        self.ui_main.status_label.setMinimumWidth(530)
        self.ui_main.status_label.setMaximumWidth(530)
        self.ui_main.running_mode.setMinimumWidth(70)
        self.ui_main.running_mode.setMaximumWidth(70)
        self.ui_main.progress_bar_running.setMinimumWidth(210)
        self.ui_main.progress_bar_running.setMaximumWidth(210)

        self.timer_ui_update.timeout.connect(
            lambda: functions.display_progress_on_statusBar(
                self.ui_main, self.read_send_thread.MAIN_WINDOW_LABEL, self.read_send_thread.MAIN_WINDOW_PROGRESS
            )
        )
        self.timer_ui_update.timeout.connect(
            lambda: self.mpl_canvas.update_graph(
                self.read_send_thread.FLOW_RATE,
                self.read_send_thread.FLOW_RATE_UNIT,
                self.read_send_thread.ELAPSED_TIME,
                self.read_send_thread.TRANSPORTED_VOLUME,
                self.read_send_thread.RUNNING_MODE,
                self.read_send_thread.COUNT_OUTER,
                self.read_send_thread.TARGET_STR,
                self.read_send_thread.LEN_RUN_COMMAND
            )
        )
        self.timer_ui_update.start(80)

        self.ui_child_steps_dialog = StepsDialogChildWindow(self)
        self.ui_child_port_setup = PortSetupChildWindow(self)
        self.ui_child_step_guide = StepGuideChildWindow(self)
        self.ui_child_port_setup.dictReady.connect(
            lambda: functions.receive_dict(self.check_serial_thread, self.ui_child_port_setup.port_param_dict)
        )

        self.ui_main.param_flowRate_1.setValidator(self.double_validator)
        self.ui_main.param_target_1.setValidator(self.double_validator)
        self.ui_main.param_flowRate_2.setValidator(self.double_validator)
        self.ui_main.param_target_2.setValidator(self.double_validator)
        self.ui_main.address_input.setValidator(self.int_validator)

        self.buttons = {
            self.ui_main.radioButton_1: {'object_name': 'irun_button', 'value': 'INF'},
            self.ui_main.radioButton_2: {'object_name': 'wrun_button', 'value': 'WD'},
            self.ui_main.radioButton_3: {'object_name': 'irun_wrun_button', 'value': 'INF/ WD'},
            self.ui_main.radioButton_4: {'object_name': 'wrun_irun_button', 'value': 'WD/ INF'},
            self.ui_main.radioButton_5: {'object_name': 'user_def_button', 'value': 'Custom method'}
        }
        for button, values in self.buttons.items():
            button.setObjectName(values['object_name'])
            button.setProperty('value', values['value'])
            tab_var = self.ui_main.flow_param_tab
            button.clicked.connect(
                lambda checked, btn=button, tab=tab_var: functions.on_button_clicked(
                    btn, tab, self.ui_main, self.setups_dict_quick_mode
                )
            )

        functions.init_combox_syrSize(self.ui_main, self.setups_dict_quick_mode)
        self.ui_main.comboBox_syrManu.addItems(functions.Get_syringe_dict().keys())
        self.ui_main.comboBox_syrSize.currentTextChanged.connect(
            lambda: functions.force_level_recommendation(self.ui_main, self.ui_main.comboBox_syrSize)
        )
        self.ui_main.syr_param_enter.textChanged.connect(
            lambda: functions.update_combox_syr_enabled(self.ui_main, self.setups_dict_quick_mode)
        )

        self.ui_main.flow_lower_button_1.clicked.connect(
            lambda: functions.set_max_min_flow_rate(self.ui_main, self.sender())
        )
        self.ui_main.flow_lower_button_2.clicked.connect(
            lambda: functions.set_max_min_flow_rate(self.ui_main, self.sender())
        )
        self.ui_main.flow_upper_button_1.clicked.connect(
            lambda: functions.set_max_min_flow_rate(self.ui_main, self.sender())
        )
        self.ui_main.flow_upper_button_2.clicked.connect(
            lambda: functions.set_max_min_flow_rate(self.ui_main, self.sender())
        )
        self.ui_main.comboBox_unit_target_1.activated.connect(
            lambda: functions.set_input_mask(self.ui_main, self.sender())
        )
        self.ui_main.comboBox_unit_target_2.activated.connect(
            lambda: functions.set_input_mask(self.ui_main, self.sender())
        )

        self.ui_main.userDefined_Add.clicked.connect(
            lambda: functions.show_user_defined_dialog(self.ui_child_steps_dialog)
        )
        self.ui_child_steps_dialog.selected_items.connect(
            lambda item_text, item_icon, parameters_dict=None, list_widget=self.ui_main.listWidget_userDefined_method:
                functions.add_to_list(item_text, item_icon, self.setups_dict_custom, list_widget)
        )

        self.ui_main.userDefined_Del.disconnect()
        self.ui_main.userDefined_Del.clicked.connect(
            lambda: functions.delete_selected_item(
                self.ui_main.listWidget_userDefined_method, self.setups_dict_custom, del_btn=self.ui_main.userDefined_Del
            )
        )

        self.ui_main.listWidget_userDefined_method.itemDoubleClicked.connect(
            lambda item_selected: functions.edit_item_parameter(
                self.ui_main.listWidget_userDefined_method, self.ui_child_step_guide, self.setups_dict_custom, item=item_selected
            )
        )

        self.ui_main.userDefined_OK.clicked.connect(
            lambda: functions.print_setups_dict_custom(self.setups_dict_custom)
        )
        self.setups_dict_custom = {}

        self.ui_main.userDefined_Export.clicked.connect(
            lambda: functions.export_user_defined_methods(self.ui_main, self.setups_dict_custom)
        )
        self.ui_main.userDefined_Import.clicked.connect(
            lambda: functions.import_user_defined_methods(
                self.ui_main.listWidget_userDefined_method, self.setups_dict_custom
            )
        )

        self.ui_main.port_button.clicked.connect(
            lambda: functions.show_port_setup_dialog(self.ui_child_port_setup)
        )

        self.ui_main.address_button.clicked.connect(lambda: self.read_send_thread.get_set_address(self.ui_main))
        self.ui_main.catalog_display_button.clicked.connect(self.read_send_thread.ser_command_catalog)
        self.ui_main.tilt_sensor_cali_button.clicked.connect(self.read_send_thread.ser_command_tilt)

        self.ui_main.bgLight_Slider.valueChanged.connect(
            lambda: self.read_send_thread.ser_bgl_label_show(self.ui_main)
        )
        self.ui_main.bgLight_Slider.sliderReleased.connect(
            lambda: self.read_send_thread.ser_bgl_level(self.ui_main)
        )

        self.ui_main.forceLimit_Slider.sliderReleased.connect(
            lambda: self.read_send_thread.ser_force_limit(self.ui_main)
        )
        self.ui_main.forceLimit_Slider.valueChanged.connect(
            lambda: self.read_send_thread.ser_force_label_show(self.ui_main)
        )

        self.ui_main.fast_forward_btn.clicked.connect(lambda: self.read_send_thread.fast_forward_button(self.ui_main))
        self.ui_main.rewinde_btn.clicked.connect(lambda: self.read_send_thread.fast_rewind_button(self.ui_main))

        self.ui_main.data_sent_send_button.clicked.connect(
            lambda: self.read_send_thread.send_command_manual(self.ui_main)
        )
        shortcut_return = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Return), self.ui_main.lineEdit_send_toPump)
        shortcut_return.activated.connect(lambda: self.ui_main.data_sent_send_button.click())

        self.ui_main.Run_button_quick.clicked.connect(
            lambda: functions.validate_and_run(
                self.ui_main, self.read_send_thread, self.setups_dict_quick_mode, self.mpl_canvas
            )
        )

        self.ui_main.actionNo_line_feed.triggered.connect(
            lambda: self.read_send_thread.set_line_feed_style(self.ui_main, self.sender())
        )
        self.ui_main.action_carrige_return.triggered.connect(
            lambda: self.read_send_thread.set_line_feed_style(self.ui_main, self.sender())
        )
        self.ui_main.action_line_feed.triggered.connect(
            lambda: self.read_send_thread.set_line_feed_style(self.ui_main, self.sender())
        )
        self.ui_main.action_CR_LF.triggered.connect(
            lambda: self.read_send_thread.set_line_feed_style(self.ui_main, self.sender())
        )

        self.ui_main.actionASCII.triggered.connect(
            lambda: self.read_send_thread.set_decode_format(self.ui_main, self.sender())
        )
        self.ui_main.actionUTF_8.triggered.connect(
            lambda: self.read_send_thread.set_decode_format(self.ui_main, self.sender())
        )

        self.ui_main.Reset_button.clicked.connect(
            lambda: functions.clear_graph_text(self.ui_main, self.read_send_thread, self.mpl_canvas)
        )
        self.ui_main.Stop_button.clicked.connect(self.read_send_thread.stop_pump_button)
        self.ui_main.Export_button.clicked.connect(self.mpl_canvas.export_data)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        a0.ignore()
        self.hide()

    @QtCore.pyqtSlot(str)
    def return_receive_status(self, receive_status):
        pass

    @QtCore.pyqtSlot(str)
    def progress_display(self, ui, str_progress: str):
        try:
            parts = str_progress.split(':')
            sequence_mode = parts[0].strip()
            progress_percent = int(parts[1].strip())
            ui.running_mode.setText(sequence_mode)
            ui.progress_bar_running.setValue(progress_percent)
        except Exception:
            pass


def load_application_fonts():
    """Load embedded Open Sans fonts from compiled Qt resource."""
    font_names = [
        'OpenSans-Regular.ttf',
        'OpenSans-SemiBold.ttf',
        'OpenSans-Light.ttf',
        'OpenSans-Medium.ttf',
        'OpenSans-Italic.ttf',
        'OpenSans-SemiBoldItalic.ttf',
        'OpenSans-LightItalic.ttf',
        'OpenSans-MediumItalic.ttf',
        'OpenSans_SemiCondensed-Medium.ttf',
        'OpenSans_SemiCondensed-MediumItalic.ttf',
        'OpenSans_SemiCondensed-Regular.ttf',
        'OpenSans_Condensed-Regular.ttf'
    ]
    for font_name in font_names:
        QtGui.QFontDatabase.addApplicationFont(f':/font_/{font_name}')


def main():
    app = QtWidgets.QApplication(sys.argv)
    load_application_fonts()

    window = MainWindow()
    window.setWindowTitle('PHD MA1 70-3xxx Series Syringe Pump v1.0.0')

    icon = QtGui.QPixmap(':window_icon_/Logo_TU_Dresden_small.svg')
    if not icon.isNull():
        icon_h_32 = icon.scaledToHeight(32, QtCore.Qt.TransformationMode.SmoothTransformation)
        window.setWindowIcon(QtGui.QIcon(icon_h_32))

    window.show()

    tray_icon = functions.MySysTrayWidget(ui=window.ui_main, app=app, window=window)

    def cleanup():
        try:
            hotkey.stop_checking_hotkeys()
        except Exception:
            pass

    app.aboutToQuit.connect(cleanup)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
