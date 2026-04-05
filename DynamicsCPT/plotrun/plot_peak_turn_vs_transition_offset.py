import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "peak_turn_vs_transition_offset.png"
EXCLUDED_STUDIES = {0}


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


def main() -> None:
    studies: list[dict[str, float]] = []

    for summary_path in summary_paths():
        metrics = load_metrics(summary_path)
        study_index = parse_study_index(summary_path)
        if study_index in EXCLUDED_STUDIES:
            continue

        scalar_error = maybe_float(metrics.get("scalar total error"))
        if scalar_error is None:
            if metrics.get("collision status") == "no collision":
                scalar_error = 0.0
            else:
                continue

        trace_path = trace_path_for_summary(summary_path)
        if not trace_path.exists():
            continue
        rows = load_rows(trace_path)
        if not rows:
            continue

        turn_values = [float(row.get("step_turn_area", "0") or 0.0) for row in rows]
        time_values = [float(row.get("time", "0") or 0.0) for row in rows]
        if not turn_values:
            continue
        peak_turn_index = max(range(len(turn_values)), key=lambda idx: turn_values[idx])

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

        studies.append(
            {
                "study_index": float(study_index),
                "abs_error": abs(float(scalar_error)),
                "time_offset": time_values[peak_turn_index] - time_values[transition_index],
            }
        )

    if not studies:
        raise FileNotFoundError(f"No usable study traces found in {DATA_DIR}")

    studies.sort(key=lambda item: item["study_index"])
    study_indices = [item["study_index"] for item in studies]
    abs_error_values = [item["abs_error"] for item in studies]
    time_offsets = [item["time_offset"] for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(10, 9))

    axes[0].plot(study_indices, time_offsets, marker="o", linewidth=1.8, color="#2563eb")
    for study_index, offset in zip(study_indices, time_offsets):
        axes[0].annotate(
            str(int(study_index)),
            (study_index, offset),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
        )
    axes[0].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    axes[0].set_title("Peak-Turn Time Minus Transition Time vs Study")
    axes[0].set_xlabel("Study Index")
    axes[0].set_ylabel("Peak Turn Time - Transition Time")
    axes[0].grid(True, alpha=0.3)

    axes[1].scatter(time_offsets, abs_error_values, c=study_indices, cmap="magma", s=75)
    axes[1].plot(time_offsets, abs_error_values, color="#64748b", linewidth=1.4, alpha=0.8)
    for study_index, offset, abs_error in zip(study_indices, time_offsets, abs_error_values):
        axes[1].annotate(
            str(int(study_index)),
            (offset, abs_error),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
        )
    axes[1].set_yscale("log")
    axes[1].set_title("|Scalar Error| vs Peak/Transition Time Offset")
    axes[1].set_xlabel("Peak Turn Time - Transition Time")
    axes[1].set_ylabel("|Scalar Momentum Error|")
    axes[1].grid(True, alpha=0.3, which="both")

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
