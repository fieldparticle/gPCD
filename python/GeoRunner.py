import pygame
from pathlib import Path
import math

from base.GeoBase import GeoBase
from base.Reporting import Reporting
from base.InLineTest import InLineTest

def _window_size(run_configuration):
    window_size = run_configuration.get("window_size", (1000, 1000))
    return int(window_size[0]), int(window_size[1])


def _view_box(run_configuration):
    x_min = float(run_configuration.get("WallXMIN", 0.0))
    x_max = float(run_configuration.get("WallXMAX", run_configuration.get("side_len", 1.0)))
    y_min = float(run_configuration.get("WallYMIN", 0.0))
    y_max = float(run_configuration.get("WallYMAX", run_configuration.get("side_len", 1.0)))
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
    return max(1, int(radius * min(scale_x, scale_y)))


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


def _total_momentum(particles):
    total_x = 0.0
    total_y = 0.0
    for particle in particles:
        momentum_x, momentum_y = _particle_momentum(particle)
        total_x += momentum_x
        total_y += momentum_y
    return total_x, total_y


def _total_kinetic_energy(particles):
    return sum(_particle_kinetic_energy(particle) for particle in particles)


def _relative_speed(particles):
    if len(particles) < 2:
        return 0.0
    first = particles[0]
    second = particles[1]
    dvx = float(second.vx) - float(first.vx)
    dvy = float(second.vy) - float(first.vy)
    dvz = float(getattr(second, "vz", 0.0)) - float(getattr(first, "vz", 0.0))
    return math.sqrt(dvx * dvx + dvy * dvy + dvz * dvz)


def _run_start_diagnostics(particles):
    return {
        "total_momentum": _total_momentum(particles),
        "ke": _total_kinetic_energy(particles),
        "rel_speed": _relative_speed(particles),
    }


def _motion_summary(start_diagnostics, particles):
    start_total_momentum = start_diagnostics["total_momentum"]
    start_x, start_y = start_total_momentum
    current_x, current_y = _total_momentum(particles)
    start_ke = start_diagnostics["ke"]
    current_ke = _total_kinetic_energy(particles)
    start_rel_speed = start_diagnostics["rel_speed"]
    current_rel_speed = _relative_speed(particles)
    return {
        "start_total_px": start_x,
        "start_total_py": start_y,
        "start_total_p": math.hypot(start_x, start_y),
        "current_total_px": current_x,
        "current_total_py": current_y,
        "current_total_p": math.hypot(current_x, current_y),
        "start_ke": start_ke,
        "curr_ke": current_ke,
        "ke_drift": current_ke - start_ke,
        "start_rel_speed": start_rel_speed,
        "curr_rel_speed": current_rel_speed,
        "rel_speed_drift": current_rel_speed - start_rel_speed,
    }


def _momentum_row(label, momentum_x, momentum_y):
    return (
        f"{label:<18}"
        f" px={momentum_x:>14.8f}"
        f" py={momentum_y:>14.8f}"
        f" |p|={math.hypot(momentum_x, momentum_y):>14.8f}"
    )


def _particle_report_row(particle):
    return (
        f"p{int(particle.pnum):>3}"
        f" x={particle.rx:>13.6f}"
        f" y={particle.ry:>13.6f}"
        f" vx={particle.vx:>13.6f}"
        f" vy={particle.vy:>13.6f}"
        f" oa={particle.oa:>14.8f}"
    )


