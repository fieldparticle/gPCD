import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "study_28_29_transition_compare.png"
STUDIES = [28, 29]


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


def main() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(4, 1, figsize=(12, 12), sharex=True)
    colors = {28: "#2563eb", 29: "#dc2626"}

    for study_index in STUDIES:
        trace = trace_path(study_index)
        summary = summary_path(study_index)
        if not trace.exists() or not summary.exists():
            continue

        rows = load_rows(trace)
        metrics = load_metrics(summary)
        if not rows or "initial |p| sum" not in metrics:
            continue

        color = colors[study_index]
        time_values = [float(row["time"]) for row in rows]
        area_values = [float(row["current_area"]) for row in rows]
        turn_values = [float(row["step_turn_area"]) for row in rows]
        error_values = scalar_error_series(rows, float(metrics["initial |p| sum"]))
        phase_values = [
            1.0 if (row.get("phase") or "").strip() == "outbound" else 0.0
            for row in rows
        ]

        axes[0].plot(time_values, area_values, linewidth=2, color=color, label=f"study {study_index}")
        axes[1].plot(time_values, turn_values, linewidth=2, color=color, label=f"study {study_index}")
        axes[2].plot(time_values, error_values, linewidth=2, color=color, label=f"study {study_index}")
        axes[3].plot(time_values, phase_values, linewidth=2, color=color, label=f"study {study_index}")

        peak_area_index = max(range(len(area_values)), key=lambda idx: area_values[idx])
        peak_turn_index = max(range(len(turn_values)), key=lambda idx: turn_values[idx])
        axes[0].annotate(
            f"{study_index} peak A",
            (time_values[peak_area_index], area_values[peak_area_index]),
            textcoords="offset points",
            xytext=(4, 6),
            fontsize=8,
            color=color,
        )
        axes[1].annotate(
            f"{study_index} peak T",
            (time_values[peak_turn_index], turn_values[peak_turn_index]),
            textcoords="offset points",
            xytext=(4, 6),
            fontsize=8,
            color=color,
        )

    axes[0].set_title("Current Area: Study 28 vs Study 29")
    axes[0].set_ylabel("current_area")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].set_title("Turning Area: Study 28 vs Study 29")
    axes[1].set_ylabel("step_turn_area")
    axes[1].grid(True, alpha=0.3)

    axes[2].set_title("Scalar Error Progression")
    axes[2].set_ylabel("scalar error")
    axes[2].grid(True, alpha=0.3)

    axes[3].set_title("Phase Switch (0 = inbound/free, 1 = outbound)")
    axes[3].set_xlabel("Time")
    axes[3].set_ylabel("phase flag")
    axes[3].set_yticks([0.0, 1.0])
    axes[3].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
