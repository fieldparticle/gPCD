import numpy as np
import pandas as pd
import math
from scipy.stats import linregress
from scipy.optimize import curve_fit

def quadratic_model(x, a, b, c):
    return a * x**2 + b * x + c

def quadratic_funct(x, a, b, c):
    return a * x**2 + b * x + c

def power_func(x, a, b,c):
    return a * (x**b)+c

#def log10_func(x, a, b ):
 #   return a * np.log(x) + b
    #return a*x*np.log(x-c)+b

def log10_func(x, a, b): # x-shifted log
    return a*np.log(x)+b

def exponential_model(self, x, a, b):
    return a * np.exp(b*x)
    
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

class TrendLine():

    
    def __init__(self):
        pass        
    
    def add_trend_line(self,lines_listx,lines_listy):
        self.lines_listx = lines_listx
        self.lines_listy = lines_listy
        #print(lines_listx.data_lines[0].field)    
        #print(lines_listy.data_lines[0].field)
        self.xvalue = lines_listx.data[lines_listx.data_lines[0].field]
        self.yvalue = lines_listy.data[lines_listy.data_lines[0].field]
        #print(lines_listy.line_type)
        if "linear_trend" in lines_listy.line_type:
            intercept, slope = self.do_linear_fit(linearFunc)
            #intercept, slope = self.do_linear_fit_regress()
            data = linearFunc(self.xvalue,intercept,slope).tolist()
            lines_listy.data[lines_listy.data_lines[0].field] = pd.Series(linearFunc(self.xvalue,intercept,slope))
            
        elif "quadratic_trend" in lines_listy.line_type:
            a,b,c = self.do_poly_fit()
            data = quadratic_model(self.xvalue,a,b,c).tolist()
            lines_listy.data[lines_listy.data_lines[0].field] = pd.Series(quadratic_model(self.xvalue,a,b,c))
        
        elif "quadratic_trend" in lines_listy.line_type:
            a,b,c = self.do_poly_fit()
            data = quadratic_model(self.xvalue,a,b,c).tolist()
            lines_listy.data[lines_listy.data_lines[0].field] = pd.Series(quadratic_model(self.xvalue,a,b,c))

        elif "power_trend" in lines_listy.line_type:
            k_val, exponent, intercept = self.do_power_fit()
            data = power_func(self.xvalue,k_val,exponent,intercept).tolist()
            lines_listy.data[lines_listy.data_lines[0].field] = pd.Series(power_func(self.xvalue,k_val,exponent,intercept))

        elif "log10_trend" in lines_listy.line_type:
            a,b = self.do_log10_fit()
            data = log10_func(self.xvalue,a,b).tolist()
            lines_listy.data[lines_listy.data_lines[0].field] = pd.Series(log10_func(self.xvalue,a,b))
    
        if "linear_residual" in lines_listy.line_type:
            y_data = lines_listy.data[lines_listy.data_lines[0].field]
            intercept, slope = self.do_linear_fit(linearFunc)
            data = linearFunc(self.xvalue,intercept,slope).tolist()
            lines_listy.data[lines_listy.data_lines[0].field] = pd.Series(linearFunc(self.xvalue,intercept,slope))
            lines_listy.data[lines_listy.data_lines[0].field] = pd.Series(y_data - data)
            
        elif "quadratic_residual" in lines_listy.line_type:
            y_data = lines_listy.data[lines_listy.data_lines[0].field]
            a,b,c = self.do_poly_fit()
            data = quadratic_model(self.xvalue,a,b,c).tolist()
            #lines_listy.data[lines_listy.data_lines[0].field] = pd.Series(linearFunc(self.xvalue,intercept,slope))
            lines_listy.data[lines_listy.data_lines[0].field] = pd.Series(y_data - data)
        
        elif "power_residual" in lines_listy.line_type:
            k_val, exponent, intercept = self.do_power_fit()
            data = lines_listy.data[lines_listy.data_lines[0].field]
            lines_listy.data[lines_listy.data_lines[0].field] = pd.Series(power_func(self.xvalue,k_val,exponent,intercept))

        elif "log10_residual" in lines_listy.line_type:
            
            k_val, exponent, intercept = self.do_power_fit()
            ydata = np.log10(lines_listy.data[lines_listy.data_lines[0].field] )
            lines_listy.data[lines_listy.data_lines[0].field] = pd.Series(np.log10((self.xvalue,a,b)))

        return
         
    def do_power_fit(self):
        #self.params, self.covariance = curve_fit(self.linearFunc, self.xvalue, self.yvalue)                          
        # This line calls the curve_fit function. It returns two arrays.
        # 'a_fit' contains the best fit parameters and 'cov' contains
        # the covariance matrix.
        if self.xvalue.size == 0 or  self.yvalue.size == 0 :
            print("TrendLine: no data")
            return
        x = np.array(self.xvalue)
        y = np.array(self.yvalue)
       # ret = self.quadratic_model(self.xvalue,self.yvalue)
        popt,cov=curve_fit(power_func,x,y)
        # The next four lines define variables for the slope, intercept, and
        # there associated uncertainties d_slope and d_inter. The uncertainties
        # are computed from elements of the covariance matrix.
        K_value = popt[0]
        exponent = popt[1]
        intercept = popt[2]
        y_predicted = power_func(self.xvalue, *popt)
        ss_total = np.sum((self.yvalue - np.mean(self.yvalue))**2)
        ss_residual = np.sum((self.yvalue - y_predicted)**2)
        r_squared = 1 - (ss_residual / ss_total)
       
        self.lines_listy['K'] = K_value
        self.lines_listy['exponent'] = exponent
        #self.lines_list[line_num]['covarance'] = cov
        self.lines_listy['r_squared'] = r_squared
        return K_value,exponent,intercept

  


    def do_log10_fit(self):
        #self.params, self.covariance = curve_fit(self.linearFunc, self.xvalue, self.yvalue)                          
            # This line calls the curve_fit function. It returns two arrays.
        # 'a_fit' contains the best fit parameters and 'cov' contains
        # the covariance matrix.
        if self.xvalue.size == 0 or  self.yvalue.size == 0 :
            print("TrendLine: no data")
            return
        x = np.array(self.xvalue)
        y = np.array(self.yvalue)
        initialParameters = np.array([0.0000010, 0.0000010, 0.0000010])
        p0_guess = [3.6E-1, 7] 
        #popt = np.polyfit(x, np.log10(y), 1)
        
        cov =[1,1]
        popt,cov=curve_fit(log10_func,x,y)
        #z = np.polyfit(x, np.log10(y), 1)
        self.params = popt
        self.covariance = cov
        # The next four lines define variables for the slope, intercept, and
        # there associated uncertainties d_slope and d_inter. The uncertainties
        # are computed from elements of the covariance matrix.
        a = popt[0]
        b = popt[1]
        self.intersect = np.sqrt(cov[0][0])
        self.slope = np.sqrt(cov[1][1])
        y_predicted = log10_func(self.xvalue, a,b)
        ss_total = np.sum((self.yvalue - np.mean(self.yvalue))**2)
        ss_residual = np.sum((self.yvalue - y_predicted)**2)
        r_squared = 1 - (ss_residual / ss_total)
       
        self.lines_listy['a'] = a
        self.lines_listy['b'] = b
        self.lines_listy['covarance'] = self.covariance
        self.lines_listy['r_squared'] = r_squared

        return a,b

    def do_poly_fit(self):
        #self.params, self.covariance = curve_fit(self.linearFunc, self.xvalue, self.yvalue)                          
            # This line calls the curve_fit function. It returns two arrays.
        # 'a_fit' contains the best fit parameters and 'cov' contains
        # the covariance matrix.
        if self.xvalue.size == 0 or  self.yvalue.size == 0 :
            print("TrendLine: no data")
            return
        x = np.array(self.xvalue)
        y = np.array(self.yvalue)
       # ret = self.quadratic_model(self.xvalue,self.yvalue)
        popt,cov=curve_fit(quadratic_model,x,y)
        self.params = popt
        self.covariance = cov
        # The next four lines define variables for the slope, intercept, and
        # there associated uncertainties d_slope and d_inter. The uncertainties
        # are computed from elements of the covariance matrix.
        a = popt[0]
        b = popt[1]
        c = popt[2]
        self.intersect = np.sqrt(cov[0][0])
        self.slope = np.sqrt(cov[1][1])
        y_predicted = quadratic_model(self.xvalue, *popt)
        ss_total = np.sum((self.yvalue - np.mean(self.yvalue))**2)
        ss_residual = np.sum((self.yvalue - y_predicted)**2)
        r_squared = 1 - (ss_residual / ss_total)
       
        self.lines_listy['K'] = a
        self.lines_listy['b'] = b
        self.lines_listy['c'] = c
        self.lines_listy['isec'] = self.intersect
        self.lines_listy['covarance'] = self.covariance
        self.lines_listy['r_squared'] = r_squared

        return a,b,c
  
    
    def do_linear_fit_regress(self):
        #self.params, self.covariance = curve_fit(self.linearFunc, self.xvalue, self.yvalue)                          
            # This line calls the curve_fit function. It returns two arrays.
        # 'a_fit' contains the best fit parameters and 'cov' contains
        # the covariance matrix.
        if self.xvalue.size == 0 or  self.yvalue.size == 0 :
            print("TrendLine: no data")
            return
        fit1 = linregress(self.xvalue, self.yvalue)
        # The next four lines define variables for the slope, intercept, and
        # there associated uncertainties d_slope and d_inter. The uncertainties
        # are computed from elements of the covariance matrix.
        self.intersect = fit1.intercept
        self.slope = fit1.slope
        y_predicted =  fit1.intercept + fit1.slope * self.xvalue
        ss_total = np.sum((self.yvalue - np.mean(self.yvalue))**2)
        ss_residual = np.sum((self.yvalue - y_predicted)**2)
        r_squared = 1 - (ss_residual / ss_total)
       
        self.lines_listy['K'] = self.slope
        self.lines_listy['isec'] = self.intersect
        self.lines_listy['covarance'] = self.covariance
        self.lines_listy['r_squared'] = r_squared

        return self.intersect,self.slope
  

    

    def do_linear_fit(self,fit_func):
        #self.params, self.covariance = curve_fit(self.linearFunc, self.xvalue, self.yvalue)                          
            # This line calls the curve_fit function. It returns two arrays.
        # 'a_fit' contains the best fit parameters and 'cov' contains
        # the covariance matrix.
        if self.xvalue.size == 0 or  self.yvalue.size == 0 :
            print("TrendLine: no data")
            return
        popt,cov=curve_fit(fit_func,self.xvalue,self.yvalue)
        self.params = popt
        self.covariance = cov
        # The next four lines define variables for the slope, intercept, and
        # there associated uncertainties d_slope and d_inter. The uncertainties
        # are computed from elements of the covariance matrix.
       
        self.intersect = popt[0]
        self.slope = popt[1]
        y_predicted = fit_func(self.xvalue, *popt)
        ss_total = np.sum((self.yvalue - np.mean(self.yvalue))**2)
        ss_residual = np.sum((self.yvalue - y_predicted)**2)
        r_squared = 1 - (ss_residual / ss_total)
       
        self.lines_listy['K'] = self.slope
        self.lines_listy['isec'] = self.intersect
        self.lines_listy['covarance'] = self.covariance
        self.lines_listy['r_squared'] = r_squared

        return self.intersect,self.slope
  

    def calculate_r_squared(y_true, y_pred):
        # Total sum of squares (TSS)
        ss_total = np.sum((y_true - np.mean(y_true)) ** 2)

        # Residual sum of squares (RSS)
        ss_residual = np.sum((y_true - y_pred) ** 2)

        # Calculate R-squared
        r_squared = 1 - (ss_residual / ss_total)
        return r_squared

   

   