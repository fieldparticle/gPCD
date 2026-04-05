import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "frame_processing_slowdown_by_study.png"
EXCLUDED_STUDIES = {4, 15}


def timing_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("tpocl_*_frame_timing.csv"))


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_study_index(path: Path) -> int:
    stem = path.stem.replace("_frame_timing", "")
    return int(stem.split("_")[-1])


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def main() -> None:
    studies: list[dict[str, float]] = []

    for path in timing_paths():
        study_index = parse_study_index(path)
        if study_index in EXCLUDED_STUDIES:
            continue

        rows = load_rows(path)
        if not rows:
            continue

        simulation_ms = [float(row["simulation_wall_ms"]) for row in rows]
        contact_ms = [
            float(row["simulation_wall_ms"])
            for row in rows
            if int(float(row.get("active_contact_count", "0"))) > 0
        ]
        free_ms = [
            float(row["simulation_wall_ms"])
            for row in rows
            if int(float(row.get("active_contact_count", "0"))) == 0
        ]

        avg_all = mean(simulation_ms)
        avg_contact = mean(contact_ms)
        avg_free = mean(free_ms)
        slowdown = avg_contact / avg_free if avg_contact > 0.0 and avg_free > 0.0 else 0.0

        studies.append(
            {
                "study_index": float(study_index),
                "avg_all": avg_all,
                "avg_contact": avg_contact,
                "avg_free": avg_free,
                "slowdown": slowdown,
            }
        )

    if not studies:
        print(
            f"No frame timing exports found in {DATA_DIR}. "
            "Re-run the studies to generate *_frame_timing.csv files."
        )
        return

    studies.sort(key=lambda item: item["study_index"])
    study_indices = [item["study_index"] for item in studies]
    avg_contact_values = [item["avg_contact"] for item in studies]
    avg_free_values = [item["avg_free"] for item in studies]
    slowdown_values = [item["slowdown"] for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

    axes[0].plot(study_indices, avg_free_values, marker="o", linewidth=2, color="#2563eb", label="Free-flight ms/frame")
    axes[0].plot(
        study_indices,
        avg_contact_values,
        marker="o",
        linewidth=2,
        color="#dc2626",
        label="Collision ms/frame",
    )
    for item in studies:
        axes[0].annotate(
            str(int(item["study_index"])),
            (item["study_index"], item["avg_contact"]),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )
    axes[0].set_title("Measured Frame Processing Time By Study")
    axes[0].set_ylabel("Simulation Wall Time (ms/frame)")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].bar(study_indices, slowdown_values, width=0.6, color="#7c3aed", alpha=0.85)
    for item in studies:
        axes[1].annotate(
            f"{item['slowdown']:.2f}x",
            (item["study_index"], item["slowdown"]),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
        )
    axes[1].set_title("Collision Slowdown Relative To Free Flight")
    axes[1].set_xlabel("Study Index")
    axes[1].set_ylabel("Slowdown Factor")
    axes[1].grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