def _draw_particles(
    screen,
    particles,
    run_configuration,
    frame_number,
    start_diagnostics,
    error_return=0,
    error_description="",
):
    screen_width, screen_height = screen.get_size()
    view_box = _view_box(run_configuration)
    screen.fill((14, 18, 24))
    motion_summary = _motion_summary(start_diagnostics, particles)

    wall_left, wall_top = _to_screen(
        float(run_configuration.get("WallXMIN", view_box[0])),
        float(run_configuration.get("WallYMAX", view_box[3])),
        view_box,
        screen_width,
        screen_height,
    )
    wall_right, wall_bottom = _to_screen(
        float(run_configuration.get("WallXMAX", view_box[1])),
        float(run_configuration.get("WallYMIN", view_box[2])),
        view_box,
        screen_width,
        screen_height,
    )
    wall_rect = pygame.Rect(
        min(wall_left, wall_right),
        min(wall_top, wall_bottom),
        abs(wall_right - wall_left),
        abs(wall_bottom - wall_top),
    )
    pygame.draw.rect(screen, (120, 135, 155), wall_rect, 2)
    side_len = float(run_configuration.get("side_len", 0.0))
    if side_len > 0.0:
        side_left, side_top = _to_screen(0.0, side_len, view_box, screen_width, screen_height)
        side_right, side_bottom = _to_screen(side_len, 0.0, view_box, screen_width, screen_height)
        side_rect = pygame.Rect(
            min(side_left, side_right),
            min(side_top, side_bottom),
            abs(side_right - side_left),
            abs(side_bottom - side_top),
        )
        pygame.draw.rect(screen, (70, 85, 105), side_rect, 1)

    font = pygame.font.Font(None, 24)
    wall_xmax = float(run_configuration.get("WallXMAX", view_box[1]))
    wall_ymax = float(run_configuration.get("WallYMAX", view_box[3]))
    xmax_label = font.render(f"x={wall_xmax:g}", True, (190, 205, 225))
    ymax_label = font.render(f"y={wall_ymax:g}", True, (190, 205, 225))
    screen.blit(
        xmax_label,
        (
            max(0, min(screen_width - xmax_label.get_width(), wall_rect.right - xmax_label.get_width())),
            max(0, min(screen_height - xmax_label.get_height(), wall_rect.centery + 6)),
        ),
    )
    screen.blit(
        ymax_label,
        (
            max(0, min(screen_width - ymax_label.get_width(), wall_rect.centerx + 6)),
            max(0, min(screen_height - ymax_label.get_height(), wall_rect.top)),
        ),
    )

    particle_screen_data = []
    for index, particle in enumerate(particles):
        center = _to_screen(particle.rx, particle.ry, view_box, screen_width, screen_height)
        radius = _radius_to_pixels(particle.radius, view_box, screen_width, screen_height)
        fill = (100, 170, 255)
        edge = (210, 230, 255)
        if particle.collision_list:
            fill = (255, 140, 110)
            edge = (255, 220, 200)
        particle_screen_data.append((index, particle, center, radius, edge))
        pygame.draw.circle(screen, fill, center, radius)

    for index, particle, center, radius, _edge in particle_screen_data:
        for target_id in particle.collision_list:
            if target_id <= index or target_id >= len(particle_screen_data):
                continue
            _target_index, _target_particle, target_center, target_radius, _target_edge = particle_screen_data[target_id]
            _draw_overlap_lens(screen, center, radius, target_center, target_radius)

    particle_label_font = pygame.font.Font(None, 22)
    for _index, particle, center, radius, edge in particle_screen_data:
        pygame.draw.circle(screen, edge, center, radius, 2)
        pygame.draw.circle(screen, (20, 26, 35), center, 3)
        label = particle_label_font.render(str(int(particle.pnum)), True, (20, 26, 35))
        screen.blit(label, (center[0] + 5, center[1] - 16))

    row_y = 10
    row_font = pygame.font.SysFont("consolas", 18)
    sim_time = frame_number * float(run_configuration.get("dt", 0.0))
    status_row = f"frame={frame_number:>8} time={sim_time:>14.8f}"
    row = row_font.render(status_row, True, (220, 230, 240))
    screen.blit(row, (10, row_y))
    row_y += 20
    for row_text in (
        _momentum_row(
            "start_total_mom",
            motion_summary["start_total_px"],
            motion_summary["start_total_py"],
        ),
        _momentum_row(
            "current_total_mom",
            motion_summary["current_total_px"],
            motion_summary["current_total_py"],
        ),
        (
            f"kinetic_energy    "
            f" start={motion_summary['start_ke']:>14.8f}"
            f" curr={motion_summary['curr_ke']:>14.8f}"
            f" drift={motion_summary['ke_drift']:>14.8f}"
        ),
    ):
        row = row_font.render(row_text, True, (220, 230, 240))
        screen.blit(row, (10, row_y))
        row_y += 20
    row_y += 6
    for particle in particles:
        row_text = _particle_report_row(particle)
        row = row_font.render(row_text, True, (220, 230, 240))
        screen.blit(row, (10, row_y))
        row_y += 20

    if error_return != 0:
        error_text = row_font.render(
            f"ErrorReturn={error_return} {error_description}",
            True,
            (255, 80, 80),
        )
        screen.blit(error_text, (10, row_y + 4))

    pygame.display.flip()


def _report_particles(reporting, frame_number, particles, start_diagnostics):
    motion_summary = _motion_summary(start_diagnostics, particles)
    reporting.report_frame_momentum(frame_number, motion_summary)
    reporting.report_contacts(frame_number, particles)
    for particle in particles:
        reporting.report_particle(frame_number, particle, motion_summary)


def run_analysis(cfg_file, batch_mode=False, end_frame=None, study=False,study_number=None):
    geo = GeoBase()
    geo.load_cfg_file(cfg_file)
    run_configuration = geo.run_configuration
    senario = None
    if study == True or "in_line_obj" in run_configuration:
        senario = InLineTest()
        geo.senario = senario
        geo.study = study
        geo.inline_test_flag = True
        senario.Create(geo.config, study_number)
    if batch_mode:
        run_configuration["end_frame"] = end_frame
    if "run_debug_dir" not in run_configuration:
        raise ValueError(
            "GeoRunner requires RUN_CONFIGURATION.run_debug_dir; "
            "capture output has no fallback directory."
        )
    report_dir = Path(run_configuration["run_debug_dir"])
    reporting = Reporting(report_dir, run_configuration.get("rpt_frames"))
    start_diagnostics = _run_start_diagnostics(geo.particles)

    pygame.init()
    screen = pygame.display.set_mode(_window_size(run_configuration))
    pygame.display.set_caption(f"GeoRunner - {geo.config.get('STUDY_NAME', cfg_file)}")
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
                geo.ShaderFlags.frameNum = frame_number
                ##JMB Main Call to geo.CollisionRun() fro every time step
                particles = geo.CollisionRun()
                _report_particles(reporting, frame_number, particles, start_diagnostics)
            else:
                particles = geo.particles
            _draw_particles(
                screen,
                particles,
                run_configuration,
                frame_number,
                start_diagnostics,
                geo.collIn.ErrorReturn,
                geo.ErrorDescription(),
            )
            if geo.collIn.ErrorReturn != geo.constants.GEO_ERROR_NONE:
                if exit_on_error:
                    print(f"GeoRunner exiting: ErrorReturn={geo.collIn.ErrorReturn}")
                    running = False
                else:
                    if not paused:
                        print(f"GeoRunner paused: ErrorReturn={geo.collIn.ErrorReturn}")
                    paused = True

            if not paused:
                frame_number += 1
                if stop_frame is not None and frame_number > stop_frame:
                    running = False
            clock.tick(frame_rate)
    finally:
        reporting.close()
        pygame.quit()
    return False
