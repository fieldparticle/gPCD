import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PROJECT_ROOT / "plots"
PARTICLE_LIMIT = 4


def resolve_trace_path() -> Path:
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1])
        if not candidate.is_absolute():
            candidate = DATA_DIR / candidate
        if candidate.suffix.lower() != ".csv":
            candidate = candidate.with_suffix(".csv")
        return candidate
    return DATA_DIR / "tpocl_1.csv"


def load_trace_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def numeric_series(rows: list[dict[str, str]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        raw = row.get(key, "")
        values.append(float(raw) if raw not in ("", None) else 0.0)
    return values


def particle_present(rows: list[dict[str, str]], index: int) -> bool:
    key = f"p{index}_mass"
    return any((row.get(key) or "").strip() for row in rows)


def main() -> None:
    trace_path = resolve_trace_path()
    rows = load_trace_rows(trace_path)
    if not rows:
        raise FileNotFoundError(f"No trace rows found in {trace_path}")

    time_values = numeric_series(rows, "time")
    current_area = numeric_series(rows, "current_area")
    current_J = numeric_series(rows, "current_J")
    step_turn_area = numeric_series(rows, "step_turn_area")
    step_max_turn_area = numeric_series(rows, "step_max_turn_area")
    step_max_turn_sweep = numeric_series(rows, "step_max_turn_sweep")

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PLOTS_DIR / f"{trace_path.stem}_collision_trace.png"

    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)

    axes[0].plot(time_values, current_area, label="current_area", color="#0f766e", linewidth=2)
    axes[0].plot(time_values, current_J, label="current_J", color="#b45309", linewidth=2)
    axes[0].set_ylabel("Contact Magnitude")
    axes[0].set_title(f"Collision Trace: {trace_path.stem}")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(time_values, step_turn_area, label="step_turn_area", color="#2563eb", linewidth=2)
    axes[1].plot(time_values, step_max_turn_area, label="step_max_turn_area", color="#7c3aed", linewidth=1.5)
    axes[1].plot(time_values, step_max_turn_sweep, label="step_max_turn_sweep", color="#dc2626", linewidth=1.5)
    axes[1].set_ylabel("Turning")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    colors = ["#1d4ed8", "#dc2626", "#059669", "#a16207"]
    for index in range(PARTICLE_LIMIT):
        if not particle_present(rows, index):
            continue
        axes[2].plot(
            time_values,
            numeric_series(rows, f"p{index}_y"),
            label=f"p{index}_y",
            color=colors[index],
            linewidth=2,
        )
    axes[2].set_xlabel("Time")
    axes[2].set_ylabel("Particle Y")
    axes[2].grid(True, alpha=0.3)
    axes[2].legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    print(f"Saved plot to {output_path}")
    plt.show()


if __name__ == "__main__":
    main()
