
from ReportClass import *
import os
import inspect

class ReportLatexPlot(ReportClass):

    def __init__(self, fields_list,itemcfg):
        super().__init__(fields_list,itemcfg)

    def get_line_format_dict(self,plot_command,line_num):
        format_dict = {}
        for vv in range(len(plot_command)):
                plot_format_string = f"plot_format{line_num}{vv+1}"
                plot_format = self.itemcfg[plot_format_string]
                for kk in plot_format:
                    all_item = kk.split("=")
                    format_dict[all_item[0]]=all_item[1]
        return format_dict            

    def do_report(self):
            
        for ii in range(1,len(self.fields_list)):
            self.fig = plt.figure(ii)
            ax = self.fig.gca()
            plot_command_string = f"PlotCommands{ii}"
            plot_command = self.itemcfg[plot_command_string]
            format_dict = self.get_line_format_dict(plot_command,ii)
            for jj in range(len(plot_command)):
                plt_eval_string = f"{plot_command[jj]}(self.fields_list[ii].data['{self.fields_list[0]['field']}'],self.fields_list[ii].data['{self.fields_list[ii]['field']}'],**format_dict)"
                #print(plt_eval_string)
                eval(plt_eval_string)
                plt.show()


            plt_commands_string = f"commands{ii}"
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

        
