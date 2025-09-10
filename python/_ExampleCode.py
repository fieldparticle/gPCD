#!/usr/bin/env python3
"""
One-page performance analysis of particle collision detection.

Inputs:
  CHATGP_Data.csv with columns:
    N   : number of particles
    gms : graphics time (s or ms)
    cms : compute time (s or ms)

Outputs:
  - analysis_page.pdf : single-page report with plots and metrics
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy.stats import linregress
from scipy.optimize import curve_fit

# === CONFIG ===
CSV = "test_data.csv"
times_in_ms = True   # set True if gms/cms are in ms
N0 = 10_000          # saturation threshold

# === Load Data ===
df = pd.read_csv(CSV)
if times_in_ms:
    df["gms"] /= 1000.0
    df["cms"] /= 1000.0
df["T"] = df["gms"] + df["cms"]

# Derived metrics
df["graphics_throughput"] = (df["N"] / df["gms"]) / 1e6
df["compute_throughput"]  = (df["N"] / df["cms"]) / 1e6
df["total_throughput"]    = (df["N"] / df["T"]) / 1e6
df["graphics_tpp"] = (df["gms"] / df["N"]) * 1e9
df["compute_tpp"]  = (df["cms"] / df["N"]) * 1e9
df["total_tpp"]    = (df["T"] / df["N"]) * 1e9

# === Log–log regression ===
logN = np.log10(df["N"])
logT = np.log10(df["T"])

def fit_range(mask):
    x, y = logN[mask], logT[mask]
    slope, intercept, r, p, se = linregress(x, y)
    return slope, intercept, r**2

# Full fit
b_all, a_all, r2_all = fit_range(np.ones(len(df), dtype=bool))
# Saturated fit
mask_sat = df["N"] >= N0
b_sat, a_sat, r2_sat = fit_range(mask_sat)

# Quadratic fit for curvature (t1 vs k)
df["t1"] = df["T"] / df["N"]
def quadratic(k, a, b, c):
    return a + b*k + c*(k**2)
params_q, _ = curve_fit(quadratic, df["N"], df["t1"])
a_q, b_q, c_q = params_q
curvature_upper = 2*c_q

# === Create single-page PDF ===
with PdfPages("analysis_page.pdf") as pdf:
    fig, axs = plt.subplots(2, 2, figsize=(11, 8.5))

    # (1) Throughput plot
    axs[0,0].loglog(df["N"], df["graphics_throughput"], 'o-', label="Graphics")
    axs[0,0].loglog(df["N"], df["compute_throughput"], 's-', label="Compute")
    axs[0,0].loglog(df["N"], df["total_throughput"], '^-', label="Total")
    axs[0,0].set_xlabel("Particles (N)")
    axs[0,0].set_ylabel("Throughput (Mpps)")
    axs[0,0].set_title("Throughput vs N")
    axs[0,0].legend()
    axs[0,0].grid(True, which="both", ls="--")

    # (2) Time per particle plot
    axs[0,1].loglog(df["N"], df["graphics_tpp"], 'o-', label="Graphics")
    axs[0,1].loglog(df["N"], df["compute_tpp"], 's-', label="Compute")
    axs[0,1].loglog(df["N"], df["total_tpp"], '^-', label="Total")
    axs[0,1].set_xlabel("Particles (N)")
    axs[0,1].set_ylabel("Time per particle (ns)")
    axs[0,1].set_title("Time per particle vs N")
    axs[0,1].legend()
    axs[0,1].grid(True, which="both", ls="--")

    # (3) Log–log regression
    axs[1,0].loglog(df["N"], df["T"], 'o', label="Measured")
    xx = np.linspace(logN.min(), logN.max(), 200)
    axs[1,0].loglog(10**xx, 10**(a_all+b_all*xx), '-', label=f"Full fit b={b_all:.2f}")
    axs[1,0].loglog(10**xx, 10**(a_sat+b_sat*xx), '--', label=f"Saturated fit b={b_sat:.2f}")
    axs[1,0].axvline(N0, color='gray', ls=':', label=f"N0={N0}")
    axs[1,0].set_xlabel("Particles (N)")
    axs[1,0].set_ylabel("Total time (s)")
    axs[1,0].set_title("Log–log regression fits")
    axs[1,0].legend()
    axs[1,0].grid(True, which="both", ls="--")

    # (4) Text summary panel
    axs[1,1].axis("off")
    text = (
        f"=== Performance Summary ===\n"
        f"Peak N = {df['N'].max():,}\n"
        f"  Total time = {df['T'].iloc[-1]:.2f} s\n"
        f"  Total throughput = {df['total_throughput'].iloc[-1]:.1f} Mpps\n"
        f"  Time per particle = {df['total_tpp'].iloc[-1]:.2f} ns\n\n"
        f"Log–log fits:\n"
        f"  Full slope b = {b_all:.3f}, R²={r2_all:.4f}\n"
        f"  Saturated slope b = {b_sat:.3f}, R²={r2_sat:.4f}\n\n"
        f"Quadratic t1(k) fit:\n"
        f"  a={a_q:.3e}, b={b_q:.3e}, c={c_q:.3e}\n"
        f"  Upper curvature bound 2c = {curvature_upper:.3e} s/particle²"
    )
    axs[1,1].text(0.0, 1.0, text, va="top", family="monospace", fontsize=9)

    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

print("Saved single-page report: analysis_page.pdf")
