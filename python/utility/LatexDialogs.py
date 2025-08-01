
from PyQt6.QtWidgets import QGridLayout, QLineEdit,QDialog,QLabel,QPushButton,QWidget
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
import time
class KeyValDialog(QDialog):
	key_data = ""
	value_datq = ""
	key = ""
	value = ""

	def __init__(self,key,value):
		super().__init__()
		self.key = key
		self.value = value
		self.setWindowTitle('Data Passing Dialog')
		self.setGeometry(100, 100, 300, 150)

		layout = QGridLayout()

		self.key_label = QLabel('Key:')
		layout.addWidget(self.key_label,0,0)

		self.key_edit = QLineEdit()
		self.key_edit.setText(self.key)
		layout.addWidget(self.key_edit,0,1)

		self.value_label = QLabel('Value:')
		
		layout.addWidget(self.value_label,1,0)

		self.value_edit = QLineEdit()
		self.value_edit.setText(self.value)
		layout.addWidget(self.value_edit,1,1)

		self.submit_button = QPushButton('Submit')
		self.submit_button.clicked.connect(self.submit_data)
		layout.addWidget(self.submit_button)

		self.setLayout(layout)

	def submit_data(self):
		self.key_data = self.key_edit.text()
		self.val_data = self.value_edit.text()
		self.accept()
		


class PreviewDialog(QDialog):
	
	flg_isopen = False
	def __init__(self,pdfName):
		super().__init__()
		self.pdfName = pdfName
		self.setWindowTitle('Data Passing Dialog')
		self.setGeometry(100, 100, 1000, 800)
		layout = QGridLayout()
		document = QPdfDocument(self)
		try:
			document.load(pdfName)
		except BaseException as e:
			self.log.log(self,e)
		view = QPdfView(self)
		#view.setPageMode(QPdfView.PageMode.MultiPage)
		view.setDocument(document)
		layout.addWidget(view)

		self.submit_button = QPushButton('Done')
		self.submit_button.clicked.connect(self.submit_data)
		layout.addWidget(self.submit_button)
		widget = QWidget()
		widget.setLayout(layout)
		self.setLayout(layout)
		self.flg_isopen = True
		self.show()

	def closeEvent(self,event):
		flg_isopen = False
		event.accept()

		

	def submit_data(self):
		self.accept()
