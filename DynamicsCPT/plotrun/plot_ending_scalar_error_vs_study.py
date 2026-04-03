import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "ending_scalar_error_vs_study.png"


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


def main() -> None:
    studies: list[tuple[int, float]] = []

    for path in summary_paths():
        metrics = load_metrics(path)
        value = metrics.get("scalar total error")

        study_index = parse_study_index(path)
        if value in (None, ""):
            if metrics.get("collision status") == "no collision":
                studies.append((study_index, 0.0))
            continue

        studies.append((study_index, float(value)))

    if not studies:
        raise FileNotFoundError(f"No scalar-error study summaries found in {DATA_DIR}")

    studies.sort(key=lambda item: item[0])
    study_indices = [item[0] for item in studies]
    error_values = [item[1] for item in studies]
    abs_error_values = [abs(value) for value in error_values]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(study_indices, error_values, marker="o", linewidth=2, color="#7c3aed")

    for study_index, error_value in studies:
        axes[0].annotate(
            f"{error_value:.1e}",
            (study_index, error_value),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )

    axes[0].set_title("Ending Scalar Momentum Error vs Study")
    axes[0].set_ylabel("Scalar Momentum Error")
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
