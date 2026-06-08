from gbase.ReportClass import *

import os
import inspect
from gbase.TrendLine import *
import re
from gbase.AttrDictFields import *
from gbase.ConfigUtility import *
from gbase.ValuesDataBase import *
from gbase.gPCDData import *
class A_PQBRT_SUMMARY_TABLE():

    def __init__(self,itemcfg,base):
        self.itemcfg = itemcfg
        self.bobj = base
        self.include = []
        self.vals_list = AttrDictFields()
        self.prefix_name = self.itemcfg.name.replace('_','')
        update_gpcd_data(base,self.itemcfg)
        
       
    def replace_between_delimiters(self,text, start_delimiter, end_delimiter, replacement_string):
        pattern = re.escape(start_delimiter) + r"(.*?)" + re.escape(end_delimiter)


        # Use re.sub() to find and replace
        # The replacement string includes the delimiters themselves
        return re.sub(pattern, start_delimiter + replacement_string + end_delimiter, text)

    
        
    header_arry = []
    def run(self):
        self.tex_output_name = self.itemcfg.tex_dir + "/" + self.itemcfg.name + ".tex"
        try:
            f = open(self.tex_output_name, "w")
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
            return

        self.df = pd.read_csv(self.itemcfg.input_data_file)
        self.df["loadedp"] = pd.to_numeric(self.df['loadedp'], downcast='integer', errors='coerce')

        N = self.df['loadedp']
        self.max_particle_count = self.df['loadedp'].max()
        self.max_collisons  = self.df['expectedc'].max()

        self.cms = self.df['cms'].max()*1000.0
        self.gms = self.df['gms'].max()*1000.0
        self.fps = self.df['fps'].min()
        self.both = np.add(self.gms,self.cms)
        self.thorughput = (self.max_particle_count/(self.both))/1000.0
        self.save_export_vals()
        f.write(r"\begin{table}[t]" + "\n")
        f.write(r"\caption{Performance summary for randomly distributed particle configurations.}" + "\n")
        f.write(r"\label{tab:performance_summary}"+ "\n")
        f.write(r"\centering"+ "\n")
        f.write(r"\begin{tabular}{lr}"+ "\n")
        f.write(r"\toprule"+ "\n")

        f.write(r"\textbf{Metric} & \textbf{Value}\\"+ "\n")
        f.write(r"\midrule"+ "\n")
        
        f.write(f"Maximum Particle Count & {int(self.max_particle_count):,} \\\\ \n")
        f.write(f"Maximum Collision Count & {int(self.max_collisons):,} \\\\ \n")
        f.write(f"Peak Throughput (million particles/s) & {int(self.thorughput):,} \\\\ \n")
        f.write(f"Peak Frame Rate (FPS) & {int(self.fps)} \\\\ \n")
        f.write(f"Largest-Case Compute Time (ms) & {self.cms:.2f} \\\\ \n")
        f.write(f"Largest-Case Graphics Time (ms) & {self.gms:.2f} \\\\ \n")
        f.write(f"Largest-Case Total Time (ms) & {self.both:.2f} \\\\ \n")

        f.write(r"\bottomrule"+ "\n")
        f.write(r"\end{tabular}"+ "\n")
        f.write(r"\end{table}"+ "\n")  
        
        f.close()
        #self.save_export_vals(mmrr)
        return None
    
    def save_export_vals(self):
        vdb = ValuesDataBase(self.bobj)
        save_lines_vals = 0
        
        prefix_name = self.itemcfg.name.replace('_','')
        
        
        self.vals_list["SUMMARYPARTICLECOUNT"] = f"{self.max_particle_count:,}"
        self.vals_list["SUMMARYCOLLISONS"] = f"{self.max_collisons:,}"
        self.vals_list["SUMMARYTHROUGHPUT"] = f"{int(self.thorughput)}"
        self.vals_list["SUMMARYFPS"] = f"{int(self.fps):,}"
        self.vals_list["SUMMARYCOMPUTE"] = f"{self.cms:.2f}"
        self.vals_list["SUMMARYGRAPHICS"] = f"{self.gms:.2f}"
        self.vals_list["SUMMARYTOTALTIME"] = f"{self.both:.2f}"
        vdb.write_values(self.vals_list)

        return
          
    
