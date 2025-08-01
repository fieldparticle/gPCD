import numpy as np
from scipy.optimize import curve_fit
from ValHandler import *
class TrendLine():

    def __init__(self, xvalue,yvalue,fitType,plotName,valHandler,valDir):
        self.xvalue = xvalue
        self.yvalue = yvalue
        self.fitType = fitType
        self.plotname = plotName
        self.valHandler = valHandler
        self.valDir = valDir

    def exponential_model(self, x, a, b):
        return a * np.exp(b*x)
    
    def linear_model(self,x, a, b):
        return a * x + b
    
    def doLinear(self):
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
        key_str = f"{self.plotname}slope"
        self.valHandler.appendValues(key_str,slp_str)
        slp_str = f"{self.intersect:10.3E}"
        key_str = f"{self.plotname}intercept"
        self.valHandler.appendValues(key_str,slp_str)
        # Print the best fit values for the slope and intercept. These print
        # statments illustrate how to print a mix of strings and variables.
        #print(f'The slope = {slope}, with uncertainty {d_slope}')
        #print(f'The intercept = {inter}, with uncertainty {d_inter}')

    def doTrendLine(self,plt,parms_dict):
        match(self.fitType):
            case "linear":
                self.doLinear()
                plt.plot(self.xvalue, self.linearFunc(self.xvalue, *self.params), **parms_dict)
            case "exponential":
                self.params, self.covariance = curve_fit(self.exponential_model, self.xvalue, self.yvalue)                          
                plt.plot(self.xvalue, self.exponential_model(self.xvalue, *self.params),**parms_dict)


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


   