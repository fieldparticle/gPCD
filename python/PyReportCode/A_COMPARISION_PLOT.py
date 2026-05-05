import numpy as np
import matplotlib.pyplot as mplt
import csv
import math
from ValuesDataBase import *
from AttrDictFields import *

data_list = []

from PlotterClass import *

class A_COMPARISION_PLOT(PlotterClass):
    
        
    def __init__(self,itemcfg,base):
        super().__init__(itemcfg,base)
        self.data_list = []
   
    def plot_item(self,plt,fig,ax):
        # Compute (N, time_per_obj_s) arrays
        N_vals = []
        tpo_vals = []
        labels = []
        types = []
        bodies = []
        yr = []
        endtoends = []

        for p in self.data_list:
            try:
                tpo = float(p["tpp"])
                tpo_vals.append(tpo)
                nm = p["name"]
                yrs = int(p["yr"])
                yr.append(yrs)
                typ = p["gpu"]
                types.append(typ)
                body = p["typ"]
                bodies.append(body)
                ete = p["e2e"]
                endtoends.append(ete)
                label = f"{nm}"
                labels.append(label)

            except Exception as e:
                print("Skipping point due to error:", p, e)

        hspace = 1.5
        # Plot (log–log)
        for ii in range(len(tpo_vals)):
            if "ksap" in labels[ii].lower():
                plt.text(yr[ii]+hspace,tpo_vals[ii],labels[ii],size=22)
            elif "bell" in labels[ii].lower():
                #plt.text(yr[ii]+hspace,tpo_vals[ii],labels[ii],size=22,color='firebrick')
                plt.text(yr[ii]+hspace,tpo_vals[ii],"Anonymized",size=22,color='firebrick')
            elif "liu" in labels[ii].lower():
                plt.text(yr[ii]+hspace,tpo_vals[ii]-50,labels[ii],size=22)
            elif "zhang" in labels[ii].lower():
                plt.text(yr[ii]+hspace,tpo_vals[ii]-50,labels[ii],size=22)
            elif "coming" in labels[ii].lower():
                plt.text(yr[ii]+hspace,tpo_vals[ii]-7500,labels[ii],size=22)
            elif "joselli" in labels[ii].lower():
                plt.text(yr[ii]+hspace,tpo_vals[ii]-5,labels[ii],size=22)
            else:
                plt.text(yr[ii]+hspace,tpo_vals[ii],labels[ii],size=22)

            if "gpcd" in labels[ii].lower():
                plt.plot(yr[ii], tpo_vals[ii], "o", markersize=15,color='green')
            elif "cpu" in types[ii].lower():
                plt.plot(yr[ii], tpo_vals[ii], "o", markersize=15,color='blue')
            elif "gpu" in types[ii].lower():
                plt.plot(yr[ii], tpo_vals[ii], "o", markersize=15,color='green')

            if "bnr" in endtoends[ii].lower():
                plt.plot(yr[ii], tpo_vals[ii], "*", markersize=15,color='w')
            elif "bn" in endtoends[ii].lower():
                plt.plot(yr[ii], tpo_vals[ii], "-", markersize=15,color='w')
            


            if "p" in bodies[ii].lower():
                plt.plot(yr[ii], tpo_vals[ii], "s", markersize=30,color='orange',fillstyle='none')


                
        #plt.loglog(N_vals[-1], tpo_vals[-1], "x", markersize=10, color='red') 
        ax.set_yscale('log')


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
