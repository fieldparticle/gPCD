import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "ThreeP005_mom_aseq"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "three_particle_magnitude_error_by_particle.png"


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


def momentum_magnitude(row: dict[str, str], particle_index: int) -> float | None:
    px_raw = row.get(f"p{particle_index}_px", "")
    py_raw = row.get(f"p{particle_index}_py", "")
    if px_raw in ("", None) or py_raw in ("", None):
        return None
    return math.hypot(float(px_raw), float(py_raw))


def main() -> None:
    studies: list[dict[str, float | int]] = []

    for path in trace_paths():
        rows = load_rows(path)
        if not rows:
            continue

        first_row = rows[0]
        last_row = rows[-1]
        particle_errors: dict[str, float | int] = {"study_index": parse_study_index(path)}

        valid = True
        for particle_index in range(3):
            initial_mag = momentum_magnitude(first_row, particle_index)
            final_mag = momentum_magnitude(last_row, particle_index)
            if initial_mag is None or final_mag is None:
                valid = False
                break
            particle_errors[f"p{particle_index}_mag_error"] = final_mag - initial_mag

        if valid:
            studies.append(particle_errors)

    if not studies:
        raise FileNotFoundError(f"No usable three-particle trace files found in {DATA_DIR}")

    studies.sort(key=lambda item: int(item["study_index"]))
    study_indices = [int(item["study_index"]) for item in studies]
    p0_errors = [float(item["p0_mag_error"]) for item in studies]
    p1_errors = [float(item["p1_mag_error"]) for item in studies]
    p2_errors = [float(item["p2_mag_error"]) for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 6.5))

    ax.plot(study_indices, p0_errors, marker="o", linewidth=1.8, color="#2563eb", label="Particle 0")
    ax.plot(study_indices, p1_errors, marker="s", linewidth=1.8, linestyle="--", color="#dc2626", label="Particle 1")
    ax.plot(study_indices, p2_errors, marker="^", linewidth=1.8, color="#059669", alpha=0.85, label="Particle 2")
    ax.axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")

    for study_index, value in zip(study_indices, p0_errors):
        ax.annotate(
            str(study_index),
            (study_index, value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=7,
            color="#2563eb",
        )
    for study_index, value in zip(study_indices, p1_errors):
        ax.annotate(
            str(study_index),
            (study_index, value),
            textcoords="offset points",
            xytext=(0, -12),
            ha="center",
            fontsize=7,
            color="#dc2626",
        )
    for study_index, value in zip(study_indices, p2_errors):
        ax.annotate(
            str(study_index),
            (study_index, value),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=7,
            color="#059669",
        )

    ax.set_title("Three-Particle Momentum Magnitude Error by Particle vs Study")
    ax.set_xlabel("Study Index")
    ax.set_ylabel("Final |p| - First-Trace |p|")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
