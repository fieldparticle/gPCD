import sys
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from TabClassLatex import *
#from FPIBGException import *

GlobalPrintbuffer =  None
sys.path.insert(0, 'J:/FPIBG/python/utility')
sys.path.insert(0, 'J:/FPIBG/python/shared')
sys.path.insert(0, 'J:/FPIBG/python')
import inspect
## The main window object that contains the tabs for the utility
class LatexWin(QWidget):
    
    def __init__(self, FPIBGBase, ObjName,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ObjName = ObjName
        self.bs = FPIBGBase
        self.log = self.bs.log
        self.log.log(self,"Logging system initialized")
        self.ObjName = ObjName
        self.setWindowTitle('Particles Forge Utility Suite')
        self.setGeometry(100, 100, 1200, 1000)
        self.setWindowIcon(QIcon("Logo.png"))
        main_layout = QGridLayout(self)
        ## Create a tab widget
        self.tabSetup = TabObjLatex(self)
        self.tabSetup.Create(FPIBGBase)
        main_layout.addWidget(self.tabSetup, 0, 0, 2, 1)
        self.quitBtn = QPushButton('Quit')
        main_layout.addWidget(self.quitBtn, 2, 0,
                        alignment=Qt.AlignmentFlag.AlignRight)
        self.quitBtn.clicked.connect(self.on_clicked)
        self.setLayout(main_layout)
        self.show()
        
        
    def closeEvent(self, event):
        plt.close("all")  
        event.accept()

    def __exit__(self):
        #sys.stdout = self.orig_stdout
        #self.f.close()
        plt.close("all")        

    def on_clicked(self) :
        exit()
        
    def Create(self,FPIBGBase):
        
        self.bs = FPIBGBase
        self.bs.log.log(self, "FPIBGLatexWin.Created")

   