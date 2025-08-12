import sys
from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtCore import Qt
from TabFormReport import *
from TabFormGenData import *
from TabFormRun import *

## Add all tabs
class UtilityTabs(QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    

    ## Add all tabs to this tab form (parent)
    def Create(self,Base):
        self.bobj = Base
        self.bobj.set_tab_object(self)
        ## Create the tabs
        self.tabFormGenData = TabGenData()        
        self.tabFormRun = TabFormRun()        
        self.tabFormReport = TabFormReport()
        self.addTab(self.tabFormRun, 'Run')
        self.addTab(self.tabFormReport, 'Reports')
        self.addTab(self.tabFormGenData, 'Generate Data')
        self.tabFormReport.Create(self.bobj)
        self.tabFormGenData.Create(self.bobj)
        self.tabFormRun.Create(self.bobj)
     
      