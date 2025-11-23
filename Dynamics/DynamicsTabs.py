import sys
from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtCore import Qt
from TabFormDyn import *


## Add all tabs
class DynamicsTabs(QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    

    ## Add all tabs to this tab form (parent)
    def Create(self,Base):
        self.bobj = Base
        #self.bobj.set_tab_object(self)
        ## Create the tabs
        self.tabFormDyn = TabFormDyn()        
        self.addTab(self.tabFormDyn, 'Particle Dynamics')
        self.tabFormDyn.Create(self.bobj)
        
      