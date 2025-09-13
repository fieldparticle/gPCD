#!/usr/bin/env python3
"""
Curvature-bound visualization for Graphics, Compute, and Total.
Generates both linear and log–log plots using CHATGP_Data.csv.
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

def fit_and_plot(N, t1_s, t1_ns, name, fname_prefix):
    # Fit quadratic on seconds
    popt, _ = curve_fit(quadratic, N, t1_s)
    a, b, c = popt
    curvature = 2*c  # s/particle^2

    # Smooth x
    xx = np.linspace(N.min(), N.max(), 300)
    t1_fit_s  = quadratic(xx, *popt)
    t1_fit_ns = t1_fit_s * 1e9

    # Curvature bound region (ns)
    mid_k = 0.5 * (N.min() + N.max())
    delta_slope = curvature * (xx - mid_k)
    curvature_band_s  = np.abs(delta_slope) * (xx - mid_k) * 0.5
    curvature_band_ns = curvature_band_s * 1e9

    upper_ns = t1_fit_ns + curvature_band_ns
    lower_ns = t1_fit_ns - curvature_band_ns

    # --- Linear plot ---
    plt.figure(figsize=(7,5))
    plt.scatter(N, t1_ns, color="black", s=18, label="Measured t1")
    plt.plot(xx, t1_fit_ns, color="C0", label="Quadratic fit")
    plt.fill_between(xx, lower_ns, upper_ns, color="C0", alpha=0.2,
                     label="Curvature bound region")
    plt.xlabel("Particles (N)")
    plt.ylabel("Time per particle (ns)")
    plt.title(f"{name}: Quadratic fit (Linear axes)\n2c={curvature:.2e} s/part²")
    plt.grid(True, ls="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{fname_prefix}_linear.png", dpi=300)

    # --- Log–log plot ---
    plt.figure(figsize=(7,5))
    plt.scatter(N, t1_ns, color="black", s=18, label="Measured t1")
    plt.plot(xx, t1_fit_ns, color="C0", label="Quadratic fit")
    plt.fill_between(xx, lower_ns, upper_ns, color="C0", alpha=0.2,
                     label="Curvature bound region")
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Particles (N, log scale)")
    plt.ylabel("Time per particle (ns, log scale)")
    plt.title(f"{name}: Quadratic fit (Log–log axes)\n2c={curvature:.2e} s/part²")
    plt.grid(True, which="both", ls="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{fname_prefix}_loglog.png", dpi=300)

    # Console summary
    print(f"{name}: a={a:.3e}, b={b:.3e}, c={c:.3e}, curvature=2c={curvature:.3e} s/part²")
    print(f"Saved {fname_prefix}_linear.png and {fname_prefix}_loglog.png\n")

# Run for Graphics, Compute, Total
fit_and_plot(df["N"].values, df["gms_t1_s"].values,   df["gms_t1_ns"].values,   "Graphics", "curvature_graphics")
fit_and_plot(df["N"].values, df["cms_t1_s"].values,   df["cms_t1_ns"].values,   "Compute",  "curvature_compute")
fit_and_plot(df["N"].values, df["total_t1_s"].values, df["total_t1_ns"].values, "Total",    "curvature_total")
