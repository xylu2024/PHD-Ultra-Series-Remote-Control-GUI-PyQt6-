# -*- coding: utf-8 -*-
"""
Robust, thread-safe serial communication worker and connection monitor for PHD Ultra pumps.
Uses PyQt6 signals for thread-safe UI updates, re-entrant locking, and graceful shutdown.
"""

import math
from decimal import Decimal
import threading
import time
from typing import Optional, Tuple

import serial
import serial.tools.list_ports
from PyQt6 import QtCore, QtGui, QtWidgets

from phd_ultra.config.logging import logger_debug_console, logger_info_console_file
from phd_ultra.database.syringes import force_level_recommendation, update_combox_syr_enabled


class CheckSerialThread(QtCore.QThread):
    """
    Serial port monitor and connector thread.
    Manages opening, configuring, reconnecting, and closing serial ports safely.
    """
    CONNECTION_STATUS_CHANGED = QtCore.pyqtSignal(str)
    SERIAL_OPENED = QtCore.pyqtSignal(bool)

    PORT_PARAM_DICT = {}
    PORT_PARAM_DICT_PREVIOUS = {}
    TIMEOUT_COUNT = 0
    MAX_TIMEOUT = 20

    def __init__(self, ui=None, parent=None):
        super().__init__(parent)
        self.ui = ui
        self.parent = parent
        self.ser: Optional[serial.Serial] = None
        self.read_send_thread: Optional['ReadSendPort'] = None
        self.connected = False
        self.auto_reconnect = True
        self._pause_thread = False

        self._lock = threading.RLock()
        self.wait_condition = QtCore.QWaitCondition()
        self.mutex = QtCore.QMutex()
        self.port_param_dict_func = {}

    def start(self, auto_reconnect=True, pause_thread=False):
        """Start thread with specified reconnection and pause flags."""
        self.auto_reconnect = auto_reconnect
        self._pause_thread = pause_thread
        super().start()

    def set_port_params(self, dict_port: dict):
        """Configure serial parameters and initiate connection."""
        if CheckSerialThread.PORT_PARAM_DICT != dict_port:
            self.resume_thread()
            self._pause_thread = False
            self.auto_reconnect = True
            self.disconnect_from_port(auto_reconnect=True, pause_thread=False)
            CheckSerialThread.PORT_PARAM_DICT = dict(dict_port)
            self.start(auto_reconnect=True, pause_thread=False)
        elif self._pause_thread and not self.auto_reconnect:
            self.resume_thread()
            CheckSerialThread.PORT_PARAM_DICT = dict(dict_port)
            self.start(auto_reconnect=True, pause_thread=False)
        elif not self._pause_thread and self.auto_reconnect:
            self.resume_thread()
            CheckSerialThread.PORT_PARAM_DICT = dict(dict_port)
            self.start(auto_reconnect=True, pause_thread=False)

    def run(self):
        with self._lock:
            try:
                if self._pause_thread and not self.auto_reconnect:
                    self.mutex.lock()
                    try:
                        self.wait_condition.wait(self.mutex)
                    finally:
                        self.mutex.unlock()
                else:
                    self.port_param_dict_func = dict(CheckSerialThread.PORT_PARAM_DICT)
                    port_name = self.port_param_dict_func.get('port', '')
                    if port_name and not self.connected:
                        self.CONNECTION_STATUS_CHANGED.emit(f"Opening port {port_name}...")
                        try:
                            self.ser = serial.Serial(**self.port_param_dict_func)
                            if hasattr(self.ser, 'set_buffer_size'):
                                self.ser.set_buffer_size(rx_size=4096, tx_size=4096)

                            self.start_read_send_thread()

                            if hasattr(self.ser, 'reset_input_buffer'):
                                self.ser.reset_input_buffer()
                                self.ser.reset_output_buffer()
                            else:
                                self.ser.flushInput()
                                self.ser.flushOutput()

                            CheckSerialThread.PORT_PARAM_DICT = {}
                            self.connected = True
                            self.CONNECTION_STATUS_CHANGED.emit(
                                f"Port {self.ser.port} successfully opened. "
                                f"[{self.ser.baudrate}, {self.ser.bytesize}, {self.ser.parity}, {self.ser.stopbits}]"
                            )
                            self.SERIAL_OPENED.emit(True)

                        except serial.SerialException as e:
                            self.connected = False
                            self.SERIAL_OPENED.emit(False)
                            self.CONNECTION_STATUS_CHANGED.emit(
                                f"Unable to open port {port_name}: {e}"
                            )
                            if 'PermissionError' in str(e):
                                self.auto_reconnect_from_failure(e, self.port_param_dict_func)
                            else:
                                self._pause_thread = False
                                self.auto_reconnect = True
                    elif not port_name:
                        self.CONNECTION_STATUS_CHANGED.emit("No serial port specified.")
                        self.SERIAL_OPENED.emit(False)
            except Exception as e:
                logger_info_console_file.error(f"Error in CheckSerialThread.run: {e}")
                self.CONNECTION_STATUS_CHANGED.emit(f"Serial Error: {e}")

    def start_read_send_thread(self):
        """Instantiate and start the ReadSendPort communication worker."""
        if self.read_send_thread and self.read_send_thread.isRunning():
            self.read_send_thread.stop()
            self.read_send_thread.wait(1000)

        self.read_send_thread = ReadSendPort(
            check_serial_thread=self,
            ser=self.ser,
            ui_main=self.ui,
            parent=self.parent
        )
        if self.parent and hasattr(self.parent, 'read_send_thread'):
            self.parent.read_send_thread = self.read_send_thread
        self.read_send_thread.start()

    def stop_read_send_thread(self):
        """Stop worker cleanly with timeout."""
        if self.read_send_thread:
            self.read_send_thread.stop()
            self.read_send_thread.wait(1500)

    def disconnect_from_port(self, auto_reconnect=False, pause_thread=True):
        """Safely close serial port and terminate communication thread."""
        with self._lock:
            self.stop_read_send_thread()
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except Exception as e:
                    logger_info_console_file.warning(f"Error closing serial port: {e}")
            self.ser = None
            self.connected = False
            self.auto_reconnect = auto_reconnect
            self._pause_thread = pause_thread
            self.CONNECTION_STATUS_CHANGED.emit("Serial port disconnected.")
            self.SERIAL_OPENED.emit(False)

    def pause_thread(self):
        self._pause_thread = True
        self.auto_reconnect = False

    def resume_thread(self):
        self._pause_thread = False
        self.auto_reconnect = True
        self.wait_condition.wakeAll()
        if not self.isRunning():
            self.start()

    def auto_reconnect_from_failure(self, failure_str, dict_port):
        """Attempt to reconnect to serial port if transiently unavailable."""
        CheckSerialThread.TIMEOUT_COUNT = 0
        while (self.ser is None or not self.connected) and CheckSerialThread.TIMEOUT_COUNT < CheckSerialThread.MAX_TIMEOUT:
            remaining = int(CheckSerialThread.MAX_TIMEOUT / 2 - CheckSerialThread.TIMEOUT_COUNT * 0.5)
            self.CONNECTION_STATUS_CHANGED.emit(
                f"Attempting to reopen port {dict_port.get('port', '')}, retry timeout: {remaining}s."
            )
            try:
                self.ser = serial.Serial(**dict_port)
                if hasattr(self.ser, 'set_buffer_size'):
                    self.ser.set_buffer_size(rx_size=4096, tx_size=4096)
                self.connected = True
                self.start_read_send_thread()
                if hasattr(self.ser, 'reset_input_buffer'):
                    self.ser.reset_input_buffer()
                    self.ser.reset_output_buffer()
                self.CONNECTION_STATUS_CHANGED.emit(
                    f"Port {self.ser.port} reopened successfully."
                )
                self.SERIAL_OPENED.emit(True)
                CheckSerialThread.PORT_PARAM_DICT = {}
                break
            except Exception:
                CheckSerialThread.TIMEOUT_COUNT += 1
                time.sleep(0.5)

        if not self.connected:
            self.CONNECTION_STATUS_CHANGED.emit("Reconnection timed out. Please check hardware connection.")
            self.SERIAL_OPENED.emit(False)


