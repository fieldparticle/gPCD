
from ReportClass import *
import os
import inspect
from TrendLine import *

class ReportLatexPlot(ReportClass):

    def __init__(self, fields_list,itemcfg):
        super().__init__(fields_list,itemcfg)

    def get_line_format_dict(self,plot_command_string):
        format_dict = {}
        plot_format = self.itemcfg[plot_command_string]
        for kk in plot_format:
            all_item = kk.split("=")
            format_dict[all_item[0]]=all_item[1]
        return format_dict            

    def do_report(self):
        td = TrendLine()
        td.add_trend_line(self.fields_list)        
                
        for plt_num in range(1,self.itemcfg.num_plots+1):
            self.fig = plt.figure(plt_num)
            ax = self.fig.gca()
            for ii in range(1,len(self.fields_list)):
                if self.fields_list[ii].plot_num != plt_num:
                    continue
                # get the list of plot commands
                plot_command_string = f"PlotCommands{plt_num}"
                plot_command = self.itemcfg[plot_command_string]
                # Go thourgh the lines in the cfg file and plot them
                
                plot_format_string = f"plot_format{plt_num}{ii}"
                format_dict = self.get_line_format_dict(plot_format_string)
                print("----------------------------------------------")
                
               # print(self.fields_list[ii].data['loadedp'])
                print(type(self.fields_list[ii].data['cpums']))
                print("----------------------------------------------")
                #plt_eval_string = f"{plot_command[ii-1]}(self.fields_list[ii].data['{self.fields_list[0]['field']}'],self.fields_list[ii].data['{self.fields_list[ii]['field']}'],**format_dict)"
                plt_eval_string = f"{plot_command[ii-1]}(self.fields_list[ii].data['{self.fields_list[0]['field']}'],self.fields_list[ii].data['{self.fields_list[ii]['field']}'],**format_dict)"
                try:
                    eval(plt_eval_string)
                except BaseException as e:
                    raise BaseException(f"Plot type:{plot_command[ii-1]} failed.")
            
            
            plt.show()
            plt_commands_string = f"commands{ii-1}"
            plt_commands = self.itemcfg[plt_commands_string]
            for pp in plt_commands:
                eval(pp)

            pltTempImg = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}{ii}.png"
            plt.savefig(pltTempImg, bbox_inches='tight')
            plt.close("all") 
        

    
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

        
