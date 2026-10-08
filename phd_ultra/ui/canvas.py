# -*- coding: utf-8 -*-
"""
Matplotlib Canvas Integration for PyQt6 GUI.
Provides dynamic flow rate and volume visualization, axis auto-scaling, and TXT/PNG data export.
"""

import os
import numpy as np

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
import matplotlib.font_manager as font_manager
from PyQt6 import QtCore, QtGui, QtWidgets


class GraphicalMplCanvas(FigureCanvas):
    DRAW_POINTS_FLOW_RATE = []
    DRAW_POINTS_TRANS_VOLUME = []
    DRAW_POINTS_ELAPSED_TIME = []
    max_flow_volume = float(0)
    min_flow_volume = float(0)
    current_volume_inf_wd = 0
    current_volume_wd_inf = 0
    max_time_len = 0
    temp_volume = []

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.segments_flow_rate = []
        self.segments_trans_volume = []
        self.max_time_lim = 0
        self.y_lim_upper = 0
        self.y_lim_lower = 0
        self.temp_x_array = np.empty(0)
        self.temp_y_array = np.empty(0)

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)

        self.lc_flow_rate = None
        self.lc_trans_volume = None

        self.flow_rate_legend_added = False
        self.transported_volume_legend_added = False
        self.legend = None

        super().__init__(self.fig)

        self.tick_font_prop = None
        self.font_prop = None
        self.font_path = None
        self.title_font = None

        # Add toolbar to parent window if parent has toolbar support
        if parent and hasattr(parent, 'addToolBar'):
            self.tool_bar = NavigationToolbar2QT(self, parent)
            parent.addToolBar(self.tool_bar)

        self.initialize_graph(axis_label_color='black')

    def initialize_graph(self, axis_label_color='black'):
        self.fig.tight_layout()
        self.ax.cla()

        font_resource = QtCore.QResource(":font_/OpenSans-Medium.ttf")
        if font_resource.isValid():
            font_data = font_resource.data()
            temp_font_file = QtCore.QTemporaryFile()
            temp_font_file.open()
            temp_font_file.write(font_data)
            temp_font_file.close()
            self.font_path = temp_font_file.fileName()
            self.tick_font_prop = font_manager.FontProperties(fname=self.font_path, size=9)
            self.font_prop = font_manager.FontProperties(fname=self.font_path, size=9)
            self.title_font = font_manager.FontProperties(fname=self.font_path, size=10)
        else:
            self.tick_font_prop = font_manager.FontProperties(size=9)
            self.font_prop = font_manager.FontProperties(size=9)
            self.title_font = font_manager.FontProperties(size=10)

        self.ax.set_xlabel('', color=axis_label_color)
        self.ax.set_ylabel('', color=axis_label_color)
        self.ax.set_title(' ', fontproperties=self.title_font)
        self.ax.set_xlabel('Time [s]', fontproperties=self.font_prop)
        self.ax.set_ylabel(r'Flow rate [ml/s]', fontproperties=self.font_prop)
        self.fig.tight_layout()
        self.ax.grid(True)

        self.flow_rate_legend_added = False
        self.transported_volume_legend_added = False

        self.ax.xaxis.set_tick_params(labelsize=8)
        self.ax.yaxis.set_tick_params(labelsize=8)

        # Reset data sets
        GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME = []
        GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME = []
        GraphicalMplCanvas.DRAW_POINTS_FLOW_RATE = []
        GraphicalMplCanvas.max_flow_volume = float(0)
        GraphicalMplCanvas.min_flow_volume = float(0)
        GraphicalMplCanvas.current_volume_inf_wd = 0
        GraphicalMplCanvas.current_volume_wd_inf = 0
        GraphicalMplCanvas.max_time_len = 0
        GraphicalMplCanvas.temp_volume = []

        self.segments_flow_rate = []
        self.segments_trans_volume = []
        self.max_time_lim = 0
        self.y_lim_upper = 0
        self.y_lim_lower = 0
        self.temp_x_array = np.empty(0)
        self.temp_y_array = np.empty(0)
        self.lc_flow_rate = LineCollection([], colors='blue')
        self.lc_trans_volume = LineCollection([], color='green')

        self.ax.add_collection(self.lc_flow_rate)
        self.ax.add_collection(self.lc_trans_volume)

        self.fig.canvas.draw()

    def update_graph(self, flow_rate, flow_rate_unit, elapsed_time, transported_volume, running_mode, count_outer,
                     target_str, len_run_commands):
        if running_mode:
            if running_mode[0] in ('i', 'I'):
                flow_rate = float(flow_rate) * 1e-12
                elapsed_time = float(elapsed_time) * 1e-3
                transported_volume = float(transported_volume) * 1e-12
            else:
                flow_rate = -float(flow_rate) * 1e-12
                elapsed_time = float(elapsed_time) * 1e-3
                transported_volume = -float(transported_volume) * 1e-12

        if flow_rate and (
                transported_volume not in GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME and
                elapsed_time not in GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME):

            if len_run_commands < 11:  # Quick mode INF or WD
                if (len(GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME) > 0 and
                        len(GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME) > 0 and
                        len(GraphicalMplCanvas.DRAW_POINTS_FLOW_RATE) > 0):

                    prev_elapsed_time = GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME[-1]
                    prev_flow_rate = GraphicalMplCanvas.DRAW_POINTS_FLOW_RATE[-1]
                    prev_trans_volume = GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME[-1]

                    self.temp_x_array = np.append(self.temp_x_array, prev_elapsed_time)
                    self.temp_y_array = np.append(self.temp_y_array, prev_flow_rate)
                    self.temp_y_array = np.append(self.temp_y_array, prev_trans_volume)

                    self.max_time_len = np.max(self.temp_x_array, axis=0)
                    self.y_lim_lower, self.y_lim_upper = np.min(self.temp_y_array, axis=0), np.max(self.temp_y_array, axis=0)

                    segment_flow_rate = [(prev_elapsed_time, prev_flow_rate), (elapsed_time, flow_rate)]
                    self.segments_flow_rate.append(segment_flow_rate)
                    connected_segments_flow_rate = np.concatenate(self.segments_flow_rate)
                    self.lc_flow_rate.set_segments([connected_segments_flow_rate])

                    segment_trans_volume = [(prev_elapsed_time, prev_trans_volume), (elapsed_time, transported_volume)]
                    self.segments_trans_volume.append(segment_trans_volume)
                    connected_segments_trans_volume = np.concatenate(self.segments_trans_volume)
                    self.lc_trans_volume.set_segments([connected_segments_trans_volume])

                    self.ax.set_xlim(0, self.max_time_len * 1.1)
                    self.ax.set_ylim(self.y_lim_lower * 1.35, self.y_lim_upper * 1.35)

                    if not self.flow_rate_legend_added:
                        self.ax.plot([], [], 'b-', label=r'Flow rate [ml/s]')
                        self.flow_rate_legend_added = True
                        self.legend = self.ax.legend(loc='upper right', fontsize=9)

                    if not self.transported_volume_legend_added:
                        self.ax.plot([], [], 'g-', label=r'Transported volume [ml]')
                        self.transported_volume_legend_added = True
                        self.legend = self.ax.legend(loc='upper right', fontsize=9)

                GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME.append(transported_volume)
                GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME.append(elapsed_time)
                GraphicalMplCanvas.DRAW_POINTS_FLOW_RATE.append(flow_rate)

            else:  # Compound modes: INF->WD or WD->INF
                if count_outer < 11 and flow_rate > 0:
                    if (len(GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME) > 0 and
                            len(GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME) > 0 and
                            len(GraphicalMplCanvas.DRAW_POINTS_FLOW_RATE) > 0):

                        GraphicalMplCanvas.max_flow_volume = max(GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME)
                        GraphicalMplCanvas.max_time_len = max(GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME)

                        prev_elapsed_time = GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME[-1]
                        prev_flow_rate = GraphicalMplCanvas.DRAW_POINTS_FLOW_RATE[-1]
                        prev_trans_volume = GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME[-1]

                        self.temp_x_array = np.append(self.temp_x_array, prev_elapsed_time)
                        self.temp_y_array = np.append(self.temp_y_array, prev_flow_rate)
                        self.temp_y_array = np.append(self.temp_y_array, prev_trans_volume)

                        self.max_time_len = np.max(self.temp_x_array, axis=0)
                        self.y_lim_lower, self.y_lim_upper = np.min(self.temp_y_array, axis=0), np.max(self.temp_y_array, axis=0)

                        segment_flow_rate = [(prev_elapsed_time, prev_flow_rate), (elapsed_time, flow_rate)]
                        self.segments_flow_rate.append(segment_flow_rate)
                        connected_segments_flow_rate = np.concatenate(self.segments_flow_rate)
                        self.lc_flow_rate.set_segments([connected_segments_flow_rate])

                        segment_trans_volume = [(prev_elapsed_time, prev_trans_volume), (elapsed_time, transported_volume)]
                        self.segments_trans_volume.append(segment_trans_volume)
                        connected_segments_trans_volume = np.concatenate(self.segments_trans_volume)
                        self.lc_trans_volume.set_segments([connected_segments_trans_volume])

                        self.ax.set_xlim(0, self.max_time_len * 1.1)
                        self.ax.set_ylim(self.y_lim_lower * 1.35, self.y_lim_upper * 1.35)

                        if not self.flow_rate_legend_added:
                            self.ax.plot([], [], 'b-', label=r'Flow rate [ml/s]')
                            self.flow_rate_legend_added = True
                            self.legend = self.ax.legend(loc='upper right', fontsize=9)

                        if not self.transported_volume_legend_added:
                            self.ax.plot([], [], 'g-', label=r'Transported volume [ml]')
                            self.transported_volume_legend_added = True
                            self.legend = self.ax.legend(loc='upper right', fontsize=9)

                    GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME.append(transported_volume)
                    GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME.append(elapsed_time)
                    GraphicalMplCanvas.DRAW_POINTS_FLOW_RATE.append(flow_rate)

                elif count_outer >= 11 and flow_rate < 0:
                    GraphicalMplCanvas.temp_volume.append(transported_volume)
                    GraphicalMplCanvas.min_flow_volume = min(GraphicalMplCanvas.temp_volume)
                    GraphicalMplCanvas.current_volume_inf_wd = GraphicalMplCanvas.max_flow_volume + GraphicalMplCanvas.min_flow_volume

                    prev_elapsed_time = GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME[-1]
                    prev_flow_rate = GraphicalMplCanvas.DRAW_POINTS_FLOW_RATE[-1]
                    prev_trans_volume = GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME[-1]

                    if prev_elapsed_time < elapsed_time + GraphicalMplCanvas.max_time_len:
                        self.temp_x_array = np.append(self.temp_x_array, prev_elapsed_time)
                        self.temp_y_array = np.append(self.temp_y_array, prev_flow_rate)
                        self.temp_y_array = np.append(self.temp_y_array, GraphicalMplCanvas.current_volume_inf_wd)

                        self.max_time_len = np.max(self.temp_x_array, axis=0)
                        self.y_lim_lower, self.y_lim_upper = np.min(self.temp_y_array, axis=0), np.max(self.temp_y_array, axis=0)

                        segment_flow_rate = [(prev_elapsed_time, prev_flow_rate),
                                             (elapsed_time + GraphicalMplCanvas.max_time_len, flow_rate)]
                        self.segments_flow_rate.append(segment_flow_rate)
                        connected_segments_flow_rate = np.concatenate(self.segments_flow_rate)
                        self.lc_flow_rate.set_segments([connected_segments_flow_rate])

                        segment_trans_volume = [(prev_elapsed_time, prev_trans_volume),
                                                (elapsed_time + GraphicalMplCanvas.max_time_len, GraphicalMplCanvas.current_volume_inf_wd)]
                        self.segments_trans_volume.append(segment_trans_volume)
                        connected_segments_trans_volume = np.concatenate(self.segments_trans_volume)
                        self.lc_trans_volume.set_segments([connected_segments_trans_volume])

                        self.ax.set_xlim(0, self.max_time_len * 1.1)
                        self.ax.set_ylim(self.y_lim_lower * 1.35, self.y_lim_upper * 1.35)

                    self.flow_rate_legend_added = True
                    self.transported_volume_legend_added = True

                    if prev_elapsed_time < elapsed_time + GraphicalMplCanvas.max_time_len:
                        GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME.append(GraphicalMplCanvas.current_volume_inf_wd)
                        GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME.append(elapsed_time + GraphicalMplCanvas.max_time_len)
                        GraphicalMplCanvas.DRAW_POINTS_FLOW_RATE.append(flow_rate)

            self.fig.canvas.draw()

    @staticmethod
    def export_data():
        """Export plotted curve data to TXT file."""
        if (GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME and
                GraphicalMplCanvas.DRAW_POINTS_FLOW_RATE and
                GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME):

            save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                None, "Save Data", "./FlowData", "Text Files (*.txt);;CSV Files (*.csv)"
            )
            if save_path:
                os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
                header = "Time [s]\tFlow rate [ml/s]\tTransported volume [ml]\n"
                data = ""
                for i in range(len(GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME)):
                    time_var = str(GraphicalMplCanvas.DRAW_POINTS_ELAPSED_TIME[i])
                    flow_rate = str(GraphicalMplCanvas.DRAW_POINTS_FLOW_RATE[i])
                    trans_volume = str(GraphicalMplCanvas.DRAW_POINTS_TRANS_VOLUME[i])
                    data += f"{time_var}\t{flow_rate}\t{trans_volume}\n"

                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(header + data)


def clear_graph_text(ui, read_send_thread, mpl_canvas):
    """Clear text displays and reset graph canvas."""
    ui.Response_from_pump.setText('')
    ui.commands_sent.setText('')
    read_send_thread.initialize_class_var()
    if ui.actionDark.isChecked():
        mpl_canvas.initialize_graph(axis_label_color='white')
    else:
        mpl_canvas.initialize_graph(axis_label_color='black')
    read_send_thread.clear_from_button(ui)
