from ReportClass import *
import os
import inspect
from TrendLine import *
import re
from AttrDictFields import *
from ConfigUtility import *
from ValuesDataBase import *
class A_TABLE_CURVATURE():

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
        
        self.df = pd.read_csv(self.itemcfg.input_data_file)
        
        self.Table = []
        num_rows = 0
        self.Table.append(self.df['loc'])
        self.Table.append(self.df['a'])
        self.Table.append(self.df['b'])
        self.Table.append(self.df['c'])
        self.Table.append(self.df['frmtime'])
        self.Table.append( self.df['delt'])
        self.Table.append( self.df['delT'])
        self.Table.append( self.df['delTFrac'])
        self.Table.append( self.df['delTPRC'])
 

        self.Table = [list(row) for row in zip(*self.Table)]
        return self.Table
    
    def save_export_vals(self):
        pass
        g = self.lines_list[0]
        vdb = ValuesDataBase(self.bobj)
        save_lines_vals = 0
        prefix_name = self.itemcfg.name.replace('_','')
        if 'save_lines_vals' in self.itemcfg:
            save_lines_vals = self.itemcfg.save_lines_vals
            for rr in range(self.rows) :
                if rr in save_lines_vals:
                    for cc in range(self.cols) :
                       print(f"row{rr} col {cc} row {vdb.alph(rr+1)} col {vdb.alph(cc+1)}")
                       self.vals_list[f"{prefix_name}{vdb.alph(rr+1)}{vdb.alph(cc+1)}"] = self.table_array[rr][cc]
                            
        vdb.write_values(self.vals_list)
        return
          
    