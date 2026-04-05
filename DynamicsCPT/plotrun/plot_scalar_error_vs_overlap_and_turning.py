import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "scalar_error_vs_overlap_and_turning.png"


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


def maybe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def parse_study_index(path: Path) -> int:
    stem = path.stem.replace("_summary", "")
    return int(stem.split("_")[-1])


def main() -> None:
    studies: list[dict[str, float | str]] = []

    for path in summary_paths():
        metrics = load_metrics(path)
        area_in = maybe_float(metrics.get("sum area in"))
        turn_area = maybe_float(metrics.get("sum turn area"))
        scalar_error = maybe_float(metrics.get("scalar total error"))

        if area_in is None or turn_area is None or scalar_error is None:
            continue

        studies.append(
            {
                "label": parse_study_index(path),
                "sum_area_in": area_in,
                "sum_turn_area": turn_area,
                "abs_scalar_error": abs(scalar_error),
            }
        )

    if not studies:
        raise FileNotFoundError(f"No usable study summary CSV files found in {DATA_DIR}")

    studies.sort(key=lambda study: float(study["label"]))

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.5, 6.5))

    ax.plot(
        [float(study["sum_area_in"]) for study in studies],
        [float(study["sum_turn_area"]) for study in studies],
        color="#64748b",
        linewidth=1.5,
        alpha=0.8,
    )
    scatter = ax.scatter(
        [float(study["sum_area_in"]) for study in studies],
        [float(study["sum_turn_area"]) for study in studies],
        c=[float(study["abs_scalar_error"]) for study in studies],
        cmap="magma",
        s=80,
    )
    for study in studies:
        ax.annotate(
            str(study["label"]),
            (float(study["sum_area_in"]), float(study["sum_turn_area"])),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )

    ax.set_title("Scalar Momentum Error vs Overlap And Turning")
    ax.set_xlabel("Sum Area In")
    ax.set_ylabel("Sum Turn Area")
    ax.grid(True, alpha=0.3)
    colorbar = fig.colorbar(scatter, ax=ax)
    colorbar.set_label("|Scalar Momentum Error|")

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
