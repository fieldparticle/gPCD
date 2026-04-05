import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "collision_duration_by_study.png"


def trace_paths() -> list[Path]:
    return sorted(
        path
        for path in DATA_DIR.glob("tpocl_*.csv")
        if not path.stem.endswith("_summary")
    )


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_summary_metrics(path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    summary_path = path.with_name(f"{path.stem}_summary{path.suffix}")
    if not summary_path.exists():
        return metrics

    with summary_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            metric = (row.get("metric") or "").strip()
            value = (row.get("value") or "").strip()
            if metric:
                metrics[metric] = value
    return metrics


def parse_y_from_init_pos(value: str) -> float:
    _, y_str = value.strip("()").split(",")
    return float(y_str.strip())


def main() -> None:
    studies: list[dict[str, float | str]] = []

    for path in trace_paths():
        rows = load_rows(path)
        if not rows:
            continue

        contact_rows = [row for row in rows if int(float(row.get("active_contact_count", "0"))) > 0]
        if contact_rows:
            start_time = float(contact_rows[0]["time"])
            end_time = float(contact_rows[-1]["time"])
            duration = end_time - start_time
        else:
            start_time = 0.0
            end_time = 0.0
            duration = 0.0

        metrics = load_summary_metrics(path)
        init_pos = metrics.get("particle 01 init pos")
        if not init_pos:
            continue

        studies.append(
            {
                "label": path.stem,
                "y_init": parse_y_from_init_pos(init_pos),
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
            }
        )

    if not studies:
        raise FileNotFoundError(f"No usable study trace CSV files found in {DATA_DIR}")

    studies.sort(key=lambda study: float(study["y_init"]))
    y_values = [float(study["y_init"]) for study in studies]
    durations = [float(study["duration"]) for study in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    axes[0].bar(y_values, durations, width=0.18, color="#2563eb", alpha=0.85)
    for study in studies:
        axes[0].annotate(
            str(study["label"]),
            (float(study["y_init"]), float(study["duration"])),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
        )
    axes[0].set_title("Collision Duration vs Initial Particle 1 Y")
    axes[0].set_ylabel("Duration")
    axes[0].grid(True, axis="y", alpha=0.3)

    for study in studies:
        y_value = float(study["y_init"])
        start_time = float(study["start_time"])
        end_time = float(study["end_time"])
        axes[1].hlines(y=y_value, xmin=start_time, xmax=end_time, linewidth=4, color="#b45309")
        axes[1].plot([start_time, end_time], [y_value, y_value], "o", color="#b45309")
        axes[1].annotate(
            str(study["label"]),
            (end_time, y_value),
            textcoords="offset points",
            xytext=(6, 0),
            va="center",
        )
    axes[1].set_title("Collision Time Window by Study")
    axes[1].set_xlabel("Time")
    axes[1].set_ylabel("Initial Particle 1 Y")
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    plt.show()


if __name__ == "__main__":
    main()
