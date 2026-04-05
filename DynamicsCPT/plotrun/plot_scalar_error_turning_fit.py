import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR_NAME = "data005"
DATA_DIR = PROJECT_ROOT / DATA_DIR_NAME
PLOTS_DIR = PROJECT_ROOT / "plots"
OUTPUT_FILE = PLOTS_DIR / "scalar_error_turning_fit.png"
TOP_OUTLIER_COUNT = 3
HIGHLIGHT_RANGE = range(26, 33)


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


def parse_study_index(path: Path) -> int:
    stem = path.stem.replace("_summary", "")
    return int(stem.split("_")[-1])


def maybe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def solve_linear_system_3x3(matrix: list[list[float]], vector: list[float]) -> list[float]:
    a = [row[:] + [rhs] for row, rhs in zip(matrix, vector)]
    size = 3

    for pivot in range(size):
        best_row = max(range(pivot, size), key=lambda row: abs(a[row][pivot]))
        if abs(a[best_row][pivot]) <= 1.0e-20:
            return [0.0, 0.0, 0.0]
        if best_row != pivot:
            a[pivot], a[best_row] = a[best_row], a[pivot]

        pivot_value = a[pivot][pivot]
        for column in range(pivot, size + 1):
            a[pivot][column] /= pivot_value

        for row in range(size):
            if row == pivot:
                continue
            factor = a[row][pivot]
            for column in range(pivot, size + 1):
                a[row][column] -= factor * a[pivot][column]

    return [a[row][size] for row in range(size)]


