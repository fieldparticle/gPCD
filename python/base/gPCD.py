import math
from logging import config
from pathlib import Path

import pygame

from base.Base import Base
from base.GeoDynamics import GeoDynamics


class Demo:
    """Pygame view for the minimal Base motion model."""

    def __init__(self):
        pygame.init()
        self.base = Base()
        self.screen_width = 1000
        self.screen_height = 1000
        self.world_box = (-3.0, 3.0, -3.0, 3.0)
        self.view_box = self.world_box
        self.zoom = 1.0
        self.bg_color = (20, 20, 30)
        self.wall_color = (235, 235, 235)
        self.default_fill = (100, 170, 255)
        self.default_edge = (160, 210, 255)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Particle Motion")
        self.clock = pygame.time.Clock()
        self.label_font = pygame.font.SysFont("consolas", 24, bold=True)
        self.report_font = pygame.font.SysFont("consolas", 16)
        self.center_dot_color = (245, 245, 245)
        self.collision_normal_color = (255, 245, 140)
        self.overlap_alpha = 185
        self.incoming_kinetic_energy = 0.0
        self.start_kinetic_energy = 0.0
        self.start_total_momentum_x = 0.0
        self.start_total_momentum_y = 0.0
        self.paused = False
        self.frame_number = 0
        self.current_fps = 0.0
        self.frame_rate = 60
        self.end_frame = None
        self.print_report_requested = False
        self.rpt_frames = set()
        self.captured_report_frames = set()
        self.report_capture_dir = Path.cwd()

    def configure(self, particle_data, run_configuration):
        self.config = {} if run_configuration is None else dict(run_configuration)
        self.report_capture_dir = Path(self.config.get("data_dir", Path.cwd()))
        self.clear_report_captures()
        self.rpt_frames = self.normalized_report_frames(self.config.get("rpt_frames", []))
        self.captured_report_frames = set()
        self.base = Base()
        self.base.dt = float(self.config.get("dt", self.base.dt))
        self.base.substeps = int(self.config.get("substeps", self.base.substeps))
        if "zero_velocity_overlap_area" in self.config:
            self.base.zero_velocity_overlap_area = float(self.config["zero_velocity_overlap_area"])
        if "zero_velocity_overlap_fraction" in self.config:
            self.base.zero_velocity_overlap_fraction = float(self.config["zero_velocity_overlap_fraction"])
        if "zero_velocity_overlap_tolerance" in self.config:
            self.base.zero_velocity_overlap_tolerance = float(self.config["zero_velocity_overlap_tolerance"])
        if "geo_rebound_min_fraction" in self.config:
            self.base.geo_rebound_min_fraction = float(self.config["geo_rebound_min_fraction"])
        self.base.max_contacts_per_particle = int(
            self.config.get("max_contacts_per_particle", self.base.max_contacts_per_particle)
        )
        self.base.dynamics.momentum_per_area = float(
            self.config.get("momentum_per_area", self.base.dynamics.momentum_per_area)
        )
        self.base.dynamics.inverse_square_softening = float(
            self.config.get("inverse_square_softening", self.base.dynamics.inverse_square_softening)
        )
        self.base.dynamics.configure_flow(self.config)

        wall_box = self.config.get("wall_box")
        if wall_box is not None and wall_box is not False:
            self.base.set_walls(*wall_box)
            self.world_box = tuple(float(value) for value in wall_box)
        elif self.config.get("world_box") is not None:
            self.world_box = tuple(float(value) for value in self.config["world_box"])
        self.set_zoom(self.config.get("zoom", 1.0))
        self.frame_rate = int(self.config.get("frame_rate", 60))
        self.end_frame = self.normalized_end_frame(self.config.get("end_frame"))

        self.screen_width, self.screen_height = self.config.get(
            "window_size",
            (self.screen_width, self.screen_height),
        )
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

        self.base.clear_particles()
        self.start_total_momentum_x, self.start_total_momentum_y = self.starting_momentum_vector(particle_data)
        self.incoming_kinetic_energy = self.particle_data_kinetic_energy(particle_data)
        for _index, particle in sorted(particle_data.items()):
            self.base.add_particle(**particle)
        self.base.reset()
        self.start_kinetic_energy = self.total_kinetic_energy()
        self.frame_number = 0
        self.current_fps = 0.0
        self.paused = False

    def clear_report_captures(self):
        self.report_capture_dir.mkdir(parents=True, exist_ok=True)
        for report_file in self.report_capture_dir.glob("*.rpt"):
            if report_file.is_file():
                report_file.unlink()

    @staticmethod
    def normalized_report_frames(rpt_frames):
        if rpt_frames is None or rpt_frames is False:
            return set()
        if isinstance(rpt_frames, int):
            return {rpt_frames}
        if isinstance(rpt_frames, str):
            return Demo.normalized_report_frame_item(rpt_frames)

        frames = set()
        for frame in rpt_frames:
            frames.update(Demo.normalized_report_frame_item(frame))
        return frames

    @staticmethod
    def normalized_report_frame_item(frame):
        if isinstance(frame, str):
            frame = frame.strip()
            if ":" in frame:
                start_frame, end_frame = frame.split(":", 1)
                start_frame = int(start_frame.strip())
                end_frame = int(end_frame.strip())
                step = 1 if start_frame <= end_frame else -1
                return set(range(start_frame, end_frame + step, step))
            return {int(frame)}
        return {int(frame)}

    @staticmethod
    def normalized_end_frame(end_frame):
        if end_frame is None or end_frame is False:
            return None
        end_frame = int(end_frame)
        if end_frame <= 0:
            return None
        return end_frame

    @staticmethod
    def starting_momentum_vector(particle_data):
        momentum_x = 0.0
        momentum_y = 0.0
        for particle in particle_data.values():
            mass = float(particle["mass"])
            momentum_x += mass * float(particle["vx"])
            momentum_y += mass * float(particle["vy"])
        return momentum_x, momentum_y

    @staticmethod
    def particle_data_kinetic_energy(particle_data):
        kinetic_energy = 0.0
        for particle in particle_data.values():
            mass = float(particle["mass"])
            vx = float(particle["vx"])
            vy = float(particle["vy"])
            kinetic_energy += 0.5 * mass * (vx * vx + vy * vy)
        return kinetic_energy

    def set_zoom(self, zoom):
        self.zoom = max(0.01, float(zoom))
        x_min, x_max, y_min, y_max = self.world_box
        center_x = 0.5 * (x_min + x_max)
        center_y = 0.5 * (y_min + y_max)
        half_width = 0.5 * (x_max - x_min) / self.zoom
        half_height = 0.5 * (y_max - y_min) / self.zoom
        self.view_box = (
            center_x - half_width,
            center_x + half_width,
            center_y - half_height,
            center_y + half_height,
        )

    def to_screen_x(self, x):
        x_min, x_max, _y_min, _y_max = self.view_box
        return int((x - x_min) / (x_max - x_min) * self.screen_width)

    def to_screen_y(self, y):
        _x_min, _x_max, y_min, y_max = self.view_box
        return int(self.screen_height - (y - y_min) / (y_max - y_min) * self.screen_height)

    def radius_to_pixels(self, radius):
        x_min, x_max, y_min, y_max = self.view_box
        scale_x = self.screen_width / (x_max - x_min)
        scale_y = self.screen_height / (y_max - y_min)
        return max(1, int(radius * min(scale_x, scale_y)))

    def to_screen(self, x, y):
        return self.to_screen_x(x), self.to_screen_y(y)

    def draw(self):
        self.screen.fill(self.bg_color)
        if self.base.walls is not None:
            left = self.to_screen_x(self.base.walls["start_x"])
            right = self.to_screen_x(self.base.walls["end_x"])
            top = self.to_screen_y(self.base.walls["end_y"])
            bottom = self.to_screen_y(self.base.walls["start_y"])
            rect = pygame.Rect(
                min(left, right),
                min(top, bottom),
                abs(right - left),
                abs(bottom - top),
            )
            pygame.draw.rect(self.screen, self.wall_color, rect, 2)

        particle_screen_data = []
        for index, particle in enumerate(self.base.particles):
            if not self.base.dynamics.is_active_particle(particle):
                continue
            x, y = self.base.current_location(particle)
            center = self.to_screen(x, y)
            radius = self.radius_to_pixels(particle["radius"])
            fill = particle.get("fill", self.default_fill)
            edge = particle.get("edge", self.default_edge)
            particle_screen_data.append((index, particle, x, y, center, radius, fill, edge))
            pygame.draw.circle(self.screen, fill, center, radius)

        self.draw_particle_overlaps(particle_screen_data)

        for index, particle, _x, _y, center, radius, _fill, edge in particle_screen_data:
            pygame.draw.circle(self.screen, edge, center, radius, 2)
            pygame.draw.circle(self.screen, self.center_dot_color, center, 4)

            label = self.label_font.render(str(index), True, self.center_dot_color)
            label_rect = label.get_rect(center=(center[0], center[1] - radius - 14))
            self.screen.blit(label, label_rect)

        self.draw_collision_normals()
        self.draw_report()

        pygame.display.flip()

    def draw_particle_overlaps(self, particle_screen_data):
        for left_pos in range(len(particle_screen_data)):
            left = particle_screen_data[left_pos]
            for right_pos in range(left_pos + 1, len(particle_screen_data)):
                right = particle_screen_data[right_pos]
                _li, left_particle, _lx, _ly, left_center, left_radius, left_fill, _left_edge = left
                _ri, right_particle, _rx, _ry, right_center, right_radius, right_fill, _right_edge = right
                if self.base.dynamics.particle_contact(left_particle, right_particle) is None:
                    continue
                self.draw_overlap_lens(left_center, left_radius, left_fill, right_center, right_radius, right_fill)

    def draw_overlap_lens(self, left_center, left_radius, left_fill, right_center, right_radius, right_fill):
        min_x = max(0, min(left_center[0] - left_radius, right_center[0] - right_radius))
        min_y = max(0, min(left_center[1] - left_radius, right_center[1] - right_radius))
        max_x = min(self.screen_width, max(left_center[0] + left_radius, right_center[0] + right_radius))
        max_y = min(self.screen_height, max(left_center[1] + left_radius, right_center[1] + right_radius))
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
        blend = (
            int((left_fill[0] + right_fill[0]) * 0.5),
            int((left_fill[1] + right_fill[1]) * 0.5),
            int((left_fill[2] + right_fill[2]) * 0.5),
            self.overlap_alpha,
        )
        overlap_surface = overlap_mask.to_surface(setcolor=blend, unsetcolor=(0, 0, 0, 0))
        self.screen.blit(overlap_surface, (min_x, min_y))

    def draw_collision_normals(self):
        drawn_pairs = set()
        for source_index, source_particle in enumerate(self.base.particles):
            for slot in range(source_particle.get("sltnum", 0)):
                contact_record = source_particle["ccs"][slot]
                if contact_record.get("clflg", 0) == 0:
                    continue
                target_index = contact_record["pindex"]
                pair_key = tuple(sorted((source_index, target_index)))
                if pair_key in drawn_pairs:
                    continue
                drawn_pairs.add(pair_key)
                self.draw_particle_collision_normal(source_particle, self.base.particles[target_index])

            for contact_record in source_particle.get("bcs", []):
                wall_flag = contact_record.get("clflg", 0)
                if wall_flag != 0:
                    self.draw_wall_collision_normal(source_particle, wall_flag)

    def draw_particle_collision_normal(self, source_particle, target_particle):
        contact = self.base.dynamics.particle_contact(source_particle, target_particle)
        if contact is None:
            return
        nx, ny, _overlap_area, _center_distance = contact
        source_x, source_y = self.base.current_location(source_particle)
        target_x, target_y = self.base.current_location(target_particle)
        mid_x = 0.5 * (source_x + target_x)
        mid_y = 0.5 * (source_y + target_y)
        self.draw_normal_line(mid_x, mid_y, nx, ny)

    def draw_wall_collision_normal(self, source_particle, wall_flag):
        contact = self.base.dynamics.wall_contact(source_particle, wall_flag, self.base.walls)
        if contact is None:
            return
        nx, ny, _overlap_area, _center_distance = contact
        source_x, source_y = self.base.current_location(source_particle)
        radius = source_particle["radius"]
        contact_x = source_x + nx * radius
        contact_y = source_y + ny * radius
        self.draw_normal_line(contact_x, contact_y, -nx, -ny)

    def draw_normal_line(self, x, y, nx, ny):
        normal_length = 0.45
        start = self.to_screen(x - nx * normal_length, y - ny * normal_length)
        end = self.to_screen(x + nx * normal_length, y + ny * normal_length)
        pygame.draw.line(self.screen, self.collision_normal_color, start, end, 3)
        pygame.draw.circle(self.screen, self.collision_normal_color, end, 5)

    def total_kinetic_energy(self):
        return sum(
            0.5 * particle["mass"] * (particle["vx"] * particle["vx"] + particle["vy"] * particle["vy"])
            for particle in self.base.particles
            if self.base.dynamics.is_active_particle(particle)
        )

    def total_momentum_vector(self):
        momentum_x = 0.0
        momentum_y = 0.0
        for particle in self.base.particles:
            if not self.base.dynamics.is_active_particle(particle):
                continue
            momentum_x += particle["mass"] * particle["vx"]
            momentum_y += particle["mass"] * particle["vy"]
        return momentum_x, momentum_y

    def particle_contact_diagnostics(self, source_index, source_particle):
        diagnostics = []
        for slot in range(source_particle.get("sltnum", 0)):
            contact_record = source_particle["ccs"][slot]
            if contact_record.get("clflg", 0) == 0:
                continue
            target_index = contact_record["pindex"]
            pair_key = tuple(sorted((source_index, target_index)))
            target_particle = self.base.particles[target_index]
            contact = self.base.dynamics.particle_contact(source_particle, target_particle)
            if contact is None:
                continue
            nx, ny, _overlap_area, _center_distance = contact
            rel_vx = target_particle["vx"] - source_particle["vx"]
            rel_vy = target_particle["vy"] - source_particle["vy"]
            rel_normal_velocity = rel_vx * nx + rel_vy * ny
            source_mass = source_particle["mass"]
            target_mass = target_particle["mass"]
            reduced_mass = (source_mass * target_mass) / (source_mass + target_mass)
            rel_normal_momentum = reduced_mass * abs(rel_normal_velocity)
            contact_state = self.base.contact_state.get(pair_key, {})
            internal_contact_momentum = contact_state.get("internal_contact_momentum", 0.0)
            overlap_contact_momentum = contact_state.get("overlap_contact_momentum", 0.0)
            last_relative_normal_velocity = contact_state.get(
                "last_relative_normal_velocity",
                rel_normal_velocity,
            )
            phase = "closing" if rel_normal_velocity < 0.0 else "separating"
            diagnostics.append(
                f"c{source_index}->{target_index} reln={rel_normal_velocity:.8f} "
                f"rmass={reduced_mass:.8f} relp={rel_normal_momentum:.8f} "
                f"omom={overlap_contact_momentum:.8f} cinternal={internal_contact_momentum:.8f} "
                f"last_reln={last_relative_normal_velocity:.8f} phase={phase}"
            )
        return diagnostics

    def starting_overlap_capture_diagnostics(self):
        if self.frame_number != 0:
            return []

        lines = []
        for source_index, source_particle in enumerate(self.base.particles):
            if not self.base.dynamics.is_active_particle(source_particle):
                continue
            for slot in range(source_particle.get("sltnum", 0)):
                contact_record = source_particle["ccs"][slot]
                if contact_record.get("clflg", 0) == 0:
                    continue

                target_index = contact_record["pindex"]
                target_particle = self.base.particles[target_index]
                contact = self.base.dynamics.particle_contact(source_particle, target_particle)
                if contact is None:
                    continue

                nx, ny, _overlap_area, center_distance = contact
                v_in_x = source_particle.get("starting_uncorrected_vx", source_particle["vx"])
                v_in_y = source_particle.get("starting_uncorrected_vy", source_particle["vy"])
                v_step_x = source_particle.get("starting_corrected_vx", source_particle["vx"])
                v_step_y = source_particle.get("starting_corrected_vy", source_particle["vy"])
                inward_speed = v_in_x * nx + v_in_y * ny
                inward_x = inward_speed * nx
                inward_y = inward_speed * ny
                v_turn_x = v_in_x - inward_x
                v_turn_y = v_in_y - inward_y
                v_rebound_x = v_in_x - 2.0 * inward_x
                v_rebound_y = v_in_y - 2.0 * inward_y
                phase = "incoming" if inward_speed > 0.0 else "not_incoming"
                lines.extend(
                    [
                        "",
                        f"[starting_overlap p{source_index}->{target_index}]",
                        f"phase: {phase}",
                        f"center_distance: {center_distance:.8f}",
                        f"normal: ({nx:.8f}, {ny:.8f})",
                        f"vin: ({v_in_x:.8f}, {v_in_y:.8f})",
                        f"vstep: ({v_step_x:.8f}, {v_step_y:.8f})",
                        f"vturn: ({v_turn_x:.8f}, {v_turn_y:.8f})",
                        f"vrebound: ({v_rebound_x:.8f}, {v_rebound_y:.8f})",
                        f"inward_speed: {inward_speed:.8f}",
                        f"|pin|: {source_particle['mass'] * math.hypot(v_in_x, v_in_y):.8f}",
                    ]
                )
        return lines

    def particle_capture_report_lines(self):
        lines = []
        for index, particle in enumerate(self.base.particles):
            momentum_x = particle["mass"] * particle["vx"]
            momentum_y = particle["mass"] * particle["vy"]
            particle_momentum = math.hypot(momentum_x, momentum_y)
            lines.extend(
                [
                    "",
                    f"[particle p{index}]",
                    f"px: {momentum_x:.8f}",
                    f"py: {momentum_y:.8f}",
                    f"|p|: {particle_momentum:.8f}",
                    f"start: {particle.get('starting_momentum', 0.0):.8f}",
                    f"dpx: {particle.get('momentum_delta_x', 0.0):.8f}",
                    f"dpy: {particle.get('momentum_delta_y', 0.0):.8f}",
                    f"v: ({particle['vx']:.8f}, {particle['vy']:.8f})",
                    "v0: "
                    f"({particle.get('starting_uncorrected_vx', particle['vx']):.8f}, "
                    f"{particle.get('starting_uncorrected_vy', particle['vy']):.8f})",
                    "old_vcorr: "
                    f"({particle.get('starting_corrected_vx', particle['vx']):.8f}, "
                    f"{particle.get('starting_corrected_vy', particle['vy']):.8f})",
                ]
            )
            contact_diagnostics = self.particle_contact_diagnostics(index, particle)
            if contact_diagnostics:
                lines.append("contacts:")
                for diagnostic in contact_diagnostics:
                    lines.append(f"  {diagnostic}")
        return lines

    def geo_dynamics_capture_lines(self):
        geo_dynamics = GeoDynamics()
        geo_dynamics.momentum_per_area = self.base.dynamics.momentum_per_area
        geo_dynamics.inverse_square_softening = self.base.dynamics.inverse_square_softening
        for particle_config in self.base.particle_configs:
            particle = dict(particle_config)
            particle["location"] = dict(particle["location"])
            geo_dynamics.add_particle(**particle)
        geo_dynamics.reset()

        start_total_momentum_x = 0.0
        start_total_momentum_y = 0.0
        rebound_total_momentum_x = 0.0
        rebound_total_momentum_y = 0.0
        for particle in geo_dynamics.particles:
            start_total_momentum_x += particle["mass"] * particle["velocity_at_starting_contact_x"]
            start_total_momentum_y += particle["mass"] * particle["velocity_at_starting_contact_y"]
            rebound_total_momentum_x += particle["mass"] * particle["velocity_at_current_overlap_rebound_x"]
            rebound_total_momentum_y += particle["mass"] * particle["velocity_at_current_overlap_rebound_y"]

        lines = [
            "[geo_total_momentum]",
            f"starting_px: {start_total_momentum_x:.8f}",
            f"starting_py: {start_total_momentum_y:.8f}",
            f"starting_|p|: {math.hypot(start_total_momentum_x, start_total_momentum_y):.8f}",
            f"current_overlap_rebound_px: {rebound_total_momentum_x:.8f}",
            f"current_overlap_rebound_py: {rebound_total_momentum_y:.8f}",
            "current_overlap_rebound_|p|: "
            f"{math.hypot(rebound_total_momentum_x, rebound_total_momentum_y):.8f}",
            "momentum_delta_x: "
            f"{rebound_total_momentum_x - start_total_momentum_x:.8f}",
            "momentum_delta_y: "
            f"{rebound_total_momentum_y - start_total_momentum_y:.8f}",
        ]
        for index, particle in enumerate(geo_dynamics.particles):
            lines.extend(
                [
                    "",
                    f"[geo_particle p{index}]",
                    "velocity_at_starting_contact: "
                    f"({particle['velocity_at_starting_contact_x']:.8f}, "
                    f"{particle['velocity_at_starting_contact_y']:.8f})",
                    "velocity_at_current_overlap_rebound: "
                    f"({particle['velocity_at_current_overlap_rebound_x']:.8f}, "
                    f"{particle['velocity_at_current_overlap_rebound_y']:.8f})",
                    f"starting_momentum: {particle['starting_momentum']:.8f}",
                    "starting_px: "
                    f"{particle['mass'] * particle['velocity_at_starting_contact_x']:.8f}",
                    "starting_py: "
                    f"{particle['mass'] * particle['velocity_at_starting_contact_y']:.8f}",
                    "current_overlap_rebound_px: "
                    f"{particle['mass'] * particle['velocity_at_current_overlap_rebound_x']:.8f}",
                    "current_overlap_rebound_py: "
                    f"{particle['mass'] * particle['velocity_at_current_overlap_rebound_y']:.8f}",
                ]
            )

        for report in geo_dynamics.contact_reports:
            source_index = report["source_index"]
            target_index = report["target_index"]
            lines.extend(
                [
                    "",
                    f"[geo_contact p{source_index}->p{target_index}]",
                    f"phase_assumption: {report['phase_assumption']}",
                    f"center_distance: {report['center_distance']:.8f}",
                    f"overlap_area: {report['overlap_area']:.8f}",
                    f"normal: ({report['normal_x']:.8f}, {report['normal_y']:.8f})",
                    "relative_normal_velocity_at_starting_contact: "
                    f"{report['relative_normal_velocity_at_starting_contact']:.8f}",
                    f"reduced_mass: {report['reduced_mass']:.8f}",
                    "incoming_relative_normal_momentum: "
                    f"{report['incoming_relative_normal_momentum']:.8f}",
                    "zero_velocity_center_distance: "
                    f"{report['zero_velocity_center_distance']:.8f}",
                    "zero_velocity_overlap_area: "
                    f"{report['zero_velocity_overlap_area']:.8f}",
                    "zero_velocity_overlap_momentum: "
                    f"{report['zero_velocity_overlap_momentum']:.8f}",
                    "zero_velocity_solution_clamped: "
                    f"{report['zero_velocity_solution_clamped']}",
                    f"compression_fraction: {report['compression_fraction']:.8f}",
                    f"rebound_fraction: {report['rebound_fraction']:.8f}",
                    f"turn_impulse: {report['turn_impulse']:.8f}",
                    f"rebound_impulse: {report['rebound_impulse']:.8f}",
                    "source_velocity_at_starting_contact: "
                    f"({report['source_velocity_at_starting_contact_x']:.8f}, "
                    f"{report['source_velocity_at_starting_contact_y']:.8f})",
                    "source_velocity_at_zero_velocity_point: "
                    f"({report['source_velocity_at_zero_velocity_point_x']:.8f}, "
                    f"{report['source_velocity_at_zero_velocity_point_y']:.8f})",
                    "source_velocity_at_current_overlap_compression: "
                    f"({report['source_velocity_at_current_overlap_compression_x']:.8f}, "
                    f"{report['source_velocity_at_current_overlap_compression_y']:.8f})",
                    "source_velocity_at_full_rebound: "
                    f"({report['source_velocity_at_full_rebound_x']:.8f}, "
                    f"{report['source_velocity_at_full_rebound_y']:.8f})",
                    "source_velocity_at_current_overlap_rebound: "
                    f"({report['source_velocity_at_current_overlap_rebound_x']:.8f}, "
                    f"{report['source_velocity_at_current_overlap_rebound_y']:.8f})",
                    "target_velocity_at_starting_contact: "
                    f"({report['target_velocity_at_starting_contact_x']:.8f}, "
                    f"{report['target_velocity_at_starting_contact_y']:.8f})",
                    "target_velocity_at_zero_velocity_point: "
                    f"({report['target_velocity_at_zero_velocity_point_x']:.8f}, "
                    f"{report['target_velocity_at_zero_velocity_point_y']:.8f})",
                    "target_velocity_at_current_overlap_compression: "
                    f"({report['target_velocity_at_current_overlap_compression_x']:.8f}, "
                    f"{report['target_velocity_at_current_overlap_compression_y']:.8f})",
                    "target_velocity_at_full_rebound: "
                    f"({report['target_velocity_at_full_rebound_x']:.8f}, "
                    f"{report['target_velocity_at_full_rebound_y']:.8f})",
                    "target_velocity_at_current_overlap_rebound: "
                    f"({report['target_velocity_at_current_overlap_rebound_x']:.8f}, "
                    f"{report['target_velocity_at_current_overlap_rebound_y']:.8f})",
                ]
            )
        return lines

    def geo_current_contact_capture_lines(self):
        lines = []
        reported_pairs = set()
        for source_index, source_particle in enumerate(self.base.particles):
            for slot in range(source_particle.get("sltnum", 0)):
                contact_record = source_particle["ccs"][slot]
                if contact_record.get("clflg", 0) == 0:
                    continue

                target_index = contact_record["pindex"]
                pair_key = tuple(sorted((source_index, target_index)))
                if pair_key in reported_pairs:
                    continue
                reported_pairs.add(pair_key)

                target_particle = self.base.particles[target_index]
                contact = self.base.dynamics.particle_contact(source_particle, target_particle)
                if contact is None:
                    continue

                nx, ny, overlap_area, center_distance = contact
                live_rel_vx = target_particle["vx"] - source_particle["vx"]
                live_rel_vy = target_particle["vy"] - source_particle["vy"]
                live_relative_normal_velocity = live_rel_vx * nx + live_rel_vy * ny
                live_phase = "compression" if live_relative_normal_velocity < 0.0 else "rebound"
                contact_state = self.base.contact_state.get(pair_key, {})
                source_mass = source_particle["mass"]
                target_mass = target_particle["mass"]
                reduced_mass = (source_mass * target_mass) / (source_mass + target_mass)
                live_relative_normal_momentum = reduced_mass * abs(live_relative_normal_velocity)
                current_overlap_momentum = self.base.dynamics.overlap_momentum(
                    overlap_area,
                    center_distance,
                    source_particle,
                )
                internal_contact_momentum = contact_state.get("internal_contact_momentum", 0.0)
                first_contact_velocities = contact_state.get("first_contact_velocities", {})
                source_start_vx, source_start_vy = first_contact_velocities.get(
                    source_index,
                    (source_particle["vx"], source_particle["vy"]),
                )
                target_start_vx, target_start_vy = first_contact_velocities.get(
                    target_index,
                    (target_particle["vx"], target_particle["vy"]),
                )

                source_x, source_y = self.base.current_location(source_particle)
                target_x, target_y = self.base.current_location(target_particle)
                geo_dynamics = GeoDynamics()
                geo_dynamics.momentum_per_area = self.base.dynamics.momentum_per_area
                geo_dynamics.inverse_square_softening = self.base.dynamics.inverse_square_softening
                geo_dynamics.add_particle(
                    source_particle["vx"],
                    source_particle["vy"],
                    source_particle["mass"],
                    source_particle["radius"],
                    x=source_x,
                    y=source_y,
                    momentum_per_area=source_particle.get("momentum_per_area"),
                    inverse_square_softening=source_particle.get("inverse_square_softening"),
                    velocity_at_starting_contact_x=source_start_vx,
                    velocity_at_starting_contact_y=source_start_vy,
                    zero_velocity_overlap_area=contact_state.get("geo_zero_velocity_overlap_area"),
                    zero_velocity_center_distance=contact_state.get("geo_zero_velocity_center_distance"),
                )
                geo_dynamics.add_particle(
                    target_particle["vx"],
                    target_particle["vy"],
                    target_particle["mass"],
                    target_particle["radius"],
                    x=target_x,
                    y=target_y,
                    momentum_per_area=target_particle.get("momentum_per_area"),
                    inverse_square_softening=target_particle.get("inverse_square_softening"),
                    velocity_at_starting_contact_x=target_start_vx,
                    velocity_at_starting_contact_y=target_start_vy,
                )
                geo_dynamics.reset()
                report = next(
                    (
                        contact_report
                        for contact_report in geo_dynamics.contact_reports
                        if contact_report["source_index"] == 0 and contact_report["target_index"] == 1
                    ),
                    None,
                )
                if report is None:
                    continue

                if live_phase == "compression":
                    source_prediction = (
                        report["source_velocity_at_current_overlap_compression_x"],
                        report["source_velocity_at_current_overlap_compression_y"],
                    )
                    target_prediction = (
                        report["target_velocity_at_current_overlap_compression_x"],
                        report["target_velocity_at_current_overlap_compression_y"],
                    )
                else:
                    source_prediction = (
                        report["source_velocity_at_current_overlap_rebound_x"],
                        report["source_velocity_at_current_overlap_rebound_y"],
                    )
                    target_prediction = (
                        report["target_velocity_at_current_overlap_rebound_x"],
                        report["target_velocity_at_current_overlap_rebound_y"],
                    )

                geo_start_px = source_mass * source_start_vx + target_mass * target_start_vx
                geo_start_py = source_mass * source_start_vy + target_mass * target_start_vy
                geo_prediction_px = (
                    source_mass * source_prediction[0] + target_mass * target_prediction[0]
                )
                geo_prediction_py = (
                    source_mass * source_prediction[1] + target_mass * target_prediction[1]
                )

                lines.extend(
                    [
                        "",
                        f"[geo_current_contact p{source_index}->p{target_index}]",
                        f"live_phase: {live_phase}",
                        "geo_phase: "
                        f"{contact_state.get('geo_phase', 'compression')}",
                        f"center_distance: {center_distance:.8f}",
                        f"overlap_area: {overlap_area:.8f}",
                        f"normal: ({nx:.8f}, {ny:.8f})",
                        f"live_relative_normal_velocity: {live_relative_normal_velocity:.8f}",
                        f"live_relative_normal_momentum: {live_relative_normal_momentum:.8f}",
                        f"current_overlap_momentum: {current_overlap_momentum:.8f}",
                        f"internal_contact_momentum: {internal_contact_momentum:.8f}",
                        "source_live_velocity: "
                        f"({source_particle['vx']:.8f}, {source_particle['vy']:.8f})",
                        "target_live_velocity: "
                        f"({target_particle['vx']:.8f}, {target_particle['vy']:.8f})",
                        "source_velocity_at_starting_contact: "
                        f"({source_start_vx:.8f}, {source_start_vy:.8f})",
                        "target_velocity_at_starting_contact: "
                        f"({target_start_vx:.8f}, {target_start_vy:.8f})",
                        "source_geo_prediction: "
                        f"({source_prediction[0]:.8f}, {source_prediction[1]:.8f})",
                        "target_geo_prediction: "
                        f"({target_prediction[0]:.8f}, {target_prediction[1]:.8f})",
                        f"geo_start_px: {geo_start_px:.8f}",
                        f"geo_start_py: {geo_start_py:.8f}",
                        "geo_prediction_px: "
                        f"{geo_prediction_px:.8f}",
                        "geo_prediction_py: "
                        f"{geo_prediction_py:.8f}",
                        "geo_prediction_momentum_delta_x: "
                        f"{geo_prediction_px - geo_start_px:.8f}",
                        "geo_prediction_momentum_delta_y: "
                        f"{geo_prediction_py - geo_start_py:.8f}",
                    f"compression_fraction: {report['compression_fraction']:.8f}",
                    f"rebound_fraction: {report['rebound_fraction']:.8f}",
                    "compression_velocity_fraction: "
                    f"{report['compression_velocity_fraction']:.8f}",
                    f"compression_progress: {report['compression_progress']:.8f}",
                    "rebound_velocity_fraction: "
                    f"{report['rebound_velocity_fraction']:.8f}",
                    "zero_velocity_overlap_area: "
                    f"{report['zero_velocity_overlap_area']:.8f}",
                        "state_zero_velocity_overlap_area: "
                        f"{contact_state.get('geo_zero_velocity_overlap_area', 0.0):.8f}",
                        "state_zero_velocity_source: "
                        f"{contact_state.get('geo_zero_velocity_source', 'none')}",
                        "state_zero_velocity_interpolated: "
                        f"{contact_state.get('geo_zero_velocity_interpolated', False)}",
                        "state_zero_velocity_interpolation_alpha: "
                        f"{contact_state.get('geo_zero_velocity_interpolation_alpha', 0.0):.8f}",
                        "zero_velocity_solution_clamped: "
                        f"{report['zero_velocity_solution_clamped']}",
                    ]
                )
        if not lines:
            return ["no active particle contacts"]
        return lines

    def draw_report(self):
        x = 12
        y = 12
        current_total_momentum_x, current_total_momentum_y = self.total_momentum_vector()
        current_kinetic_energy = self.total_kinetic_energy()
        start_total_momentum_mag = (
            self.start_total_momentum_x * self.start_total_momentum_x
            + self.start_total_momentum_y * self.start_total_momentum_y
        ) ** 0.5
        current_total_momentum_mag = (
            current_total_momentum_x * current_total_momentum_x
            + current_total_momentum_y * current_total_momentum_y
        ) ** 0.5
        total_momentum_mag_delta = current_total_momentum_mag - start_total_momentum_mag
        summary_lines = (
            f"total_momentum    |start|={start_total_momentum_mag:.8f} "
            f"|current|={current_total_momentum_mag:.8f} "
            f"diff={total_momentum_mag_delta:.8f}",
            f"ke                incoming={self.incoming_kinetic_energy:.8f} "
            f"live_start={self.start_kinetic_energy:.8f} "
            f"current={current_kinetic_energy:.8f}",
        )
        fps_line = f"frame={self.frame_number} fps={self.current_fps:.1f}"
        surface = self.report_font.render(fps_line, True, self.center_dot_color)
        self.screen.blit(surface, (x, y))
        y += 18
        for line in summary_lines:
            surface = self.report_font.render(line, True, self.center_dot_color)
            self.screen.blit(surface, (x, y))
            y += 18
        lifecycle_line = (
            f"released={self.base.dynamics.released_count} "
            f"recycled={self.base.dynamics.recycled_count} "
            f"escaped={self.base.dynamics.escaped_count}"
        )
        surface = self.report_font.render(lifecycle_line, True, self.center_dot_color)
        self.screen.blit(surface, (x, y))
        y += 18
        y += 6
        report_lines = [fps_line, *summary_lines, lifecycle_line]
        if(self.config.get("plot_report", True) == True):
                
            for index, particle in enumerate(self.base.particles):
                starting_momentum = particle.get("starting_momentum", 0.0)
                momentum_x = particle["mass"] * particle["vx"]
                momentum_y = particle["mass"] * particle["vy"]
                particle_momentum = (momentum_x * momentum_x + momentum_y * momentum_y) ** 0.5
                momentum_delta_x = particle.get("momentum_delta_x", 0.0)
                momentum_delta_y = particle.get("momentum_delta_y", 0.0)
                starting_uncorrected_vx = particle.get("starting_uncorrected_vx", particle["vx"])
                starting_uncorrected_vy = particle.get("starting_uncorrected_vy", particle["vy"])
                starting_corrected_vx = particle.get("starting_corrected_vx", particle["vx"])
                starting_corrected_vy = particle.get("starting_corrected_vy", particle["vy"])
                line = (
                    f"p{index} px={momentum_x:.8f} py={momentum_y:.8f} "
                    f"|p|={particle_momentum:.8f} "
                    f"start={starting_momentum:.8f} "
                    f"dpx={momentum_delta_x:.8f} dpy={momentum_delta_y:.8f} "
                    f"v=({particle['vx']:.8f},{particle['vy']:.8f}) "
                    f"v0=({starting_uncorrected_vx:.8f},{starting_uncorrected_vy:.8f}) "
                    f"old_vcorr=({starting_corrected_vx:.8f},{starting_corrected_vy:.8f})"
                )
                contact_diagnostics = self.particle_contact_diagnostics(index, particle)
                if contact_diagnostics:
                    line = f"{line} {' '.join(contact_diagnostics)}"
                surface = self.report_font.render(line, True, self.center_dot_color)
                self.screen.blit(surface, (x, y))
                y += 18
                report_lines.append(line)

        should_auto_capture = (
            self.frame_number in self.rpt_frames
            and self.frame_number not in self.captured_report_frames
        )
        if self.print_report_requested or should_auto_capture:
            self.write_report_capture(report_lines)
            self.captured_report_frames.add(self.frame_number)
            self.print_report_requested = False

    def write_report_capture(self, report_lines):
        self.report_capture_dir.mkdir(parents=True, exist_ok=True)
        report_file = self.report_capture_dir / f"Cap{self.frame_number:06d}.rpt"
        with report_file.open("w", encoding="utf-8") as outfile:
            outfile.write("[summary]\n")
            for line in report_lines:
                if len(line) >= 2 and line[0] == "p" and line[1].isdigit():
                    continue
                outfile.write(f"{line}\n")
            outfile.write("\n[particles]\n")
            for line in self.particle_capture_report_lines():
                outfile.write(f"{line}\n")
            outfile.write("\n[starting_overlap_diagnostics]\n")
            starting_overlap_lines = self.starting_overlap_capture_diagnostics()
            if not starting_overlap_lines:
                starting_overlap_lines = ["not frame 0 or no starting overlaps"]
            for line in starting_overlap_lines:
                outfile.write(f"{line}\n")
            outfile.write("\n[geo_dynamics]\n")
            for line in self.geo_dynamics_capture_lines():
                outfile.write(f"{line}\n")
            outfile.write("\n[geo_current_contacts]\n")
            for line in self.geo_current_contact_capture_lines():
                outfile.write(f"{line}\n")
        print(f"Wrote report capture: {report_file}")

    def run(self, particle_data, run_configuration=None):
        self.configure(particle_data, run_configuration)
        running = True
        while running:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.print_report_requested = True
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    self.set_zoom(self.zoom * 1.2)
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_KP_MINUS):
                    self.set_zoom(self.zoom / 1.2)

            self.current_fps = self.clock.get_fps()
            self.draw()
            if not self.paused:
                sub_dt = self.base.dt / self.base.substeps
                for _ in range(self.base.substeps):
                    self.base.do_substep(sub_dt)
                self.frame_number += 1
                if self.end_frame is not None and self.frame_number > self.end_frame:
                    running = False
            self.clock.tick(self.frame_rate)

        pygame.quit()
