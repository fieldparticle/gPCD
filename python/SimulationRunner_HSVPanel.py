import pygame
from pathlib import Path
import math
from types import SimpleNamespace
from gbase.HSVWheelPyGame import *
from base.ForceDynamicsBase import ForceDynamics
from base.VerAForceDynamicsBase import ForceDynamics as VerAForceDynamics
from base.Reporting import Reporting
from base.InLineTest import InLineTest
#from gbase import libconf
import io, libconf
from gbase.utilities import get_cell_dimensions, hsv_angle
from gbase.FunctionWall import bounds as wall_bounds
from gbase.FunctionWall import sample_points


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


def _ui_layout(screen, run_configuration):
    """Return the left particle viewport and the right HSV-wheel panel."""
    screen_width, screen_height = screen.get_size()

    panel_width = int(run_configuration.get("hsv_panel_width", 450))
    panel_width = max(260, min(panel_width, screen_width - 200))

    particle_rect = pygame.Rect(
        0,
        0,
        screen_width - panel_width,
        screen_height,
    )

    hsv_panel_rect = pygame.Rect(
        particle_rect.right,
        0,
        panel_width,
        screen_height,
    )

    return particle_rect, hsv_panel_rect


def _draw_hsv_panel(screen, panel_rect, wheel, font):
    """Draw the HSV wheel UI on the right side of the Pygame window."""
    pygame.draw.rect(screen, (0,0,0), panel_rect)
    pygame.draw.line(
        screen,
        (80, 90, 110),
        (panel_rect.left, panel_rect.top),
        (panel_rect.left, panel_rect.bottom),
        2,
    )

    title = font.render("HSV Direction", True, (230, 235, 245))
    screen.blit(title, (panel_rect.left + 20, panel_rect.top + 16))

    wheel_x = panel_rect.left + (panel_rect.width - wheel.size) // 2
    wheel_y = panel_rect.top + (panel_rect.height - wheel.size) // 2
    wheel.draw(screen, (wheel_x, wheel_y), font)

    help_y = wheel_y + wheel.size + 20
    help_rows = (
        "D: +1 degree",
        "A: -1 degree",
        "SPACE: pause",
        "ESC: quit",
    )
    for row_text in help_rows:
        row = font.render(row_text, True, (210, 220, 235))
        screen.blit(row, (panel_rect.left + 20, help_y))
        help_y += 22




def _particle_velocity_angle_degrees(particle_index, particle, dynamics=None):
    """Return the particle velocity direction in degrees.

    The angle follows the standard Cartesian convention used by the
    HSV wheel: 0 degrees points right, 90 degrees points up.
    """
    velocity = _runtime_particle_velocity(particle_index, particle, dynamics)
    vx = float(getattr(velocity, "x", 0.0))
    vy = float(getattr(velocity, "y", 0.0))

    if abs(vx) < 1.0e-12 and abs(vy) < 1.0e-12:
        velrad = getattr(particle, "VelRad", None)
        if velrad is not None and hasattr(velrad, "w"):
            return float(velrad.w) % 360.0
        return 0.0

    return math.degrees(math.atan2(vy, vx)) % 360.0


def _hsv_velocity_arrow_data(particles, dynamics=None):
    """Build HSV-wheel arrow data from the displayed particles.

    Particle 0 is skipped because it is the null/sentinel particle in the
    simulation data. Each returned entry is (particle_number, angle_degrees).
    """
    arrow_data = []
    
    for particle_index, particle in enumerate(particles):
        if particle_index == 0 :
            continue
        if particle.ptype > 0:
            continue
        if not _is_visible_particle(particle_index, particle, dynamics):
            continue

        particle_number = int(getattr(particle, "pnum", particle_index))
        angle_degrees = _particle_velocity_angle_degrees(
            particle_index,
            particle,
            dynamics,
        )
        arrow_data.append((particle_number, angle_degrees))
    return arrow_data

def _presentation_quality(run_configuration):
    return bool(run_configuration.get("presentation_quality", False))


def _as_points(run_configuration):
    if _presentation_quality(run_configuration):
        return False
    return bool(run_configuration.get("as_points", False))


