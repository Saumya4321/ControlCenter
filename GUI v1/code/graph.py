import pyqtgraph as pg
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QRunnable, QThreadPool
from PyQt5.QtGui import QColor
import numpy as np
from datetime import datetime, timedelta

class DataProcessor(QObject):
    dataReady = pyqtSignal(list, list)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.datasets = [[] for _ in range(16)]
        self.times = []
        self.start_time = datetime.now()

    def process_data(self):
        current_time = datetime.now()
        elapsed_time = (current_time - self.start_time).total_seconds()
        self.times.append(elapsed_time)
        
        # Use the new_temp data from the parent
        new_temps = self.parent.new_temp
        for i in range(16):
            if i < len(new_temps):
                try:
                    self.datasets[i].append(float(new_temps[i]))
                except ValueError:
                    # If conversion fails, append NaN or some default value
                    self.datasets[i].append(float('nan'))
            else:
                self.datasets[i].append(float('nan'))
        
        self.dataReady.emit(self.times, self.datasets)

class DataProcessorRunnable(QRunnable):
    def __init__(self, processor):
        super().__init__()
        self.processor = processor

    def run(self):
        self.processor.process_data()

class Graph:
    def __init__(self, parent=None):
        self.parent = parent
        self.graphWidget = self.parent.graphWidget

        self.setup_graph()
        self.setup_data_processor()

    def setup_graph(self):
        self.graphWidget.setBackground('w')
        self.graphWidget.setYRange(0, 100, padding=0)  # Adjust Y range as needed

        self.fixed_x_range = 600  # 10 minutes in seconds
        self.graphWidget.setXRange(0, self.fixed_x_range, padding=0)

        colors = self.generate_colors(16)
        self.scatter_plots = []
        self.line_plots = []
        for color in colors:
            scatter = pg.ScatterPlotItem(size=5, pen=pg.mkPen(None), brush=pg.mkBrush(color))
            line = pg.PlotDataItem(pen=pg.mkPen(color, width=1))
            self.graphWidget.addItem(scatter)
            self.graphWidget.addItem(line)
            self.scatter_plots.append(scatter)
            self.line_plots.append(line)

        self.setup_hover_label()
        self.graphWidget.scene().sigMouseMoved.connect(self.on_mouse_move)

    def setup_hover_label(self):
        self.hover_label = pg.TextItem(
            text='', 
            color=(0, 0, 0), 
            border=pg.mkPen(color=(0, 0, 0), width=1),
            fill=pg.mkBrush(QColor(255, 255, 255, 200))
        )
        self.graphWidget.addItem(self.hover_label)
        self.hover_label.hide()

    def setup_data_processor(self):
        self.data_processor = DataProcessor(self.parent)
        self.data_processor.dataReady.connect(self.update_plot_data)
        self.thread_pool = QThreadPool()

        self.timer = QTimer()
        self.timer.setInterval(5000)  # Match this with your temperature update interval
        self.timer.timeout.connect(self.process_data)
        self.timer.start()

    def process_data(self):
        runnable = DataProcessorRunnable(self.data_processor)
        self.thread_pool.start(runnable)

    @staticmethod
    def generate_colors(n):
        return [QColor.fromHsvF(i / n, 1.0, 1.0) for i in range(n)]

    def update_plot_data(self, times, datasets):
        for i in range(16):
            self.scatter_plots[i].setData(times, datasets[i])
            self.line_plots[i].setData(times, datasets[i])

        elapsed_time = times[-1]
        if elapsed_time > self.fixed_x_range:
            self.graphWidget.setXRange(elapsed_time - self.fixed_x_range, elapsed_time, padding=0)
        else:
            self.graphWidget.setXRange(0, self.fixed_x_range, padding=0)

        x_ticks = [(t, (self.data_processor.start_time + timedelta(seconds=t)).strftime('%H:%M')) 
                   for t in range(0, int(elapsed_time) + 60, 60)]
        self.graphWidget.getAxis('bottom').setTicks([x_ticks])

    def on_mouse_move(self, pos):
        mouse_point = self.graphWidget.plotItem.vb.mapSceneToView(pos)
        x, y = mouse_point.x(), mouse_point.y()

        if not self.data_processor.times:
            return

        idx = np.argmin(np.abs(np.array(self.data_processor.times) - x))
        
        if 0 <= idx < len(self.data_processor.times):
            time_value = self.data_processor.start_time + timedelta(seconds=self.data_processor.times[idx])
            
            distances = [abs(y - dataset[idx]) for dataset in self.data_processor.datasets]
            closest_dataset = np.argmin(distances)
            closest_y = self.data_processor.datasets[closest_dataset][idx]
            
            if distances[closest_dataset] < 5:
                label_text = f"Channel {closest_dataset + 1}:\nTime: {time_value.strftime('%H:%M:%S')}\ntemp = {closest_y:.2f}"
                self.show_hover_label(self.data_processor.times[idx], closest_y, label_text)
            else:
                self.hover_label.hide()
        else:
            self.hover_label.hide()

    def show_hover_label(self, x, y, text):
        self.hover_label.setText(text)
        
        x_min, x_max = self.graphWidget.viewRange()[0]
        
        anchor = (1, 0.5) if x > (x_max - (x_max - x_min) * 0.1) else (0, 0.5)
        
        self.hover_label.setPos(x, y)
        self.hover_label.setAnchor(anchor)
        self.hover_label.show()