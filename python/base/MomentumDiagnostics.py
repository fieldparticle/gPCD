import csv
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gbase import libconf


PLOT_WIDTH = 1100
PLOT_HEIGHT = 940
MARGIN_LEFT = 84
MARGIN_RIGHT = 32
MARGIN_TOP = 44
MARGIN_BOTTOM = 56
PANEL_GAP = 64
REPORT_MODES = {
    "live": "",
    "shadow": "_s",
}


def _float(row, key, default=0.0):
    value = row.get(key, default)
    if value in ("", None):
        return default
    return float(value)


def _read_rows(csv_path):
    with Path(csv_path).open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _report_path(report_dir, base_name, report_mode="live"):
    suffix = REPORT_MODES.get(report_mode, "")
    return Path(report_dir) / f"{base_name}{suffix}.csv"


def _particle_csvs(report_dir, report_mode="live"):
    suffix = REPORT_MODES.get(report_mode, "")
    csvs = sorted(Path(report_dir).glob(f"p*{suffix}.csv"))
    if suffix:
        return csvs
    return [csv_path for csv_path in csvs if not csv_path.stem.endswith("_s")]


def _particle_number_from_path(csv_path):
    stem = Path(csv_path).stem
    if stem.endswith("_s"):
        stem = stem[:-2]
    if stem.startswith("p"):
        try:
            return int(stem[1:])
        except ValueError:
            return stem
    return stem


def _particle_masses_from_cfg(cfg_path):
    if cfg_path is None:
        return {}
    cfg_path = Path(cfg_path)
    if not cfg_path.exists():
        return {}
    with cfg_path.open("r", encoding="utf-8") as cfg_file:
        cfg = libconf.load(cfg_file)
    masses = {}
    for particle_name, particle_cfg in cfg.get("PARTICLE_DATA", {}).items():
        try:
            particle_number = int(str(particle_name).lstrip("p") or 0)
        except ValueError:
            continue
        masses[particle_number] = float(particle_cfg.get("mass", 1.0))
    return masses


def _run_dt_from_cfg(cfg_path):
    if cfg_path is None:
        return None
    cfg_path = Path(cfg_path)
    if not cfg_path.exists():
        return None
    with cfg_path.open("r", encoding="utf-8") as cfg_file:
        cfg = libconf.load(cfg_file)
    run_cfg = cfg.get("RUN_CONFIGURATION", {})
    if "dt" not in run_cfg:
        return None
    return float(run_cfg["dt"])


def _particle_series(report_dir, cfg_path=None, report_mode="live"):
    masses = _particle_masses_from_cfg(cfg_path)
    series = []
    for particle_csv in _particle_csvs(report_dir, report_mode):
        rows = _read_rows(particle_csv)
        if not rows:
            continue
        particle_number = _particle_number_from_path(particle_csv)
        mass = masses.get(particle_number, 1.0)
        frames = [int(_float(row, "frame")) for row in rows]
        internal_momentum = [_float(row, "internal_mom") for row in rows]
        particle_pv = [
            mass
            * (
                _float(row, "vx") * _float(row, "vx")
                + _float(row, "vy") * _float(row, "vy")
                + _float(row, "vz") * _float(row, "vz")
            )
            ** 0.5
            for row in rows
        ]
        particle_start_minus_pv = [
            particle_pv[0] - value
            for value in particle_pv
        ]
        particle_ke = [
            0.5
            * mass
            * (
                _float(row, "vx") * _float(row, "vx")
                + _float(row, "vy") * _float(row, "vy")
                + _float(row, "vz") * _float(row, "vz")
            )
            for row in rows
        ]
        particle_frame_start_ke = [
            _float(row, "particle_frame_start_ke", particle_ke[index])
            for index, row in enumerate(rows)
        ]
        particle_after_resolve_ke = [
            _float(row, "particle_after_resolve_ke", particle_ke[index])
            for index, row in enumerate(rows)
        ]
        negative_ke = [-value for value in particle_ke]
        negative_frame_start_ke = [-value for value in particle_frame_start_ke]
        negative_after_resolve_ke = [-value for value in particle_after_resolve_ke]
        series.append(
            {
                "particle_number": particle_number,
                "frames": frames,
                "internal_momentum": internal_momentum,
                "particle_pv": particle_pv,
                "particle_start_minus_pv": particle_start_minus_pv,
                "negative_ke": negative_ke,
                "negative_frame_start_ke": negative_frame_start_ke,
                "negative_after_resolve_ke": negative_after_resolve_ke,
                "negative_ke_scaled": _scale_like(
                    negative_ke,
                    internal_momentum,
                ),
                "negative_frame_start_ke_scaled": _scale_like(
                    negative_frame_start_ke,
                    internal_momentum,
                ),
                "negative_after_resolve_ke_scaled": _scale_like(
                    negative_after_resolve_ke,
                    internal_momentum,
                ),
            }
        )
    return series


