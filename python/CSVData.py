import pandas as pd
import os
import csv
import re
import statistics
import pandas as pd
from AttrDictFields import *
from ReportClass import *
import os
import inspect
from TrendLine import *
import re
from ConfigUtility import *
from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox
from  msg_box import *

class CSVData():

    sumFile = ""
    average_list = []
    mode = 0
    mmrr_fps = 0.0
    mmrr_cpums = 0.0
    mmrr_gms = 0.0
    MODE_VERF = 1
    MODE_PERF = 0
    data_files = None    
    lines_return = pd.DataFrame()
    
    def __init__(self,Base, itemcfg):
        self.bobj = Base
        self.cfg = self.bobj.cfg
        self.log = self.bobj.log
        self.itemcfg = itemcfg

        
    def isNumber(self,value):
        try:
            float(value)
        except ValueError:
            return False
        try:
            int(value)
        except ValueError:
            return False
        return True
   
    def assign_data(self,lines_list):
        data_file = lines_list.source_dir + "/" +  lines_list.data_file
        try :
            data = pd.read_csv(data_file)
        except BaseException as e:
            raise BaseException(f"read_summary_file fail:{e}")
        return data
        
    
    def do_reports(self):
        for ii in self.itemcfg_main.include:
            self.itemcfg = ConfigUtility(ii)
            self.itemcfg.Create(self.bobj.log,ii)
            self.do_report()

    #******************************************************************
    # Create thr mmrr summary file
    #  
    def read_summary_file(self,file_dict):
        return None
            
    
       #******************************************************************
    # GP message box
    #
    def msg_box(self,text):
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.exec()

    #******************************************************************
    # Check the data counts
    #
    # Returns true if number of .tst files equal to number of R or D files
    def check_data_files(self,file_dict) -> bool:
       return True
    #******************************************************************
    # Do the performnce tests
    #
    #      
    def do_performance(self,file_dict): 
       return True
    
    #******************************************************************
    # Create the summary file wqith headers
    #
    def create_summary(self,file_dict):
        return
    #******************************************************************
    # Create the summary file wqith headers
    #
    # 
            
    #******************************************************************
    # Run thoruogh the verification files and check counts
    #
    def do_verify(self,file_dict):
        return 0
            
    #******************************************************************
    # Get averages
    #
    def get_averages(self,file_dict):
        pass

    #******************************************************************
    # Get maximuns write then to summary file
    #
    def get_maxes(self,file_dict):
        pass