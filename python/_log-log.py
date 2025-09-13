#!/usr/bin/env python3
"""
Log–log regression for graphics, compute, and total times.
Creates three plots with both full fit and saturated fit (N >= 10000).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# Load your data
df = pd.read_csv("CHATGP_Data.csv")

# --- If times are in ms, convert to seconds ---
# df["gms"] /= 1000.0
# df["cms"] /= 1000.0

# Total
df["total"] = df["gms"] + df["cms"]

def do_loglog_fit(x, y, label, Nmin=None):
    mask = np.ones_like(x, dtype=bool)
    if Nmin is not None:
        mask = x >= Nmin
    lx, ly = np.log10(x[mask]), np.log10(y[mask])
    slope, intercept, r, p, se = linregress(lx, ly)
    return slope, intercept, r**2

def make_plot(N, y, name, ylabel, filename):
    # Full fit
    s_all, i_all, r2_all = do_loglog_fit(N, y, name, Nmin=None)
    # Saturated fit (N >= 10000)
    s_sat, i_sat, r2_sat = do_loglog_fit(N, y, name, Nmin=10000)

    # Fit curves
    xx = np.logspace(np.log10(N.min()), np.log10(N.max()), 200)
    yy_all = 10**(i_all + s_all*np.log10(xx))
    yy_sat = 10**(i_sat + s_sat*np.log10(xx))

    # Plot
    plt.figure(figsize=(7,5))
    plt.loglog(N, y, 'o', label="Measured")
    plt.loglog(xx, yy_all, '-', label=f"Full fit b={s_all:.2f}, R²={r2_all:.4f}")
    plt.loglog(xx, yy_sat, '--', label=f"Saturated fit b={s_sat:.2f}, R²={r2_sat:.4f}")
    plt.axvline(10000, color='gray', ls=':', label="Saturation cutoff")
    plt.xlabel("Particles (N)")
    plt.ylabel(ylabel)
    plt.title(f"{name} log–log scaling")
    plt.grid(True, which="both", ls="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"Saved {filename}")

# Generate three plots
make_plot(df["N"].values, df["gms"].values,   "Graphics", "Graphics time (s)", "loglog_graphics.png")
make_plot(df["N"].values, df["cms"].values,   "Compute",  "Compute time (s)",  "loglog_compute.png")
make_plot(df["N"].values, df["total"].values, "Total",    "Total time (s)",    "loglog_total.png")
