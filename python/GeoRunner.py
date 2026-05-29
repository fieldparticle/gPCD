import pygame
from pathlib import Path

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


def _draw_particles(
    screen,
    particles,
    run_configuration,
    frame_number,
    reporting=None,
    error_return=0,
    error_description="",
):
    screen_width, screen_height = screen.get_size()
    view_box = _view_box(run_configuration)
    screen.fill((14, 18, 24))

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
        if reporting is not None:
            reporting.report_particle(frame_number, particle)
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
    row_font = pygame.font.Font(None, 22)
    for particle in particles:
        row_text = (
            f"p{int(particle.pnum)} "
            f"x={particle.rx:.6f} y={particle.ry:.6f} "
            f"vx={particle.vx:.6f} vy={particle.vy:.6f} "
            f"oa={particle.oa:.8f}"
        )
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
    report_dir = Path(
        run_configuration.get(
            "run_debug_dir",
            Path(geo.config.get("data_dir", ".")) / "geo_reports" / geo.config.get(
                "STUDY_NAME",
                "GeoRun",
            ),
        )
    )
    reporting = Reporting(report_dir, run_configuration.get("rpt_frames"))

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
            else:
                particles = geo.particles
            _draw_particles(
                screen,
                particles,
                run_configuration,
                frame_number,
                reporting,
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
