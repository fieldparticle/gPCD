#!/usr/bin/env python3
"""
Generate a LaTeX performance metrics table from CSV data.

CSV should contain:
  N   : number of particles
  gms : graphics time per frame (s or ms)
  cms : compute time per frame (s or ms)

Output:
  performance_metrics_table.tex
"""

import pandas as pd

# === CONFIG ===
csv_path = "CHATGP_Data.csv"       # input CSV
out_path = "performance_metrics_table.tex"  # output LaTeX file
times_in_ms = True                 # set True if gms/cms are in ms

# === Load Data ===
df = pd.read_csv('test_data.csv')

if times_in_ms:
    df["gms"] = df["gms"] / 1000.0
    df["cms"] = df["cms"] / 1000.0

df["total_time"] = df["gms"] + df["cms"]

# Throughput (Mpps)
df["graphics_throughput_mpps"] = (df["N"] / df["gms"]) / 1e6
df["compute_throughput_mpps"]  = (df["N"] / df["cms"]) / 1e6
df["total_throughput_mpps"]    = (df["N"] / df["total_time"]) / 1e6

# Time per particle (ns)
df["graphics_tpp_ns"] = (df["gms"] / df["N"]) * 1e9
df["compute_tpp_ns"]  = (df["cms"] / df["N"]) * 1e9
df["total_tpp_ns"]    = (df["total_time"] / df["N"]) * 1e9

# === Build LaTeX Table ===
header = r"""\begin{table*}[htbp]
\centering
\caption{Performance metrics across particle counts. Times are reported in seconds, throughput in million particles per second (Mpps), and time-per-particle in nanoseconds (ns).}
\begin{tabular}{r r r r r r r r r r}
\hline
$N$ & Graphics Time (s) & Compute Time (s) & Total Time (s) & Graphics (Mpps) & Compute (Mpps) & Total (Mpps) & Graphics (ns/particle) & Compute (ns/particle) & Total (ns/particle) \\
\hline
"""

rows = []
for _, row in df.iterrows():
    rows.append(
        f"{int(row['N'])} & "
        f"{row['gms']:.5e} & {row['cms']:.5e} & {row['total_time']:.5e} & "
        f"{row['graphics_throughput_mpps']:.2f} & {row['compute_throughput_mpps']:.2f} & {row['total_throughput_mpps']:.2f} & "
        f"{row['graphics_tpp_ns']:.2f} & {row['compute_tpp_ns']:.2f} & {row['total_tpp_ns']:.2f} \\\\"
    )

footer = r"""
\hline
\end{tabular}
\label{tab:performance_metrics}
\end{table*}
"""

latex_table = header + "\n".join(rows) + footer

with open(out_path, "w") as f:
    f.write(latex_table)

print(f"LaTeX table written to: {out_path}")
