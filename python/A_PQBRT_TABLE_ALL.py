from ReportClass import *
import os
import inspect
from TrendLine import *
import re
from AttrDictFields import *
from ConfigUtility import *
from ValuesDataBase import *
class A_PQBRT_TABLE_ALL():

    def __init__(self,itemcfg,base):
        self.itemcfg = itemcfg
        self.bobj = base
        self.include = []
        self.vals_list = AttrDictFields()
        self.prefix_name = self.itemcfg.name.replace('_','')
       
    def replace_between_delimiters(self,text, start_delimiter, end_delimiter, replacement_string):
        pattern = re.escape(start_delimiter) + r"(.*?)" + re.escape(end_delimiter)


        # Use re.sub() to find and replace
        # The replacement string includes the delimiters themselves
        return re.sub(pattern, start_delimiter + replacement_string + end_delimiter, text)

    
        
    header_arry = []
    def run(self):
        self.mdf = pd.read_csv(self.itemcfg.mmrr_dir)
        mmrr = np.min(self.mdf['gms'])


        self.df = pd.read_csv(self.itemcfg.input_data_file)
        self.df["loadedp"] = pd.to_numeric(self.df['loadedp'], downcast='integer', errors='coerce')

        N = self.df['loadedp']
        M = self.df['expectedc']
        cms = self.df['cms']
        gms = self.df['gms']
        fps = self.df['fps']
        both = np.add(gms,cms)
        self.Table = []
        self.Table.append(N)
        self.Table.append(M)
        self.Table.append(fps)
        self.Table.append(cms*1000)
        self.Table.append(gms*1000)
        self.Table.append(both*1000)
        self.Table.append((both/mmrr)/1000)
        self.Table = [list(row) for row in zip(*self.Table)]
        self.save_export_vals(mmrr)
        return self.Table
    
    def save_export_vals(self,mmrr):
        vdb = ValuesDataBase(self.bobj)
        save_lines_vals = 0
        
        prefix_name = self.itemcfg.name.replace('_','')
        self.vals_list[f"{prefix_name}mmrr"] = mmrr
        self.vals_list[f"{prefix_name}mmrrns"] = mmrr*1E9
        if 'save_lines_vals' in self.itemcfg:
            save_lines_vals = self.itemcfg.save_lines_vals
            self.rows = len(self.Table)
            self.cols = len(self.Table[0])
            for rr in range(self.rows) :
                if rr in save_lines_vals:
                    for cc in range(self.cols) :
                        if cc == 0 or cc == 1:
                            self.vals_list[f"{prefix_name}{vdb.alph(rr+1)}{vdb.alph(cc+1)}"] = self.Table[rr][cc]
                        else:
                            self.vals_list[f"{prefix_name}{vdb.alph(rr+1)}{vdb.alph(cc+1)}"] = f"{self.Table[rr][cc]:.2f}"
                            
        vdb.write_values(self.vals_list)
        return
          
    