#!/usr/bin/env python3
"""
Make graphics_vs_compute_throughput.png from a CSV with columns:
  N   : number of particles (int)
  gms : graphics time per frame (seconds)  # if in ms, see note below
  cms : compute time per frame (seconds)   # if in ms, see note below

Usage:
  python make_throughput_plot.py CHATGP_Data.csv

Output:
  graphics_vs_compute_throughput.png
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as mplt
import numpy as np
import csv
import math
from ValuesDataBase import *
from AttrDictFields import *
from PlotterClass import *

class A_PQBR_THROUGH_PUT_ALL(PlotterClass):
    
  def run(self):

      df = self.__open_data_file__()
      # Ensure required columns exist
      required = {"loadedp", "gms", "cms"}
      missing = required - set(df.columns)
      if missing:
          raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

      # ---- If your times are in MILLISECONDS, uncomment the next two lines ----
      # df["gms"] = df["gms"] / 1000.0
      # df["cms"] = df["cms"] / 1000.0

      # Throughput (million particles per second, Mpps)
      df["graphics_throughput_mpps"] = (df["loadedp"] / df["gms"]) / 1e6
      df["compute_throughput_mpps"]  = (df["loadedp"] / df["cms"]) / 1e6
      gms = np.array(df["gms"]).astype(float)
      cms = np.array(df["cms"]).astype(float)
      both = np.add(gms,cms)
      df["total_throughput_mpps"]  = (df["loadedp"] / both)/ 1e6

      # === Plot ===
      ##------------------------------------------
      plt,fig,ax = self.__new_figure__()
      ##-------------------------------------------
      fdct = self.__get_line_format_dict__(1)
      plt.loglog(df["loadedp"], df["graphics_throughput_mpps"],**fdct)
      fdct = self.__get_line_format_dict__(2)
      plt.loglog(df["loadedp"], df["compute_throughput_mpps"],**fdct)
      fdct = self.__get_line_format_dict__(3)
      plt.loglog(df["loadedp"], df["total_throughput_mpps"],**fdct)
      fdct = self.__get_line_format_dict__(4)
      plt.axvline(x=2245632,**fdct)
      fdct = self.__get_line_format_dict__(5)
      plt.axvline(x=100000,**fdct)
      self.__do_commands__(plt,fig,ax)
      leg_list = self.__do_legend__()
      plt.legend(leg_list)
      plt.tight_layout()
      #plt.tight_layout()
      filename = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}.png"
      self.__clean_files__(filename)
      plt.pause(0.01)
      plt.savefig(filename, dpi=self.itemcfg.dpi)
      plt.close()
      #self.__write_vals__()
      self.include.append(filename)

      prefix_name = self.itemcfg.name.replace('_','')
      vdb = ValuesDataBase(self.bobj)
      vals_list = AttrDictFields()
      name = "tot"
      