def _momentum_series(momentum_csv):
    momentum_csv = Path(momentum_csv)
    rows = _read_rows(momentum_csv)
    if not rows:
        raise ValueError(f"No rows in {momentum_csv}")
    current_ke = [_float(row, "curr_ke") for row in rows]
    negative_current_ke = [-value for value in current_ke]
    internal_total = [_float(row, "total_internal_mom") for row in rows]
    return {
        "frames": [int(_float(row, "frame")) for row in rows],
        "start_total": [_float(row, "start_total_p") for row in rows],
        "start_px": [_float(row, "start_px") for row in rows],
        "start_py": [_float(row, "start_total_py") for row in rows],
        "current_total": [_float(row, "curr_total_p") for row in rows],
        "current_px": [_float(row, "curr_px") for row in rows],
        "current_py": [_float(row, "curr_py") for row in rows],
        "internal_total": internal_total,
        "current_plus_internal": [
            _float(row, "curr_plus_internal_mom")
            for row in rows
        ],
        "momentum_balance": [
            _float(row, "start_minus_curr_plus_internal_mom")
            for row in rows
        ],
        "current_ke": current_ke,
        "negative_current_ke": negative_current_ke,
        "negative_current_ke_scaled": _scale_like(
            negative_current_ke,
            internal_total,
        ),
        "ke_drift": [_float(row, "ke_drift") for row in rows],
    }


def _scale_like(values, reference_values):
    value_min = min(values)
    value_max = max(values)
    reference_min = min(reference_values)
    reference_max = max(reference_values)
    if abs(value_max - value_min) <= 1.0e-15:
        midpoint = 0.5 * (reference_min + reference_max)
        return [midpoint for _value in values]
    reference_span = reference_max - reference_min
    return [
        reference_min + ((value - value_min) / (value_max - value_min)) * reference_span
        for value in values
    ]


def _batch_momentum_items(batch_cfg, report_mode="live"):
    batch_cfg = Path(batch_cfg)
    with batch_cfg.open("r", encoding="utf-8") as cfg_file:
        batch = libconf.load(cfg_file)
    base_dir = Path(batch["data_dir"])
    items = []
    for cfg_name, _end_frame in batch["batch_items"]:
        cfg_path = base_dir / cfg_name
        with cfg_path.open("r", encoding="utf-8") as cfg_file:
            cfg = libconf.load(cfg_file)
        report_dir = Path(cfg["RUN_CONFIGURATION"]["run_debug_dir"])
        momentum_csv = _report_path(report_dir, "momentum", report_mode)
        if not momentum_csv.exists():
            continue
        items.append(
            {
                "name": cfg.get("STUDY_NAME", cfg_path.stem),
                "cfg_path": cfg_path,
                "momentum_csv": momentum_csv,
            }
        )
    return items


def _scale(values, output_min, output_max):
    value_min = min(values)
    value_max = max(values)
    if abs(value_max - value_min) <= 1.0e-15:
        value_min -= 1.0
        value_max += 1.0

    def mapper(value):
        fraction = (value - value_min) / (value_max - value_min)
        return output_max - fraction * (output_max - output_min)

    return mapper, value_min, value_max


def _particle_style(particle_number):
    if particle_number == 1:
        return {"linestyle": "--", "marker": None}
    if particle_number == 2:
        return {"linestyle": "-", "marker": "*"}
    if particle_number == 3:
        return {"linestyle": "-", "marker": "o"}
    return {"linestyle": "-", "marker": None}


