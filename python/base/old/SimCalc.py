import random


class SimCalc:
    """Simulation-specific particle lifecycle and boundary processes.

    This is intentionally separate from the Neo collision dynamics. It handles
    flow/release/outlet/periodic simulation rules that are not raw collision
    calculations.
    """

    ESCAPE_MODE_RESERVOIR = 0
    ESCAPE_MODE_ESCAPED = 1
    ESCAPE_MODE_RETAINED = 2

    STATE_RESERVOIR = 0
    STATE_ACTIVE = 1
    STATE_ESCAPED = 2
    STATE_RETAINED = 3

    def __init__(self, base):
        self.base = base
        self.flow_type = "closed_wall"
        self.release_accumulator = 0.0
        self.released_count = 0
        self.escaped_count = 0
        self.recycled_count = 0
        self.particle_rate = 0.0
        self.inlet_velocity = 0.0
        self.inlet_x = 0.0
        self.outlet_x = 0.0
        self.pipe_y_min = 0.0
        self.pipe_y_max = 0.0
        self.reservoir_x = -999.0
        self.reservoir_y = -999.0
        self.escape_mode = self.ESCAPE_MODE_RESERVOIR

    def configure_flow(self, config):
        config = {} if config is None else config
        self.flow_type = str(config.get("flow_type", "closed_wall"))
        self.particle_rate = float(config.get("particle_rate", 0.0))
        self.inlet_velocity = float(config.get("inlet_velocity", 0.0))
        self.escape_mode = self.normalize_escape_mode(config.get("escape_mode", self.ESCAPE_MODE_RESERVOIR))

        wall_box = config.get("wall_box")
        if wall_box is not None and wall_box is not False:
            default_x_min, default_x_max, default_y_min, default_y_max = wall_box
        else:
            default_x_min = float(config.get("WallXMIN", 0.0))
            default_x_max = float(config.get("WallXMAX", 0.0))
            default_y_min = float(config.get("WallYMIN", 0.0))
            default_y_max = float(config.get("WallYMAX", 0.0))

        self.inlet_x = float(config.get("inlet_x", default_x_min))
        self.outlet_x = float(config.get("outlet_x", default_x_max))
        self.pipe_y_min = float(config.get("pipe_y_min", default_y_min))
        self.pipe_y_max = float(config.get("pipe_y_max", default_y_max))
        self.reservoir_x = float(config.get("reservoir_x", self.inlet_x - 100.0))
        self.reservoir_y = float(config.get("reservoir_y", self.pipe_y_min - 100.0))
        self.release_accumulator = 0.0
        self.released_count = 0
        self.escaped_count = 0
        self.recycled_count = 0

    def begin_step(self, particles, dt, set_location):
        if self.flow_type in ("pipe_reservoir_entry", "reservoir_release"):
            self.release_from_reservoir(particles, dt, set_location)

    def end_step(self, particles, set_location):
        if self.flow_type == "periodic":
            self.apply_periodic_boundary(particles, set_location)
        elif self.flow_type in ("pipe_reservoir_entry", "reservoir_release", "open_escape"):
            self.apply_outlet_boundary(particles, set_location)

    def release_from_reservoir(self, particles, dt, set_location):
        self.release_accumulator += self.particle_rate * dt
        release_count = int(self.release_accumulator)
        if release_count <= 0:
            return

        self.release_accumulator -= release_count
        for particle in particles:
            if release_count <= 0:
                break
            if not self.is_reservoir_particle(particle):
                continue
            self.activate_particle_at_inlet(particle, set_location)
            release_count -= 1

    def activate_particle_at_inlet(self, particle, set_location):
        radius = particle["radius"]
        y_min = self.pipe_y_min + radius
        y_max = self.pipe_y_max - radius
        if y_max < y_min:
            y_min = y_max = 0.5 * (self.pipe_y_min + self.pipe_y_max)

        x = self.inlet_x + radius
        y = random.uniform(y_min, y_max)
        particle["state_flg"] = self.STATE_ACTIVE
        particle["vx"] = self.inlet_velocity
        particle["vy"] = 0.0
        set_location(particle, x, y, activate=True)
        self.base.sync_velocity_mirror(particle)
        self.released_count += 1

    def apply_outlet_boundary(self, particles, set_location):
        for particle in particles:
            if not self.is_active_particle(particle):
                continue
            x, _y = self.base.current_location(particle)
            if x - particle["radius"] <= self.outlet_x:
                continue
            if self.escape_mode == self.ESCAPE_MODE_ESCAPED:
                particle["state_flg"] = self.STATE_ESCAPED
                self.escaped_count += 1
            elif self.escape_mode == self.ESCAPE_MODE_RETAINED:
                particle["state_flg"] = self.STATE_RETAINED
            else:
                particle["state_flg"] = self.STATE_RESERVOIR
                self.recycled_count += 1
            particle["vx"] = 0.0
            particle["vy"] = 0.0
            set_location(particle, self.reservoir_x, self.reservoir_y, activate=False)
            self.base.sync_velocity_mirror(particle)

    def apply_periodic_boundary(self, particles, set_location):
        width = self.outlet_x - self.inlet_x
        if width <= 0.0:
            return
        for particle in particles:
            if not self.is_active_particle(particle):
                continue
            x, y = self.base.current_location(particle)
            radius = particle["radius"]
            if x - radius > self.outlet_x:
                set_location(particle, self.inlet_x + radius, y, activate=True)
            elif x + radius < self.inlet_x:
                set_location(particle, self.outlet_x - radius, y, activate=True)

    def is_active_particle(self, particle):
        return int(particle.get("state_flg", self.STATE_ACTIVE)) == self.STATE_ACTIVE

    def is_reservoir_particle(self, particle):
        return int(particle.get("state_flg", self.STATE_ACTIVE)) == self.STATE_RESERVOIR

    @classmethod
    def normalize_escape_mode(cls, escape_mode):
        if isinstance(escape_mode, str):
            return {
                "reservoir": cls.ESCAPE_MODE_RESERVOIR,
                "recycle": cls.ESCAPE_MODE_RESERVOIR,
                "escaped": cls.ESCAPE_MODE_ESCAPED,
                "escape": cls.ESCAPE_MODE_ESCAPED,
                "retained": cls.ESCAPE_MODE_RETAINED,
                "retain": cls.ESCAPE_MODE_RETAINED,
            }.get(escape_mode.lower(), cls.ESCAPE_MODE_RESERVOIR)
        return int(escape_mode)
