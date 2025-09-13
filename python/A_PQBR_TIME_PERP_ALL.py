import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import csv
import math
from ValuesDataBase import *
from AttrDictFields import *
from PlotterClass import *

class A_PQBR_TIME_PERP_ALL(PlotterClass):
    
  def run(self):

    
    if not os.path.exists(self.itemcfg.input_data_file):
        raise FileNotFoundError(f"CSV not found: {self.itemcfg.input_data_file}")

    # Load data
    df = pd.read_csv(self.itemcfg.input_data_file, skiprows=range(1,28))

    # Ensure required columns exist
    required = {"loadedp", "gms", "cms"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

    # Add total stage time
    df["total"] = df["gms"] + df["cms"]

    # Compute time per particle in ns
    df["gms_tpp_ns"]   = df["gms"]   / df["loadedp"] * 1e9
    df["cms_tpp_ns"]   = df["cms"]   / df["loadedp"] * 1e9
    df["total_tpp_ns"] = df["total"] / df["loadedp"] * 1e9

    # --- Stabilization Analysis ---
    # We'll use the last k% of data to estimate "plateau" values
    def stabilization_value(series, frac=0.2):
        tail = series.iloc[int(len(series)*(1-frac)):]
        return tail.mean(), tail.std()

    stabilization = {}
    for key, label in zip(
        ["gms_tpp_ns", "cms_tpp_ns", "total_tpp_ns"],
        ["Graphics", "Compute", "Total"]
    ):
        mean_val, std_val = stabilization_value(df[key], frac=0.2)
        stabilization[label] = (mean_val, std_val)
        self.vals_list[f"{self.prefix_name}{label}stabilzes"] = f"{mean_val:.2f}"
        self.vals_list[f"{self.prefix_name}{label}stdval"] = f"{std_val:.2f}"
        print(f"{label} stabilization: {mean_val:.2f} ± {std_val:.2f} ns/particle")
    self.vals_list[f"{self.prefix_name}startval"] = f"{int(float(df['loadedp'][0]))}"
    plt,fig,ax = self.__new_figure__()
    # --- Plot ---
    fdct = self.__get_line_format_dict__(1)
    plt.plot(df["loadedp"], df["gms_tpp_ns"],**fdct)
    fdct = self.__get_line_format_dict__(2)
    plt.plot(df["loadedp"], df["cms_tpp_ns"],**fdct)
    fdct = self.__get_line_format_dict__(3)
    plt.plot(df["loadedp"], df["total_tpp_ns"],**fdct)

    # Add stabilization reference lines
    for label, (mean_val, std_val) in stabilization.items():
        plt.hlines(mean_val, xmin=df["loadedp"].min(), xmax=df["loadedp"].max(),
                colors="gray", linestyles="--", alpha=0.7,
                label=f"{label} plateau ≈ {mean_val:.2f} ns")

    
    #plt.xlabel("Particles (N, log scale)")
    #plt.ylabel("Time per particle (ns, log scale)")
   
    leg_list = self.__do_legend__()
    plt.legend(leg_list)
    self.__do_commands__(plt,self.fig,self.ax)
    plt.tight_layout()
    #plt.xscale("log")
    #plt.yscale("log")
    filename = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}.png"
    plt.savefig(filename, dpi=self.itemcfg.dpi)
    plt.close()

    self.include.append(filename)
    self.__write_vals__()