def _dynamics_diagnostics_enabled(run_configuration):
    return bool(run_configuration.get("dynamics_diagnostics", True))


def _fast_ui_mode(run_configuration):
    return not _dynamics_diagnostics_enabled(run_configuration)


def _view_box(run_configuration):
    cell_width, cell_height, _ = get_cell_dimensions(run_configuration)
    x_axis_lims = run_configuration.get("x_axis_lims")
    y_axis_lims = run_configuration.get("y_axis_lims")
    if x_axis_lims is not None and len(x_axis_lims) >= 2:
        x_min = float(x_axis_lims[0])
        x_max = float(x_axis_lims[1])
    else:
        x_min = 0.0
        x_max = float(cell_width)
    if y_axis_lims is not None and len(y_axis_lims) >= 2:
        y_min = float(y_axis_lims[0])
        y_max = float(y_axis_lims[1])
    else:
        y_min = 0.0
        y_max = float(cell_height)
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


def _fit_view_box_to_screen(view_box, screen_width, screen_height):
    """Expand the view box so world units have equal x/y pixel scale."""
    x_min, x_max, y_min, y_max = view_box
    width = x_max - x_min
    height = y_max - y_min
    if width <= 0.0 or height <= 0.0 or screen_width <= 0 or screen_height <= 0:
        return view_box

    view_aspect = width / height
    screen_aspect = screen_width / screen_height
    center_x = 0.5 * (x_min + x_max)
    center_y = 0.5 * (y_min + y_max)

    if view_aspect < screen_aspect:
        width = height * screen_aspect
    elif view_aspect > screen_aspect:
        height = width / screen_aspect

    return (
        center_x - 0.5 * width,
        center_x + 0.5 * width,
        center_y - 0.5 * height,
        center_y + 0.5 * height,
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


def _particle_radius(particle):
    data = getattr(particle, "Data", None)
    if data is not None and hasattr(data, "x"):
        return float(data.x)
    return float(getattr(particle, "radius", 0.0))


def _grid_radius(particles, run_configuration, dynamics=None):
    for index, particle in enumerate(particles):
        if _is_boundary_particle(index, particle, dynamics):
            continue
        radius = _particle_radius(particle)
        if radius > 0.0:
            return radius
    return max(0.0, float(run_configuration.get("radius", 0.0)))


def _draw_particle_diameter_grid(screen, particles, run_configuration, dynamics, view_box):
    if not bool(run_configuration.get("grid_on", False)):
        return

    radius = _grid_radius(particles, run_configuration, dynamics)
    spacing = 2.0 * radius
    if spacing <= 0.0:
        return

    screen_width, screen_height = screen.get_size()
    x_min, x_max, y_min, y_max = view_box
    color = (35, 45, 65)

    first_x = math.floor(x_min / spacing) * spacing
    x_value = first_x
    while x_value <= x_max + 1.0e-9:
        top = _to_screen(x_value, y_max, view_box, screen_width, screen_height)
        bottom = _to_screen(x_value, y_min, view_box, screen_width, screen_height)
        pygame.draw.line(screen, color, top, bottom, 1)
        x_value += spacing

    first_y = math.floor(y_min / spacing) * spacing
    y_value = first_y
    while y_value <= y_max + 1.0e-9:
        left = _to_screen(x_min, y_value, view_box, screen_width, screen_height)
        right = _to_screen(x_max, y_value, view_box, screen_width, screen_height)
        pygame.draw.line(screen, color, left, right, 1)
        y_value += spacing


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


def _runtime_particle_position(particle_index, particle, dynamics=None):
    if dynamics is not None and hasattr(dynamics, "GetCurrentParticlePosition"):
        return dynamics.GetCurrentParticlePosition(particle_index)
    return SimpleNamespace(
        x=float(getattr(particle, "rx", 0.0)),
        y=float(getattr(particle, "ry", 0.0)),
        z=float(getattr(particle, "rz", 0.0)),
    )


def _runtime_particle_velocity(particle_index, particle, dynamics=None):
    if dynamics is not None and hasattr(dynamics, "GetParticleVelocity"):
        return dynamics.GetParticleVelocity(particle_index)
    return getattr(
        particle,
        "VelRad",
        SimpleNamespace(
            x=float(getattr(particle, "vx", 0.0)),
            y=float(getattr(particle, "vy", 0.0)),
            z=float(getattr(particle, "vz", 0.0)),
        ),
    )


def _draw_piston_status_near_first_particle(
    screen,
    particles,
    run_configuration,
    dynamics,
    frame_number,
    view_box,
):
    if dynamics is None:
        return
    if not bool(run_configuration.get("dynamics_diagnostics", False)):
        return

    screen_width, screen_height = screen.get_size()
    anchor = None
    for index, particle in enumerate(particles):
        if _is_boundary_particle(index, particle, dynamics):
            continue
        if not _is_visible_particle(index, particle, dynamics):
            continue
        position = _runtime_particle_position(index, particle, dynamics)
        anchor = _to_screen(
            position.x,
            position.y,
            view_box,
            screen_width,
            screen_height,
        )
        break

    if anchor is None:
        return

    enabled = bool(dynamics.PistonEnabled()) if hasattr(dynamics, "PistonEnabled") else False
    if enabled:
        piston_x = dynamics.GetPistonPosition(frame_number)
        piston_velocity = dynamics.GetPistonVelocity(frame_number)
        label = (
            f"piston x={piston_x:.6f} "
            f"v=({piston_velocity.x:.6f},{piston_velocity.y:.6f},{piston_velocity.z:.6f})"
        )
    else:
        label = "piston disabled"

    font = pygame.font.SysFont("consolas", 18)
    text = font.render(label, True, (255, 255, 255))
    shadow = font.render(label, True, (0, 0, 0))
    label_pos = (anchor[0] + 8, anchor[1] - 34)
    screen.blit(shadow, (label_pos[0] + 1, label_pos[1] + 1))
    screen.blit(text, label_pos)


def _particle_momentum(particle_index, particle, dynamics=None):
    mass = float(getattr(particle, "mass", 1.0))
    velocity = _runtime_particle_velocity(particle_index, particle, dynamics)
    return mass * float(velocity.x), mass * float(velocity.y)


def _particle_kinetic_energy(particle_index, particle, dynamics=None):
    mass = float(getattr(particle, "mass", 1.0))
    velocity = _runtime_particle_velocity(particle_index, particle, dynamics)
    vx = float(velocity.x)
    vy = float(velocity.y)
    vz = float(velocity.z)
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
    if dynamics is not None and hasattr(dynamics, "IsParticleActiveForLifecycle"):
        return dynamics.IsParticleActiveForLifecycle(particle_index)
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


def _particle_contact_target_ids(particle_index, particle, dynamics=None):
    """Return active particle contacts, preferring authoritative slots."""
    if dynamics is not None and hasattr(dynamics, "ParticleContactTargetIDs"):
        return dynamics.ParticleContactTargetIDs(particle_index)
    return list(getattr(particle, "collision_list", ()))


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
    if _has_active_wall_contact(particle) or _particle_contact_target_ids(
        particle_index,
        particle,
        dynamics,
    ):
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
    for particle_index, particle in enumerate(particles):
        if not _is_active_particle(particle_index, dynamics):
            continue
        momentum_x, momentum_y = _particle_momentum(
            particle_index,
            particle,
            dynamics,
        )
        total_x += momentum_x
        total_y += momentum_y
    return total_x, total_y


def _total_kinetic_energy(particles, dynamics=None):
    return sum(
        _particle_kinetic_energy(particle_index, particle, dynamics)
        for particle_index, particle in enumerate(particles)
        if _is_active_particle(particle_index, dynamics)
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


def _particle_report_row(particle_index, particle, dynamics=None):
    position = _runtime_particle_position(particle_index, particle, dynamics)
    velocity = _runtime_particle_velocity(particle_index, particle, dynamics)
    internal_momentum = float(
        getattr(
            particle,
            "internal_momentum",
            getattr(particle, "report_stored_mom", 0.0),
        )
    )
    return (
        f"p{int(particle.pnum):>3}"
        f" x={position.x:>13.6f}"
        f" y={position.y:>13.6f}"
        f" vx={velocity.x:>13.6f}"
        f" vy={velocity.y:>13.6f}"
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
    #rectangle['top'] = 149
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
        points = [
            _to_screen(
                point_x,
                point_y,
                view_box,
                screen_width,
                screen_height,
            )
            for point_x, point_y in sample_points(segment, maximum_spacing=0.05)
        ]
        if len(points) < 2:
            continue
        pygame.draw.lines(screen, (60, 220, 90), False, points, 3)


def _piston_y_bounds(run_configuration, view_box):
    """Return the vertical display span for the analytic piston."""
    chamber_bounds = run_configuration.get("chamber_bounds")
    if chamber_bounds is not None and len(chamber_bounds) >= 4:
        return float(chamber_bounds[2]), float(chamber_bounds[3])

    y_values = []
    for segment in run_configuration.get("curve_wall_segments", ()):
        try:
            boundary_kind = int(round(float(segment[0])))
            if boundary_kind != 1:
                continue
            _x_min, _x_max, y_min, y_max = wall_bounds(segment)
        except (TypeError, ValueError, IndexError):
            continue
        y_values.extend((y_min, y_max))

    if y_values:
        return min(y_values), max(y_values)

    death_bounds = run_configuration.get("death_bounds")
    if death_bounds is not None and len(death_bounds) >= 4:
        return float(death_bounds[2]), float(death_bounds[3])

    return float(view_box[2]), float(view_box[3])


def _draw_piston(screen, run_configuration, dynamics, frame_number, view_box):
    """Draw the analytic piston as a white vertical line when enabled."""
    if dynamics is None or not dynamics.PistonEnabled():
        return

    screen_width, screen_height = screen.get_size()
    piston_x = dynamics.GetPistonPosition(frame_number)
    piston_y_min, piston_y_max = _piston_y_bounds(run_configuration, view_box)
    piston_bottom = _to_screen(
        piston_x,
        piston_y_min,
        view_box,
        screen_width,
        screen_height,
    )
    piston_top = _to_screen(
        piston_x,
        piston_y_max,
        view_box,
        screen_width,
        screen_height,
    )
    pygame.draw.line(
        screen,
        (0, 0, 0),
        piston_bottom,
        piston_top,
        8,
    )
    pygame.draw.line(
        screen,
        (245, 245, 245),
        piston_bottom,
        piston_top,
        4,
    )


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
    view_box = _fit_view_box_to_screen(
        _view_box(run_configuration),
        screen_width,
        screen_height,
    )
    fast_ui = _fast_ui_mode(run_configuration)
    screen.fill((0, 0, 0))
    _draw_particle_diameter_grid(screen, particles, run_configuration, dynamics, view_box)
    _draw_configuration_boundaries(screen, run_configuration, view_box)
    _draw_piston(screen, run_configuration, dynamics, frame_number, view_box)
    if fast_ui:
        for index, particle in enumerate(particles):
            if not _is_visible_particle(index, particle, dynamics):
                continue
            position = _runtime_particle_position(index, particle, dynamics)
            center = _to_screen(
                position.x,
                position.y,
                view_box,
                screen_width,
                screen_height,
            )
            radius = _radius_to_pixels(
                _particle_radius(particle),
                view_box,
                screen_width,
                screen_height,
            )
            if _is_boundary_particle(index, particle, dynamics):
                pygame.draw.circle(screen, (60, 220, 90), center, 1)
            elif _particle_contact_target_ids(index, particle, dynamics):
                pygame.draw.circle(screen, (255, 80, 80), center, radius)
            else:
                pygame.draw.circle(screen, (90, 160, 255), center, radius)
        _draw_piston(screen, run_configuration, dynamics, frame_number, view_box)
        return

    presentation_quality = _presentation_quality(run_configuration)
    as_points = _as_points(run_configuration)

    if as_points:
        hsv_color = bool(run_configuration.get("hsv_color", False))
        hsv_sat = float(run_configuration.get("hsv_sat", 0.707))
        hsv_val = float(run_configuration.get("hsv_val", 1.0))
        for index, particle in enumerate(particles):
            if not _is_visible_particle(index, particle, dynamics):
                continue
            position = _runtime_particle_position(index, particle, dynamics)
            center = _to_screen(
                position.x,
                position.y,
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
        return

    motion_summary = _motion_summary(
        start_diagnostics,
        particles,
        dynamics,
    )

    hsv_color = bool(run_configuration.get("hsv_color", False))
    hsv_sat = float(run_configuration.get("hsv_sat", 0.707))
    hsv_val = float(run_configuration.get("hsv_val", 1.0))
    particle_screen_data = []
    for index, particle in enumerate(particles):
        if not _is_visible_particle(index, particle, dynamics):
            continue
        is_boundary = _is_boundary_particle(index, particle, dynamics)
        position = _runtime_particle_position(index, particle, dynamics)
        center = _to_screen(
            position.x,
            position.y,
            view_box,
            screen_width,
            screen_height,
        )
        radius = (
            1
            if as_points
            else _radius_to_pixels(
                _particle_radius(particle),
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
        particle_screen_data.append(
            (index, particle, center, radius, edge, is_boundary)
        )
        if is_boundary:
            pygame.draw.circle(screen, fill, center, radius, 2)
        elif presentation_quality:
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
        for index, particle, center, radius, _edge, is_boundary in particle_screen_data:
            if is_boundary:
                continue
            for target_id in _particle_contact_target_ids(
                index,
                particle,
                dynamics,
            ):
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
                    _target_is_boundary,
                ) = target_screen_data
                _draw_overlap_lens(
                    screen,
                    center,
                    radius,
                    target_center,
                    target_radius,
                )

    _draw_piston(screen, run_configuration, dynamics, frame_number, view_box)
    _draw_piston_status_near_first_particle(
        screen,
        particles,
        run_configuration,
        dynamics,
        frame_number,
        view_box,
    )

    show_particle_numbers = bool(run_configuration.get("simulation_particle_numbers", True))
    particle_label_font = pygame.font.Font(None, 22) if show_particle_numbers else None
    for _index, particle, center, radius, edge, is_boundary in particle_screen_data:
        if not as_points and not presentation_quality and not is_boundary:
            pygame.draw.circle(screen, edge, center, max(1, radius), 2)
        if show_particle_numbers and not is_boundary:
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
        row_text = _particle_report_row(index, particle, dynamics)
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



def _report_particles(reporting, frame_number, particles, start_diagnostics, dynamics):
    motion_summary = _motion_summary(start_diagnostics, particles, dynamics)
    reporting.report_frame_momentum(frame_number, motion_summary)
    reporting.report_contacts(frame_number, particles)
    reporting.report_pair_phases(frame_number, dynamics)
    for particle_index, particle in enumerate(particles):
        if not _is_active_particle(particle_index, dynamics):
            continue
        reporting.report_particle(
            frame_number,
            particle,
            motion_summary,
            position=_runtime_particle_position(
                particle_index,
                particle,
                dynamics,
            ),
            velocity=_runtime_particle_velocity(
                particle_index,
                particle,
                dynamics,
            ),
        )


def run_analysis(cfg_file, batch_mode=False, end_frame=None, study=False,study_number=None):
    live, shadow = _create_configured_bases()
    display_base = _display_base_from_config(shadow)
    live.load_cfg_file(cfg_file)
    if shadow is not None:
        shadow.load_cfg_file(cfg_file)
    test_file_name = Path(cfg_file).name
    run_configuration = live.run_configuration
    dynamics_diagnostics = _dynamics_diagnostics_enabled(run_configuration)
    fast_ui = not dynamics_diagnostics
    if fast_ui:
        shadow = None
        display_base = "live"
    scenario = None
    if study == True or "in_line_obj" in run_configuration:
        scenario = InLineTest()
        live.scenario = scenario
        live.study = study
        live.inline_test_flag = True
        scenario.Create(live.config, study_number)
        if shadow is not None:
            shadow_scenario = InLineTest()
            shadow.scenario = shadow_scenario
            shadow.study = study
            shadow.inline_test_flag = True
            shadow_scenario.Create(shadow.config, study_number)
    if batch_mode:
        run_configuration["end_frame"] = end_frame
    if "run_debug_dir" not in run_configuration:
        raise ValueError(
            "SimulationRunner requires run_debug_dir; "
            "capture output has no fallback directory."
        )
    report_dir = Path(run_configuration["run_debug_dir"])
    cleared_report_count = (
        0 if fast_ui else _clear_report_directory(report_dir)
    )
    live_reporting = (
        Reporting(
            report_dir,
            run_configuration.get("rpt_frames"),
            clear_existing=False,
        )
        if dynamics_diagnostics
        else None
    )
    reporting_s = None
    if shadow is not None and dynamics_diagnostics:
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
        _run_start_diagnostics(live) if dynamics_diagnostics else None
    )
    shadow_start_diagnostics = (
        _run_start_diagnostics(shadow)
        if shadow is not None and dynamics_diagnostics
        else None
    )

    pygame.init()
    screen = pygame.display.set_mode(_window_size(run_configuration))
    pygame.display.set_caption(
        f"SimulationRunner [{display_base}] - {live.config.get('STUDY_NAME', cfg_file)}"
    )
    plot_hsv_wheel = bool(run_configuration.get("plot_hsv_wheel", True))

    # Give the particle simulation the full window whenever the HSV panel is off.
    if fast_ui or not plot_hsv_wheel:
        hsv_panel_rect = None
        particle_surface = screen
        hsv_wheel_size = 0
    else:
        particle_rect, hsv_panel_rect = _ui_layout(screen, run_configuration)
        particle_surface = screen.subsurface(particle_rect)
        hsv_wheel_size = int(
            run_configuration.get(
                "hsv_wheel_size",
                min(400, hsv_panel_rect.width - 40, hsv_panel_rect.height - 120),
            )
        )
        hsv_wheel_size = max(120, hsv_wheel_size)

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
        wheel = (
            HSVWheel(hsv_wheel_size)
            if plot_hsv_wheel and not fast_ui
            else None
        )
        font = pygame.font.SysFont("consolas", 18) if wheel is not None else None
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    paused = not paused
                elif (
                    wheel is not None
                    and event.type == pygame.KEYDOWN
                    and event.key == pygame.K_d
                ):
                    wheel.angle_deg = (wheel.angle_deg + 1.0) % 360.0
                elif (
                    wheel is not None
                    and event.type == pygame.KEYDOWN
                    and event.key == pygame.K_a
                ):
                    wheel.angle_deg = (wheel.angle_deg - 1.0) % 360.0
                

            if not paused:
                live.ShaderFlags.frameNum = frame_number
                ##JMB Main Call to live.CollisionRun()
                live_particles = live.CollisionRun()
                if dynamics_diagnostics:
                    _report_particles(
                        live_reporting,
                        frame_number,
                        live_particles,
                        live_start_diagnostics,
                        live,
                    )
                if shadow is not None and dynamics_diagnostics:
                    shadow.ShaderFlags.frameNum = frame_number
                    shadow_particles = shadow.CollisionRun()
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
                particle_surface,
                display_particles,
                run_configuration,
                display_runner,
                frame_number,
                test_file_name,
                display_start_diagnostics,
                display_runner.collIn.ErrorReturn,
                display_runner.ErrorDescription(),
            )
            if wheel is not None:
                wheel.set_particle_angles(
                    _hsv_velocity_arrow_data(display_particles, display_runner)
                )
                _draw_hsv_panel(screen, hsv_panel_rect, wheel, font)
            pygame.display.flip()
            if live.collIn.ErrorReturn != live.constants.ERROR_NONE:
                if fast_ui:
                    print(
                        "SimulationRunner stopped: "
                        f"ErrorReturn={live.collIn.ErrorReturn} "
                        f"{live.ErrorDescription()}"
                    )
                    running = False
                elif exit_on_error:
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
            clock.tick(0 if not dynamics_diagnostics else frame_rate)
    finally:
        if live_reporting is not None:
            live_reporting.close()
        if reporting_s is not None:
            reporting_s.close()
        pygame.quit()
    return False
