"""Three-panel interactive plots for ForceDynamics reports."""

import math
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gbase import libconf
from base.DiagnosticsPlots import (
    _batch_momentum_items,
    _float,
    _momentum_series,
    _read_rows,
    _report_path,
    _run_dt_from_cfg,
)


MODEL_NAME = "ForceDynamics"
PAIR_COLORS = {
    "overlap_area": "#1f77b4",
    "center_distance": "#ff7f0e",
    "rel_vn": "#2ca02c",
    "force_magnitude": "#d62728",
    "contact_potential_energy": "#9467bd",
}


def _force_report_mode():
    """Return the report stream currently assigned to ForceDynamics."""
    cfg_path = Path(__file__).resolve().parents[1] / "ParticleUtil.cfg"
    with cfg_path.open("r", encoding="utf-8") as cfg_file:
        cfg = libconf.load(cfg_file)
    for report_mode in ("live", "shadow"):
        if str(cfg.get(f"{report_mode}_base", "")) == MODEL_NAME:
            return report_mode
    raise ValueError(f"{MODEL_NAME} is not registered as live_base or shadow_base")


def _time_values(item, frames):
    dt = _run_dt_from_cfg(item.get("cfg_path"))
    return [frame * dt for frame in frames] if dt is not None else frames


def _pair_contact_series(item, frames):
    """Return second-scan contact values for each unordered particle pair."""
    report_mode = _force_report_mode()
    contacts_csv = _report_path(
        Path(item["momentum_csv"]).parent,
        "contacts",
        report_mode,
    )
    if not contacts_csv.exists():
        return {}

    pairs = {}
    for row in _read_rows(contacts_csv):
        if row.get("source_index", "") == "" or row.get("target_index", "") == "":
            continue
        source_index = int(_float(row, "source_index"))
        target_index = int(_float(row, "target_index"))
        if source_index >= target_index:
            continue
        pair = (int(_float(row, "source")), int(_float(row, "target")))
        frame = int(_float(row, "frame"))
        pair_rows = pairs.setdefault(pair, {})
        pair_rows[frame] = {
            "overlap_area": _float(row, "overlap_area"),
            "center_distance": _float(row, "center_distance", math.nan),
            "rel_vn": _float(row, "rel_vn", math.nan),
            "force_magnitude": _float(row, "force_magnitude"),
            "contact_potential_energy": _float(row, "contact_potential_energy"),
        }

    series = {}
    for pair, rows_by_frame in pairs.items():
        series[pair] = {
            "overlap_area": [
                rows_by_frame.get(frame, {}).get("overlap_area", 0.0)
                for frame in frames
            ],
            "center_distance": [
                rows_by_frame.get(frame, {}).get("center_distance", math.nan)
                for frame in frames
            ],
            "rel_vn": [
                rows_by_frame.get(frame, {}).get("rel_vn", math.nan)
                for frame in frames
            ],
            "force_magnitude": [
                rows_by_frame.get(frame, {}).get("force_magnitude", 0.0)
                for frame in frames
            ],
            "contact_potential_energy": [
                rows_by_frame.get(frame, {}).get("contact_potential_energy", 0.0)
                for frame in frames
            ],
        }
    return series


def _legend_far_right(axis):
    axis.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        borderaxespad=0.0,
    )


