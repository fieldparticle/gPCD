import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QToolBar, QSizePolicy
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtCore import Qt, QUrl

class PdfViewer(QMainWindow):
    pdf_file = None
    def __init__(self,pdf_file):
        super().__init__()
        self.pdf_file = pdf_file
        self.setWindowTitle('Preview PDF Viewer')
        self.setGeometry(100, 100, 1000, 1000)

        self.pdf_document = QPdfDocument(self)
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_document)

        # Load a sample PDF document (replace with your PDF path)
        # For a real application, you would load from a file dialog or a specific path.
        # Ensure you have a 'sample.pdf' in the same directory or provide a full path.
        try:
            self.pdf_document.load(self.pdf_file)
        except Exception as e:
            print(f"Error loading PDF: {e}. Please ensure 'sample.pdf' exists.")

        self.current_zoom_factor = 1.0  # Initial zoom factor

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.pdf_view)

        # Create a toolbar for zoom controls
        toolbar = QToolBar("Zoom Controls")
        self.addToolBar(toolbar)

        zoom_in_button = QPushButton("Zoom In")
        zoom_in_button.clicked.connect(self.zoom_in)
        toolbar.addWidget(zoom_in_button)

        zoom_out_button = QPushButton("Zoom Out")
        zoom_out_button.clicked.connect(self.zoom_out)
        toolbar.addWidget(zoom_out_button)

        fit_to_width_button = QPushButton("Fit to Width")
        fit_to_width_button.clicked.connect(self.fit_to_width)
        toolbar.addWidget(fit_to_width_button)

        fit_in_view_button = QPushButton("Fit in View")
        fit_in_view_button.clicked.connect(self.fit_in_view)
        toolbar.addWidget(fit_in_view_button)
        self.zoom_in()

    def zoom_in(self):
        self.current_zoom_factor *= 1.2  # Increase zoom by 20%
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(self.current_zoom_factor)

    def zoom_out(self):
        self.current_zoom_factor /= 1.2  # Decrease zoom by 20%
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(self.current_zoom_factor)

    def fit_to_width(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)

    def fit_in_view(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PdfViewer()
    viewer.show()
    sys.exit(app.exec())