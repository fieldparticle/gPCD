import math

from base.Dynamics import Dynamics
from base.Report import Report


class Base:
    """Minimal particle motion model.

    This clean step has motion, contact detection, and minimal Mom-style
    overlap momentum dynamics. It has no bonding, tracing, or exports.
    """

    def __init__(self):
        self.POSITION_BUFFER_A = 0
        self.POSITION_BUFFER_B = 1
        self.particle_configs = []
        self.particles = []
        self.dt = 0.05
        self.substeps = 1
        self.time = 0.0
        self.walls = None
        self.max_contacts_per_particle = 12
        # Python wall-contact support. The current GLSL particle structure has
        # bcs[4], but wall behavior is not treated as shader-ready yet.
        self.max_boundary_contacts_per_particle = 4
        self.dynamics = Dynamics()
        self.report = Report()
        self.contact_state = {}

    def clear_particles(self):
        self.particle_configs = []
        self.particles = []

    def add_particle(self, vx, vy, mass, radius, location=None, x=None, y=None, **display):
        if location is None:
            if x is None or y is None:
                raise ValueError("Particle requires either location or x/y.")
            location = {"use": self.POSITION_BUFFER_A, "x1": float(x), "y1": float(y), "x2": float(x), "y2": float(y)}
        vx = float(vx)
        vy = float(vy)
        radius = float(radius)
        location = self.normalized_location(location)
        self.particle_configs.append(
            {
                "vx": vx,
                "vy": vy,
                "mass": float(mass),
                "radius": radius,
                "starting_momentum_x": float(mass) * vx,
                "starting_momentum_y": float(mass) * vy,
                "starting_momentum": float(mass) * math.hypot(vx, vy),
                "location": location,
                **self.glsl_field_mirrors(location, vx, vy, float(mass), radius),
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
        self.contact_state = {}
        self.report.clear()
        for config in self.particle_configs:
            particle = dict(config)
            particle["location"] = dict(particle["location"])
            particle["PosLocA"] = list(particle["PosLocA"])
            particle["PosLocB"] = list(particle["PosLocB"])
            particle["VelRad"] = list(particle["VelRad"])
            particle["Data"] = list(particle["Data"])
            particle["parms"] = list(particle["parms"])
            if "ccs" in particle:
                particle["ccs"] = [dict(contact) for contact in particle["ccs"]]
            if "bcs" in particle:
                particle["bcs"] = [dict(contact) for contact in particle["bcs"]]
            particle["state_flg"] = int(particle.get("state_flg", self.dynamics.STATE_ACTIVE))
            self.particles.append(particle)
        self.detect_contacts()
        self.update_contact_state()
        self.dynamics.process_collisions(self.particles, self.walls)
        self.dynamics.resolve_starting_collisions(self.particles)
        self.record_step_report()

    def step(self, dt):
        self.dynamics.begin_step(self.particles, dt, self.set_location)
        self.detect_contacts()
        self.update_contact_state()
        self.dynamics.process_collisions(self.particles, self.walls)
        self.dynamics.apply_overlap_momentum(self.particles)
        self.move(dt)
        self.dynamics.end_step(self.particles, self.set_location)
        self.time += dt
        self.record_step_report()

    def do_substep(self, sub_dt):
        self.step(sub_dt)

    def detect_contacts(self):
        # Rebuild contact storage from scratch each step. Each particle owns a
        # fixed-size list so later response code can read predictable slots.
        for particle in self.particles:
            particle["ccs"] = [self.empty_particle_contact() for _ in range(self.max_contacts_per_particle)]
            particle["bcs"] = [self.empty_boundary_contact() for _ in range(self.max_boundary_contacts_per_particle)]
            particle["sltnum"] = 0
            particle["ColFlg"] = 0
            particle["contact_count"] = 0
            particle["wall_contact_count"] = 0
            particle["contact_overflow"] = False

        # Each particle owns its own contact storage. This pass writes only to
        # particle_i, which keeps the loop parallel-friendly when each particle
        # is processed by one worker.
        for i in range(len(self.particles)):
            particle_i = self.particles[i]
            if not self.dynamics.is_active_particle(particle_i):
                continue
            for j in range(len(self.particles)):
                if i == j:
                    continue
                particle_j = self.particles[j]
                if not self.dynamics.is_active_particle(particle_j):
                    continue
                if self.dynamics.particle_contact(particle_i, particle_j) is not None:
                    self.add_particle_contact(i, j)
            self.detect_wall_contacts(i, particle_i)

    def detect_wall_contacts(self, particle_index, particle):
        if self.walls is None:
            return

        x, y = self.current_location(particle)
        radius = particle["radius"]
        walls = self.walls
        flow_type = self.dynamics.flow_type

        if flow_type not in ("pipe_reservoir_entry", "reservoir_release", "open_escape") and x - radius < walls["start_x"]:
            self.add_wall_contact(particle_index, "left")
        if flow_type not in ("pipe_reservoir_entry", "reservoir_release", "open_escape") and x + radius > walls["end_x"]:
            self.add_wall_contact(particle_index, "right")
        if y - radius < walls["start_y"]:
            self.add_wall_contact(particle_index, "bottom")
        if y + radius > walls["end_y"]:
            self.add_wall_contact(particle_index, "top")

    def add_particle_contact(self, particle_index, target_index):
        particle = self.particles[particle_index]
        slot = particle["sltnum"]
        if slot >= self.max_contacts_per_particle:
            particle["contact_overflow"] = True
            return

        particle["ccs"][slot] = {
            "pindex": target_index,
            "clflg": 1,
        }
        particle["sltnum"] = slot + 1
        particle["contact_count"] = particle["sltnum"]
        particle["ColFlg"] = 1

    def add_wall_contact(self, particle_index, wall_name):
        particle = self.particles[particle_index]
        wall_slot = self.wall_slot(wall_name)
        if wall_slot >= self.max_boundary_contacts_per_particle:
            particle["contact_overflow"] = True
            return

        particle["bcs"][wall_slot] = {
            "clflg": self.wall_flag(wall_name),
        }
        particle["wall_contact_count"] = self.boundary_contact_count(particle)
        particle["contact_count"] = particle.get("sltnum", 0) + particle["wall_contact_count"]

    def update_contact_state(self):
        active_pairs = set()
        for source_index, source_particle in enumerate(self.particles):
            for slot in range(source_particle.get("sltnum", 0)):
                contact_record = source_particle["ccs"][slot]
                if contact_record.get("clflg", 0) == 0:
                    continue

                target_index = contact_record["pindex"]
                pair_key = tuple(sorted((source_index, target_index)))
                if pair_key in active_pairs:
                    continue

                target_particle = self.particles[target_index]
                contact = self.dynamics.particle_contact(source_particle, target_particle)
                if contact is None:
                    continue

                nx, ny, overlap_area, center_distance = contact
                rel_vx = target_particle["vx"] - source_particle["vx"]
                rel_vy = target_particle["vy"] - source_particle["vy"]
                rel_normal_velocity = rel_vx * nx + rel_vy * ny
                reduced_mass = (
                    source_particle["mass"] * target_particle["mass"]
                ) / (source_particle["mass"] + target_particle["mass"])
                rel_normal_momentum = reduced_mass * abs(rel_normal_velocity)
                overlap_contact_momentum = self.dynamics.overlap_momentum(
                    overlap_area,
                    center_distance,
                    source_particle,
                )
                state = self.contact_state.setdefault(
                    pair_key,
                    {
                        "internal_contact_momentum": 0.0,
                        "last_relative_normal_velocity": rel_normal_velocity,
                    },
                )
                if rel_normal_velocity < 0.0:
                    state["internal_contact_momentum"] += overlap_contact_momentum
                else:
                    state["internal_contact_momentum"] = max(
                        0.0,
                        state["internal_contact_momentum"] - overlap_contact_momentum,
                    )
                state["relative_normal_momentum"] = rel_normal_momentum
                state["overlap_contact_momentum"] = overlap_contact_momentum
                state["last_relative_normal_velocity"] = rel_normal_velocity
                active_pairs.add(pair_key)

    @staticmethod
    def empty_particle_contact():
        return {"pindex": 0, "clflg": 0}

    @staticmethod
    def empty_boundary_contact():
        return {"clflg": 0}

    @staticmethod
    def wall_slot(wall_name):
        return {
            "left": 0,
            "right": 1,
            "bottom": 2,
            "top": 3,
        }[wall_name]

    @staticmethod
    def wall_flag(wall_name):
        return {
            "left": 1,
            "right": 2,
            "bottom": 3,
            "top": 4,
        }[wall_name]

    @staticmethod
    def boundary_contact_count(particle):
        return sum(1 for contact in particle.get("bcs", []) if contact.get("clflg", 0) != 0)

    def current_location(self, particle):
        location = particle["location"]
        if int(location["use"]) == self.POSITION_BUFFER_A:
            return location["x1"], location["y1"]
        return location["x2"], location["y2"]

    def set_next_location(self, particle, x, y):
        location = particle["location"]
        if int(location["use"]) == self.POSITION_BUFFER_A:
            location["x2"] = float(x)
            location["y2"] = float(y)
            particle["PosLocB"][0] = float(x)
            particle["PosLocB"][1] = float(y)
        else:
            location["x1"] = float(x)
            location["y1"] = float(y)
            particle["PosLocA"][0] = float(x)
            particle["PosLocA"][1] = float(y)

    def set_location(self, particle, x, y, activate=True):
        location = particle["location"]
        location["x1"] = float(x)
        location["y1"] = float(y)
        location["x2"] = float(x)
        location["y2"] = float(y)
        location["use"] = self.POSITION_BUFFER_A
        particle["PosLocA"][0] = float(x)
        particle["PosLocA"][1] = float(y)
        particle["PosLocA"][3] = 0.0 if activate else 1.0
        particle["PosLocB"][0] = float(x)
        particle["PosLocB"][1] = float(y)
        particle["PosLocB"][3] = 1.0

    def move(self, dt):
        for particle in self.particles:
            if not self.dynamics.is_active_particle(particle):
                continue
            x, y = self.current_location(particle)
            self.set_next_location(
                particle,
                x + particle["vx"] * dt,
                y + particle["vy"] * dt,
            )
            location = particle["location"]
            location["use"] = (
                self.POSITION_BUFFER_B
                if int(location["use"]) == self.POSITION_BUFFER_A
                else self.POSITION_BUFFER_A
            )
            self.sync_position_active_flags(particle)

    def normalized_location(self, location):
        location = dict(location)
        use = int(location["use"])
        if use not in (self.POSITION_BUFFER_A, self.POSITION_BUFFER_B):
            raise ValueError(f"Unknown position buffer: {location['use']!r}")
        location["use"] = use
        return location

    @staticmethod
    def glsl_field_mirrors(location, vx, vy, mass, radius):
        use = int(location["use"])
        return {
            "PosLocA": [
                float(location["x1"]),
                float(location["y1"]),
                0.0,
                0.0 if use == 0 else 1.0,
            ],
            "PosLocB": [
                float(location["x2"]),
                float(location["y2"]),
                0.0,
                0.0 if use == 1 else 1.0,
            ],
            "VelRad": [
                float(vx),
                float(vy),
                0.0,
                math.atan2(float(vy), float(vx)) if vx != 0.0 or vy != 0.0 else 0.0,
            ],
            "Data": [
                float(radius),
                0.0,
                0.0,
                0.0,
            ],
            "parms": [
                float(mass),
                0.0,
                0.0,
                0.0,
            ],
        }

    @staticmethod
    def sync_position_active_flags(particle):
        if int(particle["location"]["use"]) == 0:
            particle["PosLocA"][3] = 0.0
            particle["PosLocB"][3] = 1.0
        else:
            particle["PosLocA"][3] = 1.0
            particle["PosLocB"][3] = 0.0

    def record_step_report(self):
        for index, particle in enumerate(self.particles):
            x, y = self.current_location(particle)
            self.report.record_particle(
                index,
                {
                    "time": self.time,
                    "mass": particle["mass"],
                    "radius": particle["radius"],
                    "PosLocA": list(particle["PosLocA"]),
                    "PosLocB": list(particle["PosLocB"]),
                    "VelRad": list(particle["VelRad"]),
                    "Data": list(particle["Data"]),
                    "parms": list(particle["parms"]),
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
                    "wall_contact_count": particle.get("wall_contact_count", 0),
                    "sltnum": particle.get("sltnum", 0),
                    "ColFlg": particle.get("ColFlg", 0),
                    "ccs": [dict(contact) for contact in particle.get("ccs", [])],
                    "bcs": [dict(contact) for contact in particle.get("bcs", [])],
                    "contact_overflow": particle.get("contact_overflow", False),
                    "state_flg": particle.get("state_flg", self.dynamics.STATE_ACTIVE),
                    "overlap_momentum_x": particle.get("overlap_momentum_x", 0.0),
                    "overlap_momentum_y": particle.get("overlap_momentum_y", 0.0),
                    "overlap_momentum": particle.get("overlap_momentum", 0.0),
                    "internal_momentum_x": particle.get("internal_momentum_x", 0.0),
                    "internal_momentum_y": particle.get("internal_momentum_y", 0.0),
                    "internal_momentum": particle.get("internal_momentum", 0.0),
                    "momentum_delta_x": particle.get("momentum_delta_x", 0.0),
                    "momentum_delta_y": particle.get("momentum_delta_y", 0.0),
                    "momentum_delta": particle.get("momentum_delta", 0.0),
                },
            )
