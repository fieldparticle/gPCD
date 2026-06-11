import numpy as np
import matplotlib.pyplot as mplt
import csv
import math
from gbase.ValuesDataBase import *
from gbase.AttrDictFields import *
from gbase.gPCDData import *
data_list = []

from gbase.PlotterClass import *

def linearFunc(x,intercept,slope):
        """This function defines the function to be fit. In this case a linear
        function.
        
        Parameters
        ----------
        x : independent variable
        slope : slope
        intercept : intercept
        
        Returns
        -------
        y : dependent variable
        """
        y = intercept + slope * x
        return y

class A_PQBS_V_PQBR(PlotterClass):
    

    # Allocates prefix_name
    def __init__(self,itemcfg,base):
        super().__init__(itemcfg,base)
        
    def linearFunc(self,x,intercept,slope):
        """This function defines the function to be fit. In this case a linear
        function.
        
        Parameters
        ----------
        x : independent variable
        slope : slope
        intercept : intercept
        
        Returns
        -------
        y : dependent variable
        """
        y = intercept + slope * x
        return y

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

    def do_plot(self,N,rboth,both):
        diff = np.subtract(rboth,both)
        intercept,slope,r_squared,mean,std = self.do_linear_fit(N,rboth)
        self.vals_list["PPBQRTIntercept"] = f"{intercept}"
        self.vals_list["PPBQRTSlope"] = f"{slope:.4e}"
        self.vals_list["PPBQRTRSsquared"] = f"{r_squared:.4f}"
        self.vals_list["PPBQRTMean"] = f"{mean:.4f}"
        self.vals_list["PPBQRTSTD"] = f"{std:.4f}"
        lrboth = self.linearFunc(N,intercept,slope)

        intercept,slope,r_squared,mean,std = self.do_linear_fit(N,both)
        self.vals_list["PPBQTIntercept"] = f"{intercept}"
        self.vals_list["PPBQTSlope"] = f"{slope:.4e}"
        self.vals_list["PPBQTRSsquared"] = f"{r_squared:.4f}"
        self.vals_list["PPBQTMean"] = f"{mean:.4f}"
        self.vals_list["PPBQTSTD"] = f"{std:.4f}"
        lboth = self.linearFunc(N,intercept,slope)
            
        intercept,slope,r_squared,mean,std = self.do_linear_fit(N,diff)
        self.vals_list["PPBQDiffIntercept"] = f"{intercept}"
        self.vals_list["PPBQDiffSlope"] = f"{slope*1E9:.2f}"
        self.vals_list["PPBQDiffRSsquared"] = f"{r_squared:.4f}"
        self.vals_list["PPBQDiffMean"] = f"{mean:.4f}"
        self.vals_list["PPBQDiffSTD"] = f"{std:.4f}"
        ldiff = self.linearFunc(N,intercept,slope)
        
        # === Plot ===
        ##------------------------------------------
        plt,fig,ax = self.__new_figure__()
        fdct = self.__get_line_format_dict__(1)
        plt.plot(N,rboth,**fdct)

        fdct = self.__get_line_format_dict__(2)
        plt.plot(N,both,**fdct)

        fdct = self.__get_line_format_dict__(3)
        plt.plot(N,ldiff,**fdct)

        fdct = self.__get_line_format_dict__(4)
        plt.plot(N,lrboth,**fdct)

        fdct = self.__get_line_format_dict__(5)
        plt.plot(N,lboth,**fdct)

        fdct = self.__get_line_format_dict__(6)
        plt.plot(N,diff,**fdct)

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
        
        try:
            file_name = self.itemcfg.input_data_file_r
            self.df = pd.read_csv(file_name)
            N = self.df['expectedp']
            rcms = self.df['cms']
            rgms = self.df['gms']            
            rboth = np.add(rcms,rgms)
            
            file_name = self.itemcfg.input_data_file_s
            self.df = pd.read_csv(file_name)
            cms = self.df['cms']
            gms = self.df['gms']            
            both = np.add(cms,gms)
        except Exception as e:
            print(f"Error reading data: {e}. Both PBQR and PBQS studies must be included in the data source.")  
            return
        print("-------------------------- TOT ----------------------------")
        self.do_plot(N,rboth,both)
        #self.itemcfg['input_images'] = self.include

        self.__write_vals__()
        return


