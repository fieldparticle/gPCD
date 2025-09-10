#!/usr/bin/env python3
"""
One-stop analysis of particle collision performance.

CSV should contain:
  N   : number of particles (int)
  gms : graphics time per frame (ms or s)
  cms : compute time per frame (ms or s)

Usage:
  python analyze_performance.py CHATGP_Data.csv

Outputs:
  - loglog_fit.png : log–log regression plot of total time vs N
  - Printed summary of regression slope, throughput, and time-per-particle
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

def main(csv_path: str):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    specific_rows = [0]
    other = list(range(10, 63))
    for ii in other:
        specific_rows.append(ii)

    df = pd.read_csv(csv_path,skiprows = lambda x: x not in specific_rows)

    # ---- Adjust units if needed ----
    # If gms/cms are in ms, convert to seconds:
    # df["gms"] = df["gms"] / 1000.0
    # df["cms"] = df["cms"] / 1000.0

    # Total time per frame (s)
    df["total_time"] = df["gms"] + df["cms"]

    # Throughput (Mpps)
    df["graphics_throughput_mpps"] = (df["N"] / df["gms"]) / 1e6
    df["compute_throughput_mpps"]  = (df["N"] / df["cms"]) / 1e6
    df["total_throughput_mpps"]    = (df["N"] / df["total_time"]) / 1e6

    # Time per particle (ns)
    df["graphics_tpp_ns"] = (df["gms"] / df["N"]) * 1e9
    df["compute_tpp_ns"]  = (df["cms"] / df["N"]) * 1e9
    df["total_tpp_ns"]    = (df["total_time"] / df["N"]) * 1e9

    # Log–log regression of total time
    logN = np.log10(df["N"])
    logT = np.log10(df["total_time"])
    slope, intercept, r_value, p_value, std_err = linregress(logN, logT)

    # Print summary
    print("\n=== Performance Summary ===")
    print(f"Slope (complexity exponent): {slope:.3f}")
    print(f"Intercept (log10 scale): {intercept:.3f}")
    print(f"R^2: {r_value**2:.4f}\n")

    # Show last row (largest N) as peak performance reference
    peak = df.iloc[df["N"].idxmax()]
    print(f"At N = {int(peak['N']):,} particles:")
    print(f"  Graphics throughput : {peak['graphics_throughput_mpps']:.1f} Mpps "
          f"({peak['graphics_tpp_ns']:.2f} ns/particle)")
    print(f"  Compute throughput  : {peak['compute_throughput_mpps']:.1f} Mpps "
          f"({peak['compute_tpp_ns']:.2f} ns/particle)")
    print(f"  Total throughput    : {peak['total_throughput_mpps']:.1f} Mpps "
          f"({peak['total_tpp_ns']:.2f} ns/particle)")

    # Regression line
    fit_line = intercept + slope * logN

    # Plot
    plt.figure(figsize=(8,6))
    plt.loglog(df["N"], df["total_time"], 'o', label="Measured total time")
    plt.loglog(df["N"], 10**fit_line, '-', label=f"Fit slope={slope:.3f}")
    plt.xlabel("Number of particles (N)")
    plt.ylabel("Total time (s)")
    plt.title("Log–Log Regression of Total Time vs N")
    plt.legend()
    plt.grid(True, which="both", ls="--", alpha=0.7)
    plt.tight_layout()

    out_path = "loglog_fit.png"
    plt.savefig(out_path, dpi=300)
    print(f"\nSaved plot: {out_path}")

if __name__ == "__main__":
    
    main('test_data.csv')
