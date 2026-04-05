import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "study_transition_zoom.png"
STUDIES = [26, 27, 28, 29, 30,31,32]
WINDOW_RADIUS = 6


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
    cmap = plt.get_cmap("tab10", max(len(STUDIES), 1))

    for color_index, study_index in enumerate(STUDIES):
        trace = trace_path(study_index)
        summary = summary_path(study_index)
        if not trace.exists() or not summary.exists():
            continue

        rows = load_rows(trace)
        metrics = load_metrics(summary)
        if not rows or "initial |p| sum" not in metrics:
            continue

        color = cmap(color_index)
        time_values = [float(row["time"]) for row in rows]
        area_values = [float(row["current_area"]) for row in rows]
        turn_values = [float(row["step_turn_area"]) for row in rows]
        error_values = scalar_error_series(rows, float(metrics["initial |p| sum"]))
        error_step_delta = [
            error_values[0] if index == 0 else error_values[index] - error_values[index - 1]
            for index in range(len(error_values))
        ]
        phase_values = [
            1.0 if (row.get("phase") or "").strip() == "outbound" else 0.0
            for row in rows
        ]

        transition_index = next(
            (
                index
                for index in range(1, len(rows))
                if (rows[index - 1].get("phase") or "").strip() == "inbound"
                and (rows[index].get("phase") or "").strip() == "outbound"
            ),
            len(rows) // 2,
        )
        start = max(0, transition_index - WINDOW_RADIUS)
        end = min(len(rows), transition_index + WINDOW_RADIUS + 1)

        local_steps = list(range(start, end))
        local_area = area_values[start:end]
        local_turn = turn_values[start:end]
        local_error_delta = error_step_delta[start:end]
        local_phase = phase_values[start:end]

        axes[0].plot(local_steps, local_area, marker="o", linewidth=2, color=color, label=f"study {study_index}")
        axes[1].plot(local_steps, local_turn, marker="o", linewidth=2, color=color, label=f"study {study_index}")
        axes[2].plot(local_steps, local_error_delta, marker="o", linewidth=2, color=color, label=f"study {study_index}")
        axes[3].step(local_steps, local_phase, where="mid", linewidth=2, color=color, label=f"study {study_index}")

        axes[0].axvline(transition_index, color=color, linestyle="--", alpha=0.6)
        axes[1].axvline(transition_index, color=color, linestyle="--", alpha=0.6)
        axes[2].axvline(transition_index, color=color, linestyle="--", alpha=0.6)
        axes[3].axvline(transition_index, color=color, linestyle="--", alpha=0.6)

    axes[0].set_title("Zoomed Current Area Around Inbound/Outbound Transition")
    axes[0].set_ylabel("current_area")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].set_title("Zoomed Turning Area Around Transition")
    axes[1].set_ylabel("step_turn_area")
    axes[1].grid(True, alpha=0.3)

    axes[2].set_title("Per-Step Scalar Error Change Around Transition")
    axes[2].set_ylabel("delta scalar error")
    axes[2].grid(True, alpha=0.3)

    axes[3].set_title("Phase Switch Window (0 = inbound, 1 = outbound)")
    axes[3].set_xlabel("Trace Row Index")
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
