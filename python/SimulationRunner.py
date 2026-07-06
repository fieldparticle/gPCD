import pygame
from pathlib import Path
import math

from base.ForceDynamicsBase import ForceDynamics
from base.VerAForceDynamicsBase import ForceDynamics as VerAForceDynamics
from base.Reporting import Reporting
from base.InLineTest import InLineTest
#from gbase import libconf
import io, libconf
from gbase.utilities import get_cell_dimensions, hsv_angle
from gbase.ParametricCurve import evaluate_point


BASE_CLASS_REGISTRY = {
    "ForceDynamics": ForceDynamics,
    "VerAForceDynamics": VerAForceDynamics,
}


def _particle_util_cfg():
    cfg_file = Path(__file__).resolve().parent / "ParticleUtil.cfg"
    if not cfg_file.exists():
        return {}
    with cfg_file.open("r") as handle:
        return libconf.load(handle)


def _base_class_from_config(
    particle_util_cfg,
    field_name,
    default_name,
    allow_none=False,
):
    base_name = str(particle_util_cfg.get(field_name, default_name))
    if allow_none and base_name.lower() == "none":
        return None
    if base_name not in BASE_CLASS_REGISTRY:
        allowed_names = sorted(BASE_CLASS_REGISTRY)
        if allow_none:
            allowed_names.append("none")
        raise ValueError(
            f"ParticleUtil.cfg {field_name}={base_name!r} is not registered. "
            f"Allowed base classes: {', '.join(allowed_names)}"
        )
    return BASE_CLASS_REGISTRY[base_name]


def _create_configured_bases():
    particle_util_cfg = _particle_util_cfg()
    live_base_class = _base_class_from_config(
        particle_util_cfg,
        "live_base",
        "ForceDynamics",
    )
    shadow_base_class = _base_class_from_config(
        particle_util_cfg,
        "shadow_base",
        "none",
        allow_none=True,
    )
    shadow = shadow_base_class() if shadow_base_class is not None else None
    return live_base_class(), shadow


def _display_base_from_config(shadow):
    particle_util_cfg = _particle_util_cfg()
    display_base = str(particle_util_cfg.get("display_base", "live")).lower()
    if display_base not in ("live", "shadow"):
        raise ValueError(
            "ParticleUtil.cfg display_base must be 'live' or 'shadow'. "
            f"Got {display_base!r}."
        )
    if display_base == "shadow" and shadow is None:
        raise ValueError(
            "ParticleUtil.cfg display_base cannot be 'shadow' when "
            "shadow_base is 'none'."
        )
    return display_base


def _clear_report_directory(report_dir):
    report_dir.mkdir(parents=True, exist_ok=True)
    deleted_count = 0
    for report_file in report_dir.iterdir():
        if report_file.is_file():
            report_file.unlink()
            deleted_count += 1
    return deleted_count

def _window_size(run_configuration):
    window_size = run_configuration.get("window_size", (1000, 1000))
    return int(window_size[0]), int(window_size[1])


def _presentation_quality(run_configuration):
    return bool(run_configuration.get("presentation_quality", False))


def _as_points(run_configuration):
    if _presentation_quality(run_configuration):
        return False
    return bool(run_configuration.get("as_points", False))


def _view_box(run_configuration):
    cell_width, cell_height, _ = get_cell_dimensions(run_configuration)
    x_axis_lims = run_configuration.get("x_axis_lims")
    y_axis_lims = run_configuration.get("y_axis_lims")
    if x_axis_lims is not None and len(x_axis_lims) >= 2:
        x_min = float(x_axis_lims[0])
        x_max = float(x_axis_lims[1])
    else:
        x_min = float(run_configuration.get("WallXMIN", 0.0))
        x_max = float(
            run_configuration.get(
                "WallXMAX",
                cell_width,
            )
        )
    if y_axis_lims is not None and len(y_axis_lims) >= 2:
        y_min = float(y_axis_lims[0])
        y_max = float(y_axis_lims[1])
    else:
        y_min = float(run_configuration.get("WallYMIN", 0.0))
        y_max = float(
            run_configuration.get(
                "WallYMAX",
                cell_height,
            )
        )
    zoom = float(run_configuration.get("zoom", 1.0))
    if zoom <= 0.0:
        zoom = 1.0

    center_x = (x_min + x_max) * 0.5
    center_y = (y_min + y_max) * 0.5
    half_width = (x_max - x_min) * 0.5 / zoom
    half_height = (y_max - y_min) * 0.5 / zoom
    return (
        center_x - half_width,
        center_x + half_width,
        center_y - half_height,
        center_y + half_height,
    )


