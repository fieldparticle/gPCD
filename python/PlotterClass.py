
from AttrDictFields import *
from DataLine import *
import math
import numpy as np
import pandas as pd

class PlotterClass():
    
    def __init__(self,itemcfg,base):
        self.itemcfg = itemcfg
        self.bobj = base
        self.include = []

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
        return start_num,end_num
    
    def run(self):
        pass
    def do_commands(self,plt,fig,ax):
        plt_commands = self.itemcfg.plot_commands
        for pp in plt_commands:
            eval(pp)
        
     #******************************************************************
    # Do the legend
    #
    def do_legend(self):
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