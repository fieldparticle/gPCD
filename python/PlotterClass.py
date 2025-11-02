from ValuesDataBase import *
from AttrDictFields import *
from DataLine import *
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class PlotterClass():
    
    def __init__(self,itemcfg,base):
        self.itemcfg = itemcfg
        self.bobj = base
        self.include = []
        self.vals_list = AttrDictFields()
        self.prefix_name = self.itemcfg.name.replace('_','')

    def __open_data_file__(self):
        if not os.path.exists(self.itemcfg.input_data_file):
          raise FileNotFoundError(f"CSV not found: {self.itemcfg.input_data_file}")
        
      # Load data
        dfr = pd.read_csv(self.itemcfg.input_data_file)
        ee = dfr.shape
        beg,last = self.get_line_slices(1,ee[0])
        df = dfr.iloc[beg:last]
        return df



    def __new_figure__(self):
        plt.cla()
        plt.clf()
        plt.close()
        self.plt = plt
        self.fig = self.plt.figure(figsize=(10,6))
        self.ax = self.fig.gca()
        return self.plt,self.fig,self.ax
    
    def is_integer(self,s):
        try:
            int(s)
            return True
        except ValueError:
            return False
    
    def is_number(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False
        
    def __write_vals__(self):
        vdb = ValuesDataBase(self.bobj)
        vdb.write_values(self.vals_list)
    
    def __get_line_format_dict__(self,nm):
        plot_format_string = f"plot_format{nm}"
        format_dict = {}
        plot_format = self.itemcfg[plot_format_string]
        out_int = 0
        out_float = 0.0
        out_string = ""
        for kk in plot_format:
            all_item = kk.split("=")
            if self.is_integer(all_item[1]):
                format_dict[all_item[0]]=int(all_item[1])
            elif  self.is_number(all_item[1]):
                format_dict[all_item[0]]=float(all_item[1])
            else:
                 format_dict[all_item[0]]=all_item[1]
        return format_dict        
        

    def get_line_slices(self,line_num,line_len):
        start_num = 0
        end_num = 0
        if 'line_slices' in self.itemcfg:
            start_str  = self.itemcfg.line_slices[line_num]
            start_ary = start_str.split(':')
            start_num = int(start_ary[0])
            # if end in the field need to get lentgh
            if 'end' in start_ary[1]:
                end_num = line_len
            else:
                end_num = int(start_ary[1])
        else:
            return start_num,line_len
            
        return start_num,end_num
    
    def __clean_files__(self,filename):
        try:
            os.unlink(filename)
            print(f"File '{filename}' deleted successfully.")
        except FileNotFoundError:
            print(f"File '{filename}' does notexist yet")
    
    def run(self):
        pass

    def __do_commands__(self,plt,fig,ax):
        plt_commands = self.itemcfg.plot_commands
        for pp in plt_commands:
            try:
                eval(pp)
            except BaseException:
                print(f"Command:{pp} Failed.")
        
        
     #******************************************************************
    # Do the legend
    #
    def __do_legend__(self):
        leg_list = []
        leg_str = ""
        legend_commands = self.itemcfg.plot_legend 
        legend_string =legend_commands[0]
        stripped_leg = re.sub('$.*?', '', legend_string)
        for ll in range(len(legend_commands)):
            if '{' in legend_commands[ll]:
                variable_string = re.findall('\((.*?)\)', legend_commands[ll])
                if len(variable_string) == 0:
                    leg_list.append(legend_commands[ll])
                    continue
                variables = variable_string[0].split(',')
                
                fld = AttrDictFields()
                for var in variables:
                    new_var_text = var.split('.')
                    #print(new_var_text[1])
                    #print(self.lines_list[ll+1].line_type,"  :  ",legend_commands[ll])
                    #self.lines_list[ll+1][new_var_text[1]]
                    try:
                        fld[new_var_text[1]] = self.lines_list[ll+1][new_var_text[1]]
                    except BaseException as e:
                        print(e)
                # print(fld.K)    
                    
                    #val = self.lines_list[ll+1][var]
                
                new_str = eval(legend_commands[ll] )
                leg_list.append(new_str)
            else:
                leg_list.append(legend_commands[ll])
            # print(new_str)
        return leg_list
        
        #******************************************************************
    # Save the DataFields<data_num> configuraton item in a list
    #
    def clear(self):
        self.lines_list = []
        pltTempImg = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}.png"
        try: 
            os.remove(pltTempImg)
            print(f"File '{pltTempImg}' deleted successfully.")
        except FileNotFoundError:
            print(f"File '{pltTempImg}' does notexist yet")