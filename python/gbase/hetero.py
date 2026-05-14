#!/usr/bin/env python3
"""
Residual + homoscedasticity analysis for Graphics, Compute, and Total
using CHATGP_Data.csv.
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

# Filter to N >= 98,304
df = df[df["N"] >= 98304].reset_index(drop=True)

# Quadratic model for fitting
def quadratic(N, a, b, c):
    return a + b*N + c*N**2

def analyze(N, T, name, fname_prefix):
    # Fit quadratic
    popt, _ = curve_fit(quadratic, N, T)
    a, b, c = popt
    
    # Compute residuals
    residuals = T - quadratic(N, *popt)
    
    # --- Residual Plot ---
    plt.figure(figsize=(7,5))
    plt.scatter(N, residuals, color="black", s=18)
    plt.axhline(0, color="red", linestyle="--")
    plt.xscale("log")
    plt.xlabel("Particles N (log scale)")
    plt.ylabel("Residuals (seconds)")
    plt.title(f"{name}: Residuals of quadratic fit")
    plt.grid(True, ls="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(f"{fname_prefix}_residuals.png", dpi=300)
    
    # --- Breusch–Pagan Test ---
    X = sm.add_constant(N)
    bp_test = het_breuschpagan(residuals, X)
    labels = ["LM stat", "LM p-value", "F-stat", "F p-value"]
    results = dict(zip(labels, bp_test))
    
    print(f"{name} Fit: a={a:.3e}, b={b:.3e}, c={c:.3e}")
    print(f"{name} Breusch–Pagan test results:")
    for k, v in results.items():
        print(f"  {k}: {v:.3e}")
    print(f"Saved {fname_prefix}_residuals.png\n")

# --- Run for Graphics, Compute, Total ---
analyze(df["N"].values, df["gms"].values,   "Graphics", "graphics")
analyze(df["N"].values, df["cms"].values,   "Compute",  "compute")
analyze(df["N"].values, df["total"].values, "Total",    "total")
