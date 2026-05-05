import numpy as np
import matplotlib.pyplot as mplt
import csv
import math
from ValuesDataBase import *
from AttrDictFields import *

data_list = []

from PlotterClass import *

class NumberPapersParticle_zhu2007(PlotterClass):
    
        
    def __init__(self,itemcfg,base):
        super().__init__(itemcfg,base)
        self.data_list = []
   
    def plot_item(self,plt,fig,ax):
       
        year = []
        papers = []

        for p in self.data_list:
            try:
                year.append(p['year'])
                papers.append(p['ppaper'])
            except Exception as e:
                print("Skipping point due to error:", p, e)

        # Convert to evenly spaced positions
        x = np.arange(len(year))
        ax.locator_params(axis='y', nbins=5)
        fig, ax = plt.subplots(figsize=(10, 8))
        
        ax.bar(x, papers, color='blue', width=0.9)  # control thickness here
        ax.set_xticks(x)
        ax.set_xticklabels(year, rotation=45, ha="right")

        plt.tight_layout()
        

                
   



    def do_plot(self):
        # === Plot ===
        ##------------------------------------------
        plt,fig,ax = self.__new_figure__()
        ##-------------------------------------------
        ## DO PLOT HERE
        # Pass values a class varialbes
        self.plot_item(plt,fig,ax) 
        ##-------------------------------------------
        self.__do_commands__(plt,fig,ax)
        
        ##-------------------------------------------
        #leg_list = self.__do_legend__()
       #plt.legend(leg_list)
        
        ##-------------------------------------------
       
        filename = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}.png"
        self.__clean_files__(filename)
        plt.savefig(filename, dpi=self.itemcfg.dpi)
        self.include.append(filename)
        plt.close()
        
        
        

    def run(self):
        with open(self.itemcfg.input_data_file, 'r') as data:
            for line in csv.DictReader(data):
                self.data_list.append(line)
                #print(line)
        
        # Do one or many plots
        for ii in range(1):
            self.do_plot()
            #self.itemcfg['input_images'] = self.include
        
        #Write all vals
        self.__write_vals__()
        return
