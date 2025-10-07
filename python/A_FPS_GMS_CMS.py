import numpy as np
import matplotlib.pyplot as mplt
import csv
import math
from ValuesDataBase import *
from AttrDictFields import *
from PlotterClass import *

class A_FPS_GMS_CMS(PlotterClass):
    

    # Allocates prefix_name
    def __init__(self,itemcfg,base):
        super().__init__(itemcfg,base)


    def do_linear_fit(self,N,ydata):
        popt,cov=curve_fit(linearFunc,N,ydata)
        self.params = popt
        self.covariance = cov
        # The next four lines define variables for the slope, intercept, and
        # there associated uncertainties d_slope and d_inter. The uncertainties
        # are computed from elements of the covariance matrix.
       
        intersect = popt[0].astype(float)
        slope = popt[1].astype(float)
        mean = np.mean(ydata).astype(float)
        std = np.std(ydata).astype(float)

        

        y_predicted = linearFunc(N, *popt)
        ss_total = np.sum((ydata - np.mean(ydata))**2)
        ss_residual = np.sum((ydata - y_predicted)**2)
        r_squared = 1 - (ss_residual / ss_total)
        return intersect,slope,r_squared,mean,std

    def do_plot(self,N,rcms,rgms,fps,rboth):
        # === Plot ===
        ##------------------------------------------
        plt,fig,ax = self.__new_figure__()
        fdct = self.__get_line_format_dict__(1)
        plt.plot(N,fps,**fdct)
        fdct = self.__get_line_format_dict__(2)
        plt.plot(N,rcms,**fdct)
        fdct = self.__get_line_format_dict__(3)
        plt.plot(N,rgms,**fdct)
        fdct = self.__get_line_format_dict__(4)
        plt.plot(N,rboth,**fdct)
        ##-------------------------------------------
        plt.pause(0.01)
        ##-------------------------------------------
        leg_list = self.__do_legend__()
        plt.legend(leg_list)
        ##-------------------------------------------
        self.__do_commands__(plt,fig,ax)
        plt.tight_layout()
        ##-------------------------------------------
        #self.plt.tight_layout()
        filename = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}.png"
        self.__clean_files__(filename)
        plt.savefig(filename, dpi=self.itemcfg.dpi)
        self.include.append(filename)
        plt.close()
                       
        #self.vals_list[f"{self.prefix_name}{name}StartRow"] = 10
        #self.vals_list[f"{self.prefix_name}{name}StartRowParticlesVal"] = int(float(data_list[0][6]))
        #self.vals_list[f"{self.prefix_name}{name}MaxParticles"] = f"{xmaN}"
        

    def run(self):
        data_source = self.itemcfg.data_source
        for ii in data_source:
             file_name = self.itemcfg.input_data_dir + "/" + f"perfData{ii}/perfdataPerformanceSummary.csv"
             self.df = pd.read_csv(file_name)
             N = self.df['loadedp']
             rcms = self.df['cms']
             rgms = self.df['gms']            
             rboth = np.add(rcms,rgms)
             fps = self.df['fps'] 
             cpums = []
             for ii in range(len(fps)):
                cpums.append(1.0/fps[ii])
                
                 
        print("-------------------------- TOT ----------------------------")
        self.do_plot(N,rcms,rgms,cpums,rboth)
        #self.itemcfg['input_images'] = self.include
        
        self.__write_vals__()
        return