def _draw_force_axes(fig, axes, item, selected_pair=None):
    """Draw the requested system-energy, momentum, and pair-contact panels."""
    energy_axis, momentum_axis, contact_axis = axes
    series = _momentum_series(item["momentum_csv"])
    frames = series["frames"]
    times = _time_values(item, frames)

    energy_axis.clear()
    energy_axis.plot(times, series["current_ke"], label="KE(t)", linewidth=2)
    energy_axis.plot(times, series["potential_energy"], label="U(t)", linewidth=2)
    energy_axis.plot(times, series["total_energy"], label="E(t) = KE(t) + U(t)", linewidth=2)
    energy_axis.plot(
        times,
        series["energy_drift"],
        label="E(t) - E(0)",
        linewidth=2,
        linestyle="--",
    )
    energy_axis.axhline(0.0, color="black", linewidth=0.8, alpha=0.4)
    energy_axis.set_title(f"{item['name']} - System Energy")
    energy_axis.set_ylabel("energy")
    energy_axis.grid(True, alpha=0.3)
    _legend_far_right(energy_axis)

    momentum_axis.clear()
    momentum_axis.plot(times, series["current_px"], label="Px(t)", linewidth=2)
    momentum_axis.plot(times, series["current_py"], label="Py(t)", linewidth=2)
    momentum_axis.plot(
        times,
        series["momentum_drift"],
        label="|P(t) - P(0)|",
        linewidth=2,
        linestyle="--",
    )
    momentum_axis.axhline(0.0, color="black", linewidth=0.8, alpha=0.4)
    momentum_axis.set_title("System Momentum")
    momentum_axis.set_ylabel("momentum")
    momentum_axis.grid(True, alpha=0.3)
    _legend_far_right(momentum_axis)

    pair_series = _pair_contact_series(item, frames)
    pairs = sorted(pair_series)
    if selected_pair not in pair_series:
        selected_pair = pairs[0] if pairs else None

    contact_axis.clear()
    if selected_pair is not None:
        values = pair_series[selected_pair]
        pair_label = f"p{selected_pair[0]}-p{selected_pair[1]}"
        contact_axis.plot(
            times,
            values["overlap_area"],
            label=f"{pair_label} Aij(t)",
            color=PAIR_COLORS["overlap_area"],
            linewidth=2,
        )
        contact_axis.plot(
            times,
            values["center_distance"],
            label=f"{pair_label} dij(t)",
            color=PAIR_COLORS["center_distance"],
            linewidth=2,
        )
        contact_axis.plot(
            times,
            values["rel_vn"],
            label=f"{pair_label} vn,ij(t)",
            color=PAIR_COLORS["rel_vn"],
            linewidth=2,
        )
        contact_axis.plot(
            times,
            values["force_magnitude"],
            label=f"{pair_label} Fij(t)",
            color=PAIR_COLORS["force_magnitude"],
            linewidth=2,
        )
        contact_axis.plot(
            times,
            values["contact_potential_energy"],
            label=f"{pair_label} Uij(t)",
            color=PAIR_COLORS["contact_potential_energy"],
            linewidth=2,
        )
    contact_axis.axhline(0.0, color="black", linewidth=0.8, alpha=0.4)
    contact_axis.set_title("Pair Contact Geometry and Force")
    contact_axis.set_xlabel("time")
    contact_axis.set_ylabel("pair value")
    contact_axis.grid(True, alpha=0.3)
    if selected_pair is not None:
        _legend_far_right(contact_axis)

    for axis in axes:
        if times:
            axis.set_xlim(min(times), max(times))
    fig.canvas.manager.set_window_title(f"{MODEL_NAME} Plots")
    fig.canvas.draw_idle()
    return pairs, selected_pair


def show_force_menu(batch_cfg):
    """Show the three-panel ForceDynamics plot window."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.widgets import RadioButtons
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "matplotlib is required for ForcePlots. "
            "Run with .venv\\Scripts\\python.exe or install matplotlib."
        ) from exc

    report_mode = _force_report_mode()
    items = _batch_momentum_items(batch_cfg, report_mode)
    if not items:
        raise ValueError(f"No {MODEL_NAME} momentum CSV files found for {batch_cfg}")

    fig, axes = plt.subplots(3, 1, figsize=(15, 11), sharex=True)
    fig.subplots_adjust(left=0.25, right=0.76, top=0.95, bottom=0.08, hspace=0.34)

    test_axis = fig.add_axes([0.02, 0.46, 0.19, 0.45])
    test_radio = RadioButtons(test_axis, [item["name"] for item in items], active=0)
    test_axis.set_title("Test")

    selected = {"item": items[0], "pair": None}
    pair_control = {"axis": None, "radio": None, "connection": None}

    def rebuild_pair_selector(pairs, selected_pair):
        if pair_control["axis"] is not None:
            pair_control["axis"].remove()
        pair_axis = fig.add_axes([0.02, 0.18, 0.19, 0.20])
        labels = [f"p{pair[0]}-p{pair[1]}" for pair in pairs] or ["no contacts"]
        active = pairs.index(selected_pair) if selected_pair in pairs else 0
        pair_radio = RadioButtons(pair_axis, labels, active=active)
        pair_axis.set_title("Pair")

        def select_pair(label):
            if label == "no contacts":
                return
            source, target = label.replace("p", "").split("-")
            selected["pair"] = (int(source), int(target))
            _draw_force_axes(fig, axes, selected["item"], selected["pair"])

        pair_control.update(
            {
                "axis": pair_axis,
                "radio": pair_radio,
                "connection": pair_radio.on_clicked(select_pair),
                "callback": select_pair,
            }
        )

    def redraw(rebuild_pairs=False):
        pairs, selected_pair = _draw_force_axes(
            fig,
            axes,
            selected["item"],
            selected["pair"],
        )
        selected["pair"] = selected_pair
        if rebuild_pairs:
            rebuild_pair_selector(pairs, selected_pair)

    def select_test(label):
        selected["item"] = next(item for item in items if item["name"] == label)
        selected["pair"] = None
        redraw(rebuild_pairs=True)

    test_connection = test_radio.on_clicked(select_test)
    redraw(rebuild_pairs=True)
    fig._force_plot_controls = {
        "test_radio": test_radio,
        "pair_control": pair_control,
        "callbacks": (select_test,),
        "connections": (test_connection,),
        "items": items,
        "selected": selected,
        "report_mode": report_mode,
    }
    plt.show()
    return fig


def run_force_plots(argv=None):
    """Run the interactive ForceDynamics plots."""
    import argparse

    parser = argparse.ArgumentParser(description="Plot ForceDynamics diagnostics.")
    parser.add_argument("path", help="Path to a run or batch cfg file.")
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the interactive ForceDynamics plot window.",
    )
    args = parser.parse_args(argv)
    return show_force_menu(Path(args.path))


if __name__ == "__main__":
    run_force_plots()
