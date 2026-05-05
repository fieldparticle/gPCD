#!/usr/bin/env python3
"""
Quadratic fit with curvature analysis, including
upper bound on curvature and 'noticeable curvature' thresholds.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

# --- Load dataset ---
df = pd.read_csv("CHATGP_Data.csv")

# Normalize column name
if "loadedp" in df.columns:
    df = df.rename(columns={"loadedp": "N"})

# Add total stage
df["total"] = df["gms"] + df["cms"]

# --- Helper: compute noticeable curvature thresholds ---
def noticeable_curvature(a, b, c, eps=0.01, dT=1e-5):
    if c <= 0:
        return {"note": "c <= 0, no positive curvature"}
    N_lin   = eps * b / c
    N_slope = eps * b / (2*c)
    N_abs   = math.sqrt(dT / c)
    return {
        "N_lin": N_lin,
        "N_slope": N_slope,
        "N_abs": N_abs,
        "N_noticeable": max(N_lin, N_slope, N_abs)
    }

# --- Fit and report for each stage ---
stages = {
    "Graphics": df["gms"],
    "Compute": df["cms"],
    "Total": df["total"]
}

for name, timings in stages.items():
    N = df["N"].to_numpy()
    T = timings.to_numpy()
    coeffs = np.polyfit(N, T, deg=2)
    a, b, c = coeffs
    curvature = 2*c
    thresholds = noticeable_curvature(a, b, c, eps=0.01, dT=1e-5)

    print(f"\n--- {name} ---")
    print(f"Quadratic fit: T(N) = {a:.3e} + {b:.3e} N + {c:.3e} N^2 [s]")
    print(f"Upper bound on curvature (2c): {curvature:.3e} s/particle^2")
    print("Noticeable curvature thresholds:")
    print(f"  N_lin   (1% quadratic vs linear): {thresholds['N_lin']:.3e}")
    print(f"  N_slope (1% slope change):       {thresholds['N_slope']:.3e}")
    print(f"  N_abs   (deltaT=1e-5s):          {thresholds['N_abs']:.3e}")
    print(f"  ==> Conservative N_noticeable:   {thresholds['N_noticeable']:.3e}")

    # Optional: plot with fit
    k_space = np.linspace(N.min(), N.max(), 200)
    T_fit = a + b*k_space + c*k_space**2
    plt.figure(figsize=(8,6))
    plt.scatter(N, T, label="Measured")
    plt.plot(k_space, T_fit, label="Quadratic Fit", color="blue")
    plt.xlabel("Particles (N)")
    plt.ylabel("Time (s)")
    plt.title(f"{name}: Quadratic Fit with Curvature Analysis")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"curvature_{name.lower()}.png", dpi=300)
    plt.close()
