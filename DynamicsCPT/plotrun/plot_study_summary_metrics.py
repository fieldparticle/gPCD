import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "study_summary_metrics.png"


def summary_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("tpocl_*_summary.csv"))


def load_metrics(path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            metric = (row.get("metric") or "").strip()
            value = (row.get("value") or "").strip()
            if metric:
                metrics[metric] = value
    return metrics


def parse_y_from_init_pos(value: str) -> float:
    _, y_str = value.strip("()").split(",")
    return float(y_str.strip())


def maybe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def main() -> None:
    paths = summary_paths()
    if not paths:
        raise FileNotFoundError(f"No study summary CSV files found in {DATA_DIR}")

    studies: list[dict[str, float | str | None]] = []
    for path in paths:
        metrics = load_metrics(path)
        init_pos = metrics.get("particle 01 init pos")
        if not init_pos:
            continue

        studies.append(
            {
                "label": path.stem.replace("_summary", ""),
                "y_init": parse_y_from_init_pos(init_pos),
                "sum_area_in": maybe_float(metrics.get("sum area in")),
                "sum_area_out": maybe_float(metrics.get("sum area out")),
                "sum_turn_area": maybe_float(metrics.get("sum turn area")),
                "sum_J_in": maybe_float(metrics.get("sum J in")),
                "scalar_error": maybe_float(metrics.get("scalar total error")),
            }
        )

    studies.sort(key=lambda study: float(study["y_init"]))
    y_values = [float(study["y_init"]) for study in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    axes[0, 0].plot(
        y_values,
        [0.0 if study["sum_area_in"] is None else float(study["sum_area_in"]) for study in studies],
        marker="o",
        linewidth=2,
        color="#b45309",
        label="Sum Area In",
    )
    axes[0, 0].plot(
        y_values,
        [0.0 if study["sum_area_out"] is None else float(study["sum_area_out"]) for study in studies],
        marker="s",
        linewidth=2,
        color="#2563eb",
        label="Sum Area Out",
    )
    for study in studies:
        axes[0, 0].annotate(
            str(study["label"]),
            (float(study["y_init"]), 0.0 if study["sum_area_in"] is None else float(study["sum_area_in"])),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )
    axes[0, 0].set_title("Inbound And Outbound Overlap Area vs Initial Particle 1 Y")
    axes[0, 0].set_xlabel("Initial Particle 1 Y")
    axes[0, 0].set_ylabel("Overlap Area")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend()

    axes[0, 1].plot(
        y_values,
        [0.0 if study["sum_turn_area"] is None else float(study["sum_turn_area"]) for study in studies],
        marker="o",
        linewidth=2,
        color="#2563eb",
    )
    for study in studies:
        axes[0, 1].annotate(
            str(study["label"]),
            (float(study["y_init"]), 0.0 if study["sum_turn_area"] is None else float(study["sum_turn_area"])),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )
    axes[0, 1].set_title("Total Turning Area vs Initial Particle 1 Y")
    axes[0, 1].set_xlabel("Initial Particle 1 Y")
    axes[0, 1].set_ylabel("Sum Turn Area")
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].plot(
        y_values,
        [0.0 if study["sum_J_in"] is None else float(study["sum_J_in"]) for study in studies],
        marker="o",
        linewidth=2,
        color="#059669",
    )
    for study in studies:
        axes[1, 0].annotate(
            str(study["label"]),
            (float(study["y_init"]), 0.0 if study["sum_J_in"] is None else float(study["sum_J_in"])),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )
    axes[1, 0].set_title("Total Inbound Impulse vs Initial Particle 1 Y")
    axes[1, 0].set_xlabel("Initial Particle 1 Y")
    axes[1, 0].set_ylabel("Sum J In")
    axes[1, 0].grid(True, alpha=0.3)

    scatter_studies = [
        study
        for study in studies
        if study["sum_area_in"] is not None
        and study["sum_turn_area"] is not None
        and study["scalar_error"] is not None
    ]
    scatter = axes[1, 1].scatter(
        [float(study["sum_area_in"]) for study in scatter_studies],
        [float(study["sum_turn_area"]) for study in scatter_studies],
        c=[abs(float(study["scalar_error"])) for study in scatter_studies],
        cmap="magma",
        s=80,
    )
    for study in scatter_studies:
        axes[1, 1].annotate(
            str(study["label"]),
            (float(study["sum_area_in"]), float(study["sum_turn_area"])),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )
    axes[1, 1].set_title("Scalar Momentum Error vs Overlap And Turning")
    axes[1, 1].set_xlabel("Sum Area In")
    axes[1, 1].set_ylabel("Sum Turn Area")
    axes[1, 1].grid(True, alpha=0.3)
    colorbar = fig.colorbar(scatter, ax=axes[1, 1])
    colorbar.set_label("|Scalar Momentum Error|")

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    plt.show()


if __name__ == "__main__":
    main()
