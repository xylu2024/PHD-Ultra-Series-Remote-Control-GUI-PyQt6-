# -*- coding: utf-8 -*-
"""
System Tray Widget and Global Hotkey Integration.
"""

from PyQt6 import QtCore, QtGui, QtWidgets
from phd_ultra.config.logging import logger_info_console_file

try:
    import global_hotkeys as hotkey
except ImportError:
    hotkey = None


class MySysTrayWidget(QtWidgets.QWidget):
    hotkey_hide_window = QtCore.pyqtSignal(bool)

    def __init__(self, ui=None, app=None, window=None):
        super().__init__()
        self.__ui = ui
        self.__app = app
        self.__window = window

        self.__trayicon = QtWidgets.QSystemTrayIcon(self)
        icon = QtGui.QIcon(':window_icon_/Logo_TU_Dresden_small.svg')
        if not icon.isNull():
            self.__trayicon.setIcon(icon)
        self.__trayicon.setToolTip('PHD Ultra Remote Control\nHotkey: Ctrl+Alt+M')

        # Context menu
        self.__traymenu = QtWidgets.QMenu()
        self.__trayaction = []
        self.addTrayMenuAction('Show Window', self.show_userinterface)
        self.addTrayMenuAction('Exit Application', self.quit)

        self.__trayicon.setContextMenu(self.__traymenu)
        self.__trayicon.show()

        # Global hotkey
        if hotkey is not None:
            self.hotkey_bindings = [
                [["control", "alt", "m"], None, self.wakeHotkey],
            ]
            try:
                hotkey.register_hotkeys(self.hotkey_bindings)
                hotkey.start_checking_hotkeys()
            except Exception as e:
                logger_info_console_file.warning(f"Could not register tray hotkey: {e}")

        self.hotkey_hide_window.connect(self.onHotkey)
        self.__trayicon.activated.connect(self.trayIconActivated)

    def addTrayMenuAction(self, text: str, callback):
        action = QtGui.QAction(text, self)
        action.triggered.connect(callback)
        self.__traymenu.addAction(action)
        self.__trayaction.append(action)

    def trayIconActivated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_userinterface()

    def quit(self):
        """Clean shutdown and exit."""
        if hotkey is not None:
            try:
                hotkey.stop_checking_hotkeys()
            except Exception:
                pass
        if self.__app:
            self.__app.quit()

    def show_userinterface(self):
        if self.__window:
            self.__window.show()
            self.__window.activateWindow()
            self.__window.raise_()

    def hide_userinterface(self):
        if self.__window:
            self.__window.hide()

    def wakeHotkey(self):
        if self.__window:
            self.hotkey_hide_window.emit(self.__window.isVisible())

    @QtCore.pyqtSlot(bool)
    def onHotkey(self, visible: bool):
        if visible:
            self.hide_userinterface()
        else:
            self.show_userinterface()
