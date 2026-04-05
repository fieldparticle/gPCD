import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "inbound_outbound_steps.png"


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


def maybe_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    return int(float(value))


def main() -> None:
    studies: list[dict[str, float]] = []

    for path in summary_paths():
        metrics = load_metrics(path)
        studies.append(
            {
                "study_index": float(parse_study_index(path)),
                "samples_in": float(maybe_int(metrics.get("field samples in")) or 0),
                "samples_out": float(maybe_int(metrics.get("field samples out")) or 0),
            }
        )

    if not studies:
        raise FileNotFoundError(f"No study summary CSV files found in {DATA_DIR}")

    studies.sort(key=lambda item: item["study_index"])
    study_indices = [item["study_index"] for item in studies]
    samples_in = [item["samples_in"] for item in studies]
    samples_out = [item["samples_out"] for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

    axes[0].plot(study_indices, samples_in, marker="o", linewidth=1.8, color="#2563eb")
    axes[0].set_title("Inbound Steps vs Study")
    axes[0].set_ylabel("Inbound Steps")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(study_indices, samples_out, marker="o", linewidth=1.8, color="#dc2626")
    axes[1].set_title("Outbound Steps vs Study")
    axes[1].set_xlabel("Study Index")
    axes[1].set_ylabel("Outbound Steps")
    axes[1].grid(True, alpha=0.3)

    for study_index, value in zip(study_indices, samples_in):
        axes[0].annotate(
            str(int(study_index)),
            (study_index, value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
        )

    for study_index, value in zip(study_indices, samples_out):
        axes[1].annotate(
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
