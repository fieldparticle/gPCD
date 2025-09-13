#!/usr/bin/env python3
"""
Curvature-bound visualization for Graphics, Compute, and Total
using raw timings (seconds) from CHATGP_Data.csv.
Plots only linear axes.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# --- Load dataset ---
df = pd.read_csv("CHATGP_Data.csv")

# Normalize column name
if "loadedp" in df.columns:
    df = df.rename(columns={"loadedp": "N"})

# Add total stage time (s)
df["total"] = df["gms"] + df["cms"]

# Filter to N >= 98,304
df = df[df["N"] >= 98304].reset_index(drop=True)

# Quadratic model
def quadratic(N, a, b, c):
    return a + b*N + c*N**2

def fit_and_plot(N, T, name, fname_prefix):
    # Fit quadratic
    popt, _ = curve_fit(quadratic, N, T)
    a, b, c = popt
    curvature = 2*c  # s/particle^2

    # Smooth curve
    xx = np.linspace(N.min(), N.max(), 300)
    T_fit = quadratic(xx, *popt)

    # Curvature band (seconds)
    mid_k = 0.5 * (N.min() + N.max())
    delta_slope = curvature * (xx - mid_k)
    curvature_band = np.abs(delta_slope) * (xx - mid_k) * 0.5
    upper = T_fit + curvature_band
    lower = T_fit - curvature_band

    # --- Linear plot ---
    plt.figure(figsize=(7,5))
    plt.scatter(N, T, color="black", s=18, label="Measured time")
    plt.plot(xx, T_fit, color="C0", label="Quadratic fit")
    plt.fill_between(xx, lower, upper, color="C0", alpha=0.2,
                     label="Curvature bound region")
    plt.xlabel("Particles (N)")
    plt.ylabel("Time (s)")
    plt.title(f"{name}: Quadratic fit (Linear axes)\n2c={curvature:.2e} s/part²")
    plt.grid(True, ls="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{fname_prefix}_linear.png", dpi=300)

    print(f"{name}: a={a:.3e}, b={b:.3e}, c={c:.3e}, curvature=2c={curvature:.3e} s/part²")
    print(f"Saved {fname_prefix}_linear.png\n")

# Run for Graphics, Compute, Total
fit_and_plot(df["N"].values, df["gms"].values,   "Graphics", "curvature_graphics")
fit_and_plot(df["N"].values, df["cms"].values,   "Compute",  "curvature_compute")
fit_and_plot(df["N"].values, df["total"].values, "Total",    "curvature_total")
