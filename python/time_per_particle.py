#!/usr/bin/env python3
"""
Log–log plots of time-per-particle (ns) for Graphics, Compute, Total
with per-particle cost stabilization indicators.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Load dataset ---
df = pd.read_csv("CHATGP_Data.csv")

# Normalize column name
if "loadedp" in df.columns:
    df = df.rename(columns={"loadedp": "N"})

# Add total stage time
df["total"] = df["gms"] + df["cms"]

# Compute time per particle in ns
df["gms_tpp_ns"]   = df["gms"]   / df["N"] * 1e9
df["cms_tpp_ns"]   = df["cms"]   / df["N"] * 1e9
df["total_tpp_ns"] = df["total"] / df["N"] * 1e9

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
    print(f"{label} stabilization: {mean_val:.2f} ± {std_val:.2f} ns/particle")

# --- Plot ---
plt.figure(figsize=(9,7))

plt.plot(df["N"], df["gms_tpp_ns"],   marker="o", linestyle="-", label="Graphics")
plt.plot(df["N"], df["cms_tpp_ns"],   marker="s", linestyle="-", label="Compute")
plt.plot(df["N"], df["total_tpp_ns"], marker="^", linestyle="-", label="Total")

# Add stabilization reference lines
for label, (mean_val, std_val) in stabilization.items():
    plt.hlines(mean_val, xmin=df["N"].min(), xmax=df["N"].max(),
               colors="gray", linestyles="--", alpha=0.7,
               label=f"{label} plateau ≈ {mean_val:.2f} ns")

plt.xscale("log")
plt.yscale("log")
plt.xlabel("Particles (N, log scale)")
plt.ylabel("Time per particle (ns, log scale)")
plt.title("Log–log Time per Particle with Stabilization (Graphics, Compute, Total)")
plt.grid(True, which="both", ls="--", alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig("time_per_particle_stabilization.png", dpi=300)
plt.show()