def _to_screen(x, y, view_box, screen_width, screen_height):
    x_min, x_max, y_min, y_max = view_box
    sx = int((x - x_min) / (x_max - x_min) * screen_width)
    sy = int(screen_height - ((y - y_min) / (y_max - y_min) * screen_height))
    return sx, sy


def _radius_to_pixels(radius, view_box, screen_width, screen_height):
    x_min, x_max, y_min, y_max = view_box
    scale_x = screen_width / (x_max - x_min)
    scale_y = screen_height / (y_max - y_min)
    return max(3, int(radius * min(scale_x, scale_y)))


def _draw_overlap_lens(screen, left_center, left_radius, right_center, right_radius):
    min_x = max(0, min(left_center[0] - left_radius, right_center[0] - right_radius))
    min_y = max(0, min(left_center[1] - left_radius, right_center[1] - right_radius))
    max_x = min(screen.get_width(), max(left_center[0] + left_radius, right_center[0] + right_radius))
    max_y = min(screen.get_height(), max(left_center[1] + left_radius, right_center[1] + right_radius))
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0:
        return

    left_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    right_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.circle(
        left_surface,
        (255, 255, 255, 255),
        (left_center[0] - min_x, left_center[1] - min_y),
        left_radius,
    )
    pygame.draw.circle(
        right_surface,
        (255, 255, 255, 255),
        (right_center[0] - min_x, right_center[1] - min_y),
        right_radius,
    )

    left_mask = pygame.mask.from_surface(left_surface)
    right_mask = pygame.mask.from_surface(right_surface)
    overlap_mask = left_mask.overlap_mask(right_mask, (0, 0))
    overlap_surface = overlap_mask.to_surface(
        setcolor=(255, 255, 255, 80),
        unsetcolor=(0, 0, 0, 0),
    )
    screen.blit(overlap_surface, (min_x, min_y))


def _particle_momentum(particle):
    mass = float(getattr(particle, "mass", 1.0))
    return mass * float(particle.vx), mass * float(particle.vy)


def _particle_kinetic_energy(particle):
    mass = float(getattr(particle, "mass", 1.0))
    vx = float(particle.vx)
    vy = float(particle.vy)
    vz = float(getattr(particle, "vz", 0.0))
    return 0.5 * mass * (vx * vx + vy * vy + vz * vz)


def _active_particles(particles, dynamics=None):
    return [
        particle
        for particle_index, particle in enumerate(particles)
        if _is_active_particle(particle_index, dynamics)
    ]


def _is_active_particle(particle_index, dynamics=None):
    if dynamics is not None and hasattr(
        dynamics, "IsMobileParticleActiveForDynamics"
    ):
        return dynamics.IsMobileParticleActiveForDynamics(particle_index)
    return particle_index != 0


def _is_visible_particle(particle_index, particle, dynamics=None):
    if dynamics is not None and hasattr(dynamics, "IsNullParticle"):
        if dynamics.IsNullParticle(particle_index):
            return False
    elif particle_index == 0:
        return False
    return float(getattr(getattr(particle, "Data", None), "w", 0.0)) >= 0.0


def _is_boundary_particle(particle_index, particle, dynamics=None):
    if dynamics is not None and hasattr(dynamics, "IsBoundaryParticle"):
        return dynamics.IsBoundaryParticle(particle_index)
    return float(getattr(particle, "ptype", 0.0)) > 0.5


def _particle_colors(
    particle_index,
    particle,
    dynamics,
    hsv_color,
    hsv_sat,
    hsv_val,
):
    if _is_boundary_particle(particle_index, particle, dynamics):
        return (60, 220, 90), (150, 255, 175)
    if hsv_color:
        color = hsv_angle(particle.VelRad.w, hsv_val, hsv_sat)
        return color, color
    if _has_active_wall_contact(particle) or particle.collision_list:
        return (255, 60, 60), (255, 210, 210)
    return (65, 125, 255), (145, 190, 255)