class ReadSendPort(QtCore.QThread):
    """
    Worker thread that continuously reads returned pump data and safely transmits commands.
    Communicates with the GUI entirely via PyQt6 signals.
    """
    # Signal emitted when a raw/decoded pump response arrives: (timestamp, text)
    SIGNAL_RESPONSE_RECEIVED = QtCore.pyqtSignal(str, str)
    # Signal emitted when a command is transmitted: (timestamp, text)
    SIGNAL_COMMAND_SENT = QtCore.pyqtSignal(str, str)
    # Signal emitted to update status bar: (mode_label, progress_percent)
    SIGNAL_PROGRESS_UPDATED = QtCore.pyqtSignal(str, int)
    # Signal emitted for canvas plotting: (flow_rate, flow_rate_unit, elapsed_time, transported_volume, current_status, target_str, len_run_commands)
    SIGNAL_DATA_POINT = QtCore.pyqtSignal(float, str, float, float, str, str, int)

    DECODE_STYLE = 'NoLF'
    __LINE_FEED_TYPE = (b':', b'<', b'>', b'*', b'T*')
    DECODE_TYPE = 'utf-8'
    ENCODE_TYPE = 'utf-8'
    PATTERN_DATA = QtCore.QRegularExpression(
        r"^\s*(\d+)\s*(\d+)\s*(\d+)\s*([iIwW][iIwW.][S.][T.][iIwW][T.])\s*([:<>*]|T\*)\s*$"
    )

    COUNT_OUTER = 0
    MAIN_WINDOW_LABEL = ''
    MAIN_WINDOW_PROGRESS = 0
    FLOW_RATE = 0
    FLOW_RATE_UNIT = ''
    ELAPSED_TIME = 0
    TRANSPORTED_VOLUME = 0
    RUNNING_MODE = ''
    TARGET_STR = ''
    LEN_RUN_COMMAND = 0
    run_commands_dict = {}
    progress_percent = 0.0

    conversion_dict = {
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

    def __init__(self, check_serial_thread=None, ser=None, ui_main=None, parent=None):
        super().__init__(parent)
        self.ui = ui_main
        self.ser = ser
        self.check_serial_thread = check_serial_thread
        self.parent = parent
        self.running = True

        self._io_lock = threading.RLock()
        self.timer_run = QtCore.QTimer()

        self.run_commands_set = {}
        self.run_commands_set_Syrm = {}
        self.run_commands_set_INF = {}
        self.run_commands_set_WD = {}
        self.run_INF = {}
        self.run_WD = {}
        self.run_INF_WD = {}
        self.run_WD_INF = {}
        self.run_commands = {}
        self.run_commands_list = []
        self.__RECEIVE_STATUS = None
        self.count_inner = 0

    @staticmethod
    def initialize_class_var():
        ReadSendPort.FLOW_RATE = 0
        ReadSendPort.FLOW_RATE_UNIT = ''
        ReadSendPort.ELAPSED_TIME = 0
        ReadSendPort.TRANSPORTED_VOLUME = 0
        ReadSendPort.RUNNING_MODE = ''
        ReadSendPort.TARGET_STR = ''
        ReadSendPort.MAIN_WINDOW_LABEL = ''
        ReadSendPort.MAIN_WINDOW_PROGRESS = 0
        ReadSendPort.COUNT_OUTER = 0
        ReadSendPort.progress_percent = 0.0

    @staticmethod
    def set_line_feed_style(ui, sender_check):
        if sender_check == ui.actionNo_line_feed:
            ReadSendPort.__LINE_FEED_TYPE = (b':', b'<', b'>', b'*', b'T*')
            ReadSendPort.DECODE_STYLE = 'NoLF'
        elif sender_check == ui.action_carrige_return:
            ReadSendPort.__LINE_FEED_TYPE = (b':\r', b'<\r', b'>\r', b'*\r', b'T*\r')
            ReadSendPort.DECODE_STYLE = 'CR'
        elif sender_check == ui.action_line_feed:
            ReadSendPort.__LINE_FEED_TYPE = (b':\n', b'<\n', b'>\n', b'*\n', b'T*\n')
            ReadSendPort.DECODE_STYLE = 'LF'
        elif sender_check == ui.action_CR_LF:
            ReadSendPort.__LINE_FEED_TYPE = (b':\r\n', b'<\r\n', b'>\r\n', b'*\r\n', b'T*\r\n')
            ReadSendPort.DECODE_STYLE = 'CR&LF'
        return ReadSendPort.__LINE_FEED_TYPE, ReadSendPort.DECODE_STYLE

    @staticmethod
    def decode_according_to_identifier(decode_style: str, response: bytes) -> str:
        try:
            if not decode_style or decode_style == 'NoLF':
                return response.decode(ReadSendPort.DECODE_TYPE, 'replace')
            elif decode_style == 'CR':
                return response.replace(b'\r', b'\r\n').decode(ReadSendPort.DECODE_TYPE, 'replace').strip()
            elif decode_style in ('LF', 'CR&LF'):
                return response.decode(ReadSendPort.DECODE_TYPE, 'replace').strip()
            return response.decode(ReadSendPort.DECODE_TYPE, 'replace').strip()
        except Exception:
            return response.decode('latin-1', 'replace').strip()

    def stop(self):
        """Flag thread to terminate and quit."""
        self.running = False

    def run(self):
        active_ser = self.ser or (self.check_serial_thread.ser if self.check_serial_thread else None)
        if active_ser is None:
            return

        while self.running:
            active_ser = self.ser or (self.check_serial_thread.ser if self.check_serial_thread else None)
            if not active_ser or not active_ser.is_open:
                break

            response = self.read_single_line(active_ser)
            if not response:
                time.sleep(0.01)
                continue

            current_time = QtCore.QDateTime.currentDateTime().toString("[hh:mm:ss]")
            response_dec = self.decode_according_to_identifier(ReadSendPort.DECODE_STYLE, response)
            result = self.handle_returned_data(response_dec.strip())

            if result is not None:
                flow_rate, elapsed_time, transported_volume, current_status, running_mode = result
                ReadSendPort.LEN_RUN_COMMAND = len(ReadSendPort.run_commands_dict)

                if ReadSendPort.LEN_RUN_COMMAND < 11:
                    if len(ReadSendPort.run_commands_dict) > 6:
                        target_dict = list(ReadSendPort.run_commands_dict.values())[6]
                        target_str = target_dict['command'].strip()
                        sequence_mode = list(ReadSendPort.run_commands_dict.keys())[6]
                        flow_rate_dict = list(ReadSendPort.run_commands_dict.values())[5]
                        flow_rate_str = flow_rate_dict['command'].strip()
                        flow_rate_unit = flow_rate_str.split(' ')[2]

                        if '@ttime' in target_str:
                            tokens = target_str.split(' ')
                            if len(tokens) > 2 and tokens[2] == 'Secs':
                                ReadSendPort.progress_percent = float(elapsed_time) * 1e-3 / float(tokens[1])
                            elif len(tokens) > 1:
                                parts = tokens[1].split(':')
                                if len(parts) == 3:
                                    total_sec = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                                    if total_sec > 0:
                                        ReadSendPort.progress_percent = float(elapsed_time) * 1e-3 / total_sec
                        else:
                            tokens = target_str.split(' ')
                            if len(tokens) > 2 and float(tokens[1]) > 0:
                                divisor = float(tokens[1])
                                if tokens[2] == 'pl':
                                    ReadSendPort.progress_percent = float(transported_volume) * 1e-3 / divisor
                                elif tokens[2] == 'nl':
                                    ReadSendPort.progress_percent = float(transported_volume) * 1e-6 / divisor
                                elif tokens[2] == 'ul':
                                    ReadSendPort.progress_percent = float(transported_volume) * 1e-9 / divisor
                                elif tokens[2] == 'ml':
                                    ReadSendPort.progress_percent = float(transported_volume) * 1e-12 / divisor

                        progress_int = min(100, max(0, math.ceil(ReadSendPort.progress_percent * 100)))
                        ReadSendPort.MAIN_WINDOW_LABEL = sequence_mode
                        ReadSendPort.MAIN_WINDOW_PROGRESS = progress_int
                        ReadSendPort.FLOW_RATE = flow_rate
                        ReadSendPort.FLOW_RATE_UNIT = flow_rate_unit
                        ReadSendPort.ELAPSED_TIME = elapsed_time
                        ReadSendPort.TRANSPORTED_VOLUME = transported_volume
                        ReadSendPort.RUNNING_MODE = current_status
                        ReadSendPort.TARGET_STR = target_str.split(' ')[2] if len(target_str.split(' ')) > 2 else ''

                        self.SIGNAL_PROGRESS_UPDATED.emit(sequence_mode, progress_int)
                        self.SIGNAL_DATA_POINT.emit(
                            flow_rate, flow_rate_unit, elapsed_time, transported_volume,
                            current_status, ReadSendPort.TARGET_STR, ReadSendPort.LEN_RUN_COMMAND
                        )

                else:
                    if len(ReadSendPort.run_commands_dict) > 11:
                        target_dict_1 = list(ReadSendPort.run_commands_dict.values())[6]
                        target_str_1 = target_dict_1['command'].strip()
                        target_dict_2 = list(ReadSendPort.run_commands_dict.values())[11]
                        target_str_2 = target_dict_2['command'].strip()

                        flow_rate_dict_1 = list(ReadSendPort.run_commands_dict.values())[5]
                        flow_rate_unit_1 = flow_rate_dict_1['command'].strip().split(' ')[2]

                        flow_rate_dict_2 = list(ReadSendPort.run_commands_dict.values())[10]
                        flow_rate_unit_2 = flow_rate_dict_2['command'].strip().split(' ')[2]

                        sequence_list = [
                            list(ReadSendPort.run_commands_dict.keys())[6],
                            list(ReadSendPort.run_commands_dict.keys())[11]
                        ]

                        if ReadSendPort.COUNT_OUTER < 9:
                            mode_name = sequence_list[0]
                            unit = flow_rate_unit_1
                            t_str = target_str_1
                        else:
                            mode_name = sequence_list[1]
                            unit = flow_rate_unit_2
                            t_str = target_str_2

                        progress_int = min(100, max(0, math.ceil(ReadSendPort.progress_percent * 100)))
                        ReadSendPort.MAIN_WINDOW_LABEL = mode_name
                        ReadSendPort.MAIN_WINDOW_PROGRESS = progress_int
                        self.SIGNAL_PROGRESS_UPDATED.emit(mode_name, progress_int)
                        self.SIGNAL_DATA_POINT.emit(
                            flow_rate, unit, elapsed_time, transported_volume,
                            current_status, t_str.split(' ')[2] if len(t_str.split(' ')) > 2 else '',
                            ReadSendPort.LEN_RUN_COMMAND
                        )

            else:
                # Prompt suffix detection
                if response_dec.endswith(':'):
                    ReadSendPort.__RECEIVE_STATUS = "Continue"
                elif response_dec.endswith('>'):
                    ReadSendPort.__RECEIVE_STATUS = "INF running"
                elif response_dec.endswith('<'):
                    ReadSendPort.__RECEIVE_STATUS = "WD running"
                elif response_dec.endswith('*'):
                    if response_dec[-2:] == 'T*':
                        ReadSendPort.__RECEIVE_STATUS = "Target reached"
                    else:
                        ReadSendPort.__RECEIVE_STATUS = "STOP"

                # Thread-safe signal to GUI
                self.SIGNAL_RESPONSE_RECEIVED.emit(current_time, response_dec)

    def read_single_line(self, ser_inst: serial.Serial) -> bytes:
        """Read a line or response token from serial port safely under IO lock."""
        with self._io_lock:
            try:
                if not ser_inst or not ser_inst.is_open:
                    return b''
                return ser_inst.readline()
            except (serial.SerialException, OSError) as e:
                logger_info_console_file.warning(f"Serial read error: {e}")
                self.running = False
                return b''

    def write_command(self, cmd: str) -> bool:
        """Thread-safe command write to pump."""
        active_ser = self.ser or (self.check_serial_thread.ser if self.check_serial_thread else None)
        with self._io_lock:
            if not active_ser or not active_ser.is_open:
                return False
            try:
                active_ser.write(cmd.encode(ReadSendPort.ENCODE_TYPE))
                return True
            except Exception as e:
                logger_info_console_file.error(f"Serial write error: {e}")
                return False

    @staticmethod
    def handle_returned_data(response_dec: str):
        match = ReadSendPort.PATTERN_DATA.match(response_dec)
        if match.hasMatch():
            values = match.capturedTexts()
            try:
                flow_rate = int(values[1].strip())
                elapsed_time = int(values[2].strip())
                transported_volume = int(values[3].strip())
                current_status = str(values[4].strip())
                running_mode = str(values[5].strip())
                return flow_rate, elapsed_time, transported_volume, current_status, running_mode
            except (ValueError, IndexError):
                return None
        return None

    @staticmethod
    def set_decode_format(ui, decode_sender):
        if decode_sender == ui.actionUTF_8:
            ReadSendPort.DECODE_TYPE = 'utf-8'
        elif decode_sender == ui.actionASCII:
            ReadSendPort.DECODE_TYPE = 'ascii'
        return ReadSendPort.DECODE_TYPE

    def ser_command_catalog(self):
        self.write_command('@cat\r\n')

    def ser_command_tilt(self):
        self.write_command('@tilt\r\n')

    def get_set_address(self, ui):
        addr = ui.address_input.text().strip()
        cmd = f"@addr. {addr}\r\n" if addr else "@addr. \r\n"
        self.write_command(cmd)

    def send_command_manual(self, ui):
        cmd_text = ui.lineEdit_send_toPump.currentText().strip()
        if not cmd_text:
            return
        current_time = QtCore.QDateTime.currentDateTime().toString("[hh:mm:ss]")
        full_cmd = f"@{cmd_text}\r\n"
        if self.write_command(full_cmd):
            ui.commands_sent.moveCursor(QtGui.QTextCursor.MoveOperation.End)
            ui.commands_sent.append(f"{current_time} >>\r\n{full_cmd}")
            if cmd_text not in [ui.lineEdit_send_toPump.itemText(i) for i in range(ui.lineEdit_send_toPump.count())]:
                ui.lineEdit_send_toPump.addItem(cmd_text)

    def ser_bgl_level(self, ui):
        val = ui.bgLight_Slider.value()
        current_time = QtCore.QDateTime.currentDateTime().toString("[hh:mm:ss]")
        if self.write_command(f"@dim {val}\r\n"):
            ui.commands_sent.moveCursor(QtGui.QTextCursor.MoveOperation.End)
            ui.commands_sent.append(f"{current_time} >>\r\nBackground light set to: {val} %\r\n")

    @staticmethod
    def ser_bgl_label_show(ui):
        ui.bgLight_Label.setText(f"BG-Light: {ui.bgLight_Slider.value()}[%]")

    def ser_force_limit(self, ui):
        val = ui.forceLimit_Slider.value()
        current_time = QtCore.QDateTime.currentDateTime().toString("[hh:mm:ss]")
        if self.write_command(f"@force {val}\r\n"):
            ui.commands_sent.moveCursor(QtGui.QTextCursor.MoveOperation.End)
            ui.commands_sent.append(f"{current_time} >>\r\nForce limit set to: {val} %\r\n")

    @staticmethod
    def ser_force_label_show(ui):
        ui.forceLimit_Label.setText(f"Force Limit: {ui.forceLimit_Slider.value()}[%]")

    def stop_pump_button(self):
        """Immediately stop pump execution."""
        self.write_command('@stop\r\n')

    def fast_forward_button(self, ui):
        if ui.fast_forward_btn.text() == 'FF':
            if self.write_command('@run\r\n'):
                ui.fast_forward_btn.setText('Stop')
        else:
            if self.write_command('@stop\r\n'):
                ui.fast_forward_btn.setText('FF')

    def fast_rewind_button(self, ui):
        if ui.rewinde_btn.text() == 'RW':
            if self.write_command('@rrun\r\n'):
                ui.rewinde_btn.setText('Stop')
        else:
            if self.write_command('@stop\r\n'):
                ui.rewinde_btn.setText('RW')

    def ser_quick_mode_command_set(self, ui, setups_dict_quick_mode: dict):
        with self._io_lock:
            update_combox_syr_enabled(ui, setups_dict_quick_mode)
            force_level = force_level_recommendation(ui)
            self.run_commands_set = {}
            self.run_commands_set_Syrm = {}
            self.run_commands_set_INF = {}
            self.run_commands_set_WD = {}

            clear_inf = {
                "Clear target t INF:": "@ctime\r\n",
                "Clear target V INF:": "@cvolume\r\n",
                "Writes to memory: OFF:": "@NVRAM\r\n",
                "Force level adjusted:": f"@force {force_level}\r\n"
            }
            clear_wd = {
                "Clear target t WD:": "@ctime\r\n",
                "Clear target V WD:": "@cvolume\r\n",
                "Writes to memory: OFF:": "@NVRAM\r\n",
                "Force level adjusted:": f"@force {force_level}\r\n"
            }

            syr_info = setups_dict_quick_mode.get('Syringe Info', {}).get('Selected Syringe', '')
            self.run_commands_set_Syrm['Syringe Type'] = {
                'prompt': f' >>Syringe selected: {syr_info}',
                'command': f'@syrm {syr_info}\r\n'
            }

            run_mode = setups_dict_quick_mode.get('Run Mode')
            flow_param = setups_dict_quick_mode.get('Flow Parameter', {})

            if run_mode in ('INF', 'INF/ WD'):
                frate = flow_param.get('Frate INF', '')
                target = flow_param.get('Target INF', '')
                self.run_commands_set_INF['Rate INF'] = {
                    'prompt': f' >>Infusion rate: {frate}',
                    'command': f'@irate {frate}\r\n'
                }
                cmd_prefix = '@tvolume' if 'l' in target else '@ttime'
                self.run_commands_set_INF['Target INF'] = {
                    'prompt': f' >>Target: {target}',
                    'command': f'{cmd_prefix} {target}\r\n'
                }
                self.run_commands_set_INF['Run Code INF'] = {
                    'prompt': ' >>Infusion running:',
                    'command': '@irun\r\n'
                }

            if run_mode in ('WD', 'WD/ INF', 'INF/ WD'):
                frate = flow_param.get('Frate WD', '')
                target = flow_param.get('Target WD', '')
                self.run_commands_set_WD['Rate WD'] = {
                    'prompt': f' >>Withdraw rate: {frate}',
                    'command': f'@wrate {frate}\r\n'
                }
                cmd_prefix = '@tvolume' if 'l' in target else '@ttime'
                self.run_commands_set_WD['Target WD'] = {
                    'prompt': f' >>Target: {target}',
                    'command': f'{cmd_prefix} {target}\r\n'
                }
                self.run_commands_set_WD['Run Code WD'] = {
                    'prompt': ' >>Withdraw running:',
                    'command': '@wrun\r\n'
                }

            self.run_commands = {}
            if run_mode == 'INF':
                self.run_commands.update(clear_inf)
                self.run_commands.update(self.run_commands_set_Syrm)
                self.run_commands.update(self.run_commands_set_INF)
                self.run_commands.update({'Get response INF:': b"@status\r\n"})
            elif run_mode == 'WD':
                self.run_commands.update(clear_wd)
                self.run_commands.update(self.run_commands_set_Syrm)
                self.run_commands.update(self.run_commands_set_WD)
                self.run_commands.update({'Get response WD:': b"@status\r\n"})
            elif run_mode == 'INF/ WD':
                self.run_commands.update(clear_inf)
                self.run_commands.update(self.run_commands_set_Syrm)
                self.run_commands.update(self.run_commands_set_INF)
                self.run_commands.update(clear_wd)
                self.run_commands.update(self.run_commands_set_WD)
                self.run_commands.update({'Get response WD:': b"@status\r\n"})
            elif run_mode == 'WD/ INF':
                self.run_commands.update(clear_wd)
                self.run_commands.update(self.run_commands_set_Syrm)
                self.run_commands.update(self.run_commands_set_WD)
                self.run_commands.update(clear_inf)
                self.run_commands.update(self.run_commands_set_INF)
                self.run_commands.update({'Get response INF:': b"@status\r\n"})

            ReadSendPort.run_commands_dict = dict(self.run_commands)
            self.run_commands_list = list(self.run_commands.items())

    def send_run_commands(self):
        """Sequential command runner with non-blocking singleShot scheduling."""
        if ReadSendPort.COUNT_OUTER < len(self.run_commands_list):
            item = self.run_commands_list[ReadSendPort.COUNT_OUTER]
            key, val = item[0], item[1]

            if ReadSendPort.__RECEIVE_STATUS in (None, 'Continue'):
                current_time = QtCore.QDateTime.currentDateTime().toString("[hh:mm:ss]")
                if isinstance(val, dict):
                    prompt = val.get('prompt', '')
                    cmd = val.get('command', '')
                    self.ui.commands_sent.append(f"{current_time}{prompt}\r\n")
                    self.write_command(cmd)
                    ReadSendPort.COUNT_OUTER += 1
                    self.timer_run.singleShot(300, self.send_run_commands)
                elif isinstance(val, str):
                    self.ui.commands_sent.append(f"{current_time} >>{key}\r\n")
                    self.write_command(val)
                    ReadSendPort.COUNT_OUTER += 1
                    self.timer_run.singleShot(300, self.send_run_commands)
                elif isinstance(val, bytes):
                    ReadSendPort.COUNT_OUTER += 1
                    self.timer_run.singleShot(300, self.send_run_commands)

            elif ReadSendPort.__RECEIVE_STATUS in ("INF running", "WD running", "Target reached"):
                if ReadSendPort.__RECEIVE_STATUS != 'Target reached':
                    self.write_command("@status\r\n")
                    self.timer_run.singleShot(80, self.send_run_commands)
                else:
                    if ReadSendPort.RUNNING_MODE:
                        if ReadSendPort.COUNT_OUTER <= 8 and ReadSendPort.RUNNING_MODE[0] in ('i', 'I'):
                            self.write_command("@citime\r\n")
                            self.write_command("@civolume\r\n")
                        elif ReadSendPort.COUNT_OUTER <= 8 and ReadSendPort.RUNNING_MODE[0] in ('w', 'W'):
                            self.write_command("@cwtime\r\n")
                            self.write_command("@cwvolume\r\n")
                    self.timer_run.singleShot(300, self.send_run_commands)

            elif ReadSendPort.__RECEIVE_STATUS == 'STOP':
                self.timer_run.stop()
        else:
            self.timer_run.stop()
            ReadSendPort.COUNT_OUTER = 0
            self.run_commands_list = []
            self.run_commands = {}

    def clear_from_button(self, ui):
        ReadSendPort.COUNT_OUTER = 0
        ReadSendPort.MAIN_WINDOW_LABEL = ''
        ReadSendPort.MAIN_WINDOW_PROGRESS = 0
        ui.running_mode.setText('')
        ui.progress_bar_running.setValue(0)
        self.write_command("@ctime\r\n")
        self.write_command("@cvolume\r\n")


def receive_dict(check_serial_thread, _param_dict):
    check_serial_thread.set_port_params(_param_dict)


def disconnect_from_port_call(check_serial_thread, auto_reconnect=False, _pause_thread=True):
    check_serial_thread.disconnect_from_port(auto_reconnect=auto_reconnect, pause_thread=_pause_thread)


def update_connection_status(ui, status: str):
    ui.status_label.setText(f"  {status}")
    if "successfully opened" in status.lower():
        ui.status_label.setStyleSheet("color: green; font-weight: bold;")
    elif "unable" in status.lower() or "error" in status.lower():
        ui.status_label.setStyleSheet("color: red; font-weight: bold;")
    else:
        ui.status_label.setStyleSheet("color: grey;")


def detect_ports(combo_box):
    combo_box.clear()
    ports = [f"{p.device}: {p.description}" for p in serial.tools.list_ports.comports()]
    combo_box.addItems(ports)


def show_port_setup_dialog(child_ui_port):
    child_ui_port.show()
    detect_ports(child_ui_port.ComboBox_port_name)


def show_user_defined_dialog(ui_child_steps_dialog):
    ui_child_steps_dialog.show()
