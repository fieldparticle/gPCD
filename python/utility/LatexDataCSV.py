import pandas as pd
from LatexDataBaseClass import *
import os
import csv
class LatexDataCSV(LatexDataBaseClass):

    def __init__(self, FPIBGBase, itemcfg,ObjName):
        super().__init__(FPIBGBase, itemcfg, ObjName)
        self.lines_return = pd.DataFrame()
        
    def get_verify(self):
        pass
    def getData(self):
        return self.lines_return

    def Create(self,plot_num):
        data_file = self.itemcfg.config.data_dir + "/" + self.itemcfg.config.data_files[plot_num]
        self.data = pd.read_csv(data_file,header=0)  
        getFieldStr = f"DataFields{plot_num+1}"
        data_fields = self.itemcfg.config[getFieldStr]
        for jj in range(len(data_fields)):
            if any(map(lambda char: char in data_fields[jj], "+-/*")):
                alt_lst = self.split(data_fields[jj])
                alt_sary = alt_lst.split(',')   
                for ss in range(len(alt_sary)):
                    file_list = alt_sary[ss].split(".")    
                    field_name = file_list[1].split(':')
                    field_name_txt = f"{field_name[0]}_{field_name[1]}"
                    if field_name_txt not in self.lines_return.keys():
                        self.build_field(field_name,field_name_txt)    
            else:
                file_list = data_fields[jj].split(".")
                field_name = file_list[1].split(':')
                field_name_txt = f"{field_name[0]}_{field_name[1]}"
                if field_name_txt not in self.lines_return.keys():
                    self.build_field(field_name,field_name_txt)    
        
    def build_field(self,field_name,key_name):
        
        field_name[0] = field_name[0].strip()
        field_name[1] = field_name[1].strip()
        key_name = key_name.strip()
        self.lines_return[key_name]=self.data[field_name[1]] 

