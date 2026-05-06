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

    def configure(self, particle_data, run_configuration):
        config = {} if run_configuration is None else dict(run_configuration)
        self.base = Base()
        self.base.dt = float(config.get("dt", self.base.dt))
        self.base.substeps = int(config.get("substeps", self.base.substeps))
        self.base.max_contacts_per_particle = int(
            config.get("max_contacts_per_particle", self.base.max_contacts_per_particle)
        )
        self.base.dynamics.momentum_per_area = float(
            config.get("momentum_per_area", self.base.dynamics.momentum_per_area)
        )
        self.base.dynamics.inverse_square_softening = float(
            config.get("inverse_square_softening", self.base.dynamics.inverse_square_softening)
        )

        wall_box = config.get("wall_box")
        if wall_box is not None and wall_box is not False:
            self.base.set_walls(*wall_box)
            self.world_box = tuple(float(value) for value in wall_box)
        elif config.get("world_box") is not None:
            self.world_box = tuple(float(value) for value in config["world_box"])
        self.set_zoom(config.get("zoom", 1.0))

        self.screen_width, self.screen_height = config.get(
            "window_size",
            (self.screen_width, self.screen_height),
        )
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

        self.base.clear_particles()
        for _index, particle in sorted(particle_data.items()):
            self.base.add_particle(**particle)
        self.base.reset()

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

        for index, particle in enumerate(self.base.particles):
            x, y = self.base.current_location(particle)
            center = (self.to_screen_x(x), self.to_screen_y(y))
            radius = self.radius_to_pixels(particle["radius"])
            fill = particle.get("fill", self.default_fill)
            edge = particle.get("edge", self.default_edge)
            pygame.draw.circle(self.screen, fill, center, radius)
            pygame.draw.circle(self.screen, edge, center, radius, 2)
            pygame.draw.circle(self.screen, self.center_dot_color, center, 4)

            label = self.label_font.render(str(index), True, self.center_dot_color)
            label_rect = label.get_rect(center=(center[0], center[1] - radius - 14))
            self.screen.blit(label, label_rect)

        self.draw_report()

        pygame.display.flip()

    def draw_report(self):
        x = 12
        y = 12
        for index, particle in enumerate(self.base.particles):
            overlap_momentum = particle.get("overlap_momentum", 0.0)
            internal_momentum = particle.get("internal_momentum", 0.0)
            kinetic_energy = 0.5 * particle["mass"] * (
                particle["vx"] * particle["vx"] + particle["vy"] * particle["vy"]
            )
            line = (
                f"p{index} overlap_momentum={overlap_momentum:.3e} "
                f"internal_momentum={internal_momentum:.3e} "
                f"ke={kinetic_energy:.3e}"
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
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    self.set_zoom(self.zoom * 1.2)
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_KP_MINUS):
                    self.set_zoom(self.zoom / 1.2)

            sub_dt = self.base.dt / self.base.substeps
            for _ in range(self.base.substeps):
                self.base.do_substep(sub_dt)
            self.draw()

        pygame.quit()
