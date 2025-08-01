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
class LatexEquation(LatexConfigurationClass):
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
    select_list = []

    def __init__(self,Parent):
        super().__init__(Parent)
        self.Parent = Parent
        self.LatexFileImage = LatexEquationWriter(self.Parent)
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
    
    def ReadData(self):
       
        eq_file = self.itemcfg.config.data_dir + "/" + self.itemcfg.config.data_file
        try:
            with open(eq_file,"r",newline='') as csvfl:
                reader = csv.reader(csvfl, delimiter=',',dialect='excel')
                for row in reader:
                    self.select_list.append(row)
        except BaseException as e:
            self.log.log(self,f"Error opening:{eq_file}, err:", e)
        
        return self.select_list             
    
    def OpenLatxCFG(self):
        self.doItems(self.itemcfg.config)
        self.ReadData()
        self.LatexFileImage.Create(self.select_list)
        

    def preview(self):
        pass
    