def _blend_color(first, second, amount):
    amount = max(0.0, min(1.0, float(amount)))
    return tuple(
        int(round(first[index] * (1.0 - amount) + second[index] * amount))
        for index in range(3)
    )


def _draw_presentation_sphere(screen, center, radius, fill, edge):
    """Draw a shaded pseudo-3D sphere using inexpensive concentric layers."""
    radius = max(2, int(radius))
    shadow_center = (
        center[0] + max(1, radius // 8),
        center[1] + max(1, radius // 8),
    )
    shadow_color = _blend_color(fill, (0, 0, 0), 0.65)
    pygame.draw.circle(screen, shadow_color, shadow_center, radius)

    dark_fill = _blend_color(fill, (0, 0, 0), 0.35)
    pygame.draw.circle(screen, dark_fill, center, radius)
    layer_count = min(18, radius)
    for layer_index in range(layer_count):
        fraction = layer_index / max(1, layer_count - 1)
        layer_radius = max(1, radius - int(fraction * radius * 0.72))
        layer_center = (
            center[0] - int(fraction * radius * 0.22),
            center[1] - int(fraction * radius * 0.22),
        )
        layer_color = _blend_color(dark_fill, fill, 0.35 + 0.65 * fraction)
        pygame.draw.circle(screen, layer_color, layer_center, layer_radius)

    highlight_radius = max(1, radius // 5)
    highlight_center = (
        center[0] - max(1, radius // 3),
        center[1] - max(1, radius // 3),
    )
    highlight_color = _blend_color(fill, (255, 255, 255), 0.72)
    pygame.draw.circle(screen, highlight_color, highlight_center, highlight_radius)
    pygame.draw.circle(screen, edge, center, radius, max(1, radius // 12))


def _total_momentum(particles, dynamics=None):
    total_x = 0.0
    total_y = 0.0
    for particle in _active_particles(particles, dynamics):
        momentum_x, momentum_y = _particle_momentum(particle)
        total_x += momentum_x
        total_y += momentum_y
    return total_x, total_y


def _total_kinetic_energy(particles, dynamics=None):
    return sum(
        _particle_kinetic_energy(particle)
        for particle in _active_particles(particles, dynamics)
    )


def _total_potential_energy(dynamics):
    total_potential_energy = getattr(dynamics, "TotalPotentialEnergy", None)
    if total_potential_energy is None:
        return 0.0
    return float(total_potential_energy())


def _total_report_kinetic_energy(particles, field_name, dynamics=None):
    return sum(
        float(getattr(particle, field_name, 0.0))
        for particle in _active_particles(particles, dynamics)
    )


def _particle_internal_momentum(particle):
    parms = getattr(particle, "parms", None)
    if parms is not None:
        return (
            float(getattr(parms, "y", 0.0)),
            float(getattr(parms, "z", 0.0)),
            float(getattr(parms, "w", 0.0)),
        )
    return (
        float(getattr(particle, "internal_momentum_px", 0.0)),
        float(getattr(particle, "internal_momentum_py", 0.0)),
        float(getattr(particle, "internal_momentum_pz", 0.0)),
    )


def _total_internal_momentum(particles, dynamics=None):
    total_x = 0.0
    total_y = 0.0
    total_z = 0.0
    for particle in _active_particles(particles, dynamics):
        internal_x, internal_y, internal_z = _particle_internal_momentum(particle)
        total_x += internal_x
        total_y += internal_y
        total_z += internal_z
    return total_x, total_y, total_z


def _sequential_contact_diagnostics(particles):
    """Read source-zero diagnostics for its next sequential particle contact."""
    if len(particles) < 2:
        return 0.0, 0.0

    source_index = next(
        (
            particle_index
            for particle_index in range(len(particles))
            if _is_active_particle(particle_index)
        ),
        None,
    )
    if source_index is None:
        return 0.0, 0.0
    source = particles[source_index]
    contacts = getattr(source, "contacts", getattr(source, "gcs", []))
    for contact in contacts:
        is_particle_contact = getattr(contact.ids, "y", 0) == 1
        is_active = getattr(contact.ids, "w", 0) == 1
        target_id = int(getattr(contact.ids, "x", -1))
        if is_particle_contact and is_active and target_id == 1:
            return (
                float(getattr(contact, "rel_vn", 0.0)),
                float(getattr(contact, "raw_impulse", 0.0)),
            )
    return 0.0, 0.0


def _has_active_wall_contact(particle):
    contacts = getattr(particle, "contacts", getattr(particle, "gcs", []))
    for contact in contacts:
        ids = getattr(contact, "ids", None)
        if ids is None:
            continue
        if int(getattr(ids, "y", 0)) == 2 and int(getattr(ids, "w", 0)) == 1:
            return True
    return False


def _run_start_diagnostics(dynamics):
    particles = dynamics.particles
    ke = _total_kinetic_energy(particles, dynamics)
    potential_energy = _total_potential_energy(dynamics)
    return {
        "total_momentum": _total_momentum(particles, dynamics),
        "ke": ke,
        "potential_energy": potential_energy,
        "total_energy": ke + potential_energy,
    }


def _motion_summary(start_diagnostics, particles, dynamics=None):
    start_total_momentum = start_diagnostics["total_momentum"]
    start_x, start_y = start_total_momentum
    current_x, current_y = _total_momentum(particles, dynamics)
    current_total_p = math.hypot(current_x, current_y)
    momentum_drift_x = current_x - start_x
    momentum_drift_y = current_y - start_y
    internal_x, internal_y, internal_z = _total_internal_momentum(particles, dynamics)
    total_internal_momentum = math.sqrt(
        internal_x * internal_x
        + internal_y * internal_y
        + internal_z * internal_z
    )
    curr_plus_internal_mom = math.hypot(current_x + internal_x, current_y + internal_y)
    start_ke = start_diagnostics["ke"]
    current_ke = _total_kinetic_energy(particles, dynamics)
    potential_energy = _total_potential_energy(dynamics) if dynamics is not None else 0.0
    total_energy = current_ke + potential_energy
    frame_start_ke = _total_report_kinetic_energy(
        particles,
        "report_frame_start_ke",
        dynamics,
    )
    after_resolve_ke = _total_report_kinetic_energy(
        particles,
        "report_after_resolve_ke",
        dynamics,
    )
    v_rel, raw_impulse = _sequential_contact_diagnostics(particles)
    piston_position = 0.0
    piston_velocity = (0.0, 0.0, 0.0)
    piston_contacts = 0
    piston_frame_impulse = 0.0
    piston_total_impulse = 0.0
    piston_total_momentum = (0.0, 0.0, 0.0)
    error_code = 0
    error_description = "ERROR_NONE"
    error_source = -1
    error_target = -1
    error_wall = 0
    if dynamics is not None:
        error_code = int(getattr(dynamics.collIn, "ErrorReturn", 0))
        error_description = dynamics.ErrorDescription()
        error_source = int(getattr(dynamics.collIn, "ErrorSourceID", -1))
        error_target = int(getattr(dynamics.collIn, "ErrorTargetID", -1))
        error_wall = int(getattr(dynamics.collIn, "ErrorWallFlag", 0))
    if dynamics is not None and dynamics.PistonEnabled():
        frame_number = int(dynamics.ShaderFlags.frameNum)
        piston_position = dynamics.GetPistonPosition(frame_number)
        velocity = dynamics.GetPistonVelocity(frame_number)
        piston_velocity = (velocity.x, velocity.y, velocity.z)
        piston_contacts = int(getattr(dynamics, "piston_contact_count", 0))
        piston_frame_impulse = float(
            getattr(dynamics, "piston_frame_impulse", 0.0)
        )
        piston_total_impulse = float(
            getattr(dynamics, "piston_total_impulse", 0.0)
        )
        total_transfer = getattr(dynamics, "piston_total_momentum", None)
        if total_transfer is not None:
            piston_total_momentum = (
                float(total_transfer.x),
                float(total_transfer.y),
                float(total_transfer.z),
            )

    return {
        "start_total_px": start_x,
        "start_total_py": start_y,
        "start_total_p": math.hypot(start_x, start_y),
        "current_total_px": current_x,
        "current_total_py": current_y,
        "current_total_p": current_total_p,
        "momentum_drift_x": momentum_drift_x,
        "momentum_drift_y": momentum_drift_y,
        "momentum_drift": math.hypot(momentum_drift_x, momentum_drift_y),
        "total_internal_mom": total_internal_momentum,
        "internal_px": internal_x,
        "internal_py": internal_y,
        "internal_pz": internal_z,
        "curr_plus_internal_mom": curr_plus_internal_mom,
        "start_minus_curr_plus_internal_mom": (
            math.hypot(start_x, start_y) - curr_plus_internal_mom
        ),
        "start_ke": start_ke,
        "curr_ke": current_ke,
        "frame_start_ke": frame_start_ke,
        "after_resolve_ke": after_resolve_ke,
        "ke_drift": current_ke - start_ke,
        "potential_energy": potential_energy,
        "total_energy": total_energy,
        "energy_drift": total_energy - start_diagnostics["total_energy"],
        "v_rel": v_rel,
        "raw_impulse": raw_impulse,
        "piston_position": piston_position,
        "piston_velocity_x": piston_velocity[0],
        "piston_velocity_y": piston_velocity[1],
        "piston_velocity_z": piston_velocity[2],
        "piston_contacts": piston_contacts,
        "piston_frame_impulse": piston_frame_impulse,
        "piston_total_impulse": piston_total_impulse,
        "piston_total_px": piston_total_momentum[0],
        "piston_total_py": piston_total_momentum[1],
        "piston_total_pz": piston_total_momentum[2],
        "error_code": error_code,
        "error_description": error_description,
        "error_source": error_source,
        "error_target": error_target,
        "error_wall": error_wall,
    }


def _table_number(value):
    if value is None:
        return f"{'':>14}"
    return f"{value:>14.8f}"


def _summary_table_row(label, total=None, px=None, py=None, combined=None, drift=None):
    return (
        f"{label:<12}"
        f"{_table_number(total)} "
        f"{_table_number(px)} "
        f"{_table_number(py)} "
        f"{_table_number(combined)} "
        f"{_table_number(drift)}"
    )


def _summary_table_header():
    return (
        f"{'metric':<12}"
        f"{'total':>14} "
        f"{'px':>14} "
        f"{'py':>14} "
        f"{'curr+int':>14} "
        f"{'drift':>14}"
    )


def _particle_report_row(particle):
    internal_momentum = float(
        getattr(
            particle,
            "internal_momentum",
            getattr(particle, "report_stored_mom", 0.0),
        )
    )
    return (
        f"p{int(particle.pnum):>3}"
        f" x={particle.rx:>13.6f}"
        f" y={particle.ry:>13.6f}"
        f" vx={particle.vx:>13.6f}"
        f" vy={particle.vy:>13.6f}"
        f" int_mom={internal_momentum:>14.8f}"
    )


def _draw_world_rect(screen, bounds, view_box, color, width):
    screen_width, screen_height = screen.get_size()
    x_min, x_max, y_min, y_max = bounds
    left_top = _to_screen(
        x_min, y_max, view_box, screen_width, screen_height
    )
    right_bottom = _to_screen(
        x_max, y_min, view_box, screen_width, screen_height
    )
    rectangle = pygame.Rect(
        min(left_top[0], right_bottom[0]),
        min(left_top[1], right_bottom[1]),
        abs(right_bottom[0] - left_top[0]),
        abs(right_bottom[1] - left_top[1]),
    )
    pygame.draw.rect(screen, color, rectangle, width)


def _draw_configuration_boundaries(screen, run_configuration, view_box):
    """Draw the cell domain, death planes, and physical wall curves."""
    screen_width, screen_height = screen.get_size()
    cell_width, cell_height, _ = get_cell_dimensions(run_configuration)
    if cell_width > 0 and cell_height > 0:
        _draw_world_rect(
            screen,
            (0.0, float(cell_width), 0.0, float(cell_height)),
            view_box,
            (50, 110, 255),
            2,
        )

    death_bounds = run_configuration.get("death_bounds")
    if death_bounds is not None and len(death_bounds) >= 4:
        _draw_world_rect(
            screen,
            tuple(float(value) for value in death_bounds[:4]),
            view_box,
            (255, 60, 60),
            2,
        )

    segments = run_configuration.get("curve_wall_segments", ())
    for segment in segments:
        points = []
        for sample_index in range(65):
            parameter = sample_index / 64.0
            point_x, point_y = evaluate_point(segment, parameter)
            points.append(
                _to_screen(
                    point_x,
                    point_y,
                    view_box,
                    screen_width,
                    screen_height,
                )
            )
        pygame.draw.lines(screen, (60, 220, 90), False, points, 3)


def _draw_particles(
    screen,
    particles,
    run_configuration,
    dynamics,
    frame_number,
    test_file_name,
    start_diagnostics,
    error_return=0,
    error_description="",
):
    screen_width, screen_height = screen.get_size()
    view_box = _view_box(run_configuration)
    screen.fill((14, 18, 24))
    _draw_configuration_boundaries(screen, run_configuration, view_box)
    presentation_quality = _presentation_quality(run_configuration)
    as_points = _as_points(run_configuration)

    if as_points:
        hsv_color = bool(run_configuration.get("hsv_color", False))
        hsv_sat = float(run_configuration.get("hsv_sat", 0.707))
        hsv_val = float(run_configuration.get("hsv_val", 1.0))
        for index, particle in enumerate(particles):
            if not _is_visible_particle(index, particle, dynamics):
                continue
            center = _to_screen(
                particle.rx,
                particle.ry,
                view_box,
                screen_width,
                screen_height,
            )
            fill, _edge = _particle_colors(
                index,
                particle,
                dynamics,
                hsv_color,
                hsv_sat,
                hsv_val,
            )
            pygame.draw.circle(screen, fill, center, 1)
        pygame.display.flip()
        return

    motion_summary = _motion_summary(
        start_diagnostics,
        particles,
        dynamics,
    )

    if dynamics is not None and dynamics.PistonEnabled():
        chamber_bounds = run_configuration["chamber_bounds"]
        piston_x = dynamics.GetPistonPosition(frame_number)
        piston_bottom = _to_screen(
            piston_x,
            float(chamber_bounds[2]),
            view_box,
            screen_width,
            screen_height,
        )
        piston_top = _to_screen(
            piston_x,
            float(chamber_bounds[3]),
            view_box,
            screen_width,
            screen_height,
        )
        pygame.draw.line(
            screen,
            (255, 210, 70),
            piston_bottom,
            piston_top,
            4,
        )

    hsv_color = bool(run_configuration.get("hsv_color", False))
    hsv_sat = float(run_configuration.get("hsv_sat", 0.707))
    hsv_val = float(run_configuration.get("hsv_val", 1.0))
    particle_screen_data = []
    for index, particle in enumerate(particles):
        if not _is_visible_particle(index, particle, dynamics):
            continue
        center = _to_screen(particle.rx, particle.ry, view_box, screen_width, screen_height)
        radius = (
            1
            if as_points
            else _radius_to_pixels(
                particle.radius,
                view_box,
                screen_width,
                screen_height,
            )
        )
        fill, edge = _particle_colors(
            index,
            particle,
            dynamics,
            hsv_color,
            hsv_sat,
            hsv_val,
        )
        particle_screen_data.append((index, particle, center, radius, edge))
        if presentation_quality:
            _draw_presentation_sphere(
                screen,
                center,
                radius,
                fill,
                edge,
            )
        else:
            pygame.draw.circle(screen, fill, center, radius)

    if not as_points:
        for index, particle, center, radius, _edge in particle_screen_data:
            for target_id in particle.collision_list:
                if target_id <= index:
                    continue
                target_screen_data = next(
                    (
                        screen_data
                        for screen_data in particle_screen_data
                        if screen_data[0] == target_id
                    ),
                    None,
                )
                if target_screen_data is None:
                    continue
                (
                    _target_index,
                    _target_particle,
                    target_center,
                    target_radius,
                    _target_edge,
                ) = target_screen_data
                _draw_overlap_lens(
                    screen,
                    center,
                    radius,
                    target_center,
                    target_radius,
                )

    show_particle_numbers = bool(run_configuration.get("simulation_particle_numbers", True))
    particle_label_font = pygame.font.Font(None, 22) if show_particle_numbers else None
    for _index, particle, center, radius, edge in particle_screen_data:
        if not as_points and not presentation_quality:
            pygame.draw.circle(screen, edge, center, max(1, radius), 2)
        if show_particle_numbers:
            label = particle_label_font.render(str(int(particle.pnum)), True, (255, 255, 255))
            screen.blit(label, (center[0] + 5, center[1] - 16))

    row_y = 10
    row_font = pygame.font.SysFont("consolas", 18)
    sim_time = frame_number * float(run_configuration.get("dt", 0.0))
    status_row = f"frame={frame_number:>8} time={sim_time:>14.8f} test={test_file_name}"
    row = row_font.render(status_row, True, (220, 230, 240))
    screen.blit(row, (10, row_y))
    row_y += 20
    for row_text in (
        _summary_table_header(),
        _summary_table_row(
            "start_p",
            motion_summary["start_total_p"],
            motion_summary["start_total_px"],
            motion_summary["start_total_py"],
        ),
        _summary_table_row(
            "current_p",
            motion_summary["current_total_p"],
            motion_summary["current_total_px"],
            motion_summary["current_total_py"],
            drift=motion_summary["start_total_p"] - motion_summary["current_total_p"],
        ),
        _summary_table_row(
            "internal_p",
            motion_summary["total_internal_mom"],
            motion_summary["internal_px"],
            motion_summary["internal_py"],
            combined=motion_summary["curr_plus_internal_mom"],
            drift=motion_summary["start_minus_curr_plus_internal_mom"],
        ),
        _summary_table_row(
            "KE",
            motion_summary["start_ke"],
            combined=motion_summary["curr_ke"],
            drift=motion_summary["ke_drift"],
        ),
    ):
        row = row_font.render(row_text, True, (220, 230, 240))
        screen.blit(row, (10, row_y))
        row_y += 20
    piston_row = (
        f"piston x={motion_summary['piston_position']:.8f} "
        f"v=({motion_summary['piston_velocity_x']:.8f},"
        f"{motion_summary['piston_velocity_y']:.8f},"
        f"{motion_summary['piston_velocity_z']:.8f}) "
        f"contacts={motion_summary['piston_contacts']} "
        f"frame_J={motion_summary['piston_frame_impulse']:.8f} "
        f"total_J={motion_summary['piston_total_impulse']:.8f} "
        f"total_P=({motion_summary['piston_total_px']:.8f},"
        f"{motion_summary['piston_total_py']:.8f},"
        f"{motion_summary['piston_total_pz']:.8f})"
    )
    row = row_font.render(piston_row, True, (220, 230, 240))
    screen.blit(row, (10, row_y))
    row_y += 20
    row_y += 6
    displayed_particle_rows = 0
    active_particle_count = len(_active_particles(particles, dynamics))
    for index, particle in enumerate(particles):
        if not _is_active_particle(index, dynamics):
            continue
        if active_particle_count > 4 and displayed_particle_rows >= 4:
            break
        row_text = _particle_report_row(particle)
        row = row_font.render(row_text, True, (220, 230, 240))
        screen.blit(row, (10, row_y))
        row_y += 20
        displayed_particle_rows += 1

    if error_return != 0:
        error_text = row_font.render(
            f"ErrorReturn={error_return} {error_description}",
            True,
            (255, 80, 80),
        )
        screen.blit(error_text, (10, row_y + 4))

    pygame.display.flip()


def _report_particles(reporting, frame_number, particles, start_diagnostics, dynamics):
    motion_summary = _motion_summary(start_diagnostics, particles, dynamics)
    reporting.report_frame_momentum(frame_number, motion_summary)
    reporting.report_contacts(frame_number, particles)
    reporting.report_pair_phases(frame_number, dynamics)
    for particle_index, particle in enumerate(particles):
        if not _is_active_particle(particle_index, dynamics):
            continue
        reporting.report_particle(frame_number, particle, motion_summary)


def run_analysis(cfg_file, batch_mode=False, end_frame=None, study=False,study_number=None):
    live, shadow = _create_configured_bases()
    display_base = _display_base_from_config(shadow)
    live.load_cfg_file(cfg_file)
    if shadow is not None:
        shadow.load_cfg_file(cfg_file)
    test_file_name = Path(cfg_file).name
    run_configuration = live.run_configuration
    thin_mode = _as_points(run_configuration)
    senario = None
    if study == True or "in_line_obj" in run_configuration:
        senario = InLineTest()
        live.senario = senario
        live.study = study
        live.inline_test_flag = True
        senario.Create(live.config, study_number)
        if shadow is not None:
            shadow_senario = InLineTest()
            shadow.senario = shadow_senario
            shadow.study = study
            shadow.inline_test_flag = True
            shadow_senario.Create(shadow.config, study_number)
    if batch_mode:
        run_configuration["end_frame"] = end_frame
    if "run_debug_dir" not in run_configuration:
        raise ValueError(
            "SimulationRunner requires run_debug_dir; "
            "capture output has no fallback directory."
        )
    report_dir = Path(run_configuration["run_debug_dir"])
    cleared_report_count = _clear_report_directory(report_dir)
    live_reporting = (
        None
        if thin_mode
        else Reporting(
            report_dir,
            run_configuration.get("rpt_frames"),
            clear_existing=False,
        )
    )
    reporting_s = None
    if shadow is not None and not thin_mode:
        reporting_s = Reporting(
            report_dir,
            run_configuration.get("rpt_frames"),
            clear_existing=False,
            file_suffix="_s",
        )
    if live_reporting is not None:
        print(
            f"SimulationRunner cleared {cleared_report_count} "
            f"report file(s): {report_dir}"
        )
    elif cleared_report_count:
        print(
            f"SimulationRunner cleared {cleared_report_count} "
            f"report file(s): {report_dir}"
        )
    live_start_diagnostics = (
        None if thin_mode else _run_start_diagnostics(live)
    )
    shadow_start_diagnostics = (
        _run_start_diagnostics(shadow)
        if shadow is not None and not thin_mode
        else None
    )

    pygame.init()
    screen = pygame.display.set_mode(_window_size(run_configuration))
    pygame.display.set_caption(
        f"SimulationRunner [{display_base}] - {live.config.get('STUDY_NAME', cfg_file)}"
    )
    clock = pygame.time.Clock()

    frame_number = 0
    frame_rate = int(run_configuration.get("frame_rate", 60))
    exit_on_error = bool(run_configuration.get("exit_on_error", False))
    stop_frame = end_frame
    if stop_frame is None:
        configured_end_frame = run_configuration.get("end_frame", 0)
        stop_frame = int(configured_end_frame) if configured_end_frame else None

    try:
        running = True
        paused = False
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    paused = not paused

            if not paused:
                live.ShaderFlags.frameNum = frame_number
                ##JMB Main Call to live.CollisionRun()
                live_particles = live.CollisionRun()
                if not thin_mode:
                    _report_particles(
                        live_reporting,
                        frame_number,
                        live_particles,
                        live_start_diagnostics,
                        live,
                    )
                if shadow is not None:
                    shadow.ShaderFlags.frameNum = frame_number
                    shadow_particles = shadow.CollisionRun()
                    if not thin_mode:
                        _report_particles(
                            reporting_s,
                            frame_number,
                            shadow_particles,
                            shadow_start_diagnostics,
                            shadow,
                        )
            else:
                live_particles = live.particles
                if shadow is not None:
                    shadow_particles = shadow.particles
            display_runner = shadow if display_base == "shadow" else live
            display_particles = (
                shadow_particles if display_base == "shadow" else live_particles
            )
            display_start_diagnostics = (
                shadow_start_diagnostics
                if display_base == "shadow"
                else live_start_diagnostics
            )
            _draw_particles(
                screen,
                display_particles,
                run_configuration,
                display_runner,
                frame_number,
                test_file_name,
                display_start_diagnostics,
                display_runner.collIn.ErrorReturn,
                display_runner.ErrorDescription(),
            )
            if live.collIn.ErrorReturn != live.constants.ERROR_NONE:
                if exit_on_error:
                    print(
                        "SimulationRunner exiting: "
                        f"ErrorReturn={live.collIn.ErrorReturn} "
                        f"{live.ErrorDescription()}"
                    )
                    running = False
                else:
                    if not paused:
                        print(
                            "SimulationRunner paused: "
                            f"ErrorReturn={live.collIn.ErrorReturn} "
                            f"{live.ErrorDescription()}"
                        )
                    paused = True

            if not paused:
                frame_number += 1
                if stop_frame is not None and frame_number > stop_frame:
                    running = False
            clock.tick(0 if thin_mode else frame_rate)
    finally:
        if live_reporting is not None:
            live_reporting.close()
        if reporting_s is not None:
            reporting_s.close()
        pygame.quit()
    return False
