#!/usr/bin/env python3
"""
Log–log performance plot: time per particle/object vs number of entities.

Each data point needs:
  - name: label to show next to the point
  - N:    number of entities (particles/objects)
  - one of:
      time_s: total time for that frame/step in seconds
      fps:    frames per second (will be converted to time_s = 1/fps)
      ns_per_obj: time per object directly in nanoseconds (will be converted)

Output:
  performance_loglog_plot.png
"""

import math
import matplotlib.pyplot as plt

def s_per_obj_from_point(p):
    if "ns_per_obj" in p:
        return p["ns_per_obj"] * 1e-9
    if "time_s" in p and p["N"] is not None:
        return p["time_s"] / p["N"]
    if "fps" in p and p["N"] is not None:
        return (1.0 / p["fps"]) / p["N"]
    raise ValueError(f"Point missing required timing fields: {p}")

# -----------------------------
# Curated sample points (edit me)
# -----------------------------
points = [
    # name, N, timing (choose one of time_s, fps, ns_per_obj)
    {"name": "Govender 2015 (DEM polyhedra)", "N": 34_000_000, "time_s": 1.0},     # "<1 s" → ~1 s
    {"name": "Govender 2016 (Blaze-DEMGPU)",  "N": 4_000_000,  "fps": 20.0},       # 20 FPS
    {"name": "Latta 2004",                    "N": 1_000_000,  "fps": 30.0},       # ~30 FPS
    {"name": "Franklin 2017 (ParCube)",       "N": 10_000_000, "time_s": 0.33},    # 0.33 s
    {"name": "Liu 2010 (GPU SaP)",            "N": 1_000_000,  "fps": 20.0},       # ~20 FPS
    {"name": "Coming & Staadt 2006 (Kinetic SaP)", "N": 600_000, "fps": 15.0},     # ~15 FPS

    # Your system
    {"name": "Our System 2025",               "N": 11_088_896, "time_s": 0.08417}, # 84.17 ms
]

# Compute (N, time_per_obj_s) arrays
N_vals = []
tpo_vals = []
labels = []

for p in points:
    try:
        tpo = s_per_obj_from_point(p)
        N_vals.append(float(p["N"]))
        tpo_vals.append(float(tpo))
        labels.append(p["name"])
    except Exception as e:
        print("Skipping point due to error:", p, e)

# Plot (log–log)
plt.figure(figsize=(8, 6))
plt.loglog(N_vals, tpo_vals, "o", markersize=7)

# Connect points in an arbitrary order (optional)
plt.loglog(N_vals, tpo_vals, "-", linewidth=1, alpha=0.4)

# Annotate each point slightly offset to avoid overlap
for x, y, lbl in zip(N_vals, tpo_vals, labels):
    plt.text(x*1.08, y*1.10, lbl, fontsize=8)

plt.xlabel("Number of Entities (N)")
plt.ylabel("Time per Entity (seconds)")
plt.title("Collision/Interaction Performance: Time per Entity vs N (log–log)")
plt.grid(True, which="both", ls="--", alpha=0.6)
plt.tight_layout()

out_path = "performance_loglog_plot.png"
plt.savefig(out_path, dpi=300)
print(f"Saved: {out_path}")

# Optional: print a small table with ns/object for quick reference
print("\nSummary (ns per entity):")
for p, tpo in sorted(zip(points, tpo_vals), key=lambda x: x[0]["N"]):
    print(f"{p['name']:<35s} N={p['N']:>9,d}  {tpo*1e9:8.3f} ns")