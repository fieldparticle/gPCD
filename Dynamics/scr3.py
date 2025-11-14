import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        self.plot()

    def plot(self):
        x = [1, 2, 3, 4, 5]
        y = [1, 4, 9, 16, 25]
        self.ax.plot(x, y, marker='o')
        self.ax.set_title('Embedded Plot')
        self.ax.set_xlabel('X-axis')
        self.ax.set_ylabel('Y-axis')
        self.ax.grid(True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Matplotlib in PyQt6')
        self.setGeometry(100, 100, 800, 600)

        widget = QWidget()
        layout = QVBoxLayout()

        self.canvas = PlotCanvas()
        layout.addWidget(self.canvas)

        toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(toolbar)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

# Create an instance of QApplication
app = QApplication(sys.argv)

# Create and display the main window
window = MainWindow()
window.show()

# Run the application's event loop
sys.exit(app.exec())