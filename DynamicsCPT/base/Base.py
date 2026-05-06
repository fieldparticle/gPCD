from base.Dynamics import Dynamics
from base.Report import Report


class Base:
    """Minimal particle motion model.

    This clean step has motion, contact detection, and minimal Mom-style
    overlap momentum dynamics. It has no bonding, tracing, or exports.
    """

    def __init__(self):
        self.particle_configs = []
        self.particles = []
        self.contact_particles = []
        self.dt = 0.05
        self.substeps = 1
        self.time = 0.0
        self.walls = None
        self.max_contacts_per_particle = 8
        self.dynamics = Dynamics()
        self.report = Report()

    def clear_particles(self):
        self.particle_configs = []
        self.particles = []
        self.contact_particles = []

    def add_particle(self, vx, vy, mass, radius, location=None, x=None, y=None, **display):
        if location is None:
            if x is None or y is None:
                raise ValueError("Particle requires either location or x/y.")
            location = {"use": 1, "x1": float(x), "y1": float(y), "x2": float(x), "y2": float(y)}
        self.particle_configs.append(
            {
                "vx": float(vx),
                "vy": float(vy),
                "mass": float(mass),
                "radius": float(radius),
                "location": dict(location),
                **display,
            }
        )

    def set_walls(self, start_x, end_x, start_y, end_y):
        self.walls = {
            "start_x": float(start_x),
            "end_x": float(end_x),
            "start_y": float(start_y),
            "end_y": float(end_y),
        }

    def clear_walls(self):
        self.walls = None

    def reset(self):
        self.time = 0.0
        self.particles = []
        self.contact_particles = []
        self.report.clear()
        for config in self.particle_configs:
            particle = dict(config)
            particle["location"] = dict(particle["location"])
            if "contacts" in particle:
                particle["contacts"] = list(particle["contacts"])
            self.particles.append(particle)
        self.detect_contacts()
        self.dynamics.process_collisions(self.particles, self.contact_particles)
        self.record_step_report()

    def step(self, dt):
        for particle in self.particles:
            x, y = self.current_location(particle)
            self.set_next_location(
                particle,
                x + particle["vx"] * dt,
                y + particle["vy"] * dt,
            )
        self.move()
        self.time += dt
        self.detect_contacts()
        self.dynamics.process_collisions(self.particles, self.contact_particles)
        self.dynamics.apply_overlap_momentum(self.particles)
        self.record_step_report()

    def do_substep(self, sub_dt):
        self.step(sub_dt)

    def detect_contacts(self):
        # Rebuild contact storage from scratch each step. Each particle owns a
        # fixed-size list so later response code can read predictable slots.
        self.contact_particles = list(self.particles)
        for particle in self.particles:
            particle["contacts"] = [None] * self.max_contacts_per_particle
            particle["contact_count"] = 0
            particle["contact_overflow"] = False

        # Each particle owns its own contact storage. This pass writes only to
        # particle_i, which keeps the loop parallel-friendly when each particle
        # is processed by one worker.
        for i in range(len(self.particles)):
            particle_i = self.particles[i]
            for j in range(len(self.particles)):
                if i == j:
                    continue
                particle_j = self.particles[j]
                if self.dynamics.particle_contact(particle_i, particle_j) is not None:
                    self.add_contact(i, j)
            self.detect_wall_contacts(i, particle_i)

    def detect_wall_contacts(self, particle_index, particle):
        if self.walls is None:
            return

        x, y = self.current_location(particle)
        radius = particle["radius"]
        walls = self.walls

        if x - radius < walls["start_x"]:
            self.add_wall_ghost_contact(particle_index, particle, 2.0 * walls["start_x"] - x, y, "left")
        if x + radius > walls["end_x"]:
            self.add_wall_ghost_contact(particle_index, particle, 2.0 * walls["end_x"] - x, y, "right")
        if y - radius < walls["start_y"]:
            self.add_wall_ghost_contact(particle_index, particle, x, 2.0 * walls["start_y"] - y, "bottom")
        if y + radius > walls["end_y"]:
            self.add_wall_ghost_contact(particle_index, particle, x, 2.0 * walls["end_y"] - y, "top")

    def add_wall_ghost_contact(self, particle_index, particle, ghost_x, ghost_y, wall_name):
        ghost_index = len(self.contact_particles)
        self.contact_particles.append(
            {
                "location": {
                    "use": 1,
                    "x1": float(ghost_x),
                    "y1": float(ghost_y),
                    "x2": float(ghost_x),
                    "y2": float(ghost_y),
                },
                "radius": particle["radius"],
                "mass": particle["mass"],
                "vx": 0.0,
                "vy": 0.0,
                "is_wall_ghost": True,
                "wall": wall_name,
            }
        )
        self.add_contact(particle_index, ghost_index)

    def add_contact(self, particle_index, other_index):
        particle = self.particles[particle_index]
        contact_count = particle["contact_count"]
        # Keep the fixed-length array stable. If more contacts exist than slots,
        # remember that overflow happened instead of resizing during detection.
        if contact_count >= self.max_contacts_per_particle:
            particle["contact_overflow"] = True
            return
        particle["contacts"][contact_count] = other_index
        particle["contact_count"] = contact_count + 1

    def current_location(self, particle):
        location = particle["location"]
        if int(location["use"]) == 1:
            return location["x1"], location["y1"]
        return location["x2"], location["y2"]

    def set_next_location(self, particle, x, y):
        location = particle["location"]
        if int(location["use"]) == 1:
            location["x2"] = float(x)
            location["y2"] = float(y)
        else:
            location["x1"] = float(x)
            location["y1"] = float(y)

    def move(self):
        for particle in self.particles:
            location = particle["location"]
            location["use"] = 2 if int(location["use"]) == 1 else 1

    def record_step_report(self):
        for index, particle in enumerate(self.particles):
            x, y = self.current_location(particle)
            self.report.record_particle(
                index,
                {
                    "time": self.time,
                    "mass": particle["mass"],
                    "radius": particle["radius"],
                    "x": x,
                    "y": y,
                    "vx": particle["vx"],
                    "vy": particle["vy"],
                    "px": particle["mass"] * particle["vx"],
                    "py": particle["mass"] * particle["vy"],
                    "ke": 0.5
                    * particle["mass"]
                    * (particle["vx"] * particle["vx"] + particle["vy"] * particle["vy"]),
                    "contact_count": particle.get("contact_count", 0),
                    "contacts": list(particle.get("contacts", [])),
                    "contact_overflow": particle.get("contact_overflow", False),
                    "overlap_momentum_x": particle.get("overlap_momentum_x", 0.0),
                    "overlap_momentum_y": particle.get("overlap_momentum_y", 0.0),
                    "overlap_momentum": particle.get("overlap_momentum", 0.0),
                    "internal_momentum_x": particle.get("internal_momentum_x", 0.0),
                    "internal_momentum_y": particle.get("internal_momentum_y", 0.0),
                    "internal_momentum": particle.get("internal_momentum", 0.0),
                },
            )
