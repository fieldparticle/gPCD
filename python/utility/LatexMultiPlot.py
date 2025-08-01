from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox,QDialog
from CfgLabel import *
from LatexClass import *
import pandas as pd
import cycler
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasAgg as FigureCanvas
from matplotlib.backends.qt_compat import QtWidgets
import numpy as np
from LatexConfigurationClass import *
from LatexPlotBase import * 
from ConfigClass import *
from AttrDictFields import *
from LatexPreview import *
from LatexDialogs import *
from TrendLine import *
from ValHandler import *
from LatexDataContainer import *
class LatexMultiPlot(LatexPlotBase):
    fignum = 0
    
    
    hasPlot = False
    npdata = None
    fig = None
    ax = None
    pixmap = None
    hasRawData = False
    hasSummaryData = False
    topdir = ""
    sumFile = ""
    data_files = []
    average_list = []


    def __init__(self,Parent):
        super().__init__(Parent)
        self.Parent = Parent
        self.LatexFileImage = LatexMultiPlotWriter(self.Parent)
        self.valHandler = ValHandler()
    
    def isNumber(self,value):
        if isinstance(float(value), float) and '.' in value:
            return True
        if isinstance(int(value), int) and '.' in value:
            return True

    def isfloat(self,value):
        try:
            return isinstance(float(value), float) and '.' in value
        except ValueError:
            return False
   
    def isInt(self,val):
        if val.isdigit():
            return True
        else:
            return False
        
    # Override LatexPlot()
    def doDataSource(self,plotNum):
        plotGrouptxt = f"DataSource"
        oob = self.itemcfg.config[plotGrouptxt][plotNum-1]
        return oob
      
    def doDataFile(self,plotNum):
        plotGrouptxt = f"DataFiles"
        oob = self.itemcfg.config[plotGrouptxt][plotNum-1]
        return oob
          
    
    def preview(self):
      pass
        
    