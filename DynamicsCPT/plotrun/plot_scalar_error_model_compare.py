import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "scalar_error_model_compare.png"
DATA_DIR_NAME = "data005"
PLOT_LABEL = "Mom"
PLOT_COLOR = "#dc2626"


def summary_paths(data_dir: Path) -> list[Path]:
    return sorted(data_dir.glob("tpocl_*_summary.csv"))


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


def load_dataset(data_dir: Path) -> list[dict[str, float | int]]:
    studies: list[dict[str, float | int]] = []

    for path in summary_paths(data_dir):
        metrics = load_metrics(path)
        scalar_error = maybe_float(metrics.get("scalar total error"))
        max_area_in = maybe_float(metrics.get("max area in"))

        if scalar_error is None:
            if metrics.get("collision status") == "no collision":
                scalar_error = 0.0
            else:
                continue

        studies.append(
            {
                "study_index": parse_study_index(path),
                "abs_scalar_error": abs(float(scalar_error)),
                "max_area_in": 0.0 if max_area_in is None else float(max_area_in),
            }
        )

    studies.sort(key=lambda item: int(item["study_index"]))
    return studies


def main() -> None:
    data_dir = PROJECT_ROOT / DATA_DIR_NAME
    studies = load_dataset(data_dir)
    if not studies:
        raise FileNotFoundError(f"No usable study summaries found in {data_dir}")

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(10, 9))

    study_indices = [int(item["study_index"]) for item in studies]
    abs_error_values = [float(item["abs_scalar_error"]) for item in studies]
    max_area_values = [float(item["max_area_in"]) for item in studies]

    axes[0].plot(
        study_indices,
        abs_error_values,
        marker="o",
        linewidth=2,
        color=PLOT_COLOR,
        label=f"{PLOT_LABEL} ({DATA_DIR_NAME})",
    )
    axes[1].plot(
        max_area_values,
        abs_error_values,
        marker="o",
        linewidth=2,
        color=PLOT_COLOR,
        label=f"{PLOT_LABEL} ({DATA_DIR_NAME})",
    )
    for study_index, abs_error_value in zip(study_indices, abs_error_values):
        axes[0].annotate(
            str(study_index),
            (study_index, abs_error_value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=7,
            color=PLOT_COLOR,
        )
    for study_index, max_area_value, abs_error_value in zip(study_indices, max_area_values, abs_error_values):
        axes[1].annotate(
            str(study_index),
            (max_area_value, abs_error_value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=7,
            color=PLOT_COLOR,
        )

    axes[0].set_yscale("log")
    axes[0].set_title("|Scalar Momentum Error| vs Study")
    axes[0].set_xlabel("Study Index")
    axes[0].set_ylabel("|Scalar Momentum Error|")
    axes[0].grid(True, alpha=0.3, which="both")
    axes[0].legend()

    axes[1].set_yscale("log")
    axes[1].set_title("|Scalar Momentum Error| vs Max Area In")
    axes[1].set_xlabel("Max Area In")
    axes[1].set_ylabel("|Scalar Momentum Error|")
    axes[1].grid(True, alpha=0.3, which="both")
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
