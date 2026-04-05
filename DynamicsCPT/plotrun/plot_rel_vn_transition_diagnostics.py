import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "rel_vn_transition_diagnostics.png"
STUDIES = [35, 36, 39]
WINDOW_RADIUS = 8


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
            scalar_total += math.hypot(float(px_raw), float(py_raw))

            internal_raw = row.get(f"p{index}_internal_p", "")
            if internal_raw not in ("", None):
                scalar_total += float(internal_raw)
        error_values.append(scalar_total - initial_abs_p_sum)
    return error_values


def rel_vn_series(rows: list[dict[str, str]]) -> list[float]:
    values: list[float] = []
    for row in rows:
        p0_x_raw = row.get("p0_x", "")
        p0_y_raw = row.get("p0_y", "")
        p1_x_raw = row.get("p1_x", "")
        p1_y_raw = row.get("p1_y", "")
        p0_vx_raw = row.get("p0_vx", "")
        p0_vy_raw = row.get("p0_vy", "")
        p1_vx_raw = row.get("p1_vx", "")
        p1_vy_raw = row.get("p1_vy", "")

        if any(value in ("", None) for value in (p0_x_raw, p0_y_raw, p1_x_raw, p1_y_raw, p0_vx_raw, p0_vy_raw, p1_vx_raw, p1_vy_raw)):
            values.append(0.0)
            continue

        dx = float(p1_x_raw) - float(p0_x_raw)
        dy = float(p1_y_raw) - float(p0_y_raw)
        distance = math.hypot(dx, dy)
        if distance <= 1.0e-15:
            nx = 1.0
            ny = 0.0
        else:
            nx = dx / distance
            ny = dy / distance

        rel_vx = float(p1_vx_raw) - float(p0_vx_raw)
        rel_vy = float(p1_vy_raw) - float(p0_vy_raw)
        values.append(rel_vx * nx + rel_vy * ny)
    return values


def main() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
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
        rel_vn_values = rel_vn_series(rows)
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

        axes[0].plot(local_steps, rel_vn_values[start:end], marker="o", linewidth=2, color=color, label=f"study {study_index}")
        axes[1].plot(local_steps, error_step_delta[start:end], marker="o", linewidth=2, color=color, label=f"study {study_index}")
        axes[2].step(local_steps, phase_values[start:end], where="mid", linewidth=2, color=color, label=f"study {study_index}")

        for axis in axes:
            axis.axvline(transition_index, color=color, linestyle="--", alpha=0.7)

    axes[0].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    axes[0].set_title("Relative Normal Velocity Around Inbound/Outbound Transition")
    axes[0].set_ylabel("rel_vn")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    axes[1].set_title("Per-Step Scalar Error Change Around Transition")
    axes[1].set_ylabel("delta scalar error")
    axes[1].grid(True, alpha=0.3)

    axes[2].set_title("Phase Window (0 = inbound, 1 = outbound)")
    axes[2].set_xlabel("Trace Row Index")
    axes[2].set_ylabel("phase flag")
    axes[2].set_yticks([0.0, 1.0])
    axes[2].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
