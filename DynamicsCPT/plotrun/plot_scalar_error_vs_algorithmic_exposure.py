import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "scalar_error_vs_algorithmic_exposure.png"


def summary_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("tpocl_*_summary.csv"))


def trace_path_for_summary(summary_path: Path) -> Path:
    return summary_path.with_name(summary_path.name.replace("_summary", ""))


def load_metrics(path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            metric = (row.get("metric") or "").strip()
            value = (row.get("value") or "").strip()
            if metric:
                metrics[metric] = value
    return metrics


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_study_index(path: Path) -> int:
    stem = path.stem.replace("_summary", "")
    return int(stem.split("_")[-1])


def maybe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def main() -> None:
    studies: list[dict[str, float]] = []

    for summary_path in summary_paths():
        metrics = load_metrics(summary_path)
        study_index = parse_study_index(summary_path)

        scalar_error = maybe_float(metrics.get("scalar total error"))
        if scalar_error is None:
            if metrics.get("collision status") == "no collision":
                scalar_error = 0.0
            else:
                continue

        trace_path = trace_path_for_summary(summary_path)
        if not trace_path.exists():
            continue
        rows = load_rows(trace_path)
        if not rows:
            continue

        contact_rows = [row for row in rows if int(float(row.get("active_contact_count", "0"))) > 0]
        duration = 0.0
        inbound_count = 0
        outbound_count = 0
        if contact_rows:
            duration = float(contact_rows[-1]["time"]) - float(contact_rows[0]["time"])
            for row in contact_rows:
                phase = (row.get("phase") or "").strip()
                if phase == "inbound":
                    inbound_count += 1
                elif phase == "outbound":
                    outbound_count += 1

        studies.append(
            {
                "study_index": float(study_index),
                "abs_error": abs(float(scalar_error)),
                "step_count": float(len(rows)),
                "duration": duration,
                "count_gap": float(abs(inbound_count - outbound_count)),
            }
        )

    if not studies:
        raise FileNotFoundError(f"No scalar-error study summaries found in {DATA_DIR}")

    studies.sort(key=lambda item: item["study_index"])
    study_indices = [item["study_index"] for item in studies]
    error_values = [item["abs_error"] for item in studies]
    step_counts = [item["step_count"] for item in studies]
    durations = [item["duration"] for item in studies]
    count_gaps = [item["count_gap"] for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(11, 12))

    axes[0].scatter(step_counts, error_values, c=study_indices, cmap="viridis", s=70)
    axes[0].plot(step_counts, error_values, color="#64748b", linewidth=1.4, alpha=0.8)
    axes[0].set_yscale("log")
    axes[0].set_title("Scalar Error Magnitude vs Recorded Step Count")
    axes[0].set_xlabel("Recorded Step Count")
    axes[0].set_ylabel("|Scalar Momentum Error|")
    axes[0].grid(True, alpha=0.3, which="both")

    axes[1].scatter(durations, error_values, c=study_indices, cmap="plasma", s=70)
    axes[1].plot(durations, error_values, color="#64748b", linewidth=1.4, alpha=0.8)
    axes[1].set_yscale("log")
    axes[1].set_title("Scalar Error Magnitude vs Contact Duration")
    axes[1].set_xlabel("Contact Duration")
    axes[1].set_ylabel("|Scalar Momentum Error|")
    axes[1].grid(True, alpha=0.3, which="both")

    axes[2].scatter(count_gaps, error_values, c=study_indices, cmap="magma", s=70)
    axes[2].plot(count_gaps, error_values, color="#64748b", linewidth=1.4, alpha=0.8)
    axes[2].set_yscale("log")
    axes[2].set_title("Scalar Error Magnitude vs |Inbound Count - Outbound Count|")
    axes[2].set_xlabel("|Inbound Count - Outbound Count|")
    axes[2].set_ylabel("|Scalar Momentum Error|")
    axes[2].grid(True, alpha=0.3, which="both")

    for ax, x_values in zip(axes, [step_counts, durations, count_gaps]):
        for study_index, x_value, error_value in zip(study_indices, x_values, error_values):
            ax.annotate(
                str(int(study_index)),
                (x_value, error_value),
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
