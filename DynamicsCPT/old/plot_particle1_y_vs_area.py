import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PROJECT_ROOT / "plots"


def resolve_trace_paths() -> tuple[list[Path], bool]:
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.lower() == "all":
            return sorted(
                path
                for path in DATA_DIR.glob("tpocl_*.csv")
                if not path.stem.endswith("_summary")
            ), False

        candidate = Path(arg)
        if not candidate.is_absolute():
            candidate = DATA_DIR / candidate
        if candidate.suffix.lower() != ".csv":
            candidate = candidate.with_suffix(".csv")
        return [candidate], True

    return sorted(
        path
        for path in DATA_DIR.glob("tpocl_*.csv")
        if not path.stem.endswith("_summary")
    ), False


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def numeric_series(rows: list[dict[str, str]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        raw = row.get(key, "")
        values.append(float(raw) if raw not in ("", None) else 0.0)
    return values


def plot_trace(trace_path: Path, show_window: bool) -> None:
    rows = load_rows(trace_path)
    if not rows:
        raise FileNotFoundError(f"No trace rows found in {trace_path}")

    particle_y = numeric_series(rows, "p1_y")
    swept_area = numeric_series(rows, "step_turn_area")
    overlap_area = numeric_series(rows, "current_area")
    time_values = numeric_series(rows, "time")

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PLOTS_DIR / f"{trace_path.stem}_particle1_y_vs_area.png"

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(particle_y, swept_area, color="#2563eb", linewidth=2, label="Swept Area")
    ax.plot(particle_y, overlap_area, color="#b45309", linewidth=2, label="Overlap Area")
    ax.set_title(f"Particle 1 Y vs Swept And Overlap Area: {trace_path.stem}")
    ax.set_xlabel("Particle 1 Y")
    ax.set_ylabel("Area")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.invert_xaxis()

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    print(f"Saved plot to {output_path}")
    print(f"Trace time span: {time_values[0]:.6f} to {time_values[-1]:.6f}")
    if show_window:
        plt.show()
    else:
        plt.close(fig)


def main() -> None:
    trace_paths, show_window = resolve_trace_paths()
    if not trace_paths:
        raise FileNotFoundError(f"No study trace CSV files found in {DATA_DIR}")

    for trace_path in trace_paths:
        plot_trace(trace_path, show_window=show_window)


if __name__ == "__main__":
    main()
