import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "sample_diff_and_scalar_error.png"


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
        scalar_error = maybe_float(metrics.get("scalar total error"))

        if scalar_error is None:
            if metrics.get("collision status") == "no collision":
                scalar_error = 0.0
            else:
                continue

        studies.append(
            {
                "study_index": float(study_index),
                "sample_diff": 0.0 if samples_in is None or samples_out is None else float(samples_in - samples_out),
                "scalar_error": float(scalar_error),
                "abs_scalar_error": abs(float(scalar_error)),
            }
        )

    if not studies:
        raise FileNotFoundError(f"No usable study summaries found in {DATA_DIR}")

    studies.sort(key=lambda item: item["study_index"])
    study_indices = [item["study_index"] for item in studies]
    sample_diffs = [item["sample_diff"] for item in studies]
    scalar_errors = [item["scalar_error"] for item in studies]
    abs_scalar_errors = [item["abs_scalar_error"] for item in studies]
    abs_sample_diffs = [abs(value) for value in sample_diffs]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    axes[0, 0].plot(study_indices, sample_diffs, marker="o", linewidth=1.8, color="#2563eb")
    axes[0, 0].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    axes[0, 0].set_title("Inbound - Outbound Sample Count Difference")
    axes[0, 0].set_ylabel("Samples In - Samples Out")
    axes[0, 0].grid(True, alpha=0.3)

    axes[1, 0].plot(study_indices, abs_scalar_errors, marker="o", linewidth=1.8, color="#dc2626")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_title("Ending Scalar Momentum Error Magnitude vs Study")
    axes[1, 0].set_xlabel("Study Index")
    axes[1, 0].set_ylabel("|Scalar Momentum Error|")
    axes[1, 0].grid(True, alpha=0.3, which="both")

    for study_index, sample_diff in zip(study_indices, sample_diffs):
        axes[0, 0].annotate(
            str(int(study_index)),
            (study_index, sample_diff),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
        )

    for study_index, abs_scalar_error in zip(study_indices, abs_scalar_errors):
        axes[1, 0].annotate(
            str(int(study_index)),
            (study_index, abs_scalar_error),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
        )

    axes[0, 1].scatter(sample_diffs, scalar_errors, color="#7c3aed", s=55)
    axes[0, 1].plot(sample_diffs, scalar_errors, color="#a78bfa", linewidth=1.2, alpha=0.8)
    axes[0, 1].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    axes[0, 1].axvline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    axes[0, 1].set_title("Signed Scalar Error vs Signed Sample Difference")
    axes[0, 1].set_xlabel("Samples In - Samples Out")
    axes[0, 1].set_ylabel("Scalar Momentum Error")
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 1].scatter(abs_sample_diffs, abs_scalar_errors, color="#059669", s=55)
    axes[1, 1].plot(abs_sample_diffs, abs_scalar_errors, color="#34d399", linewidth=1.2, alpha=0.8)
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_title("|Scalar Error| vs |Sample Difference|")
    axes[1, 1].set_xlabel("|Samples In - Samples Out|")
    axes[1, 1].set_ylabel("|Scalar Momentum Error|")
    axes[1, 1].grid(True, alpha=0.3, which="both")

    for study_index, sample_diff, scalar_error in zip(study_indices, sample_diffs, scalar_errors):
        axes[0, 1].annotate(
            str(int(study_index)),
            (sample_diff, scalar_error),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
        )

    for study_index, abs_sample_diff, abs_scalar_error in zip(study_indices, abs_sample_diffs, abs_scalar_errors):
        axes[1, 1].annotate(
            str(int(study_index)),
            (abs_sample_diff, abs_scalar_error),
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
