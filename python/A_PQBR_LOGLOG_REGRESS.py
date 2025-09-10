#!/usr/bin/env python3
"""
Log–log regression of total time vs. particle count.

CSV should contain:
  N   : number of particles (int)
  gms : graphics time per frame (ms or s)
  cms : compute time per frame (ms or s)

Usage:
  python loglog_regression.py CHATGP_Data.csv
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

from ValuesDataBase import *
from AttrDictFields import *

data_list = []

from PlotterClass import *

class A_PQBR_LOGLOG_REGRESS(PlotterClass):
    
        
    def __init__(self,itemcfg,base):
        super().__init__(itemcfg,base)
        self.df = None
    
    def run(self):
      
      
      if not os.path.exists(self.itemcfg.input_data_file):
          raise FileNotFoundError(f"CSV not found: {self.itemcfg.input_data_file}")

      # Load data
      self.df = pd.read_csv(self.itemcfg.input_data_file)

      # Ensure required columns exist
      required = {"loadedp", "gms", "cms"}
      missing = required - set(self.df.columns)
      if missing:
          raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

      # Throughput (million particles per second, Mpps)
      self.df["graphics_time"] = (self.df["loadedp"] / self.df["gms"]) / 1e6
      self.df["compute_time"]  = (self.df["loadedp"] / self.df["cms"]) / 1e6
      gms = np.array(self.df["gms"]).astype(float)
      cms = np.array(self.df["cms"]).astype(float)
      both = np.add(gms,cms)
      self.df["total_time"]  = (self.df["loadedp"] / both)/ 1e6
      # Adjust units if times are in ms (uncomment if needed)
      # self.df["gms"] = self.df["gms"] / 1000.0
      # self.df["cms"] = self.df["cms"] / 1000.0

      raw_n = np.array(self.df["loadedp"])
      raw_t = np.array(self.df["total_time"])
      self.start_num0,self.end_num0 = self.get_line_slices(0,len(raw_n))
      self.start_num1,self.end_num1 = self.get_line_slices(1,len(raw_n))
      logN = np.log10(self.df["loadedp"])
      logT = np.log10(self.df["total_time"])
      print(f"Starting at {raw_n[self.start_num0]} value of:{raw_t[0]}")

      self.do_plot('TotalTime',logN,logT)
      self.itemcfg['input_images'] = self.include
      

    def do_plot(self,name,logN,logT):
      # Log–log regression
      
      slope, intercept, r_value, p_value, std_err = linregress(logN[self.start_num0:], logT[self.start_num0:])
      print(f"Slope (complexity exponent): {slope:.3f}")
      print(f"Intercept (log10 scale): {intercept:.3f}")
      print(f"R^2: {r_value**2:.4f}")

      # Regression line
      fit_line = intercept + slope * logN[self.start_num1:]

      # Plot
      plt.figure(figsize=(8,6))
      plt.loglog(self.df["loadedp"][self.start_num0:], self.df["total_time"][self.start_num0:], 'o', label="Measured total time")
      plt.loglog(self.df["loadedp"][self.start_num1:], 10**fit_line, '-', label=f"Fit: slope={slope:.3f}")
      plt.xlabel("Number of particles (N)")
      plt.ylabel("Total time (s)")
      plt.title("Log–Log Regression of Total Time vs. N")
      plt.legend()
      plt.grid(True, which="both", ls="--")
      plt.tight_layout()
      filename = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}{name}.png"
      plt.savefig(filename, dpi=300)
      self.include.append(filename)
      plt.close()
      prefix_name = self.itemcfg.name.replace('_','')
      vdb = ValuesDataBase(self.bobj)
      vals_list = AttrDictFields()


