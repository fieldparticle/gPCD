import math
import json
from pathlib import Path

import pygame

from base.Base import Base


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
        self.error_text_color = (255, 70, 70)
        self.collision_normal_color = (255, 245, 140)
        self.overlap_alpha = 185
        self.wall_ghost_fill = (120, 220, 255, 55)
        self.wall_ghost_edge = (90, 215, 255, 210)
        self.wall_ghost_center = (245, 245, 245, 190)
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
        if not self.validate_run_configuration():
            return False
        self.report_capture_dir = Path(self.config.get("data_dir", Path.cwd())) / "reports"
        self.clear_report_captures()
        self.clear_contact_snapshots()
        self.rpt_frames = self.normalized_report_frames(self.config.get("rpt_frames", []))
        self.captured_report_frames = set()
        self.base = Base()
        self.base.skip_starting_overlap_resolution = self.should_load_contact_snapshot()
        if "collision_stiffness_q" in self.config:
            self.base.collision_stiffness_q = float(self.config["collision_stiffness_q"])
        self.base.dt = float(self.config.get("dt", self.base.dt))
        self.base.substeps = int(self.config.get("substeps", self.base.substeps))
        if "zero_velocity_overlap_tolerance" in self.config:
            self.base.zero_velocity_overlap_tolerance = float(self.config["zero_velocity_overlap_tolerance"])
        self.base.neo_prediction_mode = self.config.get(
            "neo_prediction_mode",
            self.base.neo_prediction_mode,
        )
        self.base.max_contacts_per_particle = int(
            self.config.get("max_contacts_per_particle", self.base.max_contacts_per_particle)
        )
        self.base.momentum_per_area = float(
            self.config.get("momentum_per_area", self.base.momentum_per_area)
        )
        self.base.inverse_square_softening = float(
            self.config.get("inverse_square_softening", self.base.inverse_square_softening)
        )
        self.base.configure_flow(self.config)

        wall_box = self.config.get("wall_box")
        if wall_box is not None and wall_box is not False:
            self.base.set_walls(*wall_box)
            self.world_box = tuple(float(value) for value in wall_box)
        elif self.config.get("walls_on") is True:
            wall_box = (
                float(self.config["WallXMIN"]),
                float(self.config["WallXMAX"]),
                float(self.config["WallYMIN"]),
                float(self.config["WallYMAX"]),
            )
            self.base.set_walls(*wall_box)
            self.world_box = wall_box
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
        if not self.load_contact_snapshot_if_configured():
            return False
        self.start_kinetic_energy = self.total_kinetic_energy()
        self.frame_number = 0
        self.current_fps = 0.0
        self.paused = False
        return True

    def validate_run_configuration(self):
        required_items = ("collision_stiffness_q",)
        missing_items = [
            key
            for key in required_items
            if key not in self.config or self.config[key] in (None, "")
        ]
        invalid_items = []

        if "collision_stiffness_q" in self.config:
            try:
                stiffness_q = float(self.config["collision_stiffness_q"])
            except (TypeError, ValueError):
                invalid_items.append("collision_stiffness_q must be numeric.")
            else:
                if stiffness_q <= 0.0:
                    invalid_items.append("collision_stiffness_q must be > 0.")

        if not missing_items and not invalid_items:
            return True

        message_lines = []
        if missing_items:
            message_lines.append("Missing RUN_CONFIGURATION item(s):")
            message_lines.extend(f"  - {item}" for item in missing_items)
        if invalid_items:
            if message_lines:
                message_lines.append("")
            message_lines.append("Invalid RUN_CONFIGURATION item(s):")
            message_lines.extend(f"  - {item}" for item in invalid_items)
        message = "\n".join(message_lines)
        self.show_config_error(message)
        return False

    @staticmethod
    def show_config_error(message):
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing required configuration", message)
            root.destroy()
        except Exception:
            print(f"Missing required configuration:\n{message}")

    def clear_report_captures(self):
        self.report_capture_dir.mkdir(parents=True, exist_ok=True)
        for report_file in self.report_capture_dir.glob("*.rpt"):
            if report_file.is_file():
                report_file.unlink()

    def clear_contact_snapshots(self):
        if not self.config.get("contact_snapshot_file"):
            return
        if self.should_load_contact_snapshot():
            return

        snapshot_path = self.contact_snapshot_path(0)
        snapshot_dir = snapshot_path.parent
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        snapshot_pattern = str(Path(str(self.config["contact_snapshot_file"])).name)
        snapshot_pattern = snapshot_pattern.replace("{frame:06d}", "*").replace("{frame}", "*")
        for snapshot_file in snapshot_dir.glob(snapshot_pattern):
            if snapshot_file.is_file():
                snapshot_file.unlink()

        particle_data_pattern = snapshot_pattern.replace(".json", ".particle_data.cfg")
        for particle_data_file in snapshot_dir.glob(particle_data_pattern):
            if particle_data_file.is_file():
                particle_data_file.unlink()

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

    def contact_snapshot_mode(self):
        snapshot_file = self.config.get("contact_snapshot_file")
        default_mode = "load" if snapshot_file else "off"
        return str(self.config.get("contact_snapshot_mode", default_mode)).strip().lower()

    def contact_snapshot_path(self, frame=None):
        snapshot_file = self.config.get("contact_snapshot_file")
        if not snapshot_file:
            return None

        snapshot_file = str(snapshot_file)
        if frame is not None:
            snapshot_file = snapshot_file.format(frame=frame)
        path = Path(snapshot_file)
        if not path.is_absolute():
            path = Path(self.config.get("data_dir", Path.cwd())) / path
        return path

    def should_load_contact_snapshot(self):
        return self.contact_snapshot_path() is not None and self.contact_snapshot_mode() in (
            "load",
            "import",
            "read",
        )

    def should_save_contact_snapshot(self):
        return self.contact_snapshot_path(self.frame_number) is not None and self.contact_snapshot_mode() in (
            "save",
            "export",
            "write",
        )

    def load_contact_snapshot_if_configured(self):
        if not self.should_load_contact_snapshot():
            return True

        snapshot_path = self.contact_snapshot_path()
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        if not snapshot_path.exists():
            self.show_config_error(
                "Contact snapshot not found:\n"
                f"{snapshot_path}\n\n"
                "Run the source cfg with contact_snapshot_mode=\"save\" first, "
                "using rpt_frames that include this frame."
            )
            return False
        with snapshot_path.open("r", encoding="utf-8") as infile:
            snapshot = json.load(infile)
        self.base.load_contact_state_snapshot(snapshot)
        self.base.report.clear()
        self.base.record_step_report()
        print(f"Loaded contact snapshot: {snapshot_path}")
        return True

    def write_contact_snapshot_if_configured(self):
        if not self.should_save_contact_snapshot():
            return None

        snapshot_path = self.contact_snapshot_path(self.frame_number)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        with snapshot_path.open("w", encoding="utf-8") as outfile:
            json.dump(self.base.contact_state_snapshot(), outfile, indent=2)
            outfile.write("\n")
        print(f"Wrote contact snapshot: {snapshot_path}")
        return snapshot_path

    def write_particle_data_snapshot(self, snapshot_path):
        particle_data_path = snapshot_path.with_suffix(".particle_data.cfg")
        with particle_data_path.open("w", encoding="utf-8") as outfile:
            outfile.write("PARTICLE_DATA =\n")
            outfile.write("{\n")
            for index, particle in enumerate(self.base.particles, start=1):
                x, y = self.base.current_location(particle)
                outfile.write(f"    p{index} =\n")
                outfile.write("    {\n")
                outfile.write(
                    "        location = "
                    f"{{ use = 0; x1 = {x:.8f}; y1 = {y:.8f}; z1 = 2.0; "
                    f"x2 = {x:.8f}; y2 = {y:.8f}; z2 = 2.0; }};\n"
                )
                outfile.write(f"        vx = {particle['vx']:.8f};\n")
                outfile.write(f"        vy = {particle['vy']:.8f};\n")
                outfile.write(f"        mass = {particle['mass']:.8f};\n")
                outfile.write(f"        radius = {particle['radius']:.8f};\n")
                outfile.write("    };\n")
            outfile.write("};\n")
        print(f"Wrote particle data snapshot: {particle_data_path}")
        return particle_data_path

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
            if not self.base.is_active_particle(particle):
                continue
            x, y = self.base.current_location(particle)
            center = self.to_screen(x, y)
            radius = self.radius_to_pixels(particle["radius"])
            fill = particle.get("fill", self.default_fill)
            edge = particle.get("edge", self.default_edge)
            particle_screen_data.append((index, particle, x, y, center, radius, fill, edge))
            pygame.draw.circle(self.screen, fill, center, radius)

        self.draw_wall_ghost_particles()
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

    def draw_wall_ghost_particles(self):
        if self.base.walls is None:
            return

        ghost_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        for _index, particle in enumerate(self.base.particles):
            if not self.base.is_active_particle(particle):
                continue

            for contact_record in particle.get("bcs", []):
                wall_flag = contact_record.get("clflg", 0)
                if wall_flag == 0:
                    continue

                contact = self.base.wall_ghost_contact(particle, wall_flag, self.base.walls)
                if contact is None:
                    continue

                ghost_x, ghost_y = contact["ghost_location"]
                center = self.to_screen(ghost_x, ghost_y)
                radius = self.radius_to_pixels(particle["radius"])
                pygame.draw.circle(ghost_surface, self.wall_ghost_fill, center, radius)
                pygame.draw.circle(ghost_surface, self.wall_ghost_edge, center, radius, 2)
                pygame.draw.circle(ghost_surface, self.wall_ghost_center, center, 3)

        self.screen.blit(ghost_surface, (0, 0))

    def draw_particle_overlaps(self, particle_screen_data):
        for left_pos in range(len(particle_screen_data)):
            left = particle_screen_data[left_pos]
            for right_pos in range(left_pos + 1, len(particle_screen_data)):
                right = particle_screen_data[right_pos]
                _li, left_particle, _lx, _ly, left_center, left_radius, left_fill, _left_edge = left
                _ri, right_particle, _rx, _ry, right_center, right_radius, right_fill, _right_edge = right
                if self.base.particle_contact(left_particle, right_particle) is None:
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
        contact = self.base.particle_contact(source_particle, target_particle)
        if contact is None:
            return
        nx, ny, _overlap_area, _center_distance = contact
        source_x, source_y = self.base.current_location(source_particle)
        target_x, target_y = self.base.current_location(target_particle)
        mid_x = 0.5 * (source_x + target_x)
        mid_y = 0.5 * (source_y + target_y)
        self.draw_normal_line(mid_x, mid_y, nx, ny)

    def draw_wall_collision_normal(self, source_particle, wall_flag):
        contact = self.base.wall_contact(source_particle, wall_flag, self.base.walls)
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
            if self.base.is_active_particle(particle)
        )

    def total_momentum_vector(self):
        momentum_x = 0.0
        momentum_y = 0.0
        for particle in self.base.particles:
            if not self.base.is_active_particle(particle):
                continue
            momentum_x += particle["mass"] * particle["vx"]
            momentum_y += particle["mass"] * particle["vy"]
        return momentum_x, momentum_y

    def total_internal_momentum_vector(self):
        return self.particle_side_internal_momentum_vector()

    @staticmethod
    def canonical_contact_internal_normal_momentum(state):
        return state.get(
            "neo_stored_internal_normal_momentum",
            state.get("neo_rebound_remaining_normal_momentum", 0.0),
        )

    def pair_internal_momentum_vector(self):
        return self.particle_pair_internal_momentum_vector()

    def particle_pair_internal_momentum_vector(self):
        momentum_x = 0.0
        momentum_y = 0.0
        for source_index, target_index in self.active_particle_contact_pairs():
            source_particle = self.base.particles[source_index]
            target_particle = self.base.particles[target_index]
            contact = self.base.particle_contact(source_particle, target_particle)
            if contact is None:
                continue
            nx, ny, _overlap_area, _center_distance = contact
            state = (
                self.base.source_geo_contact_state(source_particle, target_index)
                or self.base.source_geo_contact_state(target_particle, source_index)
                or {}
            )
            internal_normal_momentum = self.canonical_contact_internal_normal_momentum(state)
            # Pair-contact internal vectors are equal and opposite across the two
            # real particles, so their system-vector contribution cancels.
            momentum_x += internal_normal_momentum * nx
            momentum_y += internal_normal_momentum * ny
            momentum_x -= internal_normal_momentum * nx
            momentum_y -= internal_normal_momentum * ny
        return momentum_x, momentum_y

    def particle_side_internal_momentum_vector(self):
        momentum_x = 0.0
        momentum_y = 0.0
        for index, particle in enumerate(self.base.particles):
            if not self.base.is_active_particle(particle):
                continue
            particle_x, particle_y = self.particle_contact_internal_momentum_vector(index)
            momentum_x += particle_x
            momentum_y += particle_y
        return momentum_x, momentum_y

    def particle_contact_internal_momentum_vector(self, particle_index):
        momentum_x = 0.0
        momentum_y = 0.0
        for source_index, target_index in self.active_particle_contact_pairs():
            if particle_index not in (source_index, target_index):
                continue
            source_particle = self.base.particles[source_index]
            target_particle = self.base.particles[target_index]
            contact = self.base.particle_contact(source_particle, target_particle)
            if contact is None:
                continue
            nx, ny, _overlap_area, _center_distance = contact
            state = (
                self.base.source_geo_contact_state(source_particle, target_index)
                or self.base.source_geo_contact_state(target_particle, source_index)
                or {}
            )
            internal_normal_momentum = self.canonical_contact_internal_normal_momentum(state)
            sign = 1.0 if particle_index == source_index else -1.0
            momentum_x += sign * internal_normal_momentum * nx
            momentum_y += sign * internal_normal_momentum * ny

        for wall_key in self.active_wall_contacts():
            wall_particle_index, wall_flag = wall_key
            if wall_particle_index != particle_index:
                continue
            particle = self.base.particles[particle_index]
            contact = self.base.wall_contact(particle, wall_flag, self.base.walls)
            if contact is None:
                continue
            nx, ny, _overlap_area, _center_distance = contact
            state = self.base.wall_contact_state.get(wall_key, {})
            internal_normal_momentum = self.canonical_contact_internal_normal_momentum(state)
            momentum_x -= internal_normal_momentum * nx
            momentum_y -= internal_normal_momentum * ny
        return momentum_x, momentum_y

    def wall_internal_momentum_vector(self):
        momentum_x = 0.0
        momentum_y = 0.0
        for particle_index, wall_flag in self.active_wall_contacts():
            particle = self.base.particles[particle_index]
            contact = self.base.wall_contact(particle, wall_flag, self.base.walls)
            if contact is None:
                continue
            nx, ny, _overlap_area, _center_distance = contact
            wall_key = (particle_index, wall_flag)
            state = self.base.wall_contact_state.get(wall_key, {})
            internal_normal_momentum = self.canonical_contact_internal_normal_momentum(state)
            momentum_x += internal_normal_momentum * nx
            momentum_y += internal_normal_momentum * ny
        return momentum_x, momentum_y

    def contact_internal_momentum_vector(self):
        pair_x, pair_y = self.particle_side_internal_momentum_vector()
        wall_x, wall_y = self.wall_internal_momentum_vector()
        return pair_x + wall_x, pair_y + wall_y

    def contact_internal_scalar_totals(self):
        pair_internal = 0.0
        wall_internal = 0.0
        stored = 0.0
        released = 0.0
        remaining = 0.0

        for source_index, target_index in self.active_particle_contact_pairs():
            source_particle = self.base.particles[source_index]
            target_particle = self.base.particles[target_index]
            state = (
                self.base.source_geo_contact_state(source_particle, target_index)
                or self.base.source_geo_contact_state(target_particle, source_index)
                or {}
            )
            pair_internal += abs(self.canonical_contact_internal_normal_momentum(state))
            stored += state.get("neo_stored_internal_normal_momentum", 0.0)
            released += state.get("neo_rebound_released_normal_momentum", 0.0)
            remaining += state.get("neo_rebound_remaining_normal_momentum", 0.0)

        for wall_key in self.active_wall_contacts():
            particle_index, wall_flag = wall_key
            particle = self.base.particles[particle_index]
            contact = self.base.wall_contact(particle, wall_flag, self.base.walls)
            if contact is None:
                continue
            state = self.base.wall_contact_state.get(wall_key, {})
            wall_internal += abs(self.canonical_contact_internal_normal_momentum(state))
            stored += state.get("neo_stored_internal_normal_momentum", 0.0)
            released += state.get("neo_rebound_released_normal_momentum", 0.0)
            remaining += state.get("neo_rebound_remaining_normal_momentum", 0.0)

        return pair_internal, wall_internal, stored, released, remaining

    def momentum_diagnostic_values(self):
        current_x, current_y = self.total_momentum_vector()
        particle_side_internal_x, particle_side_internal_y = self.particle_side_internal_momentum_vector()
        particle_pair_internal_x, particle_pair_internal_y = self.particle_pair_internal_momentum_vector()
        wall_internal_x, wall_internal_y = self.wall_internal_momentum_vector()
        contact_internal_x = particle_side_internal_x + wall_internal_x
        contact_internal_y = particle_side_internal_y + wall_internal_y
        pair_scalar, wall_scalar, stored, released, remaining = self.contact_internal_scalar_totals()
        wall_velocity_reservoir_x = getattr(self.base, "wall_ghost_momentum_x", 0.0)
        wall_velocity_reservoir_y = getattr(self.base, "wall_ghost_momentum_y", 0.0)

        modeled_without_reservoir_x = current_x + contact_internal_x
        modeled_without_reservoir_y = current_y + contact_internal_y
        modeled_x = modeled_without_reservoir_x + wall_velocity_reservoir_x
        modeled_y = modeled_without_reservoir_y + wall_velocity_reservoir_y
        drift_x = self.start_total_momentum_x - modeled_x
        drift_y = self.start_total_momentum_y - modeled_y
        drift_without_reservoir_x = self.start_total_momentum_x - modeled_without_reservoir_x
        drift_without_reservoir_y = self.start_total_momentum_y - modeled_without_reservoir_y

        values = {
            "start_px": self.start_total_momentum_x,
            "start_py": self.start_total_momentum_y,
            "start_p": math.hypot(self.start_total_momentum_x, self.start_total_momentum_y),
            "current_px": current_x,
            "current_py": current_y,
            "current_p": math.hypot(current_x, current_y),
            "particle_velocity_px": current_x,
            "particle_velocity_py": current_y,
            "particle_velocity_p": math.hypot(current_x, current_y),
            "particle_side_internal_px": particle_side_internal_x,
            "particle_side_internal_py": particle_side_internal_y,
            "particle_side_internal_p": math.hypot(particle_side_internal_x, particle_side_internal_y),
            "particle_pair_internal_px": particle_pair_internal_x,
            "particle_pair_internal_py": particle_pair_internal_y,
            "particle_pair_internal_p": math.hypot(particle_pair_internal_x, particle_pair_internal_y),
            "pair_internal_px": particle_pair_internal_x,
            "pair_internal_py": particle_pair_internal_y,
            "pair_internal_p": math.hypot(particle_pair_internal_x, particle_pair_internal_y),
            "wall_internal_px": wall_internal_x,
            "wall_internal_py": wall_internal_y,
            "wall_internal_p": math.hypot(wall_internal_x, wall_internal_y),
            "wall_ghost_internal_px": wall_internal_x,
            "wall_ghost_internal_py": wall_internal_y,
            "wall_ghost_internal_p": math.hypot(wall_internal_x, wall_internal_y),
            "contact_internal_px": contact_internal_x,
            "contact_internal_py": contact_internal_y,
            "contact_internal_p": math.hypot(contact_internal_x, contact_internal_y),
            "modeled_total_without_reservoir_px": modeled_without_reservoir_x,
            "modeled_total_without_reservoir_py": modeled_without_reservoir_y,
            "modeled_total_without_reservoir_p": math.hypot(
                modeled_without_reservoir_x,
                modeled_without_reservoir_y,
            ),
            "modeled_total_px": modeled_x,
            "modeled_total_py": modeled_y,
            "modeled_total_p": math.hypot(modeled_x, modeled_y),
            "wall_velocity_reservoir_px": wall_velocity_reservoir_x,
            "wall_velocity_reservoir_py": wall_velocity_reservoir_y,
            "wall_velocity_reservoir_p": math.hypot(wall_velocity_reservoir_x, wall_velocity_reservoir_y),
            "wall_ghost_px": wall_velocity_reservoir_x,
            "wall_ghost_py": wall_velocity_reservoir_y,
            "wall_ghost_p": math.hypot(wall_velocity_reservoir_x, wall_velocity_reservoir_y),
            "modeled_total_with_wall_px": modeled_x,
            "modeled_total_with_wall_py": modeled_y,
            "modeled_total_with_wall_p": math.hypot(modeled_x, modeled_y),
            "drift_modeled_px": drift_x,
            "drift_modeled_py": drift_y,
            "drift_modeled_p": math.hypot(drift_x, drift_y),
            "drift_without_reservoir_px": drift_without_reservoir_x,
            "drift_without_reservoir_py": drift_without_reservoir_y,
            "drift_without_reservoir_p": math.hypot(
                drift_without_reservoir_x,
                drift_without_reservoir_y,
            ),
            "drift_with_wall_ghost_px": drift_x,
            "drift_with_wall_ghost_py": drift_y,
            "drift_with_wall_ghost_p": math.hypot(drift_x, drift_y),
            "pair_internal_scalar": pair_scalar,
            "wall_internal_scalar": wall_scalar,
            "contact_internal_scalar": pair_scalar + wall_scalar,
            "contact_stored_scalar": stored,
            "contact_released_scalar": released,
            "contact_remaining_scalar": remaining,
            "active_pair_contacts": float(len(self.active_particle_contact_pairs())),
            "active_wall_contacts": float(len(self.active_wall_contacts())),
        }
        return values

    @staticmethod
    def momentum_row(label, momentum_x, momentum_y):
        momentum_mag = math.hypot(momentum_x, momentum_y)
        return f"{label:<17} px={momentum_x:.8f} py={momentum_y:.8f} |p|={momentum_mag:.8f}"

    def momentum_balance_rows(self):
        current_momentum_x, current_momentum_y = self.total_momentum_vector()
        particle_side_internal_x, particle_side_internal_y = self.particle_side_internal_momentum_vector()
        wall_internal_x, wall_internal_y = self.wall_internal_momentum_vector()
        wall_velocity_reservoir_x = getattr(self.base, "wall_ghost_momentum_x", 0.0)
        wall_velocity_reservoir_y = getattr(self.base, "wall_ghost_momentum_y", 0.0)
        modeled_with_wall_x = (
            current_momentum_x
            + particle_side_internal_x
            + wall_internal_x
            + wall_velocity_reservoir_x
        )
        modeled_with_wall_y = (
            current_momentum_y
            + particle_side_internal_y
            + wall_internal_y
            + wall_velocity_reservoir_y
        )
        drift_x = self.start_total_momentum_x - modeled_with_wall_x
        drift_y = self.start_total_momentum_y - modeled_with_wall_y
        return (
            self.momentum_row("start", self.start_total_momentum_x, self.start_total_momentum_y),
            self.momentum_row("particle_velocity", current_momentum_x, current_momentum_y),
            self.momentum_row("particle_side_int", particle_side_internal_x, particle_side_internal_y),
            self.momentum_row("wall_ghost_int", wall_internal_x, wall_internal_y),
            self.momentum_row("wall_vel_reserv", wall_velocity_reservoir_x, wall_velocity_reservoir_y),
            self.momentum_row("modeled_total", modeled_with_wall_x, modeled_with_wall_y),
            self.momentum_row("drift", drift_x, drift_y),
        )

    def guardrail_errors(self):
        errors = []
        errors.extend(self.max_particle_overlap_errors())
        for index, particle in enumerate(self.base.particles):
            if not self.base.is_active_particle(particle):
                continue

            partner_count = particle.get("sltnum", 0)
            if partner_count > 4:
                errors.append(
                    f"ERROR p{index} collision_partners={partner_count} exceeds 4"
                )

            if self.base.walls is None:
                continue
            x, y = self.base.current_location(particle)
            walls = self.base.walls
            outside = []
            if x < walls["start_x"]:
                outside.append(f"x={x:.8f}<xmin={walls['start_x']:.8f}")
            if x > walls["end_x"]:
                outside.append(f"x={x:.8f}>xmax={walls['end_x']:.8f}")
            if y < walls["start_y"]:
                outside.append(f"y={y:.8f}<ymin={walls['start_y']:.8f}")
            if y > walls["end_y"]:
                outside.append(f"y={y:.8f}>ymax={walls['end_y']:.8f}")
            if outside:
                errors.append(f"ERROR p{index} boundary_exceeded {' '.join(outside)}")
        return errors

    def max_particle_overlap_errors(self):
        errors = []
        particles = self.base.particles
        for source_index, source_particle in enumerate(particles):
            if not self.base.is_active_particle(source_particle):
                continue
            source_x, source_y = self.base.current_location(source_particle)
            source_radius = source_particle["radius"]
            for target_index in range(source_index + 1, len(particles)):
                target_particle = particles[target_index]
                if not self.base.is_active_particle(target_particle):
                    continue
                target_x, target_y = self.base.current_location(target_particle)
                target_radius = target_particle["radius"]
                center_distance = math.hypot(target_x - source_x, target_y - source_y)
                radius_sum = source_radius + target_radius
                if center_distance >= radius_sum:
                    continue

                overlap_depth = radius_sum - center_distance
                max_overlap_depth = min(source_radius, target_radius)
                if overlap_depth <= max_overlap_depth + 1.0e-12:
                    continue

                overlap_pct = (
                    100.0 * overlap_depth / radius_sum
                    if radius_sum > 0.0
                    else 0.0
                )
                max_overlap_pct = (
                    100.0 * max_overlap_depth / radius_sum
                    if radius_sum > 0.0
                    else 0.0
                )
                errors.append(
                    f"ERROR p{source_index}-p{target_index} "
                    f"overlap_depth={overlap_depth:.8f} "
                    f"exceeds_max={max_overlap_depth:.8f} "
                    f"overlap={overlap_pct:.3f}% "
                    f"max={max_overlap_pct:.3f}% "
                    f"center_distance={center_distance:.8f}"
                )
        return errors

    @staticmethod
    def particle_collision_partners(particle):
        partners = []
        for contact_record in particle.get("ccs", []):
            if contact_record.get("clflg", 0) == 0:
                continue
            partners.append(contact_record.get("pindex", 0))
        return partners

    def particle_contact_diagnostics(self, source_index, source_particle):
        diagnostics = []
        for slot in range(source_particle.get("sltnum", 0)):
            contact_record = source_particle["ccs"][slot]
            if contact_record.get("clflg", 0) == 0:
                continue
            target_index = contact_record["pindex"]
            target_particle = self.base.particles[target_index]
            contact = self.base.particle_contact(source_particle, target_particle)
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
            contact_state = self.base.source_geo_contact_state(source_particle, target_index) or {}
            internal_contact_momentum = contact_state.get("internal_contact_momentum", 0.0)
            neo_internal_normal_momentum = self.canonical_contact_internal_normal_momentum(contact_state)
            neo_stored_internal_momentum = contact_state.get("neo_stored_internal_normal_momentum", 0.0)
            neo_released_internal_momentum = contact_state.get("neo_rebound_released_normal_momentum", 0.0)
            neo_remaining_internal_momentum = contact_state.get("neo_rebound_remaining_normal_momentum", 0.0)
            overlap_contact_momentum = contact_state.get("overlap_contact_momentum", 0.0)
            last_relative_normal_velocity = contact_state.get(
                "last_relative_normal_velocity",
                rel_normal_velocity,
            )
            zero_source = contact_state.get("geo_zero_velocity_source", "")
            motion_mode = contact_state.get("neo_motion_mode", "")
            internal_phase = contact_state.get("internal_momentum_phase", "")
            lock_state = contact_state.get("contact_lock_state", "free")
            blocked_relative = contact_state.get("locked_blocked_relative_normal_velocity", 0.0)
            phase = "closing" if rel_normal_velocity < 0.0 else "separating"
            diagnostics.append(
                f"c{source_index}->{target_index} reln={rel_normal_velocity:.8f} "
                f"rmass={reduced_mass:.8f} relp={rel_normal_momentum:.8f} "
                f"omom={overlap_contact_momentum:.8f} cinternal={internal_contact_momentum:.8f} "
                f"nimom={neo_internal_normal_momentum:.8f} "
                f"istore={neo_stored_internal_momentum:.8f} "
                f"irel={neo_released_internal_momentum:.8f} "
                f"irem={neo_remaining_internal_momentum:.8f} "
                f"last_reln={last_relative_normal_velocity:.8f} phase={phase} "
                f"imode={internal_phase} lock={lock_state} "
                f"block_reln={blocked_relative:.8f} mode={motion_mode} zsrc={zero_source}"
            )
        for contact_record in source_particle.get("bcs", []):
            wall_flag = contact_record.get("clflg", 0)
            if wall_flag == 0:
                continue

            contact = self.base.wall_contact(source_particle, wall_flag, self.base.walls)
            if contact is None:
                continue

            nx, ny, _overlap_area, _center_distance = contact
            normal_velocity = source_particle["vx"] * nx + source_particle["vy"] * ny
            wall_key = (source_index, wall_flag)
            contact_state = self.base.wall_contact_state.get(wall_key, {})
            overlap_contact_momentum = contact_state.get("overlap_contact_momentum", 0.0)
            neo_stored_internal_momentum = contact_state.get("neo_stored_internal_normal_momentum", 0.0)
            neo_released_internal_momentum = contact_state.get("neo_rebound_released_normal_momentum", 0.0)
            neo_remaining_internal_momentum = contact_state.get("neo_rebound_remaining_normal_momentum", 0.0)
            last_normal_velocity = contact_state.get("last_relative_normal_velocity", normal_velocity)
            zero_source = contact_state.get("geo_zero_velocity_source", "")
            motion_mode = contact_state.get("neo_motion_mode", "")
            internal_phase = contact_state.get("internal_momentum_phase", "")
            lock_state = contact_state.get("contact_lock_state", "free")
            blocked_normal = contact_state.get("locked_blocked_normal_velocity", 0.0)
            phase = contact_state.get(
                "geo_phase",
                "closing" if normal_velocity > 0.0 else "separating",
            )
            diagnostics.append(
                f"w{self.wall_name(wall_flag)} vn={normal_velocity:.8f} "
                f"p={source_particle['mass'] * abs(normal_velocity):.8f} "
                f"omom={overlap_contact_momentum:.8f} "
                f"istore={neo_stored_internal_momentum:.8f} "
                f"irel={neo_released_internal_momentum:.8f} "
                f"irem={neo_remaining_internal_momentum:.8f} "
                f"last_vn={last_normal_velocity:.8f} phase={phase} "
                f"imode={internal_phase} lock={lock_state} "
                f"block_vn={blocked_normal:.8f} mode={motion_mode} zsrc={zero_source}"
            )
        return diagnostics

    def compact_particle_capture_report_lines(self):
        lines = []
        for index, particle in enumerate(self.base.particles):
            x, y = self.base.current_location(particle)
            momentum_x = particle["mass"] * particle["vx"]
            momentum_y = particle["mass"] * particle["vy"]
            particle_momentum = math.hypot(momentum_x, momentum_y)
            internal_momentum_x, internal_momentum_y = self.particle_contact_internal_momentum_vector(index)
            collision_partners = self.particle_collision_partners(particle)
            lines.extend(
                [
                    "",
                    f"[particle p{index} Neo ]",
                    f"loc: ({x:.8f}, {y:.8f})",
                    f"px: {momentum_x:.8f}",
                    f"py: {momentum_y:.8f}",
                    f"|p|: {particle_momentum:.8f}",
                    f"start: {particle.get('starting_momentum', 0.0):.8f}",
                    f"dpx: {particle.get('momentum_delta_x', 0.0):.8f}",
                    f"dpy: {particle.get('momentum_delta_y', 0.0):.8f}",
                    "nimom: "
                    f"({internal_momentum_x:.8f}, "
                    f"{internal_momentum_y:.8f})",
                    f"v: ({particle['vx']:.8f}, {particle['vy']:.8f})",
                    "v0: "
                    f"({particle.get('starting_uncorrected_vx', particle['vx']):.8f}, "
                    f"{particle.get('starting_uncorrected_vy', particle['vy']):.8f})",
                    f"collision_partners: {collision_partners}",
                ]
            )
            contact_lines = self.particle_contact_capture_lines(index, particle)
            contact_lines.extend(self.wall_contact_capture_lines(index, particle))
            if contact_lines:
                lines.append("contacts:")
                lines.extend(contact_lines)
        return lines

    def cluster_capture_report_lines(self):
        pairs = self.active_particle_contact_pairs()
        wall_contacts = self.active_wall_contacts()
        clusters = [set(cluster) for cluster in self.base.pair_contact_clusters(pairs)]

        clustered_particles = set()
        for cluster in clusters:
            clustered_particles.update(cluster)

        for particle_index, _wall_flag in wall_contacts:
            if particle_index not in clustered_particles:
                clusters.append({particle_index})
                clustered_particles.add(particle_index)

        if not clusters:
            return []

        lines = ["", "[clusters]"]
        for cluster_index, cluster in enumerate(clusters):
            particle_indices = sorted(cluster)
            cluster_pairs = [
                pair for pair in pairs if pair[0] in cluster and pair[1] in cluster
            ]
            cluster_walls = [
                (particle_index, wall_flag)
                for particle_index, wall_flag in wall_contacts
                if particle_index in cluster
            ]
            phases, internal_modes = self.cluster_phase_modes(cluster_pairs, cluster_walls)
            current_px, current_py, current_ke = self.cluster_current_momentum_energy(particle_indices)
            start_px, start_py, start_ke = self.cluster_start_momentum_energy(particle_indices)
            cimom_x, cimom_y, cimom, cistore, cirel, cirem = self.cluster_internal_momentum_totals(
                cluster_pairs,
                cluster_walls,
            )
            contact_labels = [f"{source}-{target}" for source, target in cluster_pairs]
            contact_labels.extend(
                f"{particle_index}-{self.wall_name(wall_flag)}"
                for particle_index, wall_flag in cluster_walls
            )
            if not contact_labels:
                contact_labels = ["none"]

            lines.extend(
                [
                    "",
                    f"[cluster c{cluster_index}]",
                    "particles=" + ",".join(f"p{index}" for index in particle_indices),
                    "contacts=" + ",".join(contact_labels),
                    "phase=" + ",".join(phases),
                    "imode=" + ",".join(internal_modes),
                    f"p_start=({start_px:.8f}, {start_py:.8f})",
                    f"p_current=({current_px:.8f}, {current_py:.8f})",
                    f"ke_start={start_ke:.8f}",
                    f"ke_current={current_ke:.8f}",
                    f"cimom={cimom:.8f}",
                    f"cimom_vec=({cimom_x:.8f}, {cimom_y:.8f})",
                    f"cistore={cistore:.8f}",
                    f"cirel={cirel:.8f}",
                    f"cirem={cirem:.8f}",
                ]
            )
        return lines

    def active_particle_contact_pairs(self):
        pairs = []
        seen = set()
        for source_index, source_particle in enumerate(self.base.particles):
            for slot in range(source_particle.get("sltnum", 0)):
                contact_record = source_particle["ccs"][slot]
                if contact_record.get("clflg", 0) == 0:
                    continue
                target_index = contact_record["pindex"]
                pair = tuple(sorted((source_index, target_index)))
                if pair in seen:
                    continue
                if self.base.particle_contact(
                    self.base.particles[pair[0]],
                    self.base.particles[pair[1]],
                ) is None:
                    continue
                seen.add(pair)
                pairs.append(pair)
        return pairs

    def active_wall_contacts(self):
        contacts = []
        for particle_index, particle in enumerate(self.base.particles):
            for contact_record in particle.get("bcs", []):
                wall_flag = contact_record.get("clflg", 0)
                if wall_flag == 0:
                    continue
                if self.base.wall_contact(particle, wall_flag, self.base.walls) is None:
                    continue
                contacts.append((particle_index, wall_flag))
        return contacts

    def cluster_phase_modes(self, cluster_pairs, cluster_walls):
        phases = set()
        modes = set()
        internal_modes = set()
        for source_index, target_index in cluster_pairs:
            state = self.base.source_geo_contact_state(
                self.base.particles[source_index],
                target_index,
            ) or self.base.source_geo_contact_state(
                self.base.particles[target_index],
                source_index,
            ) or {}
            phases.add(state.get("geo_phase", "unknown"))
            modes.add(state.get("neo_motion_mode", "unknown"))
            internal_modes.add(state.get("internal_momentum_phase", "unknown"))
        for wall_key in cluster_walls:
            state = self.base.wall_contact_state.get(wall_key, {})
            phases.add(state.get("geo_phase", "unknown"))
            modes.add(state.get("neo_motion_mode", "unknown"))
            internal_modes.add(state.get("internal_momentum_phase", "unknown"))
        return sorted(phases or {"none"}), sorted((internal_modes or modes) or {"none"})

    def cluster_current_momentum_energy(self, particle_indices):
        momentum_x = 0.0
        momentum_y = 0.0
        kinetic_energy = 0.0
        for index in particle_indices:
            particle = self.base.particles[index]
            momentum_x += particle["mass"] * particle["vx"]
            momentum_y += particle["mass"] * particle["vy"]
            kinetic_energy += 0.5 * particle["mass"] * (
                particle["vx"] * particle["vx"] + particle["vy"] * particle["vy"]
            )
        return momentum_x, momentum_y, kinetic_energy

    def cluster_start_momentum_energy(self, particle_indices):
        momentum_x = 0.0
        momentum_y = 0.0
        kinetic_energy = 0.0
        for index in particle_indices:
            particle = self.base.particles[index]
            vx = particle.get("starting_uncorrected_vx", particle["vx"])
            vy = particle.get("starting_uncorrected_vy", particle["vy"])
            momentum_x += particle["mass"] * vx
            momentum_y += particle["mass"] * vy
            kinetic_energy += 0.5 * particle["mass"] * (vx * vx + vy * vy)
        return momentum_x, momentum_y, kinetic_energy

    def cluster_internal_momentum_totals(self, cluster_pairs, cluster_walls):
        cimom_x = 0.0
        cimom_y = 0.0
        cimom = 0.0
        cistore = 0.0
        cirel = 0.0
        cirem = 0.0
        for source_index, target_index in cluster_pairs:
            source_particle = self.base.particles[source_index]
            target_particle = self.base.particles[target_index]
            contact = self.base.particle_contact(source_particle, target_particle)
            if contact is None:
                continue
            nx, ny, _overlap_area, _center_distance = contact
            state = self.base.source_geo_contact_state(
                source_particle,
                target_index,
            ) or self.base.source_geo_contact_state(
                target_particle,
                source_index,
            ) or {}
            contact_internal_momentum = self.canonical_contact_internal_normal_momentum(state)
            cimom_x += contact_internal_momentum * nx
            cimom_y += contact_internal_momentum * ny
            cimom += contact_internal_momentum
            cistore += state.get("neo_stored_internal_normal_momentum", 0.0)
            cirel += state.get("neo_rebound_released_normal_momentum", 0.0)
            cirem += state.get("neo_rebound_remaining_normal_momentum", 0.0)
        for wall_key in cluster_walls:
            particle_index, wall_flag = wall_key
            particle = self.base.particles[particle_index]
            contact = self.base.wall_contact(particle, wall_flag, self.base.walls)
            if contact is None:
                continue
            nx, ny, _overlap_area, _center_distance = contact
            state = self.base.wall_contact_state.get(wall_key, {})
            contact_internal_momentum = self.canonical_contact_internal_normal_momentum(state)
            cimom_x += contact_internal_momentum * nx
            cimom_y += contact_internal_momentum * ny
            cimom += contact_internal_momentum
            cistore += state.get("neo_stored_internal_normal_momentum", 0.0)
            cirel += state.get("neo_rebound_released_normal_momentum", 0.0)
            cirem += state.get("neo_rebound_remaining_normal_momentum", 0.0)
        return cimom_x, cimom_y, cimom, cistore, cirel, cirem

    def particle_contact_capture_lines(self, source_index, source_particle):
        lines = []
        for slot in range(source_particle.get("sltnum", 0)):
            contact_record = source_particle["ccs"][slot]
            if contact_record.get("clflg", 0) == 0:
                continue
            target_index = contact_record["pindex"]
            target_particle = self.base.particles[target_index]
            contact = self.base.particle_contact(source_particle, target_particle)
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
            contact_state = self.base.source_geo_contact_state(source_particle, target_index) or {}
            internal_contact_momentum = contact_state.get("internal_contact_momentum", 0.0)
            neo_internal_normal_momentum = self.canonical_contact_internal_normal_momentum(contact_state)
            neo_stored_internal_momentum = contact_state.get("neo_stored_internal_normal_momentum", 0.0)
            neo_released_internal_momentum = contact_state.get("neo_rebound_released_normal_momentum", 0.0)
            neo_remaining_internal_momentum = contact_state.get("neo_rebound_remaining_normal_momentum", 0.0)
            overlap_contact_momentum = contact_state.get("overlap_contact_momentum", 0.0)
            last_relative_normal_velocity = contact_state.get(
                "last_relative_normal_velocity",
                rel_normal_velocity,
            )
            zero_source = contact_state.get("geo_zero_velocity_source", "")
            motion_mode = contact_state.get("neo_motion_mode", "")
            internal_phase = contact_state.get("internal_momentum_phase", "")
            lock_state = contact_state.get("contact_lock_state", "free")
            blocked_relative = contact_state.get("locked_blocked_relative_normal_velocity", 0.0)
            phase = "closing" if rel_normal_velocity < 0.0 else "separating"
            lines.extend(
                [
                    "",
                    f"[particle P{source_index} Collision]",
                    f"c{source_index}->{target_index}",
                    f"reln={rel_normal_velocity:.8f}",
                    f"rmass={reduced_mass:.8f}",
                    f"relp={rel_normal_momentum:.8f}",
                    f"omom={overlap_contact_momentum:.8f}",
                    f"cinternal={internal_contact_momentum:.8f}",
                    f"nimom={neo_internal_normal_momentum:.8f}",
                    f"istore={neo_stored_internal_momentum:.8f}",
                    f"irel={neo_released_internal_momentum:.8f}",
                    f"irem={neo_remaining_internal_momentum:.8f}",
                    f"last_reln={last_relative_normal_velocity:.8f}",
                    f"imode={internal_phase}",
                    f"lock={lock_state}",
                    f"block_reln={blocked_relative:.8f}",
                    f"mode={motion_mode}",
                    f"zsrc={zero_source}",
                    f"phase={phase}",
                ]
            )
        return lines

    def wall_contact_capture_lines(self, source_index, source_particle):
        lines = []
        for contact_record in source_particle.get("bcs", []):
            wall_flag = contact_record.get("clflg", 0)
            if wall_flag == 0:
                continue

            contact = self.base.wall_contact(source_particle, wall_flag, self.base.walls)
            if contact is None:
                continue

            nx, ny, overlap_area, center_distance = contact
            normal_velocity = source_particle["vx"] * nx + source_particle["vy"] * ny
            wall_key = (source_index, wall_flag)
            contact_state = self.base.wall_contact_state.get(wall_key, {})
            overlap_contact_momentum = contact_state.get("overlap_contact_momentum", 0.0)
            neo_stored_internal_momentum = contact_state.get("neo_stored_internal_normal_momentum", 0.0)
            neo_released_internal_momentum = contact_state.get("neo_rebound_released_normal_momentum", 0.0)
            neo_remaining_internal_momentum = contact_state.get("neo_rebound_remaining_normal_momentum", 0.0)
            last_normal_velocity = contact_state.get("last_relative_normal_velocity", normal_velocity)
            zero_source = contact_state.get("geo_zero_velocity_source", "")
            motion_mode = contact_state.get("neo_motion_mode", "")
            internal_phase = contact_state.get("internal_momentum_phase", "")
            lock_state = contact_state.get("contact_lock_state", "free")
            blocked_normal = contact_state.get("locked_blocked_normal_velocity", 0.0)
            phase = contact_state.get(
                "geo_phase",
                "closing" if normal_velocity > 0.0 else "separating",
            )
            lines.extend(
                [
                    "",
                    f"[particle P{source_index} WallCollision]",
                    f"wall={self.wall_name(wall_flag)}",
                    f"vn={normal_velocity:.8f}",
                    f"p={source_particle['mass'] * abs(normal_velocity):.8f}",
                    f"omom={overlap_contact_momentum:.8f}",
                    f"istore={neo_stored_internal_momentum:.8f}",
                    f"irel={neo_released_internal_momentum:.8f}",
                    f"irem={neo_remaining_internal_momentum:.8f}",
                    f"last_vn={last_normal_velocity:.8f}",
                    f"imode={internal_phase}",
                    f"lock={lock_state}",
                    f"block_vn={blocked_normal:.8f}",
                    f"mode={motion_mode}",
                    f"zsrc={zero_source}",
                    f"area={overlap_area:.8f}",
                    f"center_distance={center_distance:.8f}",
                    f"phase={phase}",
                ]
            )
        return lines

    @staticmethod
    def wall_name(wall_flag):
        return {
            1: "left",
            2: "right",
            3: "bottom",
            4: "top",
        }.get(wall_flag, f"unknown{wall_flag}")

    def draw_report(self):
        x = 12
        y = 12
        summary_lines = self.momentum_balance_rows()
        fps_line = f"frame={self.frame_number} fps={self.current_fps:.1f}"
        surface = self.report_font.render(fps_line, True, self.center_dot_color)
        self.screen.blit(surface, (x, y))
        y += 18
        for line in summary_lines:
            surface = self.report_font.render(line, True, self.center_dot_color)
            self.screen.blit(surface, (x, y))
            y += 18
        y += 6
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
                line = (
                    f"p{index} px={momentum_x:.8f} py={momentum_y:.8f} "
                    f"|p|={particle_momentum:.8f} "
                    f"start={starting_momentum:.8f} "
                    f"dpx={momentum_delta_x:.8f} dpy={momentum_delta_y:.8f} "
                    f"v=({particle['vx']:.8f},{particle['vy']:.8f}) "
                    f"v0=({starting_uncorrected_vx:.8f},{starting_uncorrected_vy:.8f})"
                )
                contact_diagnostics = self.particle_contact_diagnostics(index, particle)
                if contact_diagnostics:
                    line = f"{line} {' '.join(contact_diagnostics)}"
                surface = self.report_font.render(line, True, self.center_dot_color)
                self.screen.blit(surface, (x, y))
                y += 18

        for line in self.guardrail_errors():
            surface = self.report_font.render(line, True, self.error_text_color)
            self.screen.blit(surface, (x, y))
            y += 18

        should_auto_capture = (
            self.frame_number in self.rpt_frames
            and self.frame_number not in self.captured_report_frames
        )
        if self.print_report_requested or should_auto_capture:
            self.write_report_capture()
            self.captured_report_frames.add(self.frame_number)
            self.print_report_requested = False

    def write_report_capture(self):
        self.report_capture_dir.mkdir(parents=True, exist_ok=True)
        report_file = self.report_capture_dir / f"Cap{self.frame_number:06d}.rpt"
        with report_file.open("w", encoding="utf-8") as outfile:
            outfile.write("[summary]\n")
            outfile.write(f"frame={self.frame_number} fps={self.current_fps:.1f}\n")
            outfile.write("\n[momentum_balance]\n")
            for line in self.momentum_balance_rows():
                outfile.write(f"{line}\n")
            outfile.write("\n[momentum_diagnostics]\n")
            for key, value in self.momentum_diagnostic_values().items():
                if key.endswith("_contacts"):
                    outfile.write(f"{key}={int(value)}\n")
                else:
                    outfile.write(f"{key}={value:.12f}\n")
            guardrail_errors = self.guardrail_errors()
            if guardrail_errors:
                outfile.write("\n[guardrail_errors]\n")
                for line in guardrail_errors:
                    outfile.write(f"{line}\n")
            for line in self.cluster_capture_report_lines():
                outfile.write(f"{line}\n")
            outfile.write("\n[particles]\n")
            for line in self.compact_particle_capture_report_lines():
                outfile.write(f"{line}\n")
        print(f"Wrote report capture: {report_file}")
        snapshot_path = self.write_contact_snapshot_if_configured()
        if snapshot_path is not None:
            particle_data_path = self.write_particle_data_snapshot(snapshot_path)
            with report_file.open("a", encoding="utf-8") as outfile:
                outfile.write("\n[contact_snapshot]\n")
                outfile.write(f"path={snapshot_path}\n")
                outfile.write(f"particle_data_path={particle_data_path}\n")

    def run(self, particle_data, run_configuration=None):
        if not self.configure(particle_data, run_configuration):
            pygame.quit()
            return
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
            if self.guardrail_errors():
                self.paused = True
            if not self.paused:
                sub_dt = self.base.dt / self.base.substeps
                for _ in range(self.base.substeps):
                    self.base.do_substep(sub_dt)
                self.frame_number += 1
                if self.end_frame is not None and self.frame_number > self.end_frame:
                    running = False
            self.clock.tick(self.frame_rate)

        pygame.quit()
