import matplotlib.pyplot as plt

# === Input data ===
# Each entry: (label, particle_count_in_millions, ns_per_particle, rendering_included)
data = [
    ("Jack Bell (2024)", 1, 33, False),
    ("David Algis et al. (2024)", 30, 20, False),    # example kernel-only average
    ("Min Tang et al. (2011)", 0.5, 150, False),
    ("Straßer et al. (2010)", 1, 30, False),
    ("Your System (2025)", 11.09, 6.35, True),
]

# === Extract for plotting ===
labels = [d[0] for d in data]
particle_counts = [d[1] for d in data]
ns_per_particle = [d[2] for d in data]
colors = ["tab:green" if d[3] else "tab:blue" for d in data]
markers = ["s" if d[3] else "o" for d in data]  # square for rendering, circle otherwise

# === Create plot ===
plt.figure(figsize=(10, 7))

for x, y, label, color, marker in zip(particle_counts, ns_per_particle, labels, colors, markers):
    plt.scatter(x, y, color=color, s=100, marker=marker, label=label)
    plt.annotate(label, (x, y), textcoords="offset points",
                 xytext=(8, 5), ha='left', fontsize=9)

plt.xscale("log")
plt.yscale("log")
plt.xlabel("Particle Count (millions, log scale)", fontsize=12)
plt.ylabel("Time per Particle (ns, log scale)", fontsize=12)
plt.title("GPU Particle Collision Detection Performance Comparison", fontsize=14)
plt.grid(True, which="both", linestyle="--", linewidth=0.5)

# Create legend manually for rendering vs non-rendering
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='Collision detection only',
           markerfacecolor='tab:blue', markersize=10),
    Line2D([0], [0], marker='s', color='w', label='Collision + Rendering',
           markerfacecolor='tab:green', markersize=10)
]
plt.legend(handles=legend_elements, loc='best')

plt.tight_layout()

# === Save to file ===
plt.savefig("collision_detection_comparison_colored.png", dpi=300)
plt.savefig("collision_detection_comparison_colored.pdf")  # optional vector export

# === Show plot interactively (optional) ===
plt.show()
