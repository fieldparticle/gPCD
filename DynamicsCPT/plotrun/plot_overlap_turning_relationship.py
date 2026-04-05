import csv
import math
from pathlib import Path
from numpy import linspace
import numpy as np  

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "overlap_turning_relationship.png"
PARTICLE_RADIUS = 1.0
ANNOTATION_FONT_SIZE = 6


def summary_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("tpocl_*_summary.csv"))


def load_metrics(path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            metric = (row.get("metric") or "").strip()
            value = (row.get("value") or "").strip()
            if metric:
                metrics[metric] = value
    return metrics


def parse_y_from_init_pos(value: str) -> float:
    _, y_str = value.strip("()").split(",")
    return float(y_str.strip())


def maybe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def equal_circle_overlap_area(distance: float, radius: float = PARTICLE_RADIUS) -> float:
    if distance >= 2.0 * radius:
        return 0.0
    if distance <= 0.0:
        return math.pi * radius * radius

    term1 = 2.0 * radius * radius * math.acos(max(-1.0, min(1.0, distance / (2.0 * radius))))
    term2 = 0.5 * distance * math.sqrt(max(0.0, 4.0 * radius * radius - distance * distance))
    return term1 - term2


def invert_overlap_to_distance(area: float, radius: float = PARTICLE_RADIUS) -> float:
    max_area = math.pi * radius * radius
    if area <= 0.0:
        return 2.0 * radius
    if area >= max_area:
        return 0.0

    low = 0.0
    high = 2.0 * radius
    for _ in range(80):
        mid = 0.5 * (low + high)
        mid_area = equal_circle_overlap_area(mid, radius)
        if mid_area > area:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def turning_geometry_kernel(area: float, radius: float = PARTICLE_RADIUS) -> float:
    distance = invert_overlap_to_distance(area, radius)
    chord_half_sq = max(0.0, radius * radius - 0.25 * distance * distance)
    return distance * math.sqrt(chord_half_sq)


def parse_study_index(path: Path) -> int:
    stem = path.stem.replace("_summary", "")
    return int(stem.split("_")[-1])


def main() -> None:
    studies: list[dict[str, float | str]] = []

    for path in summary_paths():
        metrics = load_metrics(path)
        init_pos = metrics.get("particle 01 init pos")
        if not init_pos:
            continue

        area_in = maybe_float(metrics.get("sum area in"))
        area_out = maybe_float(metrics.get("sum area out"))
        turn_area = maybe_float(metrics.get("sum turn area"))
        if area_in is None or area_out is None or turn_area is None:
            continue

        studies.append(
            {
                "label": parse_study_index(path),
                "y_init": parse_y_from_init_pos(init_pos),
                "overlap_total": area_in + area_out,
                "overlap_balanced": 0.5 * (area_in + area_out),
                "turn_area": turn_area,
            }
        )

    if not studies:
        raise FileNotFoundError(f"No usable study summary CSV files found in {DATA_DIR}")

    studies.sort(key=lambda study: float(study["y_init"]))
    overlap_values = [float(study["overlap_balanced"]) for study in studies]
    turn_values = [float(study["turn_area"]) for study in studies]
    y_values = [float(study["y_init"]) for study in studies]
    geometry_kernel_values = [turning_geometry_kernel(value) for value in overlap_values]
    max_overlap = max(overlap_values) if overlap_values else 1.0
    max_turn = max(turn_values) if turn_values else 1.0
    turn_scale = max_overlap / max_turn if max_turn > 0.0 else 1.0
    scaled_turn_values = [value * turn_scale for value in turn_values]
    max_kernel = max(geometry_kernel_values) if geometry_kernel_values else 1.0
    kernel_scale = max_turn / max_kernel if max_kernel > 0.0 else 1.0
    scaled_kernel_values = [value * kernel_scale for value in geometry_kernel_values]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

    cmap = plt.get_cmap("viridis")
    scatter = axes[0].scatter(overlap_values, turn_values, c=y_values, cmap=cmap, s=90)
    axes[0].plot(overlap_values, turn_values, color="#64748b", linewidth=1.5, alpha=0.8)
    overlap_grid = np.linspace(0.0, max_overlap, 300)
    kernel_grid = [turning_geometry_kernel(value) * kernel_scale for value in overlap_grid]
    axes[0].plot(
        overlap_grid,
        kernel_grid,
        color="#dc2626",
        linewidth=2,
        linestyle="--",
        label="Geometry-only reference (scaled)",
    )
    for study in studies:
        axes[0].annotate(
            str(study["label"]),
            (float(study["overlap_balanced"]), float(study["turn_area"])),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=ANNOTATION_FONT_SIZE,
        )
    axes[0].set_title("Total Turning Area vs Balanced Overlap Area")
    axes[0].set_xlabel("Balanced Overlap Area")
    axes[0].set_ylabel("Total Turning Area")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    cbar = fig.colorbar(scatter, ax=axes[0])
    cbar.set_label("Initial Particle 1 Y")

    axes[1].plot(y_values, overlap_values, marker="o", linewidth=2, color="#b45309", label="Balanced Overlap Area")
    axes[1].plot(
        y_values,
        scaled_turn_values,
        marker="o",
        linewidth=2,
        color="#2563eb",
        label=f"Scaled Turning Area (x{turn_scale:.1f})",
    )
    axes[1].plot(
        y_values,
        [value * (max_overlap / max_kernel if max_kernel > 0.0 else 1.0) for value in geometry_kernel_values],
        marker="o",
        linewidth=2,
        color="#dc2626",
        linestyle="--",
        label=f"Geometry-only Reference (scaled x{(max_overlap / max_kernel) if max_kernel > 0.0 else 1.0:.1f})",
    )
    for study in studies:
        axes[1].annotate(
            str(study["label"]),
            (float(study["y_init"]), float(study["turn_area"]) * turn_scale),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=ANNOTATION_FONT_SIZE,
        )
    axes[1].set_title("Competing Effects Across Study Offset")
    axes[1].set_xlabel("Initial Particle 1 Y")
    axes[1].set_ylabel("Magnitude On Overlap Scale")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    plt.show()


if __name__ == "__main__":
    main()
