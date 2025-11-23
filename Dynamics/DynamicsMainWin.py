import sys
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from DynamicsTabs import *

GlobalPrintbuffer =  None

import inspect
## The main window object that contains the tabs for the utility
class DynamicsMainWin(QWidget):
    
    def __init__(self, Base, ObjName,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ObjName = ObjName
        self.bs = Base
        self.log = self.bs.log
        self.log.log(self,"Logging system initialized")
        self.ObjName = ObjName
        self.setWindowTitle('Dynamics Main Window')
        self.setGeometry(100, 100, 1600, 1000)
        self.setWindowIcon(QIcon("Logo.png"))
        main_layout = QGridLayout(self)
        ## Create a tab widget
        self.tabSetup = DynamicsTabs(self)
        self.tabSetup.Create(Base)
        main_layout.addWidget(self.tabSetup, 0, 0, 2, 1)
        self.quitBtn = QPushButton('Quit')
        main_layout.addWidget(self.quitBtn, 2, 0,
                        alignment=Qt.AlignmentFlag.AlignRight)
        self.quitBtn.clicked.connect(self.on_clicked)
        self.setLayout(main_layout)
        self.show()
        
        
    def closeEvent(self, event):
       # plt.close("all")  
        event.accept()

    def __exit__(self):
        pass
        #sys.stdout = self.orig_stdout
        #self.f.close()
        #plt.close("all")        


    
    def on_clicked(self) :
        exit()
        
    def Create(self,Base):
        
        self.bs = Base
        self.bs.log.log(self, "MainWin.Created",LogOnly=True)

   