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
        
    def s_per_obj_from_point(self,p):
        if "ns_per_obj" in p:
            return p["ns_per_obj"] * 1e-9
        if "time_s" in p and p["N"] is not None:
            return p["time_s"] / p["N"]
        if "fps" in p and p["N"] is not None:
            return (1.0 / p["fps"]) / p["N"]
        if "ns_pre_obj" in p and p["N"] is not None:
            return (1.0 / p["ns_pre_obj"]) / p["N"]
        raise ValueError(f"Point missing required timing fields: {p}")
    
    def plot_item(self):
        # Compute (N, time_per_obj_s) arrays
        N_vals = []
        tpo_vals = []
        labels = []

        for p in self.data_list:
            try:
                tpo = self.s_per_obj_from_point(p)
                N_vals.append(float(p["N"]))
                tpo_vals.append(float(tpo))
                labels.append(p["name"])
            except Exception as e:
                print("Skipping point due to error:", p, e)

        # Plot (log–log)
        plt.figure(figsize=(8, 6))
        plt.loglog(N_vals, tpo_vals, "o", markersize=7)

        # Connect points in an arbitrary order (optional)
        plt.loglog(N_vals, tpo_vals, "-", linewidth=1, alpha=0.4)

        # Annotate each point slightly offset to avoid overlap
        for x, y, lbl in zip(N_vals, tpo_vals, labels):
            plt.text(x*1.08, y*1.10, lbl, fontsize=8)        

    def do_plot(self):
        # === Plot ===
        ##------------------------------------------
        plt,fig,ax = self.__new_figure__()
        ##-------------------------------------------
        
        #plt.plot(k_space, T_fit, color="blue")
        
        ##-------------------------------------------
        leg_list = self.__do_legend__()
        plt.legend(leg_list)
        ##-------------------------------------------
        self.__do_commands__(plt,fig,ax)
        
        ##-------------------------------------------
        ## DO PLOT HERE
        # Pass values a class varialbes
        self.plot_item()
        filename = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}.png"
        self.__clean_files__(filename)
        plt.savefig(filename, dpi=self.itemcfg.dpi)
        self.include.append(filename)
        plt.close()
        
        ##-------------------------------------------
        # Save Values
        '''
        self.vals_list[f"{self.prefix_name}{name}StartRow"] = 10
        self.vals_list[f"{self.prefix_name}{name}StartRowParticlesVal"] = int(float(data_list[0][6]))
        self.vals_list[f"{self.prefix_name}{name}MaxParticles"] = f"{xmaN}"
        self.vals_list[f"{self.prefix_name}{name}a"] = f"{a2:0.3e}"
        self.vals_list[f"{self.prefix_name}{name}b"] = f"{b:0.3e}"
        self.vals_list[f"{self.prefix_name}{name}c"] = f"{c:0.3e}"
        self.vals_list[f"{self.prefix_name}{name}twoa"] = f"{2*a:0.3e}"
        self.vals_list[f"{self.prefix_name}{name}UpperBoundCurvature"] = f"{curvature:0.3e}"
        self.vals_list[f"{self.prefix_name}{name}QuadraticContributionta"] = f"{del_t1:0.4e}"
        self.vals_list[f"{self.prefix_name}{name}QuadraticContributiontb"] = f"{del_t2:0.4e}"
        self.vals_list[f"{self.prefix_name}{name}QuadraticContributionfrc"] = f"{del_t2_frc:0.6f}"
        self.vals_list[f"{self.prefix_name}{name}QuadraticContributionpct"] = f"{del_t2_pct:0.6f}"
        self.vals_list[f"{self.prefix_name}{name}TotalTime"] = f"{val_time*1000:0.4f}"
        self.vals_list[f"{self.prefix_name}{name}TotalTimeCont"] = f"{delt*1000:0.4f}"
        max_as_int = int(float(max_n))
        self.vals_list[f"{self.prefix_name}{name}EstimateNoticeableN"] = f"{max_as_int:,}"
        rescale = 2*a*1E7*1E6 
        self.vals_list[f"{self.prefix_name}{name}Rescale"] = f"{rescale:0.4e}"
        '''
        

    def run(self):
        ''' If you need a data frame        
        # Read data
        if not os.path.exists(self.itemcfg.input_data_file):
          raise FileNotFoundError(f"CSV not found: {self.itemcfg.input_data_file}")
        # Load data
        self.df = pd.read_csv(self.itemcfg.input_data_file)
        '''
        ''' If you need items
        with open(self.itemcfg.input_data_file, mode='r') as file:
            csv_reader = csv.reader(file)
            # If you needto skip some rows 
            for ii in range(0,28):
                next(csv_reader)  # Skip the header
            
            for row in csv_reader:
                self.data_list.append(row)
        '''
        with open(self.itemcfg.input_data_file, 'r') as data:
            for line in csv.DictReader(data):
                self.data_list.append(line)
                print(line)
        
        # Do one or many plots
        for ii in range(1):
            self.do_plot()
            self.itemcfg['input_images'] = self.include
        
        #Write all vals
        self.__write_vals__()
        return
