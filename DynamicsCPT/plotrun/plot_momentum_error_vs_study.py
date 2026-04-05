import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "ThreeP05_mom_sum"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "momentum_error_vs_study.png"


def summary_paths() -> list[Path]:
    return sorted(
        path
        for path in DATA_DIR.glob("*_summary.csv")
        if not path.name.endswith("_frame_timing_summary.csv")
    )


def load_metrics(path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            metric = (row.get("metric") or "").strip()
            value = (row.get("value") or "").strip()
            if metric:
                metrics[metric] = value
    return metrics


def parse_study_index(path: Path) -> int:
    stem = path.stem.replace("_summary", "")
    return int(stem.split("_")[-1])


def maybe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def main() -> None:
    studies: list[tuple[int, float]] = []

    for path in summary_paths():
        metrics = load_metrics(path)
        momentum_error = maybe_float(metrics.get("momentum error mag"))
        if momentum_error is None:
            if metrics.get("collision status") == "no collision":
                momentum_error = 0.0
            else:
                continue
        studies.append((parse_study_index(path), float(momentum_error)))

    if not studies:
        raise FileNotFoundError(f"No usable study summaries found in {DATA_DIR}")

    studies.sort(key=lambda item: item[0])
    study_indices = [item[0] for item in studies]
    momentum_errors = [item[1] for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(study_indices, momentum_errors, marker="o", linewidth=1.8, color="#2563eb")
    ax.axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")

    for study_index, momentum_error in zip(study_indices, momentum_errors):
        ax.annotate(
            str(study_index),
            (study_index, momentum_error),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
        )

    ax.set_title("Vector Momentum Error vs Study")
    ax.set_xlabel("Study Index")
    ax.set_ylabel("Momentum Error Magnitude")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
