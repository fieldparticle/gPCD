import sys
from PyQt6.QtWidgets import QApplication, QWidget,  QVBoxLayout, QFormLayout, QLabel, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

class TabFormWelcome(QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def Create(self):

        ## Create a container for all objects
        self.setupcontainer = QWidget(self);
        ## Set up a layout object
        self.layout = QVBoxLayout()
        ## Add the layout to the container
        self.setupcontainer.setLayout(self.layout)
        ## Create items for the layout
        label = QLabel(self)
        self.pixmap = QPixmap('Logo.png')
        label.setPixmap(self.pixmap)
        ##Add items to the layout
        self.layout.addWidget(label)
        self.setLayout(self.layout)
        
        self.show()

        