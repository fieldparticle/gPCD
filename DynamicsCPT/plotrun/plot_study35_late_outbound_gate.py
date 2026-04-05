import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "study35_late_outbound_gate.png"
STUDY_INDEX = 35
TAIL_ROWS = 120


def trace_path(study_index: int) -> Path:
    return DATA_DIR / f"tpocl_{study_index}.csv"


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    path = trace_path(STUDY_INDEX)
    if not path.exists():
        raise FileNotFoundError(f"Trace file not found: {path}")

    rows = load_rows(path)
    if not rows:
        raise FileNotFoundError(f"No rows found in {path}")

    outbound_indices = [
        index for index, row in enumerate(rows) if (row.get("phase") or "").strip() == "outbound"
    ]
    if not outbound_indices:
        raise ValueError(f"No outbound rows found for study {STUDY_INDEX}")

    tail_indices = outbound_indices[-TAIL_ROWS:]
    area_values = [float(rows[index].get("current_area", "0") or 0.0) for index in tail_indices]
    j_values = [float(rows[index].get("current_J", "0") or 0.0) for index in tail_indices]
    turn_values = [float(rows[index].get("step_turn_area", "0") or 0.0) for index in tail_indices]
    time_values = [float(rows[index].get("time", "0") or 0.0) for index in tail_indices]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)

    axes[0].plot(tail_indices, area_values, marker="o", linewidth=1.8, color="#2563eb")
    axes[0].set_title(f"Study {STUDY_INDEX} Late Outbound Current Area")
    axes[0].set_ylabel("current_area")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(tail_indices, j_values, marker="o", linewidth=1.8, color="#dc2626")
    axes[1].set_title(f"Study {STUDY_INDEX} Late Outbound Current J")
    axes[1].set_ylabel("current_J")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(tail_indices, turn_values, marker="o", linewidth=1.8, color="#059669")
    axes[2].set_title(f"Study {STUDY_INDEX} Late Outbound Turning Area")
    axes[2].set_xlabel("Trace Row Index")
    axes[2].set_ylabel("step_turn_area")
    axes[2].grid(True, alpha=0.3)

    for axis, values in zip(axes, [area_values, j_values, turn_values]):
        for row_index, value in zip(tail_indices, values):
            axis.annotate(
                str(row_index),
                (row_index, value),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=7,
            )

    fig.suptitle(
        f"Study {STUDY_INDEX} Late Outbound Rows ({time_values[0]:.3f} to {time_values[-1]:.3f})",
        y=0.995,
    )
    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
