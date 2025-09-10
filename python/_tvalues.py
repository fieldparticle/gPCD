import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- Step 1. Load or define your data ---
# CSV format: n, T_s, k
#   n   = number of particles
#   T_s = total time (seconds)
#   k   = mean neighbors per particle

# If using a CSV:
# df = pd.read_csv("your_data.csv")

# Or inline example data:
df = pd.DataFrame({
    "n": [1_000_000, 2_000_000, 5_000_000, 10_000_000],
    "T_s": [0.0065, 0.0130, 0.0320, 0.0640],
    "k": [40, 40, 40, 40],   # adjust if k varies
})

# --- Step 2. Compute t1 = T / n ---
df["t1"] = df["T_s"] / df["n"]

# --- Step 3. Fit t1 = alpha + beta * k ---
x = df["k"].values
y = df["t1"].values

# Build design matrix for OLS: [1, k]
X = np.column_stack([np.ones_like(x), x])
# Solve (X^T X) beta = X^T y
beta_hat = np.linalg.lstsq(X, y, rcond=None)[0]
alpha, beta = beta_hat

print(f"alpha (broad-phase cost/particle): {alpha:.3e} s")
print(f"beta  (narrow-phase cost per neighbor): {beta:.3e} s")

# --- Step 4. Plot ---
plt.scatter(x, y, label="data")
k_line = np.linspace(x.min(), x.max(), 200)
t1_line = alpha + beta * k_line
plt.plot(k_line, t1_line, 'r-', label=f"fit: t1 = {alpha:.2e} + {beta:.2e} k")
plt.xlabel("k (mean neighbors per particle)")
plt.ylabel("t1 (seconds per particle)")
plt.legend()
plt.tight_layout()
plt.show()
