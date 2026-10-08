# -*- coding: utf-8 -*-
"""Dialog windows for PHD Ultra GUI: Port Setup, Steps Selection, and Step Guide."""

from PyQt6 import QtCore, QtGui, QtWidgets

from PortSetup_child_UI import Ui_Dialog_PortSetup
from StepGuide_child_UI import Ui_Dialog_StepDetails
from UserDefinedSteps_child_UI import Ui_Dialog as Ui_Dialog_UserDefinedSteps


import resources_rc


class StepsDialogChildWindow(QtWidgets.QDialog, Ui_Dialog_UserDefinedSteps):
    """Dialog for choosing custom method steps."""

    selected_items = QtCore.pyqtSignal(str, QtGui.QIcon)

    def __init__(self, parent=None):
        super(StepsDialogChildWindow, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.setModal(True)
        self.buttonBox.accepted.connect(self.get_selected_item)

    def get_selected_item(self):
        """Retrieve the currently selected item and emit signal."""
        selected_items = self.listWidget.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.selected_items.emit(item.text(), item.icon())
            return item
        return None


class PortSetupChildWindow(QtWidgets.QDialog, Ui_Dialog_PortSetup):
    """Dialog for configuring serial communication parameters."""

    # Signal emitted when serial parameters are accepted by the user
    dictReady = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super(PortSetupChildWindow, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.setModal(True)
        self.port_param_dict = {}
        self.parity_list = ['N', 'E', 'O', 'M', 'S']

        self.baudrate_current = None
        self.validator = QtGui.QIntValidator(self)
        self.line_timeout.setValidator(self.validator)

        self.ComboBox_baudrate.currentIndexChanged.connect(self.on_baudrate_changed)
        self.buttonBox.accepted.connect(self.get_setup_params)

    def on_baudrate_changed(self):
        """Handle custom baudrate selection."""
        self.baudrate_current = self.ComboBox_baudrate.currentText()
        if self.baudrate_current == 'Custom':
            self.ComboBox_baudrate.setEditable(True)
            self.ComboBox_baudrate.setCurrentText('')
            self.ComboBox_baudrate.setValidator(self.validator)
        else:
            self.ComboBox_baudrate.setEditable(False)

    def get_setup_params(self):
        """Validate and package serial parameters dictionary."""
        port_text = self.ComboBox_port_name.currentText()
        if port_text:
            self.port_param_dict['port'] = port_text.split(':')[0].strip()
        else:
            self.port_param_dict['port'] = ''
            QtWidgets.QMessageBox.information(self, 'Invalid setup', 'Please check the available ports status.')

        baud_text = self.ComboBox_baudrate.currentText()
        if baud_text:
            try:
                baud_val = int(baud_text)
                if baud_val < 9600:
                    self.port_param_dict['baudrate'] = 9600
                    QtWidgets.QMessageBox.information(self, 'Invalid baud rate', 'Default baud rate set to 9600.')
                else:
                    self.port_param_dict['baudrate'] = baud_val
            except ValueError:
                self.port_param_dict['baudrate'] = 9600
                QtWidgets.QMessageBox.information(self, 'Invalid baud rate', 'Default baud rate set to 9600.')

        if self.ComboBox_data_bits.currentText():
            self.port_param_dict['bytesize'] = int(self.ComboBox_data_bits.currentText())

        if self.ComboBox_parity.currentText():
            self.port_param_dict['parity'] = self.parity_list[self.ComboBox_parity.currentIndex()]

        stop_text = self.ComboBox_stop_bits.currentText()
        if stop_text:
            if stop_text == '1.5':
                self.port_param_dict['stopbits'] = 1.5
            else:
                self.port_param_dict['stopbits'] = int(stop_text)

        flow_text = self.ComboBox_flow_type.currentText()
        if flow_text == 'None':
            self.port_param_dict['xonxoff'] = False
            self.port_param_dict['rtscts'] = False
        elif flow_text == 'RTS/ CTS':
            self.port_param_dict['xonxoff'] = False
            self.port_param_dict['rtscts'] = True
        elif flow_text == 'XON/ XOFF':
            self.port_param_dict['xonxoff'] = True
            self.port_param_dict['rtscts'] = False

        timeout_text = self.line_timeout.text().strip()
        if timeout_text:
            try:
                self.port_param_dict['timeout'] = int(timeout_text)
            except ValueError:
                self.port_param_dict['timeout'] = 0
        else:
            self.port_param_dict['timeout'] = 0
            QtWidgets.QMessageBox.information(self, 'No timeout specified', 'Default timeout set to 0.')

        if self.port_param_dict.get('port'):
            self.dictReady.emit(self.port_param_dict)


class StepGuideChildWindow(QtWidgets.QDialog, Ui_Dialog_StepDetails):
    """Dialog displaying parameter guide and reference illustration for a method step."""

    def __init__(self, parent=None):
        super(StepGuideChildWindow, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.setModal(True)

        self.text = None
        self.image_label = QtWidgets.QLabel()
        self.layout = QtWidgets.QVBoxLayout(self.groupBox)
