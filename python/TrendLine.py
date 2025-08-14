import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

def quadratic_model(x, a, b, c):
    return a * x**2 + b * x + c

def quadratic_funct(x, a, b, c):
    return a * x**2 + b * x + c

def power_func(x, a, b):
    return a * (x**b)


class TrendLine():

    fields_list = None
    def __init__(self):
        pass        
    
    def add_trend_line(self,fields_list):
        self.fields_list = fields_list 
        for ii in range(1,len(self.fields_list)):
            try:
                print(self.fields_list[ii].line_type)
            except BaseException as e:
                print(e)
            if "linear_trend" in self.fields_list[ii].line_type:
                self.xvalue = self.fields_list[ii].data[self.fields_list[0]['field']]
                self.yvalue = self.fields_list[ii].data[self.fields_list[ii]['field']]
                intercept, slope = self.do_fit(ii,self.linearFunc)
                #print(self.fields_list[ii]['field'] )
                data = self.linearFunc(self.xvalue,intercept,slope).tolist()
                self.fields_list[ii].data[self.fields_list[ii]['field']] = pd.Series(self.linearFunc(self.xvalue,intercept,slope))
                
            
            if "quadratic_trend" in self.fields_list[ii].line_type:
                self.xvalue = self.fields_list[ii].data[self.fields_list[0]['field']]
                self.yvalue = self.fields_list[ii].data[self.fields_list[ii]['field']]
                a,b,c = self.do_poly_fit(ii)
                #print(self.fields_list[ii]['field'] )
                data = quadratic_model(self.xvalue,a,b,c).tolist()
                self.fields_list[ii].data[self.fields_list[ii]['field']] = pd.Series(quadratic_model(self.xvalue,a,b,c))
            
            if "power_trend" in self.fields_list[ii].line_type:
                self.xvalue = self.fields_list[ii].data[self.fields_list[0]['field']]
                self.yvalue = self.fields_list[ii].data[self.fields_list[ii]['field']]
                k_val, exponent = self.do_power_fit(ii)
                #print(self.fields_list[ii]['field'] )
                data = power_func(self.xvalue,intercept,slope).tolist()
                self.fields_list[ii].data[self.fields_list[ii]['field']] = pd.Series(power_func(self.xvalue,k_val,exponent))
            
    def do_power_fit(self,line_num):
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
        y_predicted = power_func(self.xvalue, *popt)
        ss_total = np.sum((self.yvalue - np.mean(self.yvalue))**2)
        ss_residual = np.sum((self.yvalue - y_predicted)**2)
        r_squared = 1 - (ss_residual / ss_total)
       
        self.fields_list[line_num]['K'] = K_value
        self.fields_list[line_num]['exponent'] = exponent
        #self.fields_list[line_num]['covarance'] = cov
        self.fields_list[line_num]['r_squared'] = r_squared
        return K_value,exponent

  
    

    def do_poly_fit(self,line_num):
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
       
        self.fields_list[line_num]['K'] = a
        self.fields_list[line_num]['b'] = b
        self.fields_list[line_num]['c'] = c
        self.fields_list[line_num]['isec'] = self.intersect
        self.fields_list[line_num]['covarance'] = self.covariance
        self.fields_list[line_num]['r_squared'] = r_squared

        return a,b,c
  
    
    def exponential_model(self, x, a, b):
        return a * np.exp(b*x)
    
    
    def do_fit(self,line_num,fit_func):
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
        inter = popt[0]
        slope = popt[1]
        self.intersect = np.sqrt(cov[0][0])
        self.slope = np.sqrt(cov[1][1])
        y_predicted = fit_func(self.xvalue, *popt)
        ss_total = np.sum((self.yvalue - np.mean(self.yvalue))**2)
        ss_residual = np.sum((self.yvalue - y_predicted)**2)
        r_squared = 1 - (ss_residual / ss_total)
       
        self.fields_list[line_num]['K'] = self.slope
        self.fields_list[line_num]['isec'] = self.intersect
        self.fields_list[line_num]['covarance'] = self.covariance
        self.fields_list[line_num]['r_squared'] = r_squared

        return inter,slope
  

    def calculate_r_squared(y_true, y_pred):
        # Total sum of squares (TSS)
        ss_total = np.sum((y_true - np.mean(y_true)) ** 2)

        # Residual sum of squares (RSS)
        ss_residual = np.sum((y_true - y_pred) ** 2)

        # Calculate R-squared
        r_squared = 1 - (ss_residual / ss_total)
        return r_squared

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


   