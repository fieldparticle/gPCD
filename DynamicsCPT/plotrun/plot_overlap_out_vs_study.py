import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "overlap_area_in_out_vs_study.png"
ANNOTATION_FONT_SIZE = 7


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
    studies: list[dict[str, float | int]] = []
    for path in summary_paths():
        metrics = load_metrics(path)
        sum_area_in = maybe_float(metrics.get("sum area in"))
        sum_area_out = maybe_float(metrics.get("sum area out"))
        max_area_in = maybe_float(metrics.get("max area in"))
        max_area_out = maybe_float(metrics.get("max area out"))
        if sum_area_in is None or sum_area_out is None or max_area_in is None or max_area_out is None:
            continue

        studies.append(
            {
                "study": parse_study_index(path),
                "sum_area_in": sum_area_in,
                "sum_area_out": sum_area_out,
                "max_area_in": max_area_in,
                "max_area_out": max_area_out,
            }
        )

    if not studies:
        raise FileNotFoundError(f"No usable study summary CSV files found in {DATA_DIR}")

    studies.sort(key=lambda study: int(study["study"]))
    study_indices = [int(study["study"]) for study in studies]
    sum_area_in_values = [float(study["sum_area_in"]) for study in studies]
    sum_area_out_values = [float(study["sum_area_out"]) for study in studies]
    signed_area_difference_values = [
        value_in - value_out for value_in, value_out in zip(sum_area_in_values, sum_area_out_values)
    ]
    max_area_difference_values = [
        float(study["max_area_in"]) - float(study["max_area_out"]) for study in studies
    ]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(11, 11), sharex=True)

    axes[0].plot(
        study_indices,
        sum_area_in_values,
        marker="o",
        linewidth=2,
        color="#b45309",
    )
    for study, value in zip(study_indices, sum_area_in_values):
        axes[0].annotate(
            str(study),
            (study, value),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=ANNOTATION_FONT_SIZE,
        )
    axes[0].set_title("Sum Overlap Area In vs Study Index")
    axes[0].set_ylabel("Sum Area In")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(
        study_indices,
        signed_area_difference_values,
        marker="o",
        linewidth=2,
        color="#2563eb",
    )
    for study, value in zip(study_indices, signed_area_difference_values):
        axes[1].annotate(
            str(study),
            (study, value),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=ANNOTATION_FONT_SIZE,
        )
    axes[1].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--", alpha=0.8)
    axes[1].set_title("Signed Difference: Sum Area In - Sum Area Out")
    axes[1].set_ylabel("Area In - Area Out")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(
        study_indices,
        max_area_difference_values,
        marker="o",
        linewidth=2,
        color="#059669",
    )
    for study, value in zip(study_indices, max_area_difference_values):
        axes[2].annotate(
            str(study),
            (study, value),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=ANNOTATION_FONT_SIZE,
        )
    axes[2].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--", alpha=0.8)
    axes[2].set_title("Peak Difference: Max Area In - Max Area Out")
    axes[2].set_xlabel("Study Index")
    axes[2].set_ylabel("Max In - Max Out")
    axes[2].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    plt.show()


if __name__ == "__main__":
    main()