def main() -> None:
    studies: list[dict[str, float]] = []

    for path in summary_paths():
        metrics = load_metrics(path)
        study_index = parse_study_index(path)

        scalar_error = maybe_float(metrics.get("scalar total error"))
        if scalar_error is None:
            if metrics.get("collision status") == "no collision":
                scalar_error = 0.0
            else:
                continue

        sum_turn_area = maybe_float(metrics.get("sum turn area"))
        if sum_turn_area is None:
            continue

        studies.append(
            {
                "study_index": float(study_index),
                "abs_error": abs(float(scalar_error)),
                "sum_turn_area": float(sum_turn_area),
            }
        )

    if not studies:
        raise FileNotFoundError(f"No scalar-error study summaries found in {DATA_DIR}")

    studies.sort(key=lambda item: item["study_index"])
    turn_values = [item["sum_turn_area"] for item in studies]
    error_values = [item["abs_error"] for item in studies]
    study_indices = [item["study_index"] for item in studies]

    denominator = sum(value * value for value in turn_values)
    linear_coefficient = 0.0 if denominator <= 0.0 else sum(
        turn_value * error_value for turn_value, error_value in zip(turn_values, error_values)
    ) / denominator

    linear_fitted_values = [linear_coefficient * turn_value for turn_value in turn_values]
    linear_residual_values = [
        error_value - fitted_value
        for error_value, fitted_value in zip(error_values, linear_fitted_values)
    ]

    count = float(len(turn_values))
    sum_x = sum(turn_values)
    sum_x2 = sum(value * value for value in turn_values)
    sum_x3 = sum(value * value * value for value in turn_values)
    sum_x4 = sum(value * value * value * value for value in turn_values)
    sum_y = sum(error_values)
    sum_xy = sum(x * y for x, y in zip(turn_values, error_values))
    sum_x2y = sum(x * x * y for x, y in zip(turn_values, error_values))
    quadratic_coefficients = solve_linear_system_3x3(
        [
            [count, sum_x, sum_x2],
            [sum_x, sum_x2, sum_x3],
            [sum_x2, sum_x3, sum_x4],
        ],
        [sum_y, sum_xy, sum_x2y],
    )
    quadratic_fitted_values = [
        quadratic_coefficients[0]
        + quadratic_coefficients[1] * turn_value
        + quadratic_coefficients[2] * turn_value * turn_value
        for turn_value in turn_values
    ]
    quadratic_residual_values = [
        error_value - fitted_value
        for error_value, fitted_value in zip(error_values, quadratic_fitted_values)
    ]
    abs_residual_values = [abs(value) for value in linear_residual_values]

    outlier_ranking = sorted(
        zip(study_indices, abs_residual_values),
        key=lambda item: item[1],
        reverse=True,
    )
    outlier_indices = {int(study_index) for study_index, _ in outlier_ranking[:TOP_OUTLIER_COUNT]}

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(11, 13))

    axes[0].scatter(turn_values, error_values, color="#2563eb", s=55, label="Observed |scalar error|")
    axes[0].plot(
        turn_values,
        linear_fitted_values,
        color="#dc2626",
        linewidth=2.0,
        label=f"Linear fit (c={linear_coefficient:.2e})",
    )
    axes[0].plot(
        turn_values,
        quadratic_fitted_values,
        color="#059669",
        linewidth=2.0,
        linestyle="--",
        label=(
            "Quadratic fit "
            f"({quadratic_coefficients[0]:.2e} + {quadratic_coefficients[1]:.2e}x + {quadratic_coefficients[2]:.2e}x^2)"
        ),
    )
    for study_index, turn_value, error_value in zip(study_indices, turn_values, error_values):
        axes[0].annotate(
            str(int(study_index)),
            (turn_value, error_value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
            color="#7f1d1d" if int(study_index) in outlier_indices else "black",
        )
    axes[0].set_yscale("log")
    axes[0].set_title("|Scalar Error| vs Sum Turn Area With Linear And Quadratic Fits")
    axes[0].set_xlabel("Sum Turn Area")
    axes[0].set_ylabel("|Scalar Momentum Error|")
    axes[0].grid(True, alpha=0.3, which="both")
    axes[0].legend()

    highlighted_turn_values = [
        turn_value
        for study_index, turn_value in zip(study_indices, turn_values)
        if int(study_index) in HIGHLIGHT_RANGE
    ]
    highlighted_linear_values = [
        fitted_value
        for study_index, fitted_value in zip(study_indices, linear_fitted_values)
        if int(study_index) in HIGHLIGHT_RANGE
    ]
    if highlighted_turn_values:
        axes[0].plot(
            highlighted_turn_values,
            highlighted_linear_values,
            color="#f59e0b",
            linewidth=2.4,
            linestyle=":",
            marker="s",
            markersize=4,
            label="Linear fit, studies 26-32",
        )
        for study_index, turn_value, fitted_value in zip(study_indices, turn_values, linear_fitted_values):
            if int(study_index) in HIGHLIGHT_RANGE:
                axes[0].annotate(
                    f"cT={fitted_value:.1e}",
                    (turn_value, fitted_value),
                    textcoords="offset points",
                    xytext=(0, -12),
                    ha="center",
                    fontsize=7,
                    color="#92400e",
                )
        axes[0].legend()

    axes[1].plot(study_indices, linear_residual_values, marker="o", linewidth=1.8, color="#7c3aed")
    for study_index, residual_value in zip(study_indices, linear_residual_values):
        axes[1].annotate(
            str(int(study_index)),
            (study_index, residual_value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
            color="#7f1d1d" if int(study_index) in outlier_indices else "black",
        )
    axes[1].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    axes[1].set_title(f"Residuals After Linear Fit (Top {TOP_OUTLIER_COUNT} Outliers Highlighted)")
    axes[1].set_xlabel("Study Index")
    axes[1].set_ylabel("Residual = |Error| - Linear Fit")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(study_indices, quadratic_residual_values, marker="o", linewidth=1.8, color="#2563eb")
    for study_index, residual_value in zip(study_indices, quadratic_residual_values):
        axes[2].annotate(
            str(int(study_index)),
            (study_index, residual_value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
            color="#7f1d1d" if int(study_index) in outlier_indices else "black",
        )
    axes[2].axhline(0.0, color="#64748b", linewidth=1.0, linestyle="--")
    axes[2].set_title(f"Residuals After Quadratic Fit (Top {TOP_OUTLIER_COUNT} Outliers Highlighted)")
    axes[2].set_xlabel("Study Index")
    axes[2].set_ylabel("Residual = |Error| - Quadratic Fit")
    axes[2].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200)
    print(f"Saved plot to {OUTPUT_FILE}")
    if plt.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    main()
