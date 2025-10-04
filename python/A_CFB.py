import numpy as np
import matplotlib.pyplot as mplt
import csv
import math
from ValuesDataBase import *
from AttrDictFields import *

data_list = []

from PlotterClass import *

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

class A_CFB(PlotterClass):
    

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

    def do_plot(self,N,cms,gms):
        
        cms_intercept, cms_slope,cms_r_squared,cms_mean,cms_std, = self.do_linear_fit(N,cms)
        cms_ydata = linearFunc(N,cms_intercept,cms_slope).tolist()
        self.vals_list[f'{self.prefix_name}cmsK'] = f"{cms_slope:0.2g}"
        self.vals_list[f'{self.prefix_name}cmsIsec'] = f"{cms_intercept:0.2g}"
        self.vals_list[f'{self.prefix_name}cmsRSquared'] = f"{cms_r_squared:0.2g}"
        self.vals_list[f'{self.prefix_name}cmsMean'] = f"{cms_mean:0.2g}"
        self.vals_list[f'{self.prefix_name}cmsmstd'] = f"{cms_std:0.2g}"
        self.vals_list[f'{self.prefix_name}cmserr'] = f"{cms_std/cms_mean:0.2g}"
        gms_intercept, gms_slope,gms_r_squared,gms_mean,gms_std, = self.do_linear_fit(N,gms)
        self.vals_list[f'{self.prefix_name}gmsK'] = f"{gms_slope:0.2g}"
        self.vals_list[f'{self.prefix_name}gmsIsec'] = f"{gms_intercept:0.2g}"
        self.vals_list[f'{self.prefix_name}gmsRSquared'] = f"{gms_r_squared:0.2g}"
        self.vals_list[f'{self.prefix_name}gmsMean'] = f"{gms_mean:0.2g}"
        self.vals_list[f'{self.prefix_name}gmsmstd'] = f"{gms_std:0.2g}"
        self.vals_list[f'{self.prefix_name}gmserr'] = f"{gms_std/gms_mean:0.2g}"
        
        gms_ydata = linearFunc(N,gms_intercept,gms_slope).tolist()

        # === Plot ===
        ##------------------------------------------
        plt,fig,ax = self.__new_figure__()
        fdct = self.__get_line_format_dict__(1)
        plt.plot(N,cms,**fdct)
        fdct = self.__get_line_format_dict__(2)
        plt.plot(N,gms,**fdct)
        fdct = self.__get_line_format_dict__(3)
        plt.plot(N,cms_ydata,**fdct)
        fdct = self.__get_line_format_dict__(4)
        plt.plot(N,gms_ydata,**fdct)
        ##-------------------------------------------
        plt.pause(0.01)
        ##-------------------------------------------
        leg_list = self.__do_legend__()
        plt.legend(leg_list)
        ##-------------------------------------------
        self.__do_commands__(plt,fig,ax)
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
        # Load data
        self.df = pd.read_csv(self.itemcfg.input_data_file)
        N = self.df['expectedc']
        cms = self.df['cms']
        gms = self.df['gms']
        '''
        N = np.array(transposed[6]).astype(float)

        pc = np.array(transposed[6]).astype(float)
        particle_counts = [int(numeric_string) for numeric_string in pc]
        gms = np.array(transposed[4]).astype(float)
        cms = np.array(transposed[3]).astype(float)
        both = np.add(gms,cms)
        '''
        print("-------------------------- TOT ----------------------------")
        self.do_plot(N,cms,gms)
        #self.itemcfg['input_images'] = self.include
        
        self.__write_vals__()
        return


