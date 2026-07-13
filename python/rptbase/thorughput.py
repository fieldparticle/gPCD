#!/usr/bin/env python3
"""
Log–log plot of time-per-particle (ns) vs number of particles
(Graphics, Compute, Total) from CHATGP_Data.csv
"""

import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("CHATGP_Data.csv")

# Normalize column name
if "loadedp" in df.columns:
    df = df.rename(columns={"loadedp": "N"})

# Add total stage time
df["total"] = df["gms"] + df["cms"]

# Time per particle (ns)
df["gms_tpp_ns"]   = df["gms"]   / df["N"] * 1e9
df["cms_tpp_ns"]   = df["cms"]   / df["N"] * 1e9
df["total_tpp_ns"] = df["total"] / df["N"] * 1e9

# --- Log–log Plot ---
plt.figure(figsize=(8,6))
plt.plot(df["N"], df["gms_tpp_ns"],   marker="o", linestyle="-", label="Graphics")
plt.plot(df["N"], df["cms_tpp_ns"],   marker="s", linestyle="-", label="Compute")
plt.plot(df["N"], df["total_tpp_ns"], marker="^", linestyle="-", label="Total")

plt.xscale("log")
plt.yscale("log")
plt.xlabel("Particles (N, log scale)")
plt.ylabel("Time per particle (ns, log scale)")
plt.title("Log–log Time per Particle (Graphics, Compute, Total)")
plt.grid(True, which="both", ls="--", alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig("time_per_particle_loglog.png", dpi=300)
plt.show()
