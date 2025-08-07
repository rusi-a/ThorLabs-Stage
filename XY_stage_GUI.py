import sys
from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QMainWindow
)
from PyQt5.QtGui import QPainter, QColor, QPen


class MockStage:
    def __init__(self):
        self.x = 0
        self.y = 0

    def move_to(self, x_mm, y_mm):
        self.x = x_mm
        self.y = y_mm
        print(f"Stage moved to: X={x_mm:.2f} mm, Y={y_mm:.2f} mm")


class GridCanvas(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.grid_points = []
        self.rows = 0
        self.cols = 0
        self.sample_width = 0
        self.sample_height = 0
        self.current_index = -1
        self.custom_point = None

    def set_grid(self, rows, cols, width_mm, height_mm):
        self.rows = rows
        self.cols = cols
        self.sample_width = width_mm
        self.sample_height = height_mm
        self.grid_points.clear()
        for row in range(rows):
            for col in range(cols):
                x = col / (cols - 1) * width_mm if cols > 1 else 0
                y = row / (rows - 1) * height_mm if rows > 1 else 0
                self.grid_points.append((x, y))
        self.current_index = -1
        self.custom_point = None
        self.update()

    def set_current_index(self, idx):
        self.current_index = idx
        self.update()

    def set_custom_point(self, x_mm, y_mm):
        self.custom_point = (x_mm, y_mm)
        self.update()

    def paintEvent(self, event):
        if not self.grid_points:
            return

        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        cell_w = w / (self.cols + 1)
        cell_h = h / (self.rows + 1)
        cell_size = min(cell_w, cell_h)

        x_offset = (w - (self.cols - 1) * cell_size) / 2 if self.cols > 1 else w / 2
        y_offset = (h - (self.rows - 1) * cell_size) / 2 if self.rows > 1 else h / 2

        for idx, (x_mm, y_mm) in enumerate(self.grid_points):
            row = idx // self.cols
            col = idx % self.cols
            x = x_offset + col * cell_size
            y = y_offset + row * cell_size
            size = 6

            color = QColor("green") if idx == self.current_index else QColor("blue")
            qp.setPen(QPen(Qt.black, 1))
            qp.setBrush(color)
            qp.drawEllipse(QPoint(int(x), int(y)), size, size)

        # Draw custom point (yellow)
        if self.custom_point and None not in self.custom_point:
            x_mm, y_mm = self.custom_point
            x_ratio = x_mm / self.sample_width if self.sample_width else 0
            y_ratio = y_mm / self.sample_height if self.sample_height else 0
            x_px = x_offset + x_ratio * (self.cols - 1) * cell_size
            y_px = y_offset + y_ratio * (self.rows - 1) * cell_size
            qp.setBrush(QColor("yellow"))
            qp.setPen(QPen(Qt.black, 1))
            qp.drawEllipse(QPoint(int(x_px), int(y_px)), 6, 6)

    def mousePressEvent(self, event):
        if not self.grid_points:
            return

        w = self.width()
        h = self.height()
        cell_w = w / (self.cols + 1)
        cell_h = h / (self.rows + 1)
        cell_size = min(cell_w, cell_h)

        x_offset = (w - (self.cols - 1) * cell_size) / 2 if self.cols > 1 else w / 2
        y_offset = (h - (self.rows - 1) * cell_size) / 2 if self.rows > 1 else h / 2

        clicked_col = int(round((event.x() - x_offset) / cell_size))
        clicked_row = int(round((event.y() - y_offset) / cell_size))

        if 0 <= clicked_row < self.rows and 0 <= clicked_col < self.cols:
            idx = clicked_row * self.cols + clicked_col
            if idx < len(self.grid_points):
                x_mm, y_mm = self.grid_points[idx]
                self.controller.on_grid_point_selected(idx, x_mm, y_mm)


class GridControlWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XY Stage Grid Control")
        self.setMinimumSize(900, 700)

        self.stage = MockStage()
        self.scan_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.scan_step)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Grid input
        self.width_input = QLineEdit("20")
        self.height_input = QLineEdit("20")
        self.rows_input = QSpinBox()
        self.rows_input.setRange(1, 100)
        self.rows_input.setValue(6)
        self.cols_input = QSpinBox()
        self.cols_input.setRange(1, 100)
        self.cols_input.setValue(6)

        layout.addLayout(self._labeled_field("Sample Width (mm):", self.width_input))
        layout.addLayout(self._labeled_field("Sample Height (mm):", self.height_input))
        layout.addLayout(self._labeled_field("Grid Rows (Y):", self.rows_input))
        layout.addLayout(self._labeled_field("Grid Columns (X):", self.cols_input))

        # Custom point input
        custom_layout = QHBoxLayout()
        self.custom_x_input = QLineEdit()
        self.custom_y_input = QLineEdit()
        custom_layout.addWidget(QLabel("Custom X (mm):"))
        custom_layout.addWidget(self.custom_x_input)
        custom_layout.addWidget(QLabel("Y (mm):"))
        custom_layout.addWidget(self.custom_y_input)
        self.go_custom_button = QPushButton("Go to Custom Point")
        self.go_custom_button.clicked.connect(self.go_to_custom_point)
        custom_layout.addWidget(self.go_custom_button)
        layout.addLayout(custom_layout)

        # Scan delay input
        delay_layout = QHBoxLayout()
        self.delay_input = QLineEdit("1.0")  # seconds
        delay_layout.addWidget(QLabel("Scan Delay per Point (s):"))
        delay_layout.addWidget(self.delay_input)
        layout.addLayout(delay_layout)

        # Control buttons
        btn_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate Grid")
        self.generate_button.clicked.connect(self.generate_grid)
        btn_layout.addWidget(self.generate_button)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_scan)
        btn_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_scan)
        btn_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_scan)
        btn_layout.addWidget(self.stop_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_scan)
        btn_layout.addWidget(self.reset_button)

        layout.addLayout(btn_layout)

        # Canvas
        self.canvas = GridCanvas(controller=self)
        layout.addWidget(self.canvas, stretch=1)

        central_widget.setLayout(layout)

    def _labeled_field(self, label, widget):
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel(label))
        hbox.addWidget(widget)
        return hbox

    def generate_grid(self):
        try:
            width_mm = float(self.width_input.text())
            height_mm = float(self.height_input.text())
            rows = self.rows_input.value()
            cols = self.cols_input.value()
            self.canvas.set_grid(rows, cols, width_mm, height_mm)
        except ValueError:
            print("Invalid input: Width and height must be numbers")

    def on_grid_point_selected(self, idx, x_mm, y_mm):
        self.canvas.set_current_index(idx)
        self.canvas.set_custom_point(None, None)
        self.stage.move_to(x_mm, y_mm)

    def go_to_custom_point(self):
        try:
            x = float(self.custom_x_input.text())
            y = float(self.custom_y_input.text())
            self.canvas.set_current_index(-1)
            self.canvas.set_custom_point(x, y)
            self.stage.move_to(x, y)
        except ValueError:
            print("Invalid custom point input")

    def start_scan(self):
        if not self.canvas.grid_points:
            return
        try:
            delay_sec = float(self.delay_input.text())
            self.timer.start(int(delay_sec * 1000))
        except ValueError:
            print("Invalid delay time")

    def pause_scan(self):
        self.timer.stop()

    def stop_scan(self):
        self.timer.stop()

    def reset_scan(self):
        self.timer.stop()
        self.scan_index = 0
        self.canvas.set_current_index(-1)

    def scan_step(self):
        if self.scan_index >= len(self.canvas.grid_points):
            self.timer.stop()
            return
        x, y = self.canvas.grid_points[self.scan_index]
        self.stage.move_to(x, y)
        self.canvas.set_current_index(self.scan_index)
        self.scan_index += 1


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GridControlWindow()
    window.show()
    sys.exit(app.exec_())
