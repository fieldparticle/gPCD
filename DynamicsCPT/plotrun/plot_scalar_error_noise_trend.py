import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "scalar_error_noise_trend.png"
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
def main() -> None:
    studies: list[dict[str, float]] = []

    for path in summary_paths():
        metrics = load_metrics(path)
        study_index = parse_study_index(path)

        scalar_error = maybe_float(metrics.get("scalar total error"))
        if scalar_error is None:
            if metrics.get("collision status") == "no collision":
                scalar_error = 0.0
            else:
                continue

        studies.append(
            {
                "study_index": float(study_index),
                "abs_error": abs(float(scalar_error)),
                "sum_turn_area": 0.0 if maybe_float(metrics.get("sum turn area")) is None else float(metrics["sum turn area"]),
            }
        )

    if not studies:
        raise FileNotFoundError(f"No scalar-error study summaries found in {DATA_DIR}")

    studies.sort(key=lambda item: item["study_index"])
    study_indices = [item["study_index"] for item in studies]
    abs_error_values = [item["abs_error"] for item in studies]
    turn_values = [item["sum_turn_area"] for item in studies]
    normalized_error_values = [
        (abs_error / turn_value) if turn_value > 0.0 else None
        for abs_error, turn_value in zip(abs_error_values, turn_values)
    ]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(11, 11), sharex=False)

    axes[0].plot(study_indices, abs_error_values, marker="o", linewidth=1.8, color="#2563eb", label="|Scalar error|")
    for study_index, abs_error_value in zip(study_indices, abs_error_values):
        axes[0].annotate(
            str(int(study_index)),
            (study_index, abs_error_value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
        )
    axes[0].set_yscale("log")
    axes[0].set_title("Scalar Error Magnitude Noise Trend vs Study")
    axes[0].set_xlabel("Study Index")
    axes[0].set_ylabel("|Scalar Momentum Error|")
    axes[0].grid(True, alpha=0.3, which="both")

    ratio_studies = [
        study_index
        for study_index, normalized_error in zip(study_indices, normalized_error_values)
        if normalized_error is not None
    ]
    ratio_values = [
        normalized_error
        for normalized_error in normalized_error_values
        if normalized_error is not None
    ]
    axes[1].scatter(ratio_studies, ratio_values, color="#059669", s=45)
    axes[1].plot(ratio_studies, ratio_values, color="#94a3b8", linewidth=1.4, alpha=0.8)
    for study_index, ratio_value in zip(ratio_studies, ratio_values):
        axes[1].annotate(
            str(int(study_index)),
            (study_index, ratio_value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
        )
    axes[1].set_yscale("log")
    axes[1].set_title("|Scalar Error| / Sum Turn Area vs Study")
    axes[1].set_xlabel("Study Index")
    axes[1].set_ylabel("|Scalar Error| / Sum Turn Area")
    axes[1].grid(True, alpha=0.3, which="both")

    difference_studies = [
        study_index
        for study_index, normalized_error in zip(study_indices, normalized_error_values)
        if normalized_error is not None
    ]
    difference_values = [
        abs_error - normalized_error
        for abs_error, normalized_error in zip(abs_error_values, normalized_error_values)
        if normalized_error is not None
    ]
    axes[2].plot(difference_studies, difference_values, marker="o", linewidth=1.8, color="#7c3aed")
    for study_index, difference_value in zip(difference_studies, difference_values):
        axes[2].annotate(
            str(int(study_index)),
            (study_index, difference_value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
        )
    axes[2].set_title("Difference Between Row 1 And Row 2")
    axes[2].set_xlabel("Study Index")
    axes[2].set_ylabel("|Scalar Error| - (|Scalar Error| / Sum Turn Area)")
    axes[2].grid(True, alpha=0.3, which="both")

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