def _polyline(points, color, width=2, dash=""):
    if not points:
        return ""
    point_text = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
    dash_text = ' stroke-dasharray="5,5"' if dash else ""
    return (
        f'<polyline points="{point_text}" fill="none" '
        f'stroke="{color}" stroke-width="{width}"{dash_text} />'
    )


def _svg_marker(x, y, color, marker):
    if marker == "o":
        return f'<circle cx="{x:.3f}" cy="{y:.3f}" r="3.5" fill="{color}" />'
    if marker == "*":
        return (
            f'<text x="{x:.3f}" y="{y + 4:.3f}" font-family="Consolas, monospace" '
            f'font-size="14" fill="{color}" text-anchor="middle">*</text>'
        )
    return ""


def _text(x, y, text, size=14, color="#d8dee9", anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-family="Consolas, monospace" '
        f'font-size="{size}" fill="{color}" text-anchor="{anchor}">'
        f"{text}</text>"
    )


def _format_value(value):
    if abs(value) >= 0.001 and abs(value) < 10000:
        return f"{value:.6f}"
    return f"{value:.3e}"


def _draw_panel(frames, series, x_min, x_max, y_top, y_bottom, title):
    values = []
    for series_item in series:
        _label, _color, items = series_item[:3]
        values.extend(items)
    y_map, value_min, value_max = _scale(values, y_top, y_bottom)
    x_span = max(1, x_max - x_min)

    def x_map(frame):
        fraction = (frame - x_min) / x_span
        return MARGIN_LEFT + fraction * (PLOT_WIDTH - MARGIN_LEFT - MARGIN_RIGHT)

    elements = [
        f'<rect x="{MARGIN_LEFT}" y="{y_top}" '
        f'width="{PLOT_WIDTH - MARGIN_LEFT - MARGIN_RIGHT}" '
        f'height="{y_bottom - y_top}" fill="#111827" stroke="#526070" />',
        _text(MARGIN_LEFT, y_top - 14, title, 17, "#f2f5f8"),
        _text(12, y_top + 8, _format_value(value_max), 12, "#b7c0cc"),
        _text(12, y_bottom, _format_value(value_min), 12, "#b7c0cc"),
        _text(MARGIN_LEFT, y_bottom + 24, str(x_min), 12, "#b7c0cc"),
        _text(PLOT_WIDTH - MARGIN_RIGHT, y_bottom + 24, str(x_max), 12, "#b7c0cc", "end"),
    ]

    if value_min < 0.0 < value_max:
        zero_y = y_map(0.0)
        elements.append(
            f'<line x1="{MARGIN_LEFT}" y1="{zero_y:.3f}" '
            f'x2="{PLOT_WIDTH - MARGIN_RIGHT}" y2="{zero_y:.3f}" '
            f'stroke="#526070" stroke-dasharray="5,5" />'
        )

    legend_x = MARGIN_LEFT + 12
    legend_y = y_top + 22
    for series_item in series:
        label, color, items = series_item[:3]
        style = series_item[3] if len(series_item) > 3 else {}
        if isinstance(style, str):
            dash = bool(style)
            marker = None
        else:
            dash = style.get("linestyle") == "--"
            marker = style.get("marker")
        points = [
            (x_map(frame), y_map(value))
            for frame, value in zip(frames, items)
        ]
        elements.append(_polyline(points, color, dash=dash))
        if marker:
            step = max(1, len(points) // 24)
            for x, y in points[::step]:
                elements.append(_svg_marker(x, y, color, marker))
        dash_text = ' stroke-dasharray="5,5"' if dash else ""
        elements.append(
            f'<line x1="{legend_x}" y1="{legend_y - 4}" '
            f'x2="{legend_x + 24}" y2="{legend_y - 4}" '
            f'stroke="{color}" stroke-width="3"{dash_text} />'
        )
        if marker:
            elements.append(_svg_marker(legend_x + 12, legend_y - 4, color, marker))
        elements.append(_text(legend_x + 32, legend_y, label, 12))
        legend_y += 18

    return elements


def _report_mode_from_momentum_path(momentum_csv):
    return "shadow" if Path(momentum_csv).stem.endswith("_s") else "live"


def _particle_plot_series(momentum_csv, cfg_path=None):
    items = []
    colors = [
        "#8dd3c7",
        "#fb8072",
        "#80b1d3",
        "#fdb462",
        "#bebada",
        "#b3de69",
    ]
    report_mode = _report_mode_from_momentum_path(momentum_csv)
    for index, particle in enumerate(
        _particle_series(Path(momentum_csv).parent, cfg_path, report_mode)
    ):
        color = colors[index % len(colors)]
        particle_label = f"p{particle['particle_number']}"
        style = _particle_style(particle["particle_number"])
        items.append((f"{particle_label} internal", color, particle["internal_momentum"], style))
        items.append((f"{particle_label} -KE scaled", color, particle["negative_ke_scaled"], style))
    return items


def _particle_by_number(momentum_csv, cfg_path, particle_number):
    report_mode = _report_mode_from_momentum_path(momentum_csv)
    for particle in _particle_series(Path(momentum_csv).parent, cfg_path, report_mode):
        if particle["particle_number"] == particle_number:
            return particle
    return None


def _contact_series(momentum_csv, source_number, target_number, frames, field_name):
    report_mode = _report_mode_from_momentum_path(momentum_csv)
    contacts_csv = _report_path(Path(momentum_csv).parent, "contacts", report_mode)
    values_by_frame = {frame: 0.0 for frame in frames}
    if not contacts_csv.exists():
        return [0.0 for _frame in frames]
    for row in _read_rows(contacts_csv):
        if row.get("source") != str(source_number):
            continue
        if row.get("target") != str(target_number):
            continue
        frame = int(_float(row, "frame"))
        if frame in values_by_frame:
            values_by_frame[frame] += _float(row, field_name)
    return [values_by_frame[frame] for frame in frames]


def _source_contact_series(momentum_csv, source_number, frames, field_name):
    report_mode = _report_mode_from_momentum_path(momentum_csv)
    contacts_csv = _report_path(Path(momentum_csv).parent, "contacts", report_mode)
    values_by_frame = {frame: 0.0 for frame in frames}
    if not contacts_csv.exists():
        return [0.0 for _frame in frames]
    for row in _read_rows(contacts_csv):
        if row.get("source") != str(source_number):
            continue
        frame = int(_float(row, "frame"))
        if frame in values_by_frame:
            values_by_frame[frame] += _float(row, field_name)
    return [values_by_frame[frame] for frame in frames]


def _running_total(values):
    total = 0.0
    totals = []
    for value in values:
        total += value
        totals.append(total)
    return totals


def _plot_column_name(label):
    return (
        label.replace(" ", "_")
        .replace("->", "_to_")
        .replace("-", "neg_")
        .replace("/", "_")
    )


def _write_panel_data(output_dir, panel_name, frames, series):
    csv_path = Path(output_dir) / f"MomentumDiagnostics_{panel_name}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["frame", *[_plot_column_name(item[0]) for item in series]])
        for row_index, frame in enumerate(frames):
            writer.writerow(
                [
                    frame,
                    *[
                        item[2][row_index] if row_index < len(item[2]) else ""
                        for item in series
                    ],
                ]
            )
    return csv_path


def _write_panel_data_with_extra(output_dir, panel_name, frames, series, extra_series=None):
    extra_series = extra_series or []
    return _write_panel_data(output_dir, panel_name, frames, [*series, *extra_series])


def _latest(series, name):
    values = series.get(name, [])
    return values[-1] if values else 0.0


def _draw_totals_panel(axis, item, series):
    frame = _latest(series, "frames")
    mode = item.get("report_mode", _report_mode_from_momentum_path(item["momentum_csv"]))
    dt = _run_dt_from_cfg(item.get("cfg_path"))
    time_text = f"  time {frame * dt:.12g}" if dt is not None else ""
    lines = [
        f"{item['name']}  {mode}  frame {frame}{time_text}",
        (
            "start "
            f"p={_latest(series, 'start_total'):.12g} "
            f"px={_latest(series, 'start_px'):.12g} "
            f"py={_latest(series, 'start_py'):.12g}"
        ),
        (
            "current "
            f"p={_latest(series, 'current_total'):.12g} "
            f"px={_latest(series, 'current_px'):.12g} "
            f"py={_latest(series, 'current_py'):.12g}"
        ),
        (
            "internal "
            f"p={_latest(series, 'internal_total'):.12g} "
            f"curr+internal={_latest(series, 'current_plus_internal'):.12g} "
            f"drift={_latest(series, 'momentum_balance'):.12g}"
        ),
        (
            "KE "
            f"current={_latest(series, 'current_ke'):.12g} "
            f"drift={_latest(series, 'ke_drift'):.12g}"
        ),
    ]
    axis.clear()
    axis.set_axis_off()
    axis.text(
        0.01,
        0.5,
        "\n".join(lines),
        transform=axis.transAxes,
        va="center",
        ha="left",
        family="monospace",
        fontsize=10,
    )


def plot_momentum_diagnostics(momentum_csv, output_svg=None, title=None, cfg_path=None):
    momentum_csv = Path(momentum_csv)
    series_data = _momentum_series(momentum_csv)
    frames = series_data["frames"]
    start_total = series_data["start_total"]
    current_total = series_data["current_total"]
    internal_total = series_data["internal_total"]
    current_plus_internal = series_data["current_plus_internal"]
    momentum_balance = series_data["momentum_balance"]
    ke_drift = series_data["ke_drift"]
    p1 = _particle_by_number(momentum_csv, cfg_path, 1)
    bottom_frames = p1["frames"] if p1 else frames
    p1_compression = _source_contact_series(
        momentum_csv,
        1,
        bottom_frames,
        "compression_impulse",
    )
    p1_release = _source_contact_series(
        momentum_csv,
        1,
        bottom_frames,
        "release_impulse",
    )
    p1_parabolic_target = _source_contact_series(
        momentum_csv,
        1,
        bottom_frames,
        "parabolic_target_internal_mom",
    )
    p1_parabolic_compression = _source_contact_series(
        momentum_csv,
        1,
        bottom_frames,
        "parabolic_compression_impulse",
    )
    p1_parabolic_release = _source_contact_series(
        momentum_csv,
        1,
        bottom_frames,
        "parabolic_release_impulse",
    )
    p1_cumulative_compression = _running_total(p1_compression)
    p1_cumulative_release = _running_total(p1_release)
    p1_cumulative_parabolic_compression = _running_total(p1_parabolic_compression)
    p1_cumulative_parabolic_release = _running_total(p1_parabolic_release)
    top_series = _particle_plot_series(momentum_csv, cfg_path)
    middle_series = (
        [
            ("p1 internal_mom", "#fdb462", p1["internal_momentum"]),
            ("p1 pv", "#fb8072", p1["particle_pv"]),
            ("p1 start_minus_pv", "#80b1d3", p1["particle_start_minus_pv"]),
        ]
        if p1
        else [
            ("total_internal_mom", "#fdb462", internal_total),
            ("-curr_ke", "#bebada", series_data["negative_current_ke"]),
            ("-curr_ke scaled", "#80b1d3", series_data["negative_current_ke_scaled"]),
        ]
    )
    bottom_series = (
        [
            ("p1 internal_mom", "#fdb462", p1["internal_momentum"]),
            ("p1 cumulative_compression", "#fb8072", p1_cumulative_compression),
            ("p1 cumulative_release", "#80b1d3", p1_cumulative_release),
            ("p1 parabolic_target_internal_mom", "#b3de69", p1_parabolic_target),
            ("p1 -KE scaled", "#bebada", p1["negative_ke_scaled"]),
        ]
        if p1
        else []
    )
    middle_extra_series = (
        [
            ("p1 frame_start_ke", "", [-value for value in p1["negative_frame_start_ke"]]),
            ("p1 after_resolve_ke", "", [-value for value in p1["negative_after_resolve_ke"]]),
            ("p1 curr_ke", "", [-value for value in p1["negative_ke"]]),
        ]
        if p1
        else []
    )
    bottom_extra_series = (
        [
            ("p1 compression_impulse", "", p1_compression),
            ("p1 release_impulse", "", p1_release),
            ("p1 parabolic_compression_impulse", "", p1_parabolic_compression),
            ("p1 parabolic_release_impulse", "", p1_parabolic_release),
            ("p1 cumulative_parabolic_compression", "", p1_cumulative_parabolic_compression),
            ("p1 cumulative_parabolic_release", "", p1_cumulative_parabolic_release),
            ("p1 curr_ke", "", [-value for value in p1["negative_ke"]]),
        ]
        if p1
        else []
    )

    frame_min = min(frames)
    frame_max = max(frames)
    panel_height = (
        PLOT_HEIGHT
        - MARGIN_TOP
        - MARGIN_BOTTOM
        - 2 * PANEL_GAP
    ) / 3
    top_panel_top = MARGIN_TOP
    top_panel_bottom = top_panel_top + panel_height
    middle_panel_top = top_panel_bottom + PANEL_GAP
    middle_panel_bottom = middle_panel_top + panel_height
    bottom_panel_top = middle_panel_bottom + PANEL_GAP
    bottom_panel_bottom = PLOT_HEIGHT - MARGIN_BOTTOM

    title_text = title or momentum_csv.parent.name
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PLOT_WIDTH}" height="{PLOT_HEIGHT}" viewBox="0 0 {PLOT_WIDTH} {PLOT_HEIGHT}">',
        '<rect width="100%" height="100%" fill="#0b1020" />',
        _text(PLOT_WIDTH / 2, 26, title_text, 20, "#f2f5f8", "middle"),
    ]

    elements.extend(
        _draw_panel(
            frames,
            top_series,
            frame_min,
            frame_max,
            top_panel_top,
            top_panel_bottom,
            "Particle Internal Momentum vs Scaled KE",
        )
    )
    elements.extend(
        _draw_panel(
            bottom_frames,
            middle_series,
            min(p1["frames"]) if p1 else frame_min,
            max(p1["frames"]) if p1 else frame_max,
            middle_panel_top,
            middle_panel_bottom,
            (
                "p1 Internal Momentum vs Velocity Momentum"
                if p1
                else "Internal Momentum vs Reversed Kinetic Energy"
            ),
        )
    )
    if p1:
        elements.extend(
            _draw_panel(
                bottom_frames,
                bottom_series,
                min(p1["frames"]),
                max(p1["frames"]),
                bottom_panel_top,
                bottom_panel_bottom,
                "p1 Internal Momentum vs Cumulative Compression/Release",
            )
        )

    elements.append("</svg>")
    output_svg = Path(output_svg) if output_svg else momentum_csv.with_name("momentum_diagnostics.svg")
    output_svg.write_text("\n".join(elements), encoding="utf-8")
    _write_panel_data(momentum_csv.parent, "top", frames, top_series)
    _write_panel_data_with_extra(
        momentum_csv.parent,
        "middle",
        bottom_frames,
        middle_series,
        middle_extra_series,
    )
    if bottom_series:
        _write_panel_data_with_extra(
            momentum_csv.parent,
            "bottom",
            bottom_frames,
            bottom_series,
            bottom_extra_series,
        )
    return output_svg


