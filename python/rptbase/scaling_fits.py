#!/usr/bin/env python3
# analyze_scaling.py
import pandas as pd, numpy as np, matplotlib.pyplot as plt
from scipy.stats import linregress
from scipy.optimize import minimize_scalar

CSV = "test_data.csv"
N0 = 10_000  # saturation threshold you expect (≈ 1e4)

df = pd.read_csv(CSV)
# If gms/cms are ms, convert to seconds:
# df["gms"] /= 1000.0; df["cms"] /= 1000.0
df["T"] = df["gms"] + df["cms"]

logN = np.log10(df["N"].values.astype(float))
logT = np.log10(df["T"].values.astype(float))

def fit_range(mask):
    x, y = logN[mask], logT[mask]
    slope, intercept, r, p, se = linregress(x, y)
    return slope, intercept, r**2, x, y

# 1) Full fit
b_all, a_all, r2_all, x_all, y_all = fit_range(np.ones(len(df), dtype=bool))

# 2) Saturated fit (N >= N0)
mask_sat = df["N"].values >= N0
b_sat, a_sat, r2_sat, x_sat, y_sat = fit_range(mask_sat)

# 3) Piecewise (two-line) fit in log–log with unknown breakpoint
#    We try each possible breakpoint index and choose the one minimizing total SSE.
def sse_two_segments(k_idx):
    # left = [0..k_idx], right = [k_idx+1..end]
    if k_idx < 2 or k_idx > len(logN)-3:  # need enough points on both sides
        return np.inf
    mask_left = np.arange(len(logN)) <= k_idx
    mask_right = np.arange(len(logN)) > k_idx
    bL, aL, r2L, xL, yL = fit_range(mask_left)
    bR, aR, r2R, xR, yR = fit_range(mask_right)
    sse = np.sum((yL - (aL + bL*xL))**2) + np.sum((yR - (aR + bR*xR))**2)
    return sse

best_idx = np.argmin([sse_two_segments(i) for i in range(len(logN))])
mask_left = np.arange(len(logN)) <= best_idx
mask_right = ~mask_left
bL, aL, r2L, xL, yL = fit_range(mask_left)
bR, aR, r2R, xR, yR = fit_range(mask_right)
N_break = df["N"].iloc[best_idx]

print("\n=== Log–log scaling fits ===")
print(f"Full fit:           slope b = {b_all:.3f}, R^2 = {r2_all:.4f}")
print(f"Saturated fit N>={N0}: slope b = {b_sat:.3f}, R^2 = {r2_sat:.4f}")
print(f"Piecewise fit:")
print(f"  left  (N <= {N_break:,}): b = {bL:.3f}, R^2 = {r2L:.4f}")
print(f"  right (N >  {N_break:,}): b = {bR:.3f}, R^2 = {r2R:.4f}")

# Plot
plt.figure(figsize=(8,6))
N = df["N"].values
plt.loglog(N, df["T"], 'o', label="Measured T(N)")

# lines
xx = np.linspace(logN.min(), logN.max(), 200)
plt.loglog(10**xx, 10**(a_all + b_all*xx), '-',  label=f"Full fit b={b_all:.2f}")
plt.loglog(10**xx, 10**(a_sat + b_sat*xx), '--', label=f"Saturated fit b={b_sat:.2f} (N≥{N0:,})")

# piecewise lines over their domains
xL_line = np.linspace(xL.min(), xL.max(), 100)
xR_line = np.linspace(xR.min(), xR.max(), 100)
plt.loglog(10**xL_line, 10**(aL + bL*xL_line), ':',  label=f"Piecewise left b={bL:.2f}")
plt.loglog(10**xR_line, 10**(aR + bR*xR_line), ':',  label=f"Piecewise right b={bR:.2f}")

plt.axvline(N_break, color='gray', ls=':', alpha=0.6, label=f"Breakpoint ≈ {int(N_break):,}")
plt.xlabel("Particles (N)")
plt.ylabel("Total time T(N) (s)")
plt.title("Log–log scaling: full vs saturated vs piecewise fits")
plt.legend()
plt.grid(True, which="both", ls="--", alpha=0.6)
plt.tight_layout()
plt.savefig("scaling_fits.png", dpi=300)
print("Saved plot: scaling_fits.png")
