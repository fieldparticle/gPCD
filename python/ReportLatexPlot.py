
from ReportClass import *
import os
import inspect
from TrendLine import *
import re
from AttrDictFields import *
class ReportLatexPlot(ReportClass):

    def __init__(self, fields_list,itemcfg):
        super().__init__(fields_list,itemcfg)

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



    def do_report(self):
        td = TrendLine()
        td.add_trend_line(self.fields_list)        
        #plt.rcParams['text.usetex'] = True
        for plt_num in range(1,self.itemcfg.num_plots+1):
            fig = plt.figure(plt_num,figsize=(6.5,6.5))
            ax = fig.gca()
            for ii in range(1,len(self.fields_list)):
                if self.fields_list[ii].plot_num != plt_num:
                    continue
                # get the list of plot commands
                plot_command_string = f"PlotCommands{plt_num}"
                plot_command = self.itemcfg[plot_command_string]
                # Go thourgh the lines in the cfg file and plot them
                plot_format_string = f"plot_format{plt_num}{ii}"
                format_dict = self.get_line_format_dict(plot_format_string)
                #print("----------------------------------------------")
                #print(type(self.fields_list[ii].data['cpums']))
                #print("----------------------------------------------")
                #plt_eval_string = f"{plot_command[ii-1]}(self.fields_list[ii].data['{self.fields_list[0]['field']}'],self.fields_list[ii].data['{self.fields_list[ii]['field']}'],**format_dict)"
                plt_eval_string = f"{plot_command[ii-1]}(self.fields_list[ii].data['{self.fields_list[0]['field']}'],self.fields_list[ii].data['{self.fields_list[ii]['field']}'],**format_dict)"
                    #plt.scatter(self.fields_list[ii].data['loadedp'],self.fields_list[ii].data['cpums'])
               
                eval(plt_eval_string)
                
            
            # Format the plot area
            

            plt_commands_string = f"commands{plt_num}"
            plt_commands = self.itemcfg[plt_commands_string]
            for pp in plt_commands:
                eval(pp)
            
            leg_list = self.do_legend(plt_num)
            ax.legend(leg_list)
            
            plt.show()
            pltTempImg = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}{ii}.png"
            plt.savefig(pltTempImg, bbox_inches='tight')
            plt.close("all") 
        

    # Legends
    def do_legend(self, plot_num):
    
        leg_list = []
        leg_str = ""
        legend_commands_string = f"legend{plot_num}"
        legend_commands = self.itemcfg[legend_commands_string]

        for ll in range(len(legend_commands)):
            if '{' in legend_commands[ll]:
                variable_string = re.findall('\((.*?)\)', legend_commands[ll])
                variables = variable_string[0].split(',')
                fld = AttrDictFields()
                for var in variables:
                    new_var_text = var.split('.')
                    self.fields_list[ll+1][new_var_text[1]]
                    fld[new_var_text[1]] = self.fields_list[ll+1][new_var_text[1]]
                   # print(fld.K)    
                    
                    #val = self.fields_list[ll+1][var]
                
                new_str = eval(legend_commands[ll] )
                self.fields_list[ll+1]['legend'] = new_str
                leg_list.append(new_str)
            else:
                self.fields_list[ll+1]['legend'] = legend_commands[ll]
                leg_list.append(legend_commands[ll])
               # print(new_str)
        return leg_list
    

    def save_latex(self):
        
        for ii in range(1,len(self.fields_list)):
            self.tex_output_name = self.itemcfg.tex_dir + "/" + self.itemcfg.name + ".tex"
            try:
                f = open(self.tex_output_name , "w")
            except IOError as e:
                print(e)
                self.log.log(self,f"Couldn't write to file ({e})")
                raise IOError(f"Couldn't write to file ({e})")
            tex_output_name = self.tex_output_name 
            try:
                
                w ="\\begingroup\n"
                f.write(w)
                w = "\\centering\n"
                f.write(w)
                w = "\\begin{figure*}[" + self.itemcfg.placement + "]\n"
                f.write(w)
                previewTex = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}{ii}.png"
                gdir = "".join(previewTex.rsplit(self.itemcfg.tex_dir))
                sgdir = ''.join( c for c in gdir if  c not in '/' )
        #                print(sgdir)    
                w = "\t\t\\includegraphics[width=" +  str(self.itemcfg.plot_width) +  "in]{" + sgdir + "}\n"
                f.write(w)
                refname = os.path.splitext(os.path.basename(gdir))[0]
                w = "\t\t\\label{fig:" + refname + "}\n"
                f.write(w)
                w = "\\hspace{" + str(self.itemcfg.hspace) + "in}\n"
                f.write(w)
                w = "\\caption[TITLE:" + self.itemcfg.title + "]{\\textit{" + self.itemcfg.caption + "}}\n"
                f.write(w)
                w = "\t\t\\label{fig:" + self.itemcfg.name + "}\n"
                f.write(w)
                w = "\\end{figure*}\n"
                f.write(w)
                w = "\\endgroup"
                f.write(w)
            except IOError as err:
                self.log.log(self,f"Couldn't write to file ({err})")
                f.close()
                return
            f.close()

        
    def replace_between_delimiters(self,text, start_delimiter, end_delimiter, replacement_string):
        """
        Replaces the substring between specified start and end delimiters with a new string.

        Args:
            text (str): The original string.
            start_delimiter (str): The starting delimiter.
            end_delimiter (str): The ending delimiter.
            replacement_string (str): The string to replace the content between delimiters.

        Returns:
            str: The modified string with the replaced content.
        """

        
        # Construct the regex pattern:
        # re.escape() handles special characters in delimiters
        # (.*?) matches any character non-greedily between delimiters
        pattern = re.escape(start_delimiter) + r"(.*?)" + re.escape(end_delimiter)


        # Use re.sub() to find and replace
        # The replacement string includes the delimiters themselves
        return re.sub(pattern, start_delimiter + replacement_string + end_delimiter, text)

