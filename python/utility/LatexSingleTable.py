from PyQt6.QtCore import Qt,QAbstractTableModel
from PyQt6.QtWidgets import QTableView
from CfgLabel import *
from LatexClass import *
from LatexConfigurationClass import *
from LatexDataContainer import *
import pandas as pd
import numpy as np


class LatexSingleTable(LatexConfigurationClass):

    tableModel = None
    def __init__(self,Parent,itemCFG=None):
        self.Parent = Parent
        self.bobj = self.Parent.bobj
        self.log = self.bobj.log
        self.cfg = Parent.itemcfg.config 
        self.itemcfg = Parent.itemcfg 
        self.LatexTable = LatexTableWriter(self.Parent)

    def updateCfgData(self):
        for oob in self.objArry:
            oob.updateCFGData()
        self.itemcfg.updateCfg()
        self.updateTableData()
        self.LatexTable.Write() 

    def itemChanged(self,key,value):
        pass

    def OpenLatxCFG(self):
       #print(self.itemcfg)
        self.doItems(self.itemcfg.config)
        self.updateTableData()

    def doDataFields(self,plotNum):
        # Get color. Its special becasue it has no rcParams
        plotGrouptxt = f"DataFields{plotNum}"
        oob = self.itemcfg.config[plotGrouptxt]
        return oob
    
    def updateTableData(self):
        temp_ary = []
        data_fields = self.doDataFields(1)
        #self.data = pd.read_csv(self.cfg.data_file,header=0)  
        dataObj = LatexDataContainer(self.bobj,self.itemcfg,"LatexDataContainer")
        try :
            dataObj.Create(1,data_fields)
        except BaseException as e:
            print("Data Base error:",e)
            #print("There is not data or there is an error with the path.")
            print(f"Current path is:{self.cfg.data_dir}")
            return False
        # Get the data
        data = dataObj.getData()
        temp_ary = []
        # allocate a attribute dictionary
        fld = AttrDictFields()
        for name, df in data.items():
            fld[name] = data[name]

        for k,v in self.cfg.items():
            plotGrouptxt = "DataFields" + str(1)
            if plotGrouptxt in k:
                for ii in range(len(v)):
                    fld_name = v[ii].replace(':','_')
                    if any(map(lambda char: char in v[ii], "+-/*")):
                        field = eval(fld_name)
                        temp_ary.append(field)
                    else:
                        # Else strip the fld. from the field and get the array at that column name
                        fldtxt = fld_name.split('.')
                        temp_ary.append(data[fldtxt[1]])
                    self.onpdata = np.array(temp_ary)   
                temp_ary = []
                  
        self.LatexTable.Create(self.onpdata)
        self.hasPlot = True

    
class SingleTableWidget(QAbstractTableModel):
    
    def __init__(self, data):
        super().__init__()
        self._data = data
        
    rowlength = 0
    collength = 0
    def data(self, index, role):
        #self.Latex.setLatexData(self)
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
            

    
    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])

            #if orientation == Qt.Orientation.Vertical:
              #  return str(self._data.index[section])

class LatexSplitTable(LatexSingleTable):
    def __init__(self,Parent,itemCFG=None):
        super().__init__(Parent)
        self.LatexTable = LatexSplitTableWriter(self.Parent)
        self.LatexFileImage = LatexSplitTableWriter(self.Parent)

class LatexMultiTable(LatexSingleTable):
    def __init__(self,Parent,itemCFG=None):
        super().__init__(Parent)
        self.LatexTable = LatexMultiTableWriter(self.Parent)
        self.LatexFileImage = LatexMultiTableWriter(self.Parent)