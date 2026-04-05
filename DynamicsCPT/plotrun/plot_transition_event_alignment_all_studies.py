import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "transition_event_alignment_all_studies.png"
EXCLUDED_STUDIES = {0}
ANNOTATION_FONT_SIZE = 7


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


def first_difference(values: list[float]) -> list[float]:
    if not values:
        return []
    differences = [0.0]
    for index in range(1, len(values)):
        differences.append(values[index] - values[index - 1])
    return differences


def main() -> None:
    studies: list[dict[str, float | int]] = []

    for summary_path in summary_paths():
        study_index = parse_study_index(summary_path)
        if study_index in EXCLUDED_STUDIES:
            continue

        metrics = load_metrics(summary_path)
        initial_abs_p_sum = maybe_float(metrics.get("initial |p| sum"))
        scalar_total_error = maybe_float(metrics.get("scalar total error"))
        if initial_abs_p_sum is None or scalar_total_error is None:
            continue

        trace_path = trace_path_for_summary(summary_path)
        if not trace_path.exists():
            continue

        rows = load_rows(trace_path)
        if not rows:
            continue

        time_values = [float(row.get("time", "0") or 0.0) for row in rows]
        overlap_values = [float(row.get("current_area", "0") or 0.0) for row in rows]
        turn_values = [float(row.get("step_turn_area", "0") or 0.0) for row in rows]
        error_values = scalar_error_series(rows, initial_abs_p_sum)
        error_step_values = first_difference(error_values)

        transition_index = next(
            (
                index
                for index in range(1, len(rows))
                if (rows[index - 1].get("phase") or "").strip() == "inbound"
                and (rows[index].get("phase") or "").strip() == "outbound"
            ),
            None,
        )
        if transition_index is None:
            continue

        peak_overlap_index = max(range(len(overlap_values)), key=lambda idx: overlap_values[idx])
        peak_turn_index = max(range(len(turn_values)), key=lambda idx: turn_values[idx])

        studies.append(
            {
                "study_index": study_index,
                "transition_time": time_values[transition_index],
                "peak_overlap_time": time_values[peak_overlap_index],
                "peak_turn_time": time_values[peak_turn_index],
                "peak_overlap_offset": time_values[peak_overlap_index] - time_values[transition_index],
                "peak_turn_offset": time_values[peak_turn_index] - time_values[transition_index],
                "transition_error_step": error_step_values[transition_index],
                "peak_overlap_error_step": error_step_values[peak_overlap_index],
                "peak_turn_error_step": error_step_values[peak_turn_index],
                "abs_scalar_error": abs(scalar_total_error),
            }
        )

    if not studies:
        raise FileNotFoundError(f"No usable study traces found in {DATA_DIR}")

    studies.sort(key=lambda item: int(item["study_index"]))
    study_indices = [int(item["study_index"]) for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex="col")

    axes[0, 0].plot(
        study_indices,
        [float(item["transition_time"]) for item in studies],
        marker="o",
        linewidth=1.8,
        color="#2563eb",
        label="Transition time",
    )
    axes[0, 0].plot(
        study_indices,
        [float(item["peak_overlap_time"]) for item in studies],
        marker="s",
        linewidth=1.8,
        color="#b45309",
        label="Peak overlap time",
    )
    axes[0, 0].plot(
        study_indices,
        [float(item["peak_turn_time"]) for item in studies],
        marker="^",
        linewidth=1.8,
        color="#059669",
        label="Peak turn time",
    )
    for study_index, item in zip(study_indices, studies):
        axes[0, 0].annotate(
            str(study_index),
            (study_index, float(item["peak_turn_time"])),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=ANNOTATION_FONT_SIZE,
        )
    axes[0, 0].set_title("Transition And Peak Event Times")
    axes[0, 0].set_ylabel("Time")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend()

    axes[0, 1].plot(
        study_indices,
        [float(item["peak_overlap_offset"]) for item in studies],
        marker="s",
        linewidth=1.8,
        color="#b45309",
        label="Peak overlap - transition",
    )
    axes[0, 1].plot(
        study_indices,
        [float(item["peak_turn_offset"]) for item in studies],
        marker="^",
        linewidth=1.8,
        color="#059669",
        label="Peak turn - transition",
    )
    axes[0, 1].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    for study_index, item in zip(study_indices, studies):
        axes[0, 1].annotate(
            str(study_index),
            (study_index, float(item["peak_turn_offset"])),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=ANNOTATION_FONT_SIZE,
        )
    axes[0, 1].set_title("Event Timing Relative To Transition")
    axes[0, 1].set_ylabel("Time Offset")
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend()

    axes[1, 0].plot(
        study_indices,
        [float(item["transition_error_step"]) for item in studies],
        marker="o",
        linewidth=1.8,
        color="#2563eb",
        label="At transition row",
    )
    axes[1, 0].plot(
        study_indices,
        [float(item["peak_overlap_error_step"]) for item in studies],
        marker="s",
        linewidth=1.8,
        color="#b45309",
        label="At peak overlap row",
    )
    axes[1, 0].plot(
        study_indices,
        [float(item["peak_turn_error_step"]) for item in studies],
        marker="^",
        linewidth=1.8,
        color="#059669",
        label="At peak turn row",
    )
    axes[1, 0].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    for study_index, item in zip(study_indices, studies):
        axes[1, 0].annotate(
            str(study_index),
            (study_index, float(item["peak_turn_error_step"])),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=ANNOTATION_FONT_SIZE,
        )
    axes[1, 0].set_title("Scalar Error Increment At Key Rows")
    axes[1, 0].set_xlabel("Study Index")
    axes[1, 0].set_ylabel("Per-Step Scalar Error Change")
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend()

    axes[1, 1].plot(
        study_indices,
        [float(item["abs_scalar_error"]) for item in studies],
        marker="o",
        linewidth=1.8,
        color="#7c3aed",
    )
    for study_index, item in zip(study_indices, studies):
        axes[1, 1].annotate(
            str(study_index),
            (study_index, float(item["abs_scalar_error"])),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=ANNOTATION_FONT_SIZE,
        )
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_title("Final |Scalar Momentum Error|")
    axes[1, 1].set_xlabel("Study Index")
    axes[1, 1].set_ylabel("|Scalar Momentum Error|")
    axes[1, 1].grid(True, alpha=0.3, which="both")

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