def plot_batch(batch_cfg, report_mode="live"):
    outputs = []
    for item in _batch_momentum_items(batch_cfg, report_mode):
        outputs.append(
            plot_momentum_diagnostics(
                item["momentum_csv"],
                title=item["name"],
                cfg_path=item["cfg_path"],
            )
        )
    return outputs


def _draw_matplotlib_axes(fig, axes, item, particle_visible=None):
    series = _momentum_series(item["momentum_csv"])
    frames = series["frames"]
    totals_axis, top_axis, middle_axis, bottom_axis = axes
    _draw_totals_panel(totals_axis, item, series)
    top_axis.clear()
    middle_axis.clear()
    bottom_axis.clear()
    particle_visible = particle_visible or {}

    for particle in _particle_series(
        Path(item["momentum_csv"]).parent,
        item.get("cfg_path"),
        _report_mode_from_momentum_path(item["momentum_csv"]),
    ):
        particle_label = f"p{particle['particle_number']}"
        style = _particle_style(particle["particle_number"])
        markevery = max(1, len(particle["frames"]) // 24)
        visible = particle_visible.get(particle_label, True)
        top_axis.plot(
            particle["frames"],
            particle["internal_momentum"],
            label=f"{particle_label} internal",
            linewidth=2,
            linestyle=style["linestyle"],
            marker=style["marker"],
            markevery=markevery,
            visible=visible,
        )
        top_axis.plot(
            particle["frames"],
            particle["negative_ke_scaled"],
            label=f"{particle_label} -KE scaled",
            linewidth=2,
            linestyle=style["linestyle"],
            marker=style["marker"],
            markevery=markevery,
            visible=visible,
        )
    top_axis.set_ylabel("particle value")
    top_axis.set_title(f"{item['name']} ({item.get('report_mode', 'live')})")
    top_axis.grid(True, alpha=0.3)
    top_axis.legend(loc="best")

    p1 = _particle_by_number(item["momentum_csv"], item.get("cfg_path"), 1)
    if p1:
        middle_axis.plot(
            p1["frames"],
            p1["internal_momentum"],
            label="p1 internal_mom",
            linewidth=2,
        )
        middle_axis.plot(
            p1["frames"],
            p1["particle_pv"],
            label="p1 pv",
            linewidth=2,
        )
        middle_axis.plot(
            p1["frames"],
            p1["particle_start_minus_pv"],
            label="p1 start_minus_pv",
            linewidth=2,
        )
        middle_axis.set_title("p1 Internal Momentum vs Velocity Momentum")
    else:
        middle_axis.plot(frames, series["internal_total"], label="total_internal_mom", linewidth=2)
        middle_axis.plot(frames, series["negative_current_ke"], label="-curr_ke", linewidth=2)
        middle_axis.plot(
            frames,
            series["negative_current_ke_scaled"],
            label="-curr_ke scaled to internal_mom",
            linewidth=2,
            linestyle="--",
        )
        middle_axis.set_title("Internal Momentum vs Reversed Kinetic Energy")
    middle_axis.axhline(0.0, color="black", linewidth=1, alpha=0.5)
    middle_axis.set_ylabel("diagnostic value")
    middle_axis.grid(True, alpha=0.3)
    middle_axis.legend(loc="best")

    if p1:
        p1_compression = _source_contact_series(
            item["momentum_csv"],
            1,
            p1["frames"],
            "compression_impulse",
        )
        p1_release = _source_contact_series(
            item["momentum_csv"],
            1,
            p1["frames"],
            "release_impulse",
        )
        p1_parabolic_target = _source_contact_series(
            item["momentum_csv"],
            1,
            p1["frames"],
            "parabolic_target_internal_mom",
        )
        bottom_axis.plot(
            p1["frames"],
            p1["internal_momentum"],
            label="p1 internal_mom",
            linewidth=2,
        )
        bottom_axis.plot(
            p1["frames"],
            _running_total(p1_compression),
            label="p1 cumulative_compression",
            linewidth=2,
        )
        bottom_axis.plot(
            p1["frames"],
            _running_total(p1_release),
            label="p1 cumulative_release",
            linewidth=2,
        )
        bottom_axis.plot(
            p1["frames"],
            p1_parabolic_target,
            label="p1 parabolic_target_internal_mom",
            linewidth=2,
        )
        bottom_axis.plot(
            p1["frames"],
            p1["negative_ke_scaled"],
            label="p1 -KE scaled",
            linewidth=2,
            linestyle="--",
        )
        bottom_axis.set_title("p1 Internal Momentum vs Cumulative Compression/Release")
    bottom_axis.axhline(0.0, color="black", linewidth=1, alpha=0.5)
    bottom_axis.set_xlabel("frame")
    bottom_axis.set_ylabel("diagnostic value")
    bottom_axis.grid(True, alpha=0.3)
    bottom_axis.legend(loc="best")

    fig.canvas.manager.set_window_title(
        f"Momentum Diagnostics - {item['name']} ({item.get('report_mode', 'live')})"
    )
    fig.canvas.draw_idle()


def show_batch_menu(batch_cfg, report_mode="live"):
    try:
        import matplotlib.pyplot as plt
        from matplotlib.widgets import CheckButtons, RadioButtons
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "matplotlib is required for the interactive diagnostics menu. "
            "Run with .venv\\Scripts\\python.exe or install matplotlib."
        ) from exc

    current_report_mode = {"mode": report_mode}
    items = _batch_momentum_items(batch_cfg, current_report_mode["mode"])
    if not items:
        raise ValueError(
            f"No momentum CSV files found for {batch_cfg} in {current_report_mode['mode']} mode"
        )
    for item in items:
        item["report_mode"] = current_report_mode["mode"]

    fig, axes = plt.subplots(
        4,
        1,
        figsize=(12, 11),
        sharex=False,
        gridspec_kw={"height_ratios": [0.9, 2.0, 2.0, 2.0]},
    )
    fig.subplots_adjust(left=0.32, hspace=0.48)
    menu_axis = fig.add_axes([0.03, 0.35, 0.24, 0.49])
    labels = [item["name"] for item in items]
    radio = RadioButtons(menu_axis, labels, active=0)
    menu_axis.set_title("Test")
    mode_axis = fig.add_axes([0.03, 0.24, 0.24, 0.08])
    mode_labels = list(REPORT_MODES.keys())
    mode_radio = RadioButtons(
        mode_axis,
        mode_labels,
        active=mode_labels.index(current_report_mode["mode"]),
    )
    mode_axis.set_title("Report")
    particle_visible = {"p1": True, "p2": True, "p3": True}
    particle_axis = fig.add_axes([0.03, 0.08, 0.24, 0.14])
    particle_checks = CheckButtons(
        particle_axis,
        list(particle_visible.keys()),
        list(particle_visible.values()),
    )
    particle_axis.set_title("Particles")
    selected_item = {"item": items[0], "name": items[0]["name"]}

    def select(label):
        for item in items:
            if item["name"] == label:
                selected_item["item"] = item
                selected_item["name"] = label
                _draw_matplotlib_axes(fig, axes, item, particle_visible)
                return

    def select_mode(label):
        current_report_mode["mode"] = label
        new_items = _batch_momentum_items(batch_cfg, label)
        for item in new_items:
            item["report_mode"] = label
        if not new_items:
            return
        items[:] = new_items
        selected_name = selected_item.get("name")
        selected_item["item"] = next(
            (item for item in items if item["name"] == selected_name),
            items[0],
        )
        selected_item["name"] = selected_item["item"]["name"]
        _draw_matplotlib_axes(fig, axes, selected_item["item"], particle_visible)

    def toggle_particle(label):
        particle_visible[label] = not particle_visible[label]
        for line in axes[1].lines:
            if line.get_label().startswith(f"{label} "):
                line.set_visible(particle_visible[label])
        axes[1].legend(loc="best")
        fig.canvas.draw_idle()

    radio.on_clicked(select)
    mode_radio.on_clicked(select_mode)
    particle_checks.on_clicked(toggle_particle)
    _draw_matplotlib_axes(fig, axes, selected_item["item"], particle_visible)
    plt.show()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Plot momentum/internal-momentum and KE drift diagnostics.",
    )
    parser.add_argument(
        "path",
        help="Path to momentum.csv or a batch cfg file.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show an interactive matplotlib menu for a batch cfg.",
    )
    parser.add_argument(
        "--svg",
        action="store_true",
        help="Write SVG files instead of showing the matplotlib menu.",
    )
    parser.add_argument(
        "--report-mode",
        choices=sorted(REPORT_MODES.keys()),
        default="live",
        help="Choose live CSV files or shadow *_s.csv files.",
    )
    args = parser.parse_args()
    path = Path(args.path)
    if args.show or (path.suffix.lower() == ".cfg" and not args.svg):
        show_batch_menu(path, args.report_mode)
        return
    if path.suffix.lower() == ".cfg":
        outputs = plot_batch(path, args.report_mode)
    else:
        outputs = [plot_momentum_diagnostics(path)]
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
