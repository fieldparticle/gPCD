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
N0 = 10_0000   
from PlotterClass import *

class A_PQBR_LOGLOG_REGRESS(PlotterClass):
    
        
    def __init__(self,itemcfg,base):
        super().__init__(itemcfg,base)
        self.df = None

    def fit_range(self,mask):
      x, y = self.logN[mask], self.logT[mask]
      slope, intercept, r, p, se = linregress(x, y)
      return slope, intercept, r**2
    
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


      # === Log–log regression ===
      self.logN = np.log10(self.df["loadedp"])
      self.logT = np.log10(self.df["gms"])
      self.do_plot('gms')  
      self.logN = np.log10(self.df["loadedp"])
      self.logT = np.log10(self.df["cms"])
      self.do_plot('cms')  
      self.logN = np.log10(self.df["loadedp"])
      self.df['tot'] = self.df["cms"]+self.df["gms"]
      self.logT = np.log10(self.df['tot'])
      self.do_plot('tot')  
      
      #elf.do_plot('TotalTime',self.logN,self.logT)
      self.itemcfg['input_images'] = self.include
      vdb = ValuesDataBase(self.bobj)
      vdb.write_values(self.vals_list)
      

    def do_plot(self,name):
      # Log–log regression
      # Full fit
      a_all, b_all, r2_all = self.fit_range(np.ones(len(self.df), dtype=bool))
      # Saturated fit
      mask_sat = self.df["loadedp"] >= N0
      a_sat, b_sat, r2_sat = self.fit_range(mask_sat)

      # Quadratic fit for curvature (t1 vs k)
      self.df["t1"] = self.df[name] / self.df["loadedp"]
      def quadratic(k, a, b, c):
          return a + b*k + c*(k**2)
      params_q, _ = curve_fit(quadratic, self.df["loadedp"], self.df["t1"])
      a_q, b_q, c_q = params_q
      curvature_upper = 2*c_q
      fig = plt.figure(figsize=(10, 6))
      axs = fig.gca()
       # (3) Log–log regression
      axs.loglog(self.df["loadedp"], self.df[name], 'o', label="Measured")
      xx = np.linspace(self.logN.min(), self.logN.max(), 200)
      axs.loglog(10**xx, 10**(a_all+b_all*xx), '-', label=f"Full fit b={b_all:.2f}")
      axs.loglog(10**xx, 10**(a_sat+b_sat*xx), '--', label=f"Saturated fit b={b_sat:.2f}")
      axs.axvline(N0, color='gray', ls=':', label=f"N0={N0}")
      axs.set_xlabel("Particles (N)")
      axs.set_ylabel("Total time (s)")
      #axs.set_title("Log–log regression fits")
      axs.legend()
      axs.grid(True, which="both", ls="--")
      prefix_name = self.itemcfg.name.replace('_','')
      filename = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}{name}.png"
      plt.savefig(filename, dpi=300)
      self.include.append(filename)
      plt.close()
      prefix_name = self.itemcfg.name.replace('_','')
      vdb = ValuesDataBase(self.bobj)
      vals_list = AttrDictFields()
      if 'tot' in name:
        self.vals_list[f"{prefix_name}{name}"] = 'Total'
      elif 'gms' in name:
        self.vals_list[f"{prefix_name}{name}"] = 'Graphics'
      elif 'cms' in name:
        self.vals_list[f"{prefix_name}{name}"] = 'Compute'
        
      self.vals_list[f"{prefix_name}{name}satval"] = f"{N0}"
      self.vals_list[f"{prefix_name}{name}ball"] = f"{b_all:0.2f}"
      self.vals_list[f"{prefix_name}{name}aall"] = f"{a_all:0.2f}"
      self.vals_list[f"{prefix_name}{name}rtwoall"] = f"{r2_all:0.2f}"
      self.vals_list[f"{prefix_name}{name}bsat"] = f"{b_sat:0.2f}"
      self.vals_list[f"{prefix_name}{name}asat"] = f"{a_sat:0.2f}"
      self.vals_list[f"{prefix_name}{name}rtwosat"] = f"{r2_all:0.2f}"
      self.vals_list[f"{prefix_name}{name}aq"] = f"{a_q:0.4e}"
      self.vals_list[f"{prefix_name}{name}bq"] = f"{b_q:0.4e}"
      self.vals_list[f"{prefix_name}{name}cq"] = f"{c_q:0.4e}"
      self.vals_list[f"{prefix_name}{name}curvatureupper"] = f"{curvature_upper:0.4e}"
      

