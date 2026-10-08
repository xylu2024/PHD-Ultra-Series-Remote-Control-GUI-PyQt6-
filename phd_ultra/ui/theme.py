# -*- coding: utf-8 -*-
"""
Theme management for PyQt6 GUI (Native, Light, and Dark themes).
Provides built-in pure QSS stylesheets with optional qdarktheme integration.
"""

from PyQt6 import QtCore, QtGui, QtWidgets
import matplotlib.font_manager as font_manager

try:
    import qdarktheme
except ImportError:
    qdarktheme = None

DARK_THEME_QSS = """
QWidget {
    background-color: #202124;
    color: #e8eaed;
    font-family: 'Open Sans', 'Segoe UI', sans-serif;
}
QTextEdit, QPlainTextEdit {
    background-color: #2d2e31;
    color: #e8eaed;
    border: 1px solid #5f6368;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 10pt;
}
QLineEdit {
    background-color: #2d2e31;
    color: #e8eaed;
    border: 1px solid #5f6368;
    border-radius: 3px;
    padding: 3px 6px;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #8ab4f8;
}
QListWidget {
    background-color: #2d2e31;
    color: #e8eaed;
    border: 1px solid #5f6368;
    border-radius: 4px;
}
QListWidget::item {
    margin: 3px;
    padding: 4px;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #1a73e8;
    color: #ffffff;
}
QPushButton {
    background-color: #3c4043;
    color: #e8eaed;
    border: 1px solid #5f6368;
    border-radius: 4px;
    padding: 4px 12px;
    min-height: 22px;
}
QPushButton:hover {
    background-color: #4a4d51;
}
QPushButton:pressed {
    background-color: #1a73e8;
    color: #ffffff;
}
QPushButton:disabled {
    background-color: #28292c;
    color: #80868b;
    border-color: #3c4043;
}
QComboBox {
    background-color: #2d2e31;
    color: #e8eaed;
    border: 1px solid #5f6368;
    border-radius: 3px;
    padding: 3px 8px;
}
QComboBox QAbstractItemView {
    background-color: #2d2e31;
    color: #e8eaed;
    selection-background-color: #1a73e8;
}
QTabWidget::pane {
    border: 1px solid #5f6368;
    background-color: #202124;
}
QTabBar::tab {
    background-color: #2d2e31;
    color: #9aa0a6;
    padding: 6px 14px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #3c4043;
    color: #ffffff;
    font-weight: bold;
}
QGroupBox {
    border: 1px solid #5f6368;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #e8eaed;
}
QMenuBar {
    background-color: #202124;
    color: #e8eaed;
}
QMenuBar::item:selected {
    background-color: #3c4043;
}
QMenu {
    background-color: #2d2e31;
    color: #e8eaed;
    border: 1px solid #5f6368;
}
QMenu::item:selected {
    background-color: #1a73e8;
    color: #ffffff;
}
QStatusBar {
    background-color: #18191c;
    color: #9aa0a6;
}
QProgressBar {
    border: 1px solid #5f6368;
    border-radius: 4px;
    text-align: center;
    background-color: #2d2e31;
    color: #ffffff;
}
QProgressBar::chunk {
    background-color: #1a73e8;
}
QSlider::groove:horizontal {
    height: 4px;
    background: #5f6368;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #8ab4f8;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}
QToolTip {
    background-color: #303134;
    color: #e8eaed;
    border: 1px solid #5f6368;
    padding: 4px;
}
"""

LIGHT_THEME_QSS = """
QWidget {
    background-color: #f8f9fa;
    color: #202124;
    font-family: 'Open Sans', 'Segoe UI', sans-serif;
}
QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #202124;
    border: 1px solid #dadce0;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 10pt;
}
QLineEdit {
    background-color: #ffffff;
    color: #202124;
    border: 1px solid #dadce0;
    border-radius: 3px;
    padding: 3px 6px;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #1a73e8;
}
QListWidget {
    background-color: #ffffff;
    color: #202124;
    border: 1px solid #dadce0;
    border-radius: 4px;
}
QListWidget::item {
    margin: 3px;
    padding: 4px;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #1a73e8;
    color: #ffffff;
}
QPushButton {
    background-color: #f1f3f4;
    color: #202124;
    border: 1px solid #dadce0;
    border-radius: 4px;
    padding: 4px 12px;
    min-height: 22px;
}
QPushButton:hover {
    background-color: #e8eaed;
}
QPushButton:pressed {
    background-color: #1a73e8;
    color: #ffffff;
}
QComboBox {
    background-color: #ffffff;
    color: #202124;
    border: 1px solid #dadce0;
    border-radius: 3px;
    padding: 3px 8px;
}
QGroupBox {
    border: 1px solid #dadce0;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #202124;
}
QMenuBar {
    background-color: #f8f9fa;
    color: #202124;
}
QMenu {
    background-color: #ffffff;
    color: #202124;
    border: 1px solid #dadce0;
}
QStatusBar {
    background-color: #f1f3f4;
    color: #5f6368;
}
QProgressBar {
    border: 1px solid #dadce0;
    border-radius: 4px;
    text-align: center;
    background-color: #e8eaed;
    color: #202124;
}
QProgressBar::chunk {
    background-color: #1a73e8;
}
"""


