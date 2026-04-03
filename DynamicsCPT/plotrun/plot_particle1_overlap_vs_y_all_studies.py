import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "particle1_overlap_area_vs_y_all_studies.png"
HIGHLIGHT_STUDIES = {8, 12}
#INCLUDED_STUDIES: list[int] = [11,12,13,14, 15,16,17,18, 19, 20]
INCLUDED_STUDIES: list[int] = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
EXCLUDED_STUDIES: set[int] = set()


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


def scalar_error_series(rows: list[dict[str, str]], initial_abs_p_sum: float) -> tuple[list[float], list[float]]:
    time_values: list[float] = []
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

        time_values.append(float(row["time"]))
        error_values.append(scalar_total - initial_abs_p_sum)

    return time_values, error_values


def annotate_curve_peak(ax, x_values: list[float], y_values: list[float], text: str, color) -> None:
    if not x_values or not y_values:
        return
    peak_index = max(range(len(y_values)), key=lambda idx: y_values[idx])
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

    fig, axes = plt.subplots(3, 1, figsize=(10, 13))
    cmap = plt.get_cmap("tab20", max(len(paths), 1))

    for index, path in enumerate(paths):
        study_index = parse_study_index(path)
        if not include_study(study_index):
            continue
        rows = load_rows(path)
        if not rows:
            continue
        progress = normalized_progress(rows)
        overlap_area = numeric_series(rows, "current_area")
        turning_area = numeric_series(rows, "step_turn_area")
        color = cmap(index)
        linewidth = 2.8 if study_index in HIGHLIGHT_STUDIES else 2.0
        linestyle = "--" if study_index in HIGHLIGHT_STUDIES else "-"
        label = f"{path.stem}*" if study_index in HIGHLIGHT_STUDIES else path.stem

        axes[0].plot(
            progress,
            overlap_area,
            linewidth=linewidth,
            linestyle=linestyle,
            color=color,
            label=label,
        )
        annotate_curve_peak(axes[0], progress, overlap_area, str(study_index), color)
        axes[1].plot(
            progress,
            turning_area,
            linewidth=linewidth,
            linestyle=linestyle,
            color=color,
            label=label,
        )
        annotate_curve_peak(axes[1], progress, turning_area, str(study_index), color)

        metrics = load_summary_metrics(path)
        if "initial |p| sum" in metrics:
            error_time, error_values = scalar_error_series(rows, float(metrics["initial |p| sum"]))
            axes[2].plot(
                error_time,
                error_values,
                color=color,
                linewidth=linewidth,
                linestyle=linestyle,
                label=label,
            )

    axes[0].set_title("Particle 1 Overlap Area vs Normalized Collision Progress")
    axes[0].set_ylabel("Overlap Area")
    axes[0].grid(True, alpha=0.3)

    axes[1].set_title("Particle 1 Turning Area vs Normalized Collision Progress")
    axes[1].set_xlabel("Normalized Collision Progress")
    axes[1].set_ylabel("Turning Area")
    axes[1].grid(True, alpha=0.3)

    axes[2].set_title("Scalar Momentum Error Progression By Study")
    axes[2].set_xlabel("Time")
    axes[2].set_ylabel("Scalar Momentum Error")
    axes[2].grid(True, alpha=0.3)
    axes[2].legend(ncol=2)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    plt.show()


if __name__ == "__main__":
    main()
