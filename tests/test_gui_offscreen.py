# -*- coding: utf-8 -*-
"""
Offscreen GUI tests for PyQt6 MainWindow and dialogs.
"""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6 import QtWidgets, QtCore, QtGui
import main
import functions


class TestGUIOffscreen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        main.load_application_fonts()

    def test_main_window_instantiation(self):
        window = main.MainWindow()
        self.assertIsNotNone(window)
        self.assertIsNotNone(window.ui_main)
        self.assertIsNotNone(window.mpl_canvas)
        window.close()

    def test_child_dialogs_instantiation(self):
        port_dialog = main.PortSetupChildWindow()
        self.assertIsNotNone(port_dialog)
        port_dialog.close()

        steps_dialog = main.StepsDialogChildWindow()
        self.assertIsNotNone(steps_dialog)
        steps_dialog.close()

        guide_dialog = main.StepGuideChildWindow()
        self.assertIsNotNone(guide_dialog)
        guide_dialog.close()

    def test_canvas_export_components(self):
        window = main.MainWindow()
        canvas = window.mpl_canvas
        self.assertIsNotNone(canvas.fig)
        self.assertIsNotNone(canvas.ax)
        window.close()


if __name__ == "__main__":
    unittest.main()
