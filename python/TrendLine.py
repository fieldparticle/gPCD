import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

class TrendLine():

    def __init__(self):
        pass        
    
    def add_trend_line(self,fields_list):
        for ii in range(1,len(fields_list)):
            if "linear_trend" in fields_list[ii].line_type:
                self.xvalue = fields_list[ii].data[fields_list[0]['field']]
                self.yvalue = fields_list[ii].data[fields_list[ii]['field']]
                intercept, slope = self.do_linear()
                print(fields_list[ii]['field'] )
                data = self.linearFunc(self.xvalue,intercept,slope).tolist()
                fields_list[ii].data[fields_list[ii]['field']] = pd.Series(self.linearFunc(self.xvalue,intercept,slope))
                print(fields_list[ii]['field'] )
                print(fields_list[ii].data[fields_list[ii]['field']] )
            #case "exponential":
            #    self.params, self.covariance = curve_fit(self.exponential_model, self.xvalue, self.yvalue)                          
            #    plt.plot(self.xvalue, self.exponential_model(self.xvalue, *self.params),**parms_dict)

    
    
    def exponential_model(self, x, a, b):
        return a * np.exp(b*x)
    
    def linear_model(self,x, a, b):
        return a * x + b
    
    def do_linear(self):
        #self.params, self.covariance = curve_fit(self.linearFunc, self.xvalue, self.yvalue)                          
            # This line calls the curve_fit function. It returns two arrays.
        # 'a_fit' contains the best fit parameters and 'cov' contains
        # the covariance matrix.
        if self.xvalue.size == 0 or  self.yvalue.size == 0 :
            print("TrendLine: no data")
            return
        a_fit,cov=curve_fit(self.linearFunc,self.xvalue,self.yvalue)
        self.params = a_fit
        self.covariance = cov
        # The next four lines define variables for the slope, intercept, and
        # there associated uncertainties d_slope and d_inter. The uncertainties
        # are computed from elements of the covariance matrix.
        inter = a_fit[0]
        slope = a_fit[1]
        self.intersect = np.sqrt(cov[0][0])
        self.slope = np.sqrt(cov[1][1])
        # Compute a best fit line from the fit intercept and slope.
        yfit = inter + slope*self.xvalue
        
        slp_str = f"{self.slope:10.3E}"
        print(slp_str)
        #key_str = f"{self.plotname}slope"
        #self.valHandler.appendValues(key_str,slp_str)
        isect_str = f"{self.intersect:10.3E}"
        print(isect_str)
        #key_str = f"{self.plotname}intercept"
        #self.valHandler.appendValues(key_str,slp_str)
        # Print the best fit values for the slope and intercept. These print
        # statments illustrate how to print a mix of strings and variables.
        #print(f'The slope = {slope}, with uncertainty {d_slope}')
        #print(f'The intercept = {inter}, with uncertainty {d_inter}')
        return inter,slope
  

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


   