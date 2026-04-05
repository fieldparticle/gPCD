import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "ThreeP005_mom"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "three_particle_scalar_error_vs_study.png"


def summary_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("tph_*_summary.csv"))


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


def main() -> None:
    studies: list[tuple[int, float, float]] = []

    for path in summary_paths():
        metrics = load_metrics(path)
        scalar_error = maybe_float(metrics.get("scalar total error"))
        turn_area = maybe_float(metrics.get("sum turn area"))

        if scalar_error is None:
            if metrics.get("collision status") == "no collision":
                scalar_error = 0.0
            else:
                continue

        studies.append(
            (
                parse_study_index(path),
                float(scalar_error),
                0.0 if turn_area is None else float(turn_area),
            )
        )

    if not studies:
        raise FileNotFoundError(f"No three-particle summary files found in {DATA_DIR}")

    studies.sort(key=lambda item: item[0])
    study_indices = [item[0] for item in studies]
    scalar_errors = [item[1] for item in studies]
    abs_scalar_errors = [abs(item[1]) for item in studies]
    turn_areas = [item[2] for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    axes[0].plot(study_indices, turn_areas, marker="o", linewidth=2, color="#dc2626")
    for study_index, turn_area in zip(study_indices, turn_areas):
        axes[0].annotate(
            f"{turn_area:.1e}",
            (study_index, turn_area),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=8,
        )
    axes[0].set_title("Three-Particle Sum Turning Area vs Study")
    axes[0].set_ylabel("Sum Turn Area")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(study_indices, abs_scalar_errors, marker="o", linewidth=2, color="#2563eb")
    for study_index, abs_scalar_error in zip(study_indices, abs_scalar_errors):
        axes[1].annotate(
            str(study_index),
            (study_index, abs_scalar_error),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=8,
        )
    axes[1].set_yscale("log")
    axes[1].set_title("Three-Particle Ending Scalar Momentum Error Magnitude vs Study")
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
