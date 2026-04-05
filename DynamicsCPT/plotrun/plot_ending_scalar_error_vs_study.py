import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
#DATA_DIR_NAME = "data005"
DATA_DIR_NAME = "ThreeP005_mom"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "ending_scalar_error_vs_study.png"
PARTICLE_RADIUS = 1.0


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


def parse_study_index(path: Path) -> int:
    stem = path.stem.replace("_summary", "")
    return int(stem.split("_")[-1])


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


def main() -> None:
    studies: list[tuple[int, float, float]] = []

    for path in summary_paths():
        metrics = load_metrics(path)
        value = metrics.get("scalar total error")
        area_in = maybe_float(metrics.get("max area in"))
        area_out = maybe_float(metrics.get("max area out"))

        study_index = parse_study_index(path)
        balanced_max_overlap = 0.0
        if area_in is not None and area_out is not None:
            balanced_max_overlap = 0.5 * (area_in + area_out)
        if value in (None, ""):
            if metrics.get("collision status") == "no collision":
                studies.append((study_index, 0.0, turning_geometry_kernel(balanced_max_overlap)))
            continue

        studies.append((study_index, float(value), turning_geometry_kernel(balanced_max_overlap)))

    if not studies:
        raise FileNotFoundError(f"No scalar-error study summaries found in {DATA_DIR}")

    studies.sort(key=lambda item: item[0])
    study_indices = [item[0] for item in studies]
    error_values = [item[1] for item in studies]
    kernel_values = [item[2] for item in studies]
    abs_error_values = [abs(value) for value in error_values]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(study_indices, kernel_values, marker="o", linewidth=2, color="#dc2626")

    for study_index, _, kernel_value in studies:
        axes[0].annotate(
            f"{kernel_value:.1e}",
            (study_index, kernel_value),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )

    axes[0].set_title("Geometry-only Kernel From Balanced Max Overlap vs Study")
    axes[0].set_ylabel("Geometry-only Kernel")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(study_indices, abs_error_values, marker="o", linewidth=2, color="#2563eb")
    for study_index, abs_error_value in zip(study_indices, abs_error_values):
        axes[1].annotate(
            f"{study_index}",
            (study_index, abs_error_value),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )
    axes[1].set_yscale("log")
    axes[1].set_title("Ending Scalar Momentum Error Magnitude vs Study")
    axes[1].set_xlabel("Study Index")
    axes[1].set_ylabel("|Scalar Momentum Error|")
    axes[1].grid(True, alpha=0.3, which="both")

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
