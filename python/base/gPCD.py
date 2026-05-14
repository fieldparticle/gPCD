from logging import config

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
        self.collision_normal_color = (255, 245, 140)
        self.overlap_alpha = 185
        self.start_overlap_momentum = 0.0
        self.start_kinetic_energy = 0.0
        self.paused = False
        self.frame_number = 0
        self.current_fps = 0.0
        self.frame_rate = 60

    def configure(self, particle_data, run_configuration):
        self.config = {} if run_configuration is None else dict(run_configuration)
        self.base = Base()
        self.base.dt = float(self.config.get("dt", self.base.dt))
        self.base.substeps = int(self.config.get("substeps", self.base.substeps))
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

        self.screen_width, self.screen_height = self.config.get(
            "window_size",
            (self.screen_width, self.screen_height),
        )
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

        self.base.clear_particles()
        for _index, particle in sorted(particle_data.items()):
            self.base.add_particle(**particle)
        self.base.reset()
        self.start_overlap_momentum = self.total_overlap_momentum()
        self.start_kinetic_energy = self.total_kinetic_energy()
        self.frame_number = 0
        self.current_fps = 0.0
        self.paused = False

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

    def total_overlap_momentum(self):
        return sum(particle.get("overlap_momentum", 0.0) for particle in self.base.particles)

    def total_kinetic_energy(self):
        return sum(
            0.5 * particle["mass"] * (particle["vx"] * particle["vx"] + particle["vy"] * particle["vy"])
            for particle in self.base.particles
            if self.base.dynamics.is_active_particle(particle)
        )

    def draw_report(self):
        x = 12
        y = 12
        current_overlap_momentum = self.total_overlap_momentum()
        current_kinetic_energy = self.total_kinetic_energy()
        summary_lines = (
            f"overlap_momentum start={self.start_overlap_momentum:.8f} end={current_overlap_momentum:.8f}",
            f"ke               start={self.start_kinetic_energy:.8f} end={current_kinetic_energy:.8f}",
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
        if(self.config.get("plot_report") == True):
                
            for index, particle in enumerate(self.base.particles):
                overlap_momentum = particle.get("overlap_momentum", 0.0)
                internal_momentum = particle.get("internal_momentum", 0.0)
                kinetic_energy = 0.5 * particle["mass"] * (
                    particle["vx"] * particle["vx"] + particle["vy"] * particle["vy"]
                )
                line = (
                    f"p{index} overlap_momentum={overlap_momentum:.8f} "
                    f"internal_momentum={internal_momentum:.8f} "
                    f"ke={kinetic_energy:.8f}"
                )
                surface = self.report_font.render(line, True, self.center_dot_color)
                self.screen.blit(surface, (x, y))
                y += 18

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
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    self.set_zoom(self.zoom * 1.2)
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_KP_MINUS):
                    self.set_zoom(self.zoom / 1.2)

            if not self.paused:
                sub_dt = self.base.dt / self.base.substeps
                for _ in range(self.base.substeps):
                    self.base.do_substep(sub_dt)
            self.current_fps = self.clock.get_fps()
            self.frame_number += 1
            self.draw()
            self.clock.tick(self.frame_rate)

        pygame.quit()
