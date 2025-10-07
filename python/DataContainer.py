from gPCDData import *

from AttrDictFields import *
from DataLine import *
import math
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QMessageBox
from CSVData import *
from ValuesDataBase import *

class DataContainer():

    raw_lines_list = []
    lines_list = []
     #******************************************************************
    # GP message box
    #
    def msg_box(self,text):
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.exec()
    #******************************************************************
    # init
    #
    def __init__(self, Base, itemcfg):
        self.active_lines = []
        self.bobj = Base
        self.cfg = self.bobj.cfg
        self.log = self.bobj.log
        self.data_base = None
        self.itemcfg = itemcfg
    
    
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
    
   
    def get_particle_data_fields_table(self):
        self.raw_lines_list.clear()
        data_fields = self.itemcfg['data_fields']
        for jj in range(len(data_fields)):
            self.raw_lines_list.append(data_fields[jj])
            self.active_lines.append(1)
        

    #******************************************************************
    # Save the DataFields<data_num> configuraton item in a list
    #
    def get_particle_data_fields(self):
        more_fields = True
        self.raw_lines_list.clear()
        data_fields = self.itemcfg['data_fields']
        for jj in range(len(data_fields)):
            if self.itemcfg.data_type == 'xdata':
                self.raw_lines_list.append(data_fields[jj])
                self.active_lines.append(1)
            if self.itemcfg.plot_switch[jj] == 'true':
                self.raw_lines_list.append(data_fields[jj])
                self.active_lines.append(1)
            else:
                self.raw_lines_list.append(data_fields[jj])
                self.active_lines.append(0)
        
        return 
    
    def split_transendential(self,string):
        fields= []
        string = string.replace('np.log',"")
        char_remove = ["(",")"]
        for char in char_remove:
            string = string.replace(char, " ") 
        all_fields = string.split(" ") 
        fields.append(all_fields[1])
        #fields.append(all_fields[0])
        return fields
    
    def split_equation(self,string):
        new_str =string
        if 'log10' in string or 'log' in string:
            fields = self.split_transendential(string)
            new_str =  " ".join(fields)
        char_remove = ["(",")"]
        for char in char_remove:
            new_str = new_str.replace(char, " ")                
        char_remove = ["+","-","/","*"]
        for char in char_remove:
            new_str = new_str.replace(char, "?")       
        all_fields = new_str.split(',')
        fields = all_fields[0].split('?')
        for nn in fields:
            if 'fld' not in nn:
                fields.remove(nn)
        return fields

    def extract_fields(self,string):
        #string = "np.log((fld.gms+fld.cms)/fld.loadedp)"
        if "np.log" in string:
            string = string.replace('np.log',"")
        if "np.log10" in string:
            string = string.replace('np.log10',"")
        str_len = len(string)
        nn = 0
        bld_fld = []
        out_list = []
        while (nn < str_len):
            jj = string.find('fld.',nn)
            if jj > -1:
                bld_fld.clear()
                stop_len = str_len
                start_len = jj
                for ii in range(start_len,stop_len):
                    if string[ii] not in "()/+-*":
                        #print(string[ii])
                        bld_fld.append(string[ii])
                    else:
                        break
                new_str = "".join(bld_fld)
                out_list.append(new_str)
                nn = jj +1 #print(new_str)                
            else:
                break
        return out_list        

            #print(nn)
    
    #******************************************************************
    # parse the fields from the list and add to a dictionary 
    #
    def parse_lines_list(self):
        line = 0
        data_type = self.itemcfg.data_type
        data_source = self.itemcfg.data_source
        for fnum in range(len(self.raw_lines_list)):
    
           #print(any(map(lambda char: char in data_lines, "+-/*")))
            if any(map(lambda char: char in self.raw_lines_list[fnum], "+-/*()")) :

                dl = DataLine()
                if self.active_lines[line] == 0:
                    dl['is_active'] = False
                else:
                    dl['is_active'] = True
                #data_type = data_lines.split(',')
                equation = self.raw_lines_list[fnum]
                dl['is_equation'] = True
                dl['equation']= equation
                dl['line_type'] = data_type[line]
                dl["line_num"] = line
                lines_list = self.extract_fields(equation)
                data_sources = data_source[fnum].split(',')
                if len(data_sources) != len(lines_list):
                    raise BaseException("cfg.data_source number of items do not match number of fields in cfg.data_fields (is it an equation?)") 
                for jj in range(len(lines_list)):
                    fields_dict = AttrDictFields()
                    fields_dict["data_source"] = data_sources[jj]
                    fields_dict['whole_field'] = lines_list[jj].strip(" ") 
                    field_name = lines_list[jj].split('.')  
                    fields_dict["field"] = field_name[1].strip(" ") 
                    
                    fields_dict["test_type"] = self.itemcfg.mode
                    
                    dl.data_lines.append(fields_dict)  
                self.lines_list.append(dl)
                line +=1    
            else:
                #print(data_lines)
                dl = DataLine()
                if self.active_lines[line] == 0:
                    dl['is_active'] = False
                else:
                    dl['is_active'] = True
                fields_dict = AttrDictFields()
                comma_split = self.raw_lines_list[fnum].split(',')
                dot_split = comma_split[0].split('.') 
                dl['is_equation'] = False
                dl['line_type'] = data_type[line]
                if 'csvplot' in self.itemcfg.type or 'csvtable' in self.itemcfg.type:
                    dl['data_file'] = self.itemcfg.data_files[line]
                fields_dict['line_type'] = data_type[line]
                fields_dict['field'] = dot_split[1].strip(" ")
                fields_dict['whole_field'] = comma_split[0].strip(" ")
                fields_dict['data_source'] =  data_source[line]
                dl['line_num'] = line
                dl.data_lines.append(fields_dict)  
                line +=1
                self.lines_list.append(dl)
       # self.print_field_list()
        return

    #******************************************************************
    # Diagnostic print fields list
    # 
    def print_field_list(self):
        print(f"Length of print_field_list is : {len(self.lines_list)}.")
        for lines in self.lines_list:
            print(f"Length of line: {len(lines)}.")
            for items in lines:
                item = items[1]
                record = items[0]
                print(f"line_type:{item.line_type},field :{item.field}")

    #******************************************************************
    # Get the field list
    #
    def get_feilds_list(self):
        return self.lines_list

    def get_line_format_dict(self,plot_command_string):
        format_dict = {}
        plot_format = self.itemcfg[plot_command_string]
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
        
    def do_equations(self):
        for line in self.lines_list:
            if line.is_equation == True:
                ydata = self.do_equation(line)
                line.data[line.data_lines[0].field] = ydata

    def do_equation(self,liney):
        #print(len(plot_liney.data_lines))
        fld = AttrDictFields()
        for nm in range(len(liney.data_lines)):
            #print(plot_liney.data_lines[nm])    
            #print(plot_liney.data_lines[nm].field)
            fld[liney.data_lines[nm].field] = liney.data[liney.data_lines[nm].field]
            #print(plot_liney.data[plot_liney])
        
        try:
            ydata = eval(liney.equation)  
            #
        except BaseException as e:
             print(f"eval equaiton error {e}")

        return ydata

     ############################################
    # Do a single line of ydata
    def run_plot(self,xdata,ydata,plot_command,format_dict) :
        # get the list of plot commands
        print(xdata.data.line_data)
        # Go thourgh the lines in the cfg file and plot them
        plt_eval_string = f"{plot_command}(xdata.data.line_data,ydata.data.line_data,**format_dict)"
        #print(plt_eval_string)
        try:
            eval(plt_eval_string)
        except BaseException as e:
            print(e)

    def do_report(self):

        # get plot fig and axes 
        fig = plt.figure(figsize=(6.5,6.5))
        ax = fig.gca()
        xdata = None

        # Ru thru plot lines
        for nm in range(len(self.lines_list)):
            if self.lines_list[nm]['is_active'] == True:
                #print(self.lines_list[nm].data)
                # If the line contains an equation then perform the math before anyhtin else
                
                if self.lines_list[nm].is_equation == True:
                    ydata = self.do_equation(self.lines_list[nm])
                    self.lines_list[nm].data['line_data'] = ydata
                    #self.lines_list[nm].data_lines[0].field = self.lines_list[nm].equation
                else:
                   print(self.lines_list[nm].data_lines[0].field)
                   self.lines_list[nm].data['line_data'] = self.lines_list[nm].data[self.lines_list[nm].data_lines[0].field] 
                # Just ydata
                if self.lines_list[nm].line_type == "ydata":
                    plot_format_string = f"plot_format{self.lines_list[nm].line_num}"
                    format_dict = self.get_line_format_dict(plot_format_string)
                    pn = self.lines_list[nm].line_num - 1
                    plot_command = self.itemcfg.line_commands[pn]
                    self.run_plot(self.lines_list[0],self.lines_list[nm],plot_command,format_dict)
                # Skip this we already got the xdata
                elif self.lines_list[nm].line_type == "xdata":
                    continue
                # If its a treandline the perform the fit
                elif 'trend' in self.lines_list[nm].line_type or 'residual' in self.lines_list[nm].line_type :
                    td = TrendLine(self.bobj)
                    self.lines_list[nm]
                    ydata = td.add_trend_line(self.lines_list[0],self.lines_list[nm])
                    self.lines_list[nm].data['line_data'] = ydata
                    plot_format_string = f"plot_format{self.lines_list[nm].line_num}"
                    format_dict = self.get_line_format_dict(plot_format_string)
                    pn = self.lines_list[nm].line_num - 1
                    plot_command = self.itemcfg.line_commands[pn]
                    self.run_plot(self.lines_list[0],self.lines_list[nm],plot_command,format_dict)

        
        # Do plot commands
        plt_commands = self.itemcfg.plot_commands
        for pp in plt_commands:
            eval(pp)
        
        leg_list = self.do_legend()
        ax.legend(leg_list)
        
       # plt.show()
        pltTempImg = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}.png"
        try: 
            os.remove(pltTempImg)
            print(f"File '{pltTempImg}' deleted successfully.")
        except FileNotFoundError:
            print(f"File '{pltTempImg}' does notexist yet")
    
        plt.savefig(pltTempImg, bbox_inches='tight')
        plt.close("all") 
    

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
            if self.active_lines[ll+1] == 1:
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
    # Call the first data base and verify
    #
    def do_verify(self):
        field_dict= self.lines_list[0]
        data_obj = field_dict.data_object
        return data_obj.do_verify(field_dict)

    #******************************************************************
    # Call the first data base and verify
    #
    def apply_data_to_fields(self):
        start_num = 0
        slice_flag = 0
        for nm in range(len(self.lines_list)):
            if 'line_slices' in self.itemcfg:
                start_str  = self.itemcfg.line_slices[nm-1]
                start_ary = start_str.split(':')
                start_num = int(start_ary[0])
                # if end in the field need to get lentgh
                if 'end' in start_ary[1]:
                    slice_flag = 1
                else:
                    #if length is fed
                    slice_flag = 2
                    end_num = int(start_ary[1])
            else:
                # No Slice
                slice_flag = 3
            data_obj = self.lines_list[nm].data_object
            try:
                data = data_obj.assign_data(self.lines_list[nm])
            except BaseException as e:
                print(f"Could not assign data in apply_data_to_fields:{e}")
                return
            if nm == 0:
                if('save_vals') in self.itemcfg:
                    vdb = ValuesDataBase(self.bobj)
                    prefix_name = self.itemcfg.name.replace('_','')
                    vals_list = AttrDictFields()
                    
                    for vals in self.itemcfg.save_vals:
                        fld = vals.split('=')
                        row = int(fld[1])
                        line_data = float(data[fld[0]].values[0])
                        vals_list[f"{prefix_name}{fld[0]}"] = int(line_data)
                        vdb.write_values(vals_list)
                        

            #self.lines_list[0]['start_val'] = start_num
            self.lines_list[nm]['start_val'] = start_num

            for ii in self.lines_list[nm].data_lines:
                if slice_flag == 1:
                    end_num = len(data[ii.field])
                    self.lines_list[0]['end_val'] = end_num
                    self.lines_list[nm].data[ii.field] = data[ii.field][start_num:end_num]
                    self.lines_list[nm]['end_val'] = end_num
                elif(slice_flag == 2):
                    self.lines_list[0]['end_val'] = end_num
                    self.lines_list[nm].data[ii.field] = data[ii.field,start_num:end_num]
                    self.lines_list[nm]['end_val'] = end_num
                elif(slice_flag == 3):
                    end_num = len(data[ii.field])
                    self.lines_list[0]['end_val'] = end_num
                    self.lines_list[nm].data[ii.field] = data[ii.field]
                    self.lines_list[nm]['end_val'] = end_num

        
        return 
        

    #******************************************************************
    # Call the first data base and verify
    #
    def do_performance(self):
        for ii in self.lines_list:
            data_obj = ii.data_object
            data_obj.check_data_files(ii)
            data_obj.do_performance(ii)
            data_obj.read_summary_file(ii)

    #******************************************************************
    # load the data into the fields
    #
    def resolve_data_files(self):
        
        for ln in range(len(self.lines_list)):
                #print(jj)
                self.lines_list[ln]["source_dir"] = self.itemcfg.input_data_dir
                self.out_folder = os.path.dirname(self.itemcfg.input_data_dir)
                for ii in range(len(self.lines_list[ln].data_lines)):
                    
                    if self.itemcfg.type == 'plot' or self.itemcfg.type == 'gpcd_table':
                        self.lines_list[ln]["data_object"] = gPCDData(self,self.itemcfg)
                        self.lines_list[ln]["target_dir"]  = self.out_folder + '/' + "perfData" + self.lines_list[ln].data_lines[ii].data_source    
                        self.lines_list[ln]["mode"] = self.itemcfg.mode
                        self.lines_list[ln]["compute_type"] = self.itemcfg.compute_type
                    else:
                        self.lines_list[ln]["data_object"] = CSVData(self,self.itemcfg)
                        self.lines_list[ln]["target_dir"]  = self.itemcfg.input_data_dir
        
        return 


        
