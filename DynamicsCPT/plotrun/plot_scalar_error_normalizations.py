import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "scalar_error_normalizations.png"


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


def safe_ratio(numerator: float, denominator: float | None) -> float | None:
    if denominator is None or abs(denominator) <= 1.0e-15:
        return None
    return numerator / denominator


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
                "max_turn_area": 0.0 if maybe_float(metrics.get("max turn area")) is None else float(metrics["max turn area"]),
                "max_area_in": 0.0 if maybe_float(metrics.get("max area in")) is None else float(metrics["max area in"]),
                "sum_area_in": 0.0 if maybe_float(metrics.get("sum area in")) is None else float(metrics["sum area in"]),
                "max_turn_sweep": 0.0 if maybe_float(metrics.get("max turn sweep")) is None else float(metrics["max turn sweep"]),
            }
        )

    if not studies:
        raise FileNotFoundError(f"No scalar-error study summaries found in {DATA_DIR}")

    studies.sort(key=lambda item: item["study_index"])
    study_indices = [item["study_index"] for item in studies]

    panel_specs = [
        ("|Scalar Error| / Sum Turn Area", [safe_ratio(item["abs_error"], item["sum_turn_area"]) for item in studies]),
        ("|Scalar Error| / Max Turn Area", [safe_ratio(item["abs_error"], item["max_turn_area"]) for item in studies]),
        ("|Scalar Error| / Max Area In", [safe_ratio(item["abs_error"], item["max_area_in"]) for item in studies]),
        ("|Scalar Error| / Sum Area In", [safe_ratio(item["abs_error"], item["sum_area_in"]) for item in studies]),
        ("|Scalar Error| / Max Turn Sweep", [safe_ratio(item["abs_error"], item["max_turn_sweep"]) for item in studies]),
    ]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(len(panel_specs), 1, figsize=(11, 16), sharex=True)

    for ax, (title, ratio_values) in zip(axes, panel_specs):
        valid_points = [
            (study_index, ratio_value)
            for study_index, ratio_value in zip(study_indices, ratio_values)
            if ratio_value is not None
        ]
        if valid_points:
            x_values = [point[0] for point in valid_points]
            y_values = [point[1] for point in valid_points]
            ax.plot(x_values, y_values, marker="o", linewidth=1.8, color="#2563eb")
            for x_value, y_value in valid_points:
                ax.annotate(
                    str(int(x_value)),
                    (x_value, y_value),
                    textcoords="offset points",
                    xytext=(0, 6),
                    ha="center",
                    fontsize=8,
                )
            ax.set_yscale("log")
        ax.set_title(title)
        ax.set_ylabel("Normalized Error")
        ax.grid(True, alpha=0.3, which="both")

    axes[-1].set_xlabel("Study Index")

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
