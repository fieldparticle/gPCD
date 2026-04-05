import csv
import math
from pathlib import Path
import time
import pygame

from base.scenarios import DEFAULT_WALL_BOX, build_base, configure_two_particle_horizontal

class Demo:
    def __init__(self, configure_scenario=None, export_data_file=None, base_class=None):
        pygame.init()
        if configure_scenario is None:
            configure_scenario = configure_two_particle_horizontal
        self.configure_scenario = configure_scenario
        self.base_class = base_class
        self.base = build_base(self.configure_scenario, base_class=self.base_class)
        self.export_data_file = self.resolve_export_data_file(export_data_file)
        self.export_written = False
        self.frame_timing_written = False
        self.W = 1000
        self.H = 1000
        self.screen = pygame.display.set_mode((self.W, self.H))
        self.screen_title = "Impulse-In / Impulse-Out Symmetry"
        pygame.display.set_caption(self.screen_title)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 16)
        self.small_font = pygame.font.SysFont("consolas", 16)
        self.particle_label_font = pygame.font.SysFont("consolas", 24, bold=True)

        self.default_post_collision_frames = 90
        self.post_collision_frames = self.default_post_collision_frames
        self.default_zoom = 2.0
        self.zoom = self.default_zoom
        self.min_zoom = 0.25
        self.max_zoom = 8.0
        
        self.paused = False
        self.frames_since_collision_end = None
        self.momentum_history_seconds = 2.5
        self.momentum_history = []
        self.frame_timing_trace = []


        # Visual scale
        self.output_width = 1000
        self.output_height = 1000
        self.output_object_x = DEFAULT_WALL_BOX[0]
        self.output_object_y = DEFAULT_WALL_BOX[2]
        self.output_object_width = DEFAULT_WALL_BOX[1] - DEFAULT_WALL_BOX[0]
        self.output_object_height = DEFAULT_WALL_BOX[3] - DEFAULT_WALL_BOX[2]

        self.set_output_screen_size(
            width=self.output_width,
            height=self.output_height,
        )
        self.set_output_object_space(
            x=self.output_object_x,
            y=self.output_object_y,
            width=self.output_object_width,
            height=self.output_object_height,
        )
        self.apply_scenario_options()

    def reset(self):
        self.frames_since_collision_end = None
        self.base = build_base(self.configure_scenario, base_class=self.base_class)
        self.momentum_history = []
        self.frame_timing_trace = []
        self.zoom = self.default_zoom
        self.export_written = False
        self.frame_timing_written = False
        self.particle_label_font = pygame.font.SysFont("consolas", 24, bold=True)
        self.apply_scenario_options()
        self.set_output_object_space(
            x=self.output_object_x,
            y=self.output_object_y,
            width=self.output_object_width,
            height=self.output_object_height,
        )

    def resolve_export_data_file(self, export_data_file):
        if not export_data_file:
            return None

        export_path = Path(export_data_file)
        if not export_path.is_absolute():
            project_root = Path(__file__).resolve().parents[1]
            export_path = project_root / export_path
        return export_path

    def write_export_data(self):
        if self.export_written or self.export_data_file is None or not self.base.final_report_lines:
            return

        self.export_data_file.parent.mkdir(parents=True, exist_ok=True)
        if self.base.collision_trace:
            with self.export_data_file.open("w", newline="", encoding="utf-8") as handle:
                fieldnames = list(self.base.collision_trace[0].keys())
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.base.collision_trace)

            summary_path = self.export_data_file.with_name(
                f"{self.export_data_file.stem}_summary{self.export_data_file.suffix}"
            )
            with summary_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["metric", "value"])
                for line in self.base.final_report_lines:
                    if "=" in line:
                        metric, value = line.split("=", 1)
                        writer.writerow([metric.strip(), value.strip()])
                    else:
                        writer.writerow([line.strip(), ""])
        else:
            with self.export_data_file.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["metric", "value"])
                for line in self.base.final_report_lines:
                    if "=" in line:
                        metric, value = line.split("=", 1)
                        writer.writerow([metric.strip(), value.strip()])
                    else:
                        writer.writerow([line.strip(), ""])
        self.export_written = True

    def write_frame_timing_export(self):
        if self.frame_timing_written or self.export_data_file is None or not self.frame_timing_trace:
            return

        timing_path = self.export_data_file.with_name(
            f"{self.export_data_file.stem}_frame_timing{self.export_data_file.suffix}"
        )
        timing_path.parent.mkdir(parents=True, exist_ok=True)
        with timing_path.open("w", newline="", encoding="utf-8") as handle:
            fieldnames = list(self.frame_timing_trace[0].keys())
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.frame_timing_trace)
        self.frame_timing_written = True

    def apply_scenario_options(self):
        self.post_collision_frames = self.base.scenario_options.get(
            "post_collision_frames",
            self.default_post_collision_frames,
        )

    def set_output_screen_size(self, width=None, height=None):
        new_w = self.W if width is None else int(width)
        new_h = self.H if height is None else int(height)
        if new_w <= 0 or new_h <= 0:
            raise ValueError("Window width and height must be positive.")
        self.W = new_w
        self.H = new_h
        self.screen = pygame.display.set_mode((self.W, self.H))

    def set_output_object_space(self, x, y, width, height):
        if width <= 0.0 or height <= 0.0:
            raise ValueError("Object-space width and height must be positive.")

        self.object_x_min = float(x)
        self.object_y_min = float(y)
        self.object_width = float(width)
        self.object_height = float(height)
        self.world_panel_x = 0
        self.world_panel_y = 0
        self.world_panel_width = self.W
        self.world_panel_height = self.H // 2
        self.plot_panel_x = 0
        self.plot_panel_y = self.world_panel_height
        self.plot_panel_width = self.W
        self.plot_panel_height = self.H - self.world_panel_height
        self.scale_x = self.world_panel_width / self.object_width
        self.scale_y = self.world_panel_height / self.object_height
        self.object_scale = min(self.scale_x, self.scale_y)
        self.object_scale *= self.zoom
        self.pixel_radius_scale = self.object_scale
        self.viewport_pixel_width = self.object_width * self.object_scale
        self.viewport_pixel_height = self.object_height * self.object_scale
        self.viewport_offset_x = self.world_panel_x + 0.5 * (self.world_panel_width - self.viewport_pixel_width)
        self.viewport_offset_y = self.world_panel_y + 0.5 * (self.world_panel_height - self.viewport_pixel_height)

    def set_zoom(self, zoom):
        self.zoom = max(self.min_zoom, min(self.max_zoom, float(zoom)))
        self.set_output_object_space(
            x=self.output_object_x,
            y=self.output_object_y,
            width=self.output_object_width,
            height=self.output_object_height,
        )
    
    

    def to_screen_x(self, x):
        return int(self.viewport_offset_x + (x - self.object_x_min) * self.object_scale)

    def to_screen_y(self, y):
        return int(
            self.world_panel_y
            + self.world_panel_height
            - self.viewport_offset_y
            - (y - self.object_y_min) * self.object_scale
        )

    def draw_alpha_circle(self, color_rgba, x_world, y_world, radius_world):
        r_px = max(1, int(radius_world * self.pixel_radius_scale))
        temp = pygame.Surface((2 * r_px, 2 * r_px), pygame.SRCALPHA)
        pygame.draw.circle(temp, color_rgba, (r_px, r_px), r_px)
        self.screen.blit(temp, (self.to_screen_x(x_world) - r_px, self.to_screen_y(y_world) - r_px))

    def record_momentum_history(self):
        sample = {"time": self.base.time, "values": []}
        for particle in self.base.particles:
            sample["values"].append(math.hypot(particle["px"], particle["py"]))
        self.momentum_history.append(sample)

        min_time = self.base.time - self.momentum_history_seconds
        while len(self.momentum_history) > 2 and self.momentum_history[1]["time"] < min_time:
            self.momentum_history.pop(0)

    def draw_momentum_panel(self):
        if not self.momentum_history:
            return

        panel_w = self.plot_panel_width
        panel_h = self.plot_panel_height
        panel_x = self.plot_panel_x
        panel_y = self.plot_panel_y
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        panel_surface = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surface.fill((8, 12, 18, 210))
        pygame.draw.rect(panel_surface, (90, 100, 120, 220), panel_surface.get_rect(), 1)

        title = self.small_font.render("Particle |p|", True, self.base.WHITE)
        panel_surface.blit(title, (16, 10))

        plot_left = 56
        plot_top = 34
        plot_w = panel_w - 76
        plot_h = panel_h - 62
        plot_rect = pygame.Rect(plot_left, plot_top, plot_w, plot_h)
        pygame.draw.rect(panel_surface, (50, 60, 78, 255), plot_rect, 1)

        all_values = [
            value
            for sample in self.momentum_history
            for value in sample["values"]
        ]
        if not all_values:
            self.screen.blit(panel_surface, panel_rect.topleft)
            return

        y_min = min(all_values)
        y_max = max(all_values)
        if abs(y_max - y_min) < 1.0e-12:
            y_min -= 0.5
            y_max += 0.5
        else:
            pad = 0.08 * (y_max - y_min)
            y_min -= pad
            y_max += pad

        x_min = self.momentum_history[0]["time"]
        x_max = self.momentum_history[-1]["time"]
        if abs(x_max - x_min) < 1.0e-12:
            x_max = x_min + 1.0

        for frac in (0.25, 0.5, 0.75):
            y = plot_top + int((1.0 - frac) * plot_h)
            pygame.draw.line(
                panel_surface,
                (35, 44, 58, 255),
                (plot_left, y),
                (plot_left + plot_w, y),
                1,
            )

        colors = [
            particle.get("edge", self.base.WHITE)
            for particle in self.base.particles
        ]

        def to_plot_xy(time_value, momentum_value):
            x_frac = (time_value - x_min) / max(x_max - x_min, 1.0e-12)
            y_frac = (momentum_value - y_min) / max(y_max - y_min, 1.0e-12)
            x = plot_left + int(x_frac * plot_w)
            y = plot_top + plot_h - int(y_frac * plot_h)
            return x, y

        particle_count = len(self.momentum_history[-1]["values"])
        for index in range(particle_count):
            points = [
                to_plot_xy(sample["time"], sample["values"][index])
                for sample in self.momentum_history
            ]
            if len(points) >= 2:
                pygame.draw.lines(panel_surface, colors[index % len(colors)], False, points, 2)

        ymin_text = self.small_font.render(f"{y_min:.2f}", True, self.base.WHITE)
        ymax_text = self.small_font.render(f"{y_max:.2f}", True, self.base.WHITE)
        panel_surface.blit(ymax_text, (6, plot_top - 8))
        panel_surface.blit(ymin_text, (6, plot_top + plot_h - 8))

        legend_y = panel_h - 18
        legend_x = 16
        for index in range(particle_count):
            color = colors[index % len(colors)]
            pygame.draw.line(panel_surface, color, (legend_x, legend_y), (legend_x + 16, legend_y), 3)
            label = self.small_font.render(str(index), True, self.base.WHITE)
            panel_surface.blit(label, (legend_x + 20, legend_y - 8))
            legend_x += 42

        self.screen.blit(panel_surface, panel_rect.topleft)

   

    
    

    def run(self):
        running = True
        self.record_momentum_history()

        while running:
            frame_start = time.perf_counter()
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.reset()
                    elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                        self.set_zoom(self.zoom * 1.2)
                    elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_KP_MINUS):
                        self.set_zoom(self.zoom / 1.2)

            if not self.paused:
                sim_start = time.perf_counter()
                sub_dt = self.base.dt / self.base.substeps
                for _ in range(self.base.substeps):
                    self.base.do_substep(sub_dt)
                self.base.time += self.base.dt
                simulation_wall_ms = (time.perf_counter() - sim_start) * 1000.0
                self.record_momentum_history()

                self.frame_timing_trace.append(
                    {
                        "frame_index": len(self.frame_timing_trace),
                        "time": self.base.time,
                        "frame_dt": self.base.dt,
                        "substeps": self.base.substeps,
                        "sub_dt": sub_dt,
                        "simulation_wall_ms": simulation_wall_ms,
                        "active_contact_count": getattr(self.base, "active_contact_count", 0),
                        "pair_contact_count": getattr(self.base, "active_pair_contact_count", 0),
                        "wall_contact_count": getattr(self.base, "active_wall_contact_count", 0),
                        "bond_contact_count": getattr(self.base, "active_bond_contact_count", 0),
                        "collision_complete": int(self.base.collision_complete),
                    }
                )

                if self.base.collision_complete and self.frames_since_collision_end is None:
                    self.frames_since_collision_end = 0
                    if self.base.final_report_lines:
                        self.write_export_data()
                        print()
                        for line in self.base.final_report_lines:
                            print(line)
                        print()

                if self.frames_since_collision_end is not None:
                    self.frames_since_collision_end += 1
                    if (
                        self.post_collision_frames is not None
                        and self.frames_since_collision_end >= self.post_collision_frames
                    ):
                        running = False

            contacts_after = self.base.get_contacts()

            if not contacts_after:
                nx = 1.0
                ny = 0.0
                alpha = 0.0
                delta = 0.0
                area = 0.0
                area_pcnt = 0.0
                proxPercent = 1.0
                d = 0.0
                contact_strength = 0.0
                contact_strength_label = "force"
                contact_pair = None
            else:
                contact_pair = contacts_after[0]
                i, j, contact_after = contact_pair
                nx, ny, alpha, delta, area, area_pcnt, proxPercent, d = contact_after
                if hasattr(self.base, "contact_force_from_area"):
                    pi = self.base.particles[i]
                    pj = self.base.particles[j]
                    contact_strength = self.base.contact_force_from_area(
                        area,
                        pi["mass"],
                        pj["mass"],
                    )
                    contact_strength_label = "force"
                elif getattr(self.base, "rejection_accel_per_area", None) is not None:
                    contact_strength = self.base.rejection_accel_per_area * area
                    contact_strength_label = "accel"
                else:
                    contact_strength = self.base.k * area
                    contact_strength_label = "force"

            p_total_x, p_total_y = self.base.total_momentum()
            p_error_x = p_total_x - self.base.initial_total_momentum_x
            p_error_y = p_total_y - self.base.initial_total_momentum_y
            p_error = math.hypot(p_error_x, p_error_y)
            internal_px, internal_py = self.base.total_internal_momentum_vector()
            net_internal_p = math.hypot(internal_px, internal_py)
            step_internal_p = getattr(self.base, "step_internal_momentum", 0.0)
            step_internal_by_particle = getattr(self.base, "step_internal_momentum_by_particle", [])
            ke = self.base.total_kinetic_energy()
            ke_error = ke - self.base.initial_ke

            if contact_pair is None:
                rel_vn = 0.0
            else:
                i, j, _ = contact_pair
                pi = self.base.particles[i]
                pj = self.base.particles[j]
                vix = pi["px"] / pi["mass"]
                viy = pi["py"] / pi["mass"]
                vjx = pj["px"] / pj["mass"]
                vjy = pj["py"] / pj["mass"]
                rel_vn = (vjx - vix) * nx + (vjy - viy) * ny

            self.screen.fill(self.base.BG)

            if self.base.walls is not None:
                wall_left = self.to_screen_x(self.base.walls["start_x"])
                wall_right = self.to_screen_x(self.base.walls["end_x"])
                wall_top = self.to_screen_y(self.base.walls["end_y"])
                wall_bottom = self.to_screen_y(self.base.walls["start_y"])
                wall_rect = pygame.Rect(
                    min(wall_left, wall_right),
                    min(wall_top, wall_bottom),
                    abs(wall_right - wall_left),
                    abs(wall_bottom - wall_top),
                )
                pygame.draw.rect(self.screen, self.base.WHITE, wall_rect, 2)

            for index, particle in enumerate(self.base.particles):
                center_x = self.to_screen_x(particle["x"])
                center_y = self.to_screen_y(particle["y"])
                self.draw_alpha_circle(particle["fill"], particle["x"], particle["y"], particle["radius"])
                pygame.draw.circle(
                    self.screen,
                    particle["edge"],
                    (center_x, center_y),
                    int(particle["radius"] * self.pixel_radius_scale),
                    2,
                )
                pygame.draw.circle(
                    self.screen,
                    self.base.WHITE,
                    (center_x, center_y),
                    4,
                )
                label_surface = self.particle_label_font.render(str(index), True, self.base.WHITE)
                label_rect = label_surface.get_rect(center=(center_x + 12, center_y - 12))
                self.screen.blit(label_surface, label_rect)

            for i, j, contact_after in contacts_after:
                pair_nx, pair_ny, _alpha, _delta, pair_area, _area_pcnt, _proxPercent, _d = contact_after
                pi = self.base.particles[i]
                pj = self.base.particles[j]
                pygame.draw.line(
                    self.screen,
                    self.base.GREEN,
                    (self.to_screen_x(pi["x"]), self.to_screen_y(pi["y"])),
                    (self.to_screen_x(pj["x"]), self.to_screen_y(pj["y"])),
                    2,
                )

                if hasattr(self.base, "contact_force_from_area"):
                    pair_contact_strength = self.base.contact_force_from_area(
                        pair_area,
                        pi["mass"],
                        pj["mass"],
                    )
                elif getattr(self.base, "rejection_accel_per_area", None) is not None:
                    pair_contact_strength = self.base.rejection_accel_per_area * pair_area
                else:
                    pair_contact_strength = self.base.k * pair_area

                if pair_contact_strength > 0.0:
                    arrow_scale = 0.015
                    fx = pair_nx * pair_contact_strength * arrow_scale
                    fy = pair_ny * pair_contact_strength * arrow_scale
                    start = (self.to_screen_x(pi["x"]), self.to_screen_y(pi["y"]))
                    end = (self.to_screen_x(pi["x"] + fx), self.to_screen_y(pi["y"] + fy))
                    pygame.draw.line(self.screen, self.base.YELLOW, start, end, 4)

            area_diff = abs(self.base.max_area_in - self.base.max_area_out)
            J_diff = abs(self.base.max_J_in - self.base.max_J_out)

            lines = [
                "SPACE pause/resume   R reset   +/- zoom   ESC quit",
                f"time                 = {self.base.time:.8f}",
                f"zoom                 = {self.zoom:.2f}x",
                #f"output size          = {self.W} x {self.H}",
                #f"object view origin   = ({self.object_x_min:.4f}, {self.object_y_min:.4f})",
                #f"object view size     = ({self.object_width:.4f}, {self.object_height:.4f})",
                #f"object scale         = {self.object_scale:.4f}",
                #f"viewport padding     = ({self.viewport_offset_x:.1f}, {self.viewport_offset_y:.1f})",
                #f"internal dt          = {self.base.dt / self.base.substeps:.8f}",
                f"step internal |p|    = {step_internal_p:.8f}",
                #f"net internal p       = ({internal_px:.8f}, {internal_py:.8f})",
                #f"net internal |p|     = {net_internal_p:.8f}",
                f"vector momentum err  = {p_error:.8e}",
                #f"collision started    = {self.collision_started}",
                #f"rebound mode         = {self.rebound_mode}",
                #f"final reported       = {self.final_report_printed}",
                #f"post frames left     = {'-' if self.frames_since_collision_end is None else max(self.post_collision_frames - self.frames_since_collision_end, 0)}",
                #f"particle count       = {len(self.particles)}",
                #f"active contacts      = {len(contacts_after)}",
                #f"relative v dot n     = {rel_vn:.8f}",
                #f"momentum error       = {p_error:.8e}",
                #f"distance d           = {d:.8f}",
                #f"penetration delta    = {delta:.8f}",
                #f"current area         = {self.current_area:.8f}",
                #f"current J            = {self.current_J:.8e}",
                #f"max area in          = {self.max_area_in:.8f}",
                #f"max area out         = {self.max_area_out:.8f}",
                #f"max area diff        = {area_diff:.8e}",
                #f"max J in             = {self.max_J_in:.8e}",
                #f"max J out            = {self.max_J_out:.8e}",
                #f"max J diff           = {J_diff:.8e}",
                #f"kinetic energy       = {ke:.8f}",
                f"KE error             = {ke_error:.8e}",
            ]
            for index, value in enumerate(step_internal_by_particle):
                lines.append(f"step int |p| p{index}   = {value:.8f}")

            ytxt = 16
            for line in lines:
                surf = self.font.render(line, True, self.base.WHITE)
                self.screen.blit(surf, (16, ytxt))
                ytxt += 24

            self.draw_momentum_panel()

            pygame.display.flip()
            frame_wall_ms = (time.perf_counter() - frame_start) * 1000.0
            if self.frame_timing_trace and not self.paused:
                self.frame_timing_trace[-1]["frame_wall_ms"] = frame_wall_ms
                self.frame_timing_trace[-1]["render_wall_ms"] = max(
                    0.0,
                    frame_wall_ms - self.frame_timing_trace[-1]["simulation_wall_ms"],
                )

        self.write_frame_timing_export()
        pygame.quit()


if __name__ == "__main__":
    Demo().run()
