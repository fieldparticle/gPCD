import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "ThreeP005_mom"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "three_particle_vector_momentum_error.png"


def summary_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("tph_*_summary.csv"))


def parse_study_index(path: Path) -> int:
    return int(path.stem.replace("_summary", "").split("_")[-1])


def load_metrics(path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            metric = (row.get("metric") or "").strip()
            value = (row.get("value") or "").strip()
            if metric:
                metrics[metric] = value
    return metrics


def parse_vector(value: str | None) -> tuple[float, float] | None:
    if not value:
        return None
    stripped = value.strip()
    if not (stripped.startswith("(") and stripped.endswith(")")):
        return None
    left, right = stripped[1:-1].split(",")
    return float(left), float(right)


def main() -> None:
    studies: list[dict[str, float]] = []

    for summary_path in summary_paths():
        metrics = load_metrics(summary_path)
        initial_momentum = parse_vector(metrics.get("initial momentum"))
        final_momentum = parse_vector(metrics.get("final momentum"))
        error_mag_text = metrics.get("momentum error mag")

        if initial_momentum is None or final_momentum is None or error_mag_text in (None, ""):
            continue

        error_px = final_momentum[0] - initial_momentum[0]
        error_py = final_momentum[1] - initial_momentum[1]
        studies.append(
            {
                "study_index": float(parse_study_index(summary_path)),
                "error_px": error_px,
                "error_py": error_py,
                "error_mag": float(error_mag_text),
            }
        )

    if not studies:
        raise FileNotFoundError(f"No usable three-particle summaries found in {DATA_DIR}")

    studies.sort(key=lambda item: item["study_index"])
    study_indices = [item["study_index"] for item in studies]
    error_px = [item["error_px"] for item in studies]
    error_py = [item["error_py"] for item in studies]
    error_mag = [item["error_mag"] for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(11, 11), sharex=True)

    axes[0].plot(study_indices, error_px, marker="o", linewidth=1.8, color="#2563eb")
    axes[0].axhline(0.0, color="black", linestyle="--", linewidth=1.0, alpha=0.5)
    axes[0].set_title("Three-Particle Vector Momentum Error: X Component")
    axes[0].set_ylabel("Final Px - Initial Px")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(study_indices, error_py, marker="o", linewidth=1.8, color="#dc2626")
    axes[1].axhline(0.0, color="black", linestyle="--", linewidth=1.0, alpha=0.5)
    axes[1].set_title("Three-Particle Vector Momentum Error: Y Component")
    axes[1].set_ylabel("Final Py - Initial Py")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(study_indices, error_mag, marker="o", linewidth=1.8, color="#059669")
    axes[2].set_yscale("log")
    axes[2].set_title("Three-Particle Vector Momentum Error Magnitude")
    axes[2].set_xlabel("Study Index")
    axes[2].set_ylabel("|Final P - Initial P|")
    axes[2].grid(True, alpha=0.3, which="both")

    for axis, values in zip(axes, [error_px, error_py, error_mag]):
        for study_index, value in zip(study_indices, values):
            axis.annotate(
                str(int(study_index)),
                (study_index, value),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=8,
            )

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
