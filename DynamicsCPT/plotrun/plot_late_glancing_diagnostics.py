import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "late_glancing_diagnostics.png"
STUDIES = [16, 17, 18, 19]


def trace_path(study_index: int) -> Path:
    return DATA_DIR / f"tpocl_{study_index}.csv"


def summary_path(study_index: int) -> Path:
    return DATA_DIR / f"tpocl_{study_index}_summary.csv"


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_metrics(path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            metric = (row.get("metric") or "").strip()
            value = (row.get("value") or "").strip()
            if metric:
                metrics[metric] = value
    return metrics


def numeric_series(rows: list[dict[str, str]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        raw = row.get(key, "")
        values.append(float(raw) if raw not in ("", None) else 0.0)
    return values


def scalar_error_series(rows: list[dict[str, str]], initial_abs_p_sum: float) -> list[float]:
    error_values: list[float] = []
    for row in rows:
        scalar_total = 0.0
        for index in range(4):
            px_raw = row.get(f"p{index}_px", "")
            py_raw = row.get(f"p{index}_py", "")
            if px_raw in ("", None) or py_raw in ("", None):
                continue
            scalar_total += (float(px_raw) ** 2 + float(py_raw) ** 2) ** 0.5

            internal_raw = row.get(f"p{index}_internal_p", "")
            if internal_raw not in ("", None):
                scalar_total += float(internal_raw)
        error_values.append(scalar_total - initial_abs_p_sum)
    return error_values


def inbound_outbound_gap(rows: list[dict[str, str]]) -> list[int]:
    gap_values: list[int] = []
    inbound = 0
    outbound = 0
    for row in rows:
        active_contacts = int(float(row.get("active_contact_count", "0")))
        if active_contacts > 0:
            phase = (row.get("phase") or "").strip()
            if phase == "inbound":
                inbound += 1
            elif phase == "outbound":
                outbound += 1
        gap_values.append(inbound - outbound)
    return gap_values


def main() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True)
    cmap = plt.get_cmap("tab10", len(STUDIES))

    for index, study_index in enumerate(STUDIES):
        trace = trace_path(study_index)
        summary = summary_path(study_index)
        if not trace.exists() or not summary.exists():
            continue

        rows = load_rows(trace)
        metrics = load_metrics(summary)
        if not rows or "initial |p| sum" not in metrics:
            continue

        color = cmap(index)
        time_values = numeric_series(rows, "time")
        overlap_values = numeric_series(rows, "current_area")
        turning_values = numeric_series(rows, "step_turn_area")
        error_values = scalar_error_series(rows, float(metrics["initial |p| sum"]))
        gap_values = inbound_outbound_gap(rows)
        final_error = float(metrics.get("scalar total error", "0.0"))

        label = f"study {study_index} ({final_error:.1e})"
        axes[0, 0].plot(time_values, overlap_values, linewidth=2, color=color, label=label)
        axes[0, 1].plot(time_values, turning_values, linewidth=2, color=color, label=label)
        axes[1, 0].plot(time_values, error_values, linewidth=2, color=color, label=label)
        axes[1, 1].plot(time_values, gap_values, linewidth=2, color=color, label=label)

    axes[0, 0].set_title("Current Overlap Area")
    axes[0, 0].set_ylabel("current_area")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend()

    axes[0, 1].set_title("Step Turning Area")
    axes[0, 1].set_ylabel("step_turn_area")
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].set_title("Scalar Error Progression")
    axes[1, 0].set_xlabel("Time")
    axes[1, 0].set_ylabel("scalar error")
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].set_title("Inbound - Outbound Active-Step Count")
    axes[1, 1].set_xlabel("Time")
    axes[1, 1].set_ylabel("count gap")
    axes[1, 1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
