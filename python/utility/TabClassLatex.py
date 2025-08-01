import sys
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton
from PyQt6.QtCore import Qt
from TabFormLatex import *
from TabFormGenData import *
from TabFormWelcome import *
## Add all tabs
class TabObjLatex(QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    

    ## Add all tabs to this tab form (parent)
    def Create(self,FPIBGBase):
        self.bobj = FPIBGBase
        ## Create the tabs
        self.tabFormGenData = TabGenData()        
        self.tabFormLatex = TabFormLatex()
        self.tabFormWelcome = TabFormWelcome()
        self.addTab(self.tabFormWelcome, 'Welcome')
        self.addTab(self.tabFormGenData, 'Data Generation')
        self.addTab(self.tabFormLatex, 'Reporting')
        self.tabFormLatex.Create(self.bobj)
        self.tabFormGenData.Create(self.bobj)
        self.tabFormWelcome.Create()