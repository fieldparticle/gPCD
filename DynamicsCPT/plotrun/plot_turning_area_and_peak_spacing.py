import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "turning_area_and_peak_spacing.png"
INCLUDED_STUDIES: list[int] | None = None
EXCLUDED_STUDIES: set[int] = set()
MIN_PEAK_HEIGHT = 1.0e-12


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def numeric_series(rows: list[dict[str, str]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        raw = row.get(key, "")
        values.append(float(raw) if raw not in ("", None) else 0.0)
    return values


def normalized_progress(rows: list[dict[str, str]]) -> list[float]:
    time_values = numeric_series(rows, "time")
    if not time_values:
        return []
    start_time = time_values[0]
    end_time = time_values[-1]
    span = end_time - start_time
    if span <= 0.0:
        return [0.0 for _ in time_values]
    return [(time_value - start_time) / span for time_value in time_values]


def study_paths() -> list[Path]:
    return sorted(
        path
        for path in DATA_DIR.glob("tpocl_*.csv")
        if not path.stem.endswith("_summary") and not path.stem.endswith("_frame_timing")
    )


def parse_study_index(path: Path) -> int:
    return int(path.stem.split("_")[-1])


def include_study(study_index: int) -> bool:
    if INCLUDED_STUDIES is not None:
        return study_index in INCLUDED_STUDIES
    return study_index not in EXCLUDED_STUDIES


def find_peak_indices(values: list[float]) -> list[int]:
    if len(values) < 3:
        return []

    peak_indices: list[int] = []
    for index in range(1, len(values) - 1):
        if values[index] <= MIN_PEAK_HEIGHT:
            continue
        if values[index - 1] < values[index] and values[index] >= values[index + 1]:
            peak_indices.append(index)
    return peak_indices


def annotate_peak(ax, x_values: list[float], y_values: list[float], text: str, color) -> None:
    peak_indices = find_peak_indices(y_values)
    if not peak_indices:
        return
    peak_index = max(peak_indices, key=lambda idx: y_values[idx])
    ax.annotate(
        text,
        (x_values[peak_index], y_values[peak_index]),
        textcoords="offset points",
        xytext=(4, 6),
        va="bottom",
        fontsize=8,
        color=color,
        fontweight="bold",
    )


def main() -> None:
    paths = study_paths()
    if not paths:
        raise FileNotFoundError(f"No study trace CSV files found in {DATA_DIR}")

    paths.sort(key=parse_study_index)
    paths = [path for path in paths if include_study(parse_study_index(path))]
    if not paths:
        raise FileNotFoundError("No study traces matched the current INCLUDED_STUDIES / EXCLUDED_STUDIES filter.")

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 1, figsize=(10, 10))
    cmap = plt.get_cmap("tab20", max(len(paths), 1))
    study_peak_values: list[tuple[int, float]] = []

    for index, path in enumerate(paths):
        study_index = parse_study_index(path)
        rows = load_rows(path)
        if not rows:
            continue

        progress = normalized_progress(rows)
        turning_area = numeric_series(rows, "step_turn_area")
        color = cmap(index)
        label = f"tpocl_{study_index}"

        axes[0].plot(
            progress,
            turning_area,
            linewidth=2,
            color=color,
            label=label,
        )
        annotate_peak(axes[0], progress, turning_area, str(study_index), color)

        peak_indices = find_peak_indices(turning_area)
        if peak_indices:
            main_peak_index = max(peak_indices, key=lambda idx: turning_area[idx])
            study_peak_values.append((study_index, turning_area[main_peak_index]))

    axes[0].set_title("Turning Area vs Normalized Collision Progress")
    axes[0].set_xlabel("Normalized Collision Progress")
    axes[0].set_ylabel("Turning Area")
    axes[0].grid(True, alpha=0.3)

    if len(study_peak_values) >= 2:
        difference_indices = list(range(1, len(study_peak_values)))
        peak_differences = [
            study_peak_values[ii - 1][1] - study_peak_values[ii][1]
            for ii in range(1, len(study_peak_values))
        ]
        axes[1].plot(
            difference_indices,
            peak_differences,
            linewidth=2,
            marker="o",
            color="#2563eb",
        )
        for ii in range(1, len(study_peak_values)):
            prev_study = study_peak_values[ii - 1][0]
            next_study = study_peak_values[ii][0]
            axes[1].annotate(
                f"{prev_study}-{next_study}",
                (difference_indices[ii - 1], peak_differences[ii - 1]),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=8,
            )

    axes[1].set_title("Difference Between Main Peak Heights of Successive Studies")
    axes[1].set_xlabel("Difference Index")
    axes[1].set_ylabel("Previous Peak Height - Next Peak Height")
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
