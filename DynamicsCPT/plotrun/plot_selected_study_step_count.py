import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
STUDY_INDEX = 35
SUBSTEPS_PER_FRAME = 5
OUTPUT_FILE = PLOTS_DIR / f"tpocl_{STUDY_INDEX}_step_count.png"


def trace_path(study_index: int) -> Path:
    return DATA_DIR / f"tpocl_{study_index}.csv"


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    path = trace_path(STUDY_INDEX)
    if not path.exists():
        raise FileNotFoundError(f"No trace file found for study {STUDY_INDEX}: {path}")

    rows = load_rows(path)
    if not rows:
        raise FileNotFoundError(f"No trace rows found in {path}")

    time_values = [float(row["time"]) for row in rows]
    step_counts = list(range(1, len(rows) + 1))
    frame_counts = [step_count / SUBSTEPS_PER_FRAME for step_count in step_counts]
    contact_step_counts = [
        step_count if int(float(row.get("active_contact_count", "0"))) > 0 else None
        for step_count, row in zip(step_counts, rows)
    ]
    contact_frame_counts = [
        frame_count if int(float(row.get("active_contact_count", "0"))) > 0 else None
        for frame_count, row in zip(frame_counts, rows)
    ]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    axes[0].plot(time_values, step_counts, linewidth=2, color="#2563eb")
    axes[0].set_title(f"Study {STUDY_INDEX}: Cumulative Recorded Steps vs Time")
    axes[0].set_ylabel("Recorded Steps")
    axes[0].grid(True, alpha=0.3)
    ax0_frames = axes[0].twinx()
    ax0_frames.set_ylabel("Equivalent Outer Frames")
    ax0_frames.set_ylim(
        axes[0].get_ylim()[0] / SUBSTEPS_PER_FRAME,
        axes[0].get_ylim()[1] / SUBSTEPS_PER_FRAME,
    )

    contact_times = [
        time_value
        for time_value, contact_step_count in zip(time_values, contact_step_counts)
        if contact_step_count is not None
    ]
    contact_counts = [
        contact_step_count
        for contact_step_count in contact_step_counts
        if contact_step_count is not None
    ]
    axes[1].plot(time_values, step_counts, linewidth=1.5, color="#94a3b8", label="All recorded steps")
    if contact_times:
        axes[1].scatter(contact_times, contact_counts, s=10, color="#dc2626", label="Contact-active steps")
    axes[1].set_title(f"Study {STUDY_INDEX}: Contact-Active Steps Within Total Recorded Steps")
    axes[1].set_xlabel("Time")
    axes[1].set_ylabel("Recorded Steps")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    ax1_frames = axes[1].twinx()
    ax1_frames.set_ylabel("Equivalent Outer Frames")
    ax1_frames.set_ylim(
        axes[1].get_ylim()[0] / SUBSTEPS_PER_FRAME,
        axes[1].get_ylim()[1] / SUBSTEPS_PER_FRAME,
    )

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
