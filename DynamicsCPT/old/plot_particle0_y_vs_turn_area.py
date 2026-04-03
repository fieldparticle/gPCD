import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "particle0_y_vs_turn_area.png"


def parse_metric_file(path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            metric = (row.get("metric") or "").strip()
            value = (row.get("value") or "").strip()
            if metric:
                metrics[metric] = value
    return metrics


def parse_y_from_init_pos(value: str) -> float:
    x_str, y_str = value.strip("()").split(",")
    return float(y_str.strip())


def collect_points() -> list[tuple[float, float, str]]:
    points: list[tuple[float, float, str]] = []
    for csv_path in sorted(DATA_DIR.glob("tpocl_*_summary.csv")):
        metrics = parse_metric_file(csv_path)
        y_value = parse_y_from_init_pos(metrics["particle 00 init pos"])
        turn_area = float(metrics["sum turn area"])
        points.append((y_value, turn_area, csv_path.stem.replace("_summary", "")))
    points.sort(key=lambda item: item[0])
    return points


def main() -> None:
    points = collect_points()
    if not points:
        raise FileNotFoundError(f"No tpocl CSV files found in {DATA_DIR}")

    y_values = [point[0] for point in points]
    turn_areas = [point[1] for point in points]

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(y_values, turn_areas, marker="o", linewidth=2, color="#1f77b4")
    ax.set_title("Particle 0 Initial Y vs Turning Area")
    ax.set_xlabel("Particle 0 Initial Y")
    ax.set_ylabel("Turning Area")
    ax.grid(True, alpha=0.3)

    for y_value, turn_area, label in points:
        ax.annotate(label, (y_value, turn_area), textcoords="offset points", xytext=(0, 8), ha="center")

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    plt.show()


if __name__ == "__main__":
    main()
