from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data/depth_test"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_PATH = PLOTS_DIR / "penetration_depth_vs_repulsion.png"
SHOW_PLOT = True


def study_indices_from_trace_name(path: Path) -> tuple[int, int]:
    stem = path.stem
    if not stem.startswith("depth_v") or "_f" not in stem:
        raise ValueError(f"Unexpected depth trace filename: {path.name}")
    velocity_part, force_part = stem.replace("depth_v", "", 1).split("_f", 1)
    return int(velocity_part), int(force_part)


def load_summary_metrics(summary_path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    with summary_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            metrics[row[0]] = row[1]
    return metrics


def max_penetration_fraction(trace_path: Path) -> float:
    max_fraction = 0.0
    with trace_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row.get("p1_x"):
                continue
            x0 = float(row["p0_x"])
            y0 = float(row["p0_y"])
            x1 = float(row["p1_x"])
            y1 = float(row["p1_y"])
            r0 = float(row["p0_radius"])
            r1 = float(row["p1_radius"])
            distance = math.hypot(x1 - x0, y1 - y0)
            penetration = max(0.0, (r0 + r1) - distance)
            radius_scale = min(r0, r1)
            if radius_scale <= 0.0:
                continue
            max_fraction = max(max_fraction, penetration / radius_scale)
    return max_fraction


def load_depth_series() -> dict[int, list[tuple[int, float, float, float]]]:
    trace_paths = sorted(
        path
        for path in DATA_DIR.glob("depth_*.csv")
        if "_frame_timing" not in path.stem and "_summary" not in path.stem
    )
    series_by_velocity: dict[int, list[tuple[int, float, float, float]]] = {}
    for trace_path in trace_paths:
        velocity_index, force_index = study_indices_from_trace_name(trace_path)
        summary_path = trace_path.with_name(f"{trace_path.stem}_summary{trace_path.suffix}")
        metrics = load_summary_metrics(summary_path)
        force_value = float(metrics["study repulsion force per area"])
        velocity_value = float(metrics["study velocity"])
        depth_fraction = max_penetration_fraction(trace_path)
        series_by_velocity.setdefault(velocity_index, []).append(
            (force_index, force_value, depth_fraction, velocity_value)
        )
    for velocity_index in series_by_velocity:
        series_by_velocity[velocity_index].sort(key=lambda item: item[1])
    return series_by_velocity


def main() -> None:
    series_by_velocity = load_depth_series()
    if not series_by_velocity:
        raise FileNotFoundError(f"No depth study traces found in {DATA_DIR}")

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    color_map = plt.cm.get_cmap("tab10", max(1, len(series_by_velocity)))

    for color_index, velocity_index in enumerate(sorted(series_by_velocity)):
        series = series_by_velocity[velocity_index]
        forces = [item[1] for item in series]
        depth_fractions = [item[2] for item in series]
        velocity_value = series[0][3]
        color = color_map(color_index)
        ax.plot(
            forces,
            depth_fractions,
            color=color,
            linewidth=1.5,
            marker="o",
            markersize=6,
            label=f"v{velocity_index} = {velocity_value:.3f}",
        )

        for force_index, x_value, y_value, _velocity_value in series:
            ax.annotate(
                f"v{velocity_index}f{force_index}",
                (x_value, y_value),
                textcoords="offset points",
                xytext=(4, 4),
                fontsize=7,
                color=color,
            )

    ax.set_title("Repulsion Force vs Penetration Depth")
    ax.set_xlabel("Repulsion Force Per Area")
    ax.set_ylabel("Max Penetration Depth / Radius")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=150)
    if SHOW_PLOT:
        plt.show()
    plt.close(fig)

    print(f"Saved plot to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
