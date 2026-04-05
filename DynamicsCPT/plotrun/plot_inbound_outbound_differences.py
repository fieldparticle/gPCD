import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "inbound_outbound_differences.png"


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


def maybe_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    return int(float(value))


def main() -> None:
    studies: list[dict[str, float]] = []

    for path in summary_paths():
        metrics = load_metrics(path)
        study_index = parse_study_index(path)

        samples_in = maybe_int(metrics.get("field samples in"))
        samples_out = maybe_int(metrics.get("field samples out"))
        area_in = maybe_float(metrics.get("sum area in"))
        area_out = maybe_float(metrics.get("sum area out"))
        j_in = maybe_float(metrics.get("sum J in"))
        j_out = maybe_float(metrics.get("sum J out"))

        studies.append(
            {
                "study_index": float(study_index),
                "sample_diff": 0.0 if samples_in is None or samples_out is None else float(samples_in - samples_out),
                "area_diff": 0.0 if area_in is None or area_out is None else area_in - area_out,
                "j_diff": 0.0 if j_in is None or j_out is None else j_in - j_out,
            }
        )

    if not studies:
        raise FileNotFoundError(f"No study summary CSV files found in {DATA_DIR}")

    studies.sort(key=lambda item: item["study_index"])
    study_indices = [item["study_index"] for item in studies]
    sample_diffs = [item["sample_diff"] for item in studies]
    area_diffs = [item["area_diff"] for item in studies]
    j_diffs = [item["j_diff"] for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)

    axes[0].plot(study_indices, sample_diffs, marker="o", linewidth=1.8, color="#2563eb")
    axes[0].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    axes[0].set_title("Inbound - Outbound Sample Count Difference")
    axes[0].set_ylabel("Samples In - Samples Out")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(study_indices, area_diffs, marker="o", linewidth=1.8, color="#dc2626")
    axes[1].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    axes[1].set_title("Inbound - Outbound Summed Area Difference")
    axes[1].set_ylabel("Sum Area In - Sum Area Out")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(study_indices, j_diffs, marker="o", linewidth=1.8, color="#059669")
    axes[2].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    axes[2].set_title("Inbound - Outbound Summed Impulse Difference")
    axes[2].set_xlabel("Study Index")
    axes[2].set_ylabel("Sum J In - Sum J Out")
    axes[2].grid(True, alpha=0.3)

    for ax, values in zip(axes, [sample_diffs, area_diffs, j_diffs]):
        for study_index, value in zip(study_indices, values):
            ax.annotate(
                str(int(study_index)),
                (study_index, value),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=8,
            )

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