def switch_theme_qdarktheme(ui, ui_step, mpl_canvas, theme_sender, app=None, style_sheet=None) -> None:
    """Switch application theme and dynamically re-style Matplotlib canvas."""
    qss_additional = """
    QTextEdit { font-family: 'Courier New'; font-size: 10pt; }
    QFrame { border: none; }
    QListWidget::item { margin-top: 5px; }
    QListWidget { border: 1px solid gray; }
    QGraphicsView { border: 1px solid gray; }
    """

    font_resource = QtCore.QResource(":font_/OpenSans-Medium.ttf")
    if font_resource.isValid():
        font_data = font_resource.data()
        temp_font_file = QtCore.QTemporaryFile()
        temp_font_file.open()
        temp_font_file.write(font_data)
        temp_font_file.close()
        mpl_canvas.font_path = temp_font_file.fileName()
        mpl_canvas.tick_font_prop = font_manager.FontProperties(fname=mpl_canvas.font_path, size=9)
        mpl_canvas.font_prop = font_manager.FontProperties(fname=mpl_canvas.font_path, size=9)
        mpl_canvas.title_font = font_manager.FontProperties(fname=mpl_canvas.font_path, size=10)

    if theme_sender == ui.actionDefaultTheme:
        if app:
            app.setStyle('windowsvista' if 'windowsvista' in QtWidgets.QStyleFactory.keys() else 'Fusion')
            app.setStyleSheet(style_sheet or "")
        ui.menubar.setStyleSheet("color: black")
        mpl_canvas.fig.set_facecolor((235/255, 235/255, 235/255))
        mpl_canvas.ax.set_facecolor('white')
        mpl_canvas.ax.tick_params(axis='both', colors='black')
        mpl_canvas.ax.spines['bottom'].set_color('black')
        mpl_canvas.ax.spines['left'].set_color('black')
        mpl_canvas.ax.set_xlabel('Time [s]', color='black', fontproperties=mpl_canvas.font_prop)
        mpl_canvas.ax.set_ylabel(r'Flow rate [ml/s]', color='black', fontproperties=mpl_canvas.font_prop)
        mpl_canvas.ax.grid(True)
        mpl_canvas.fig.tight_layout()
        mpl_canvas.fig.canvas.draw()

    elif theme_sender == ui.actionDark:
        if app:
            app.setStyleSheet("")
        ui.menubar.setStyleSheet("")
        ui.listWidget_userDefined_method.setStyleSheet("")
        ui_step.listWidget.setStyleSheet("")

        mpl_canvas.fig.set_facecolor((32/255, 33/255, 36/255))
        mpl_canvas.ax.set_facecolor((57/255, 58/255, 62/255))
        mpl_canvas.ax.tick_params(axis='both', colors='white')
        mpl_canvas.ax.spines['bottom'].set_color('white')
        mpl_canvas.ax.spines['left'].set_color('white')
        mpl_canvas.ax.set_xlabel('Time [s]', color='white', fontproperties=mpl_canvas.font_prop)
        mpl_canvas.ax.set_ylabel(r'Flow rate [ml/s]', color='white', fontproperties=mpl_canvas.font_prop)
        mpl_canvas.ax.grid(True)
        mpl_canvas.fig.tight_layout()
        mpl_canvas.fig.canvas.draw()

        if qdarktheme:
            if hasattr(qdarktheme, 'setup_theme'):
                qdarktheme.setup_theme('dark', additional_qss=qss_additional)
            elif hasattr(qdarktheme, 'load_stylesheet') and app:
                app.setStyleSheet(qdarktheme.load_stylesheet('dark') + "\n" + qss_additional)
        elif app:
            app.setStyle('Fusion')
            app.setStyleSheet(DARK_THEME_QSS)

    elif theme_sender == ui.actionLight:
        if app:
            app.setStyleSheet("")
        ui.menubar.setStyleSheet("")
        ui.listWidget_userDefined_method.setStyleSheet("")
        ui_step.listWidget.setStyleSheet("")

        mpl_canvas.fig.set_facecolor('white')
        mpl_canvas.ax.set_facecolor('white')
        mpl_canvas.ax.tick_params(axis='both', colors='black')
        mpl_canvas.ax.spines['bottom'].set_color('black')
        mpl_canvas.ax.spines['left'].set_color('black')
        mpl_canvas.ax.set_xlabel('Time [s]', color='black', fontproperties=mpl_canvas.font_prop)
        mpl_canvas.ax.set_ylabel(r'Flow rate [ml/s]', color='black', fontproperties=mpl_canvas.font_prop)
        mpl_canvas.ax.grid(True)
        mpl_canvas.fig.tight_layout()
        mpl_canvas.fig.canvas.draw()

        if qdarktheme:
            if hasattr(qdarktheme, 'setup_theme'):
                qdarktheme.setup_theme('light', additional_qss=qss_additional)
            elif hasattr(qdarktheme, 'load_stylesheet') and app:
                app.setStyleSheet(qdarktheme.load_stylesheet('light') + "\n" + qss_additional)
        elif app:
            app.setStyle('Fusion')
            app.setStyleSheet(LIGHT_THEME_QSS)


def apply_dark_theme(app=None):
    """Apply dark theme to QApplication instance."""
    if qdarktheme:
        if hasattr(qdarktheme, 'setup_theme'):
            qdarktheme.setup_theme('dark')
        elif hasattr(qdarktheme, 'load_stylesheet') and app:
            app.setStyleSheet(qdarktheme.load_stylesheet('dark'))
    elif app:
        app.setStyle('Fusion')
        app.setStyleSheet(DARK_THEME_QSS)


def apply_light_theme(app=None):
    """Apply light theme to QApplication instance."""
    if qdarktheme:
        if hasattr(qdarktheme, 'setup_theme'):
            qdarktheme.setup_theme('light')
        elif hasattr(qdarktheme, 'load_stylesheet') and app:
            app.setStyleSheet(qdarktheme.load_stylesheet('light'))
    elif app:
        app.setStyle('Fusion')
        app.setStyleSheet(LIGHT_THEME_QSS)
