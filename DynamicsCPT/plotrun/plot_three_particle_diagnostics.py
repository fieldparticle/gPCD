import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "ThreeP005_mom_aseq"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "three_particle_diagnostics.png"


def summary_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("tph_*_summary.csv"))


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


def max_pair_contacts(rows: list[dict[str, str]]) -> float:
    if not rows:
        return 0.0
    return max(float(row.get("pair_contact_count", "0") or 0.0) for row in rows)


def simultaneous_pair_contact_rows(rows: list[dict[str, str]]) -> float:
    return float(sum(1 for row in rows if float(row.get("pair_contact_count", "0") or 0.0) >= 2.0))


def main() -> None:
    studies: list[dict[str, float]] = []

    for summary_path in summary_paths():
        metrics = load_metrics(summary_path)
        trace_path = trace_path_for_summary(summary_path)
        rows = load_rows(trace_path) if trace_path.exists() else []

        scalar_error = maybe_float(metrics.get("scalar total error"))
        turn_area = maybe_float(metrics.get("sum turn area"))
        max_turn_area = maybe_float(metrics.get("max turn area"))

        if scalar_error is None:
            if metrics.get("collision status") == "no collision":
                scalar_error = 0.0
            else:
                continue

        studies.append(
            {
                "study_index": float(parse_study_index(summary_path)),
                "abs_scalar_error": abs(float(scalar_error)),
                "sum_turn_area": 0.0 if turn_area is None else float(turn_area),
                "max_turn_area": 0.0 if max_turn_area is None else float(max_turn_area),
                "max_pair_contacts": max_pair_contacts(rows),
                "simultaneous_pair_rows": simultaneous_pair_contact_rows(rows),
            }
        )

    if not studies:
        raise FileNotFoundError(f"No usable three-particle study summaries found in {DATA_DIR}")

    studies.sort(key=lambda item: item["study_index"])
    study_indices = [item["study_index"] for item in studies]
    abs_scalar_errors = [item["abs_scalar_error"] for item in studies]
    sum_turn_areas = [item["sum_turn_area"] for item in studies]
    simultaneous_rows = [item["simultaneous_pair_rows"] for item in studies]
    max_pair_contact_values = [item["max_pair_contacts"] for item in studies]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(11, 11), sharex=True)

    axes[0].plot(study_indices, sum_turn_areas, marker="o", linewidth=1.8, color="#dc2626")
    axes[0].set_title("Three-Particle Sum Turning Area vs Study")
    axes[0].set_ylabel("Sum Turn Area")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(study_indices, simultaneous_rows, marker="o", linewidth=1.8, color="#059669", label="Rows with >=2 pair contacts")
    axes[1].plot(study_indices, max_pair_contact_values, marker="s", linewidth=1.4, color="#0f766e", label="Max pair_contact_count")
    axes[1].set_title("Three-Particle Contact Overlap Structure")
    axes[1].set_ylabel("Contact Overlap Metrics")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    axes[2].plot(study_indices, abs_scalar_errors, marker="o", linewidth=1.8, color="#2563eb")
    axes[2].set_yscale("log")
    axes[2].set_title("Three-Particle Ending Scalar Momentum Error Magnitude vs Study")
    axes[2].set_xlabel("Study Index")
    axes[2].set_ylabel("|Scalar Momentum Error|")
    axes[2].grid(True, alpha=0.3, which="both")

    for axis, values in zip(axes, [sum_turn_areas, simultaneous_rows, abs_scalar_errors]):
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
