#!/usr/bin/env python3
"""
Residual + homoscedasticity analysis for Graphics, Compute, and Total
using CHATGP_Data.csv, with residuals plotted in ns/particle.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan

# --- Load dataset ---
df = pd.read_csv("CHATGP_Data.csv")

# Normalize column name
if "loadedp" in df.columns:
    df = df.rename(columns={"loadedp": "N"})

# Add total stage time
df["total"] = df["gms"] + df["cms"]

# Time per particle in seconds + nanoseconds
df["gms_t1_s"]   = df["gms"]   / df["N"]
df["cms_t1_s"]   = df["cms"]   / df["N"]
df["total_t1_s"] = df["total"] / df["N"]

df["gms_t1_ns"]   = df["gms_t1_s"]   * 1e9
df["cms_t1_ns"]   = df["cms_t1_s"]   * 1e9
df["total_t1_ns"] = df["total_t1_s"] * 1e9

# Filter to N >= 98,304
df = df[df["N"] >= 98304].reset_index(drop=True)

# Quadratic model
def quadratic(N, a, b, c):
    return a + b*N + c*N**2

def analyze(N, t1_s, t1_ns, name, fname_prefix):
    # Fit quadratic on seconds
    popt, _ = curve_fit(quadratic, N, t1_s)
    a, b, c = popt
    
    # Compute residuals (s and ns)
    residuals_s  = t1_s - quadratic(N, *popt)
    residuals_ns = residuals_s * 1e9
    
    # --- Residual Plot (ns/particle) ---
    plt.figure(figsize=(7,5))
    plt.scatter(N, residuals_ns, color="black", s=18)
    plt.axhline(0, color="red", linestyle="--")
    plt.xscale("log")
    plt.xlabel("Particles N (log scale)")
    plt.ylabel("Residuals (ns/particle)")
    plt.title(f"{name}: Residuals of quadratic fit")
    plt.grid(True, ls="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(f"{fname_prefix}_residuals.png", dpi=300)
    
    # --- Breusch–Pagan Test ---
    X = sm.add_constant(N)
    bp_test = het_breuschpagan(residuals_s, X)
    labels = ["LM stat", "LM p-value", "F-stat", "F p-value"]
    results = dict(zip(labels, bp_test))
    
    print(f"{name} Fit: a={a:.3e}, b={b:.3e}, c={c:.3e}")
    print(f"{name} Breusch–Pagan test results:")
    for k, v in results.items():
        print(f"  {k}: {v:.3e}")
    print(f"Saved {fname_prefix}_residuals.png\n")

# --- Run for Graphics, Compute, Total ---
analyze(df["N"].values, df["gms_t1_s"].values,   df["gms_t1_ns"].values,   "Graphics", "graphics")
analyze(df["N"].values, df["cms_t1_s"].values,   df["cms_t1_ns"].values,   "Compute",  "compute")
analyze(df["N"].values, df["total_t1_s"].values, df["total_t1_ns"].values, "Total",    "total")
