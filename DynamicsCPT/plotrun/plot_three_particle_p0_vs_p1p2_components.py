import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "ThreeP005_mom"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "three_particle_p0_vs_p1p2_components.png"


def trace_paths() -> list[Path]:
    paths = []
    for path in DATA_DIR.glob("tph_*.csv"):
        name = path.name
        if name.endswith("_summary.csv") or name.endswith("_frame_timing.csv"):
            continue
        paths.append(path)
    return sorted(paths)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_study_index(path: Path) -> int:
    return int(path.stem.split("_")[-1])


def main() -> None:
    studies: list[dict[str, float | int]] = []

    for path in trace_paths():
        rows = load_rows(path)
        if not rows:
            continue

        last_row = rows[-1]
        studies.append(
            {
                "study_index": parse_study_index(path),
                "p0_px": float(last_row["p0_px"]),
                "p0_py": float(last_row["p0_py"]),
                "neg_p12_px": -(float(last_row["p1_px"]) + float(last_row["p2_px"])),
                "neg_p12_py": -(float(last_row["p1_py"]) + float(last_row["p2_py"])),
            }
        )

    if not studies:
        raise FileNotFoundError(f"No usable three-particle trace files found in {DATA_DIR}")

    studies.sort(key=lambda item: int(item["study_index"]))
    study_indices = [int(item["study_index"]) for item in studies]
    p0_px_values = [float(item["p0_px"]) for item in studies]
    p0_py_values = [float(item["p0_py"]) for item in studies]
    neg_p12_px_values = [float(item["neg_p12_px"]) for item in studies]
    neg_p12_py_values = [float(item["neg_p12_py"]) for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

    axes[0].plot(study_indices, p0_px_values, marker="o", linewidth=1.8, color="#2563eb", label="p0_px")
    axes[0].plot(study_indices, neg_p12_px_values, marker="s", linewidth=1.8, linestyle="--", color="#dc2626", label="-(p1_px + p2_px)")
    axes[0].set_title("Particle 0 vs -(Particles 1 + 2) X-Momentum")
    axes[0].set_ylabel("px")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(study_indices, p0_py_values, marker="o", linewidth=1.8, color="#2563eb", label="p0_py")
    axes[1].plot(study_indices, neg_p12_py_values, marker="s", linewidth=1.8, linestyle="--", color="#dc2626", label="-(p1_py + p2_py)")
    axes[1].set_title("Particle 0 vs -(Particles 1 + 2) Y-Momentum")
    axes[1].set_xlabel("Study Index")
    axes[1].set_ylabel("py")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    for study_index, value in zip(study_indices, p0_px_values):
        axes[0].annotate(
            str(study_index),
            (study_index, value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=7,
            color="#2563eb",
        )

    for study_index, value in zip(study_indices, p0_py_values):
        axes[1].annotate(
            str(study_index),
            (study_index, value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=7,
            color="#2563eb",
        )

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
