import math
import random

from base.NeoDynamics import NeoDynamics
from base.Report import Report


class Base:
    """Minimal particle motion model.

    This clean step has motion, contact detection, and minimal Mom-style
    overlap momentum tracking. It has no bonding, tracing, or exports.
    """

    ESCAPE_MODE_RESERVOIR = 0
    ESCAPE_MODE_ESCAPED = 1
    ESCAPE_MODE_RETAINED = 2

    STATE_RESERVOIR = 0
    STATE_ACTIVE = 1
    STATE_ESCAPED = 2
    STATE_RETAINED = 3

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
        self.zero_velocity_overlap_area = None
        self.zero_velocity_overlap_fraction = None
        self.zero_velocity_overlap_tolerance = 0.01
        self.geo_rebound_min_fraction = 0.02
        self.collision_stiffness_q = 1.0
        self.momentum_per_area = 0.001
        self.inverse_square_softening = 1.0
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
        self.report = Report()
        self.wall_contact_state = {}

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
        self.sync_velocity_mirror(particle)
        self.released_count += 1

    def apply_outlet_boundary(self, particles, set_location):
        for particle in particles:
            if not self.is_active_particle(particle):
                continue
            x, _y = self.current_location(particle)
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
            self.sync_velocity_mirror(particle)

    def apply_periodic_boundary(self, particles, set_location):
        width = self.outlet_x - self.inlet_x
        if width <= 0.0:
            return
        for particle in particles:
            if not self.is_active_particle(particle):
                continue
            x, y = self.current_location(particle)
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
        self.wall_contact_state = {}
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
            particle["gcs"] = self.empty_geo_contact_states()
            particle["state_flg"] = int(particle.get("state_flg", self.STATE_ACTIVE))
            self.particles.append(particle)
        self.detect_contacts()
        self.update_contact_state()
        self.update_wall_contact_state()
        self.initialize_geo_starting_overlap_zero_state()
        self.initialize_geo_starting_wall_overlap_zero_state()
        self.apply_geo_starting_overlap()
        self.apply_geo_starting_wall_overlap()
        self.detect_contacts()
        self.update_contact_state()
        self.update_wall_contact_state()
        self.initialize_starting_diagnostics()
        self.record_step_report()

    def apply_geo_starting_overlap(self):
        neo_model = self.new_neo_model()
        neo_model.momentum_per_area = self.momentum_per_area
        neo_model.inverse_square_softening = self.inverse_square_softening

        for particle_config in self.particle_configs:
            particle = dict(particle_config)
            particle["location"] = dict(particle["location"])
            neo_model.add_particle(**particle)
        neo_model.reset()

        for index, neo_particle in enumerate(neo_model.particles):
            if index >= len(self.particles):
                continue
            if not self.particle_has_starting_overlap(index):
                continue

            particle = self.particles[index]
            particle["vx"] = neo_particle["velocity_at_current_overlap_rebound_x"]
            particle["vy"] = neo_particle["velocity_at_current_overlap_rebound_y"]
            self.sync_velocity_mirror(particle)

    def apply_geo_starting_wall_overlap(self):
        predictions = self.geo_wall_velocity_predictions()
        if predictions:
            self.apply_geo_velocity_predictions(predictions)

    def initialize_geo_starting_overlap_zero_state(self):
        for source_index, source_particle in enumerate(self.particles):
            for state in source_particle.get("gcs", []):
                if not state.get("active", False):
                    continue
                target_index = state.get("target_index")
                if target_index is None:
                    continue
                report = self.geo_starting_overlap_source_report(source_index, target_index)
                if report is None:
                    continue
                state["geo_phase"] = "rebound"
                state["geo_zero_velocity_overlap_area"] = report["zero_velocity_overlap_area"]
                state["geo_zero_velocity_center_distance"] = report["zero_velocity_center_distance"]
                state["geo_zero_velocity_overlap_momentum"] = report["zero_velocity_overlap_momentum"]
                state["geo_zero_velocity_source"] = report["zero_velocity_solution_source"]
                state["geo_starting_overlap"] = True

    def initialize_geo_starting_wall_overlap_zero_state(self):
        for wall_key, state in self.wall_contact_state.items():
            particle_index, wall_flag = wall_key
            particle = self.particles[particle_index]
            contact = self.wall_contact(particle, wall_flag, self.walls)
            if contact is None:
                continue

            _nx, _ny, overlap_area, center_distance = contact
            zero_geometry = self.solved_wall_zero_velocity_geometry(particle, state)
            if zero_geometry["overlap_area"] + 1.0e-12 < overlap_area:
                zero_geometry = {
                    "overlap_area": overlap_area,
                    "center_distance": center_distance,
                    "solution_source": "promoted_to_current_overlap",
                }

            state["geo_phase"] = "rebound"
            state["geo_zero_velocity_overlap_area"] = zero_geometry["overlap_area"]
            state["geo_zero_velocity_center_distance"] = zero_geometry["center_distance"]
            state["geo_zero_velocity_source"] = zero_geometry["solution_source"]
            state["geo_starting_overlap"] = True

    def geo_starting_overlap_pair_report(self, pair_key):
        source_index, target_index = pair_key
        return self.geo_starting_overlap_source_report(source_index, target_index)

    def geo_starting_overlap_source_report(self, source_index, target_index):
        source_particle = self.particles[source_index]
        target_particle = self.particles[target_index]
        contact = self.particle_contact(source_particle, target_particle)
        if contact is None:
            return None

        source_x, source_y = self.current_location(source_particle)
        target_x, target_y = self.current_location(target_particle)
        neo_model = self.new_neo_model()
        neo_model.momentum_per_area = self.momentum_per_area
        neo_model.inverse_square_softening = self.inverse_square_softening
        neo_model.add_particle(
            source_particle["vx"],
            source_particle["vy"],
            source_particle["mass"],
            source_particle["radius"],
            x=source_x,
            y=source_y,
            momentum_per_area=source_particle.get("momentum_per_area"),
            inverse_square_softening=source_particle.get("inverse_square_softening"),
        )
        neo_model.add_particle(
            target_particle["vx"],
            target_particle["vy"],
            target_particle["mass"],
            target_particle["radius"],
            x=target_x,
            y=target_y,
            momentum_per_area=target_particle.get("momentum_per_area"),
            inverse_square_softening=target_particle.get("inverse_square_softening"),
        )
        neo_model.reset()
        return next(
            (
                contact_report
                for contact_report in neo_model.contact_reports
                if contact_report["source_index"] == 0 and contact_report["target_index"] == 1
            ),
            None,
        )

    def initialize_starting_diagnostics(self):
        for particle in self.particles:
            if not self.is_active_particle(particle):
                continue

            linear_momentum_x = particle["mass"] * particle["vx"]
            linear_momentum_y = particle["mass"] * particle["vy"]
            particle["starting_momentum_x"] = linear_momentum_x
            particle["starting_momentum_y"] = linear_momentum_y
            particle["starting_momentum"] = math.hypot(linear_momentum_x, linear_momentum_y)
            particle["starting_uncorrected_vx"] = particle["vx"]
            particle["starting_uncorrected_vy"] = particle["vy"]
            particle["starting_corrected_vx"] = particle["vx"]
            particle["starting_corrected_vy"] = particle["vy"]
            particle["starting_velocity_correction_x"] = 0.0
            particle["starting_velocity_correction_y"] = 0.0
            particle["starting_uncorrected_speed"] = math.hypot(particle["vx"], particle["vy"])
            particle["starting_corrected_speed"] = particle["starting_uncorrected_speed"]
            particle["internal_momentum_x"] = 0.0
            particle["internal_momentum_y"] = 0.0
            particle["internal_momentum"] = 0.0
            particle["momentum_delta_x"] = 0.0
            particle["momentum_delta_y"] = 0.0
            particle["momentum_delta"] = 0.0

    def particle_has_starting_overlap(self, particle_index):
        if particle_index >= len(self.particles):
            return False
        particle = self.particles[particle_index]
        return particle.get("sltnum", 0) > 0 or self.boundary_contact_count(particle) > 0

    def step(self, dt):
        self.current_step_dt = dt
        self.begin_step(self.particles, dt, self.set_location)
        self.detect_contacts()
        self.update_contact_state()
        self.update_wall_contact_state()
        self.apply_neo_model()
        self.move(dt)
        self.detect_contacts()
        self.update_wall_contact_state()
        self.clip_configured_zero_velocity_overlaps()
        self.clip_configured_zero_velocity_wall_overlaps()
        self.end_step(self.particles, self.set_location)
        self.time += dt
        self.record_step_report()

    def apply_neo_model(self):
        applied_predictions = False
        predictions = self.geo_velocity_predictions()
        if predictions is not None:
            self.apply_geo_velocity_predictions(predictions)
            applied_predictions = True
        wall_predictions = self.geo_wall_velocity_predictions()
        if wall_predictions is not None:
            self.apply_geo_velocity_predictions(wall_predictions)
            applied_predictions = True
        if applied_predictions:
            return
        for particle in self.particles:
            particle["momentum_delta_x"] = 0.0
            particle["momentum_delta_y"] = 0.0
            particle["momentum_delta"] = 0.0
            particle["internal_momentum_x"] = 0.0
            particle["internal_momentum_y"] = 0.0
            particle["internal_momentum"] = 0.0

    def apply_geo_velocity_predictions(self, predictions):
        for particle_index, velocity in predictions.items():
            particle = self.particles[particle_index]
            old_momentum_x = particle["mass"] * particle["vx"]
            old_momentum_y = particle["mass"] * particle["vy"]
            particle["vx"], particle["vy"] = velocity
            new_momentum_x = particle["mass"] * particle["vx"]
            new_momentum_y = particle["mass"] * particle["vy"]
            particle["momentum_delta_x"] = new_momentum_x - old_momentum_x
            particle["momentum_delta_y"] = new_momentum_y - old_momentum_y
            particle["momentum_delta"] = math.hypot(
                particle["momentum_delta_x"],
                particle["momentum_delta_y"],
            )
            particle["internal_momentum_x"] = 0.0
            particle["internal_momentum_y"] = 0.0
            particle["internal_momentum"] = 0.0
            self.sync_velocity_mirror(particle)
        self.clip_configured_zero_velocity_overlaps()
        self.clip_configured_zero_velocity_wall_overlaps()

    def has_configured_zero_velocity_overlap(self):
        return self.zero_velocity_overlap_area is not None or self.zero_velocity_overlap_fraction is not None

    def has_pair_zero_velocity_model(self):
        return True

    def new_neo_model(self):
        neo_model = NeoDynamics()
        neo_model.collision_stiffness_q = self.collision_stiffness_q
        return neo_model

    def clip_configured_zero_velocity_overlaps(self):
        processed_pairs = set()
        for source_index, source_particle in enumerate(self.particles):
            for state in source_particle.get("gcs", []):
                if not state.get("active", False):
                    continue
                target_index = state.get("target_index")
                if target_index is None:
                    continue
                pair_key = tuple(sorted((source_index, target_index)))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                if state.get("geo_phase") != "rebound":
                    continue

                pair_source_index, pair_target_index = pair_key
                pair_source_particle = self.particles[pair_source_index]
                pair_target_particle = self.particles[pair_target_index]
                zero_geometry = self.contact_state_zero_velocity_geometry(state)
                if zero_geometry is None:
                    zero_geometry = self.configured_zero_velocity_geometry(pair_source_particle, pair_target_particle)
                if zero_geometry is None:
                    continue

                contact = self.particle_contact(pair_source_particle, pair_target_particle)
                if contact is None:
                    continue

                nx, ny, overlap_area, center_distance = contact
                if overlap_area <= zero_geometry["overlap_area"]:
                    continue

                self.set_pair_center_distance(
                    pair_source_particle,
                    pair_target_particle,
                    nx,
                    ny,
                    zero_geometry["center_distance"],
                )
                state["geo_zero_velocity_clipped"] = True

    def clip_configured_zero_velocity_wall_overlaps(self):
        for wall_key, state in self.wall_contact_state.items():
            if state.get("geo_phase") != "rebound":
                continue

            particle_index, wall_flag = wall_key
            particle = self.particles[particle_index]
            zero_geometry = self.contact_state_zero_velocity_geometry(state)
            if zero_geometry is None:
                zero_geometry = self.configured_wall_zero_velocity_geometry(particle)
            if zero_geometry is None:
                continue

            contact = self.wall_contact(particle, wall_flag, self.walls)
            if contact is None:
                continue

            _nx, _ny, overlap_area, _center_distance = contact
            if overlap_area <= zero_geometry["overlap_area"]:
                continue

            self.set_wall_center_distance(particle, wall_flag, zero_geometry["center_distance"])
            state["geo_zero_velocity_clipped"] = True

    def set_wall_center_distance(self, particle, wall_flag, target_center_distance):
        if self.walls is None:
            return
        x, y = self.current_location(particle)
        distance_to_wall = 0.5 * max(0.0, target_center_distance)
        if wall_flag == 1:
            x = self.walls["start_x"] + distance_to_wall
        elif wall_flag == 2:
            x = self.walls["end_x"] - distance_to_wall
        elif wall_flag == 3:
            y = self.walls["start_y"] + distance_to_wall
        elif wall_flag == 4:
            y = self.walls["end_y"] - distance_to_wall
        self.set_location(particle, x, y)

    def set_pair_center_distance(self, source_particle, target_particle, nx, ny, target_distance):
        source_x, source_y = self.current_location(source_particle)
        target_x, target_y = self.current_location(target_particle)
        current_distance = math.hypot(target_x - source_x, target_y - source_y)
        correction = current_distance - target_distance
        if abs(correction) <= 1.0e-12:
            return

        source_mass = source_particle["mass"]
        target_mass = target_particle["mass"]
        total_mass = source_mass + target_mass
        if total_mass <= 0.0:
            source_fraction = target_fraction = 0.5
        else:
            source_fraction = target_mass / total_mass
            target_fraction = source_mass / total_mass

        source_new_x = source_x + correction * source_fraction * nx
        source_new_y = source_y + correction * source_fraction * ny
        target_new_x = target_x - correction * target_fraction * nx
        target_new_y = target_y - correction * target_fraction * ny
        self.set_location(source_particle, source_new_x, source_new_y)
        self.set_location(target_particle, target_new_x, target_new_y)

    def geo_velocity_predictions(self):
        active_contacts = []
        active_pairs = set()
        for source_index, source_particle in enumerate(self.particles):
            if not self.is_active_particle(source_particle):
                continue
            for slot in range(source_particle.get("sltnum", 0)):
                contact_record = source_particle["ccs"][slot]
                if contact_record.get("clflg", 0) == 0:
                    continue
                target_index = contact_record["pindex"]
                pair_key = tuple(sorted((source_index, target_index)))
                active_pairs.add(pair_key)
                contact_key = (source_index, target_index)
                if contact_key not in active_contacts:
                    active_contacts.append(contact_key)

        if not active_contacts:
            return None

        if len(active_pairs) != 1 and not self.has_pair_zero_velocity_model():
            return None

        combined_velocities = {}
        for source_index, target_index in active_contacts:
            prediction = self.geo_pair_prediction(source_index, target_index)
            if prediction is None:
                return None

            start_velocity = prediction["start_velocity"]
            predicted_velocity = prediction["predicted_velocity"]
            if source_index not in combined_velocities:
                combined_velocities[source_index] = [start_velocity[0], start_velocity[1]]
            combined_velocities[source_index][0] += predicted_velocity[0] - start_velocity[0]
            combined_velocities[source_index][1] += predicted_velocity[1] - start_velocity[1]

        return {
            particle_index: (velocity[0], velocity[1])
            for particle_index, velocity in combined_velocities.items()
        }

    def geo_wall_velocity_predictions(self):
        active_walls = []
        for particle_index, particle in enumerate(self.particles):
            if not self.is_active_particle(particle):
                continue
            for contact_record in particle.get("bcs", []):
                wall_flag = contact_record.get("clflg", 0)
                if wall_flag == 0:
                    continue
                wall_key = (particle_index, wall_flag)
                if wall_key not in active_walls:
                    active_walls.append(wall_key)

        if not active_walls:
            return None

        combined_velocities = {}
        for wall_key in active_walls:
            prediction = self.geo_wall_prediction(wall_key)
            if prediction is None:
                return None
            particle_index = wall_key[0]
            start_velocity = prediction["start_velocity"]
            predicted_velocity = prediction["predicted_velocity"]
            if particle_index not in combined_velocities:
                combined_velocities[particle_index] = [start_velocity[0], start_velocity[1]]
            combined_velocities[particle_index][0] += predicted_velocity[0] - start_velocity[0]
            combined_velocities[particle_index][1] += predicted_velocity[1] - start_velocity[1]

        return {
            particle_index: (velocity[0], velocity[1])
            for particle_index, velocity in combined_velocities.items()
        }

    def geo_wall_prediction(self, wall_key):
        particle_index, wall_flag = wall_key
        particle = self.particles[particle_index]
        contact = self.wall_contact(particle, wall_flag, self.walls)
        if contact is None:
            return None

        nx, ny, overlap_area, center_distance = contact
        normal_velocity = particle["vx"] * nx + particle["vy"] * ny
        phase = "compression" if normal_velocity > 0.0 else "rebound"
        state = self.wall_contact_state.get(wall_key, {})
        state_zero = self.contact_state_zero_velocity_geometry(state)
        configured_zero = None
        if state_zero is None:
            configured_zero = self.configured_wall_zero_velocity_geometry(particle)
        if configured_zero is not None:
            self.update_configured_geo_wall_phase(
                state,
                overlap_area=overlap_area,
                center_distance=center_distance,
                normal_velocity=normal_velocity,
                particle=particle,
                configured_zero=configured_zero,
            )
            phase = state.get("geo_phase", phase)
        elif state_zero is not None:
            phase = state.get("geo_phase", "rebound")
        elif state.get("geo_phase") != "rebound":
            return None

        start_vx, start_vy = state.get("first_contact_velocity", (particle["vx"], particle["vy"]))
        incoming_speed = start_vx * nx + start_vy * ny
        if incoming_speed <= 0.0:
            return None

        zero_area = (
            state_zero["overlap_area"]
            if state_zero is not None
            else (
                configured_zero["overlap_area"]
                if configured_zero is not None
                else state.get("geo_zero_velocity_overlap_area")
            )
        )
        if zero_area is None or zero_area <= 1.0e-12:
            return None

        compression_fraction = max(0.0, min(1.0, overlap_area / zero_area))
        compression_velocity_fraction = math.sqrt(max(0.0, 1.0 - compression_fraction))
        compression_progress = 1.0 - compression_velocity_fraction
        rebound_velocity_fraction = math.sqrt(max(0.0, 1.0 - compression_fraction))

        turn_vx = start_vx - incoming_speed * nx
        turn_vy = start_vy - incoming_speed * ny
        full_vx = start_vx - 2.0 * incoming_speed * nx
        full_vy = start_vy - 2.0 * incoming_speed * ny

        if phase == "compression":
            predicted_velocity = (
                start_vx + compression_progress * (turn_vx - start_vx),
                start_vy + compression_progress * (turn_vy - start_vy),
            )
        else:
            predicted_velocity = (
                turn_vx + rebound_velocity_fraction * (full_vx - turn_vx),
                turn_vy + rebound_velocity_fraction * (full_vy - turn_vy),
            )

        return {
            "start_velocity": (start_vx, start_vy),
            "predicted_velocity": predicted_velocity,
        }

    def geo_pair_prediction(self, source_index, target_index):
        source_particle = self.particles[source_index]
        target_particle = self.particles[target_index]
        contact = self.particle_contact(source_particle, target_particle)
        if contact is None:
            return None

        nx, ny, _overlap_area, _center_distance = contact
        rel_vx = target_particle["vx"] - source_particle["vx"]
        rel_vy = target_particle["vy"] - source_particle["vy"]
        rel_normal_velocity = rel_vx * nx + rel_vy * ny
        phase = "compression" if rel_normal_velocity < 0.0 else "rebound"
        contact_state = self.source_geo_contact_state(source_particle, target_index) or {}
        state_zero = self.contact_state_zero_velocity_geometry(contact_state)
        configured_zero = None
        if state_zero is None:
            configured_zero = self.configured_zero_velocity_geometry(source_particle, target_particle)
        if configured_zero is not None:
            self.update_configured_geo_phase(
                contact_state,
                overlap_area=_overlap_area,
                center_distance=_center_distance,
                rel_normal_velocity=rel_normal_velocity,
                source_particle=source_particle,
                target_particle=target_particle,
                configured_zero=configured_zero,
            )
            phase = contact_state.get("geo_phase", phase)
        elif state_zero is not None:
            self.update_configured_geo_phase(
                contact_state,
                overlap_area=_overlap_area,
                center_distance=_center_distance,
                rel_normal_velocity=rel_normal_velocity,
                source_particle=source_particle,
                target_particle=target_particle,
                configured_zero=state_zero,
            )
            phase = contact_state.get("geo_phase", "rebound")
        elif contact_state.get("geo_phase") != "rebound":
            return None

        first_contact_velocities = contact_state.get("first_contact_velocities", {})
        source_start_vx, source_start_vy = first_contact_velocities.get(
            source_index,
            (source_particle["vx"], source_particle["vy"]),
        )
        target_start_vx, target_start_vy = first_contact_velocities.get(
            target_index,
            (target_particle["vx"], target_particle["vy"]),
        )

        source_x, source_y = self.current_location(source_particle)
        target_x, target_y = self.current_location(target_particle)
        neo_model = self.new_neo_model()
        neo_model.momentum_per_area = self.momentum_per_area
        neo_model.inverse_square_softening = self.inverse_square_softening
        neo_model.add_particle(
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
            zero_velocity_overlap_area=(
                state_zero["overlap_area"]
                if state_zero is not None
                else (
                    configured_zero["overlap_area"]
                    if configured_zero is not None
                    else contact_state.get("geo_zero_velocity_overlap_area")
                )
            ),
            zero_velocity_center_distance=(
                state_zero["center_distance"]
                if state_zero is not None
                else (
                    configured_zero["center_distance"]
                    if configured_zero is not None
                    else contact_state.get("geo_zero_velocity_center_distance")
                )
            ),
        )
        neo_model.add_particle(
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
        neo_model.reset()
        report = next(
            (
                contact_report
                for contact_report in neo_model.contact_reports
                if contact_report["source_index"] == 0 and contact_report["target_index"] == 1
            ),
            None,
        )
        if report is None:
            return None

        if phase == "compression":
            source_velocity = (
                report["source_velocity_at_current_overlap_compression_x"],
                report["source_velocity_at_current_overlap_compression_y"],
            )
            target_velocity = (
                report["target_velocity_at_current_overlap_compression_x"],
                report["target_velocity_at_current_overlap_compression_y"],
            )
        else:
            source_velocity = (
                report["source_velocity_at_current_overlap_rebound_x"],
                report["source_velocity_at_current_overlap_rebound_y"],
            )
            target_velocity = (
                report["target_velocity_at_current_overlap_rebound_x"],
                report["target_velocity_at_current_overlap_rebound_y"],
            )
            source_velocity, target_velocity = self.outward_clamped_rebound_velocities(
                source_velocity,
                target_velocity,
                nx,
                ny,
                source_start_vx,
                source_start_vy,
                target_start_vx,
                target_start_vy,
            )

        return {
            "start_velocity": (source_start_vx, source_start_vy),
            "predicted_velocity": source_velocity,
        }

    @staticmethod
    def contact_state_zero_velocity_geometry(contact_state):
        if contact_state.get("geo_zero_velocity_overlap_area") is None:
            return None
        if contact_state.get("geo_zero_velocity_center_distance") is None:
            return None
        return {
            "overlap_area": contact_state["geo_zero_velocity_overlap_area"],
            "center_distance": contact_state["geo_zero_velocity_center_distance"],
        }

    def outward_clamped_rebound_velocities(
        self,
        source_velocity,
        target_velocity,
        nx,
        ny,
        source_start_vx,
        source_start_vy,
        target_start_vx,
        target_start_vy,
    ):
        rel_vx = target_velocity[0] - source_velocity[0]
        rel_vy = target_velocity[1] - source_velocity[1]
        rel_normal_velocity = rel_vx * nx + rel_vy * ny

        start_rel_vx = target_start_vx - source_start_vx
        start_rel_vy = target_start_vy - source_start_vy
        start_closing_speed = max(0.0, -(start_rel_vx * nx + start_rel_vy * ny))
        minimum_outward_speed = self.geo_rebound_min_fraction * start_closing_speed
        if rel_normal_velocity >= minimum_outward_speed:
            return source_velocity, target_velocity

        correction = minimum_outward_speed - rel_normal_velocity
        half_correction = 0.5 * correction
        return (
            (
                source_velocity[0] - half_correction * nx,
                source_velocity[1] - half_correction * ny,
            ),
            (
                target_velocity[0] + half_correction * nx,
                target_velocity[1] + half_correction * ny,
            ),
        )

    def configured_zero_velocity_geometry(self, source_particle, target_particle):
        if self.zero_velocity_overlap_area is None and self.zero_velocity_overlap_fraction is None:
            return None

        max_overlap_area = self.circle_overlap_area(
            source_particle["radius"],
            target_particle["radius"],
            0.0,
        )
        if self.zero_velocity_overlap_area is not None:
            zero_overlap_area = float(self.zero_velocity_overlap_area)
        else:
            zero_overlap_area = float(self.zero_velocity_overlap_fraction) * max_overlap_area
        zero_overlap_area = max(0.0, min(max_overlap_area, zero_overlap_area))
        zero_center_distance = self.center_distance_for_overlap_area(
            zero_overlap_area,
            source_particle,
            target_particle,
        )
        return {
            "overlap_area": zero_overlap_area,
            "center_distance": zero_center_distance,
        }

    def configured_wall_zero_velocity_geometry(self, particle):
        if self.zero_velocity_overlap_area is None and self.zero_velocity_overlap_fraction is None:
            return None

        max_overlap_area = self.circle_overlap_area(
            particle["radius"],
            particle["radius"],
            0.0,
        )
        if self.zero_velocity_overlap_area is not None:
            zero_overlap_area = float(self.zero_velocity_overlap_area)
        else:
            zero_overlap_area = float(self.zero_velocity_overlap_fraction) * max_overlap_area
        zero_overlap_area = max(0.0, min(max_overlap_area, zero_overlap_area))
        zero_center_distance = self.center_distance_for_wall_overlap_area(zero_overlap_area, particle)
        return {
            "overlap_area": zero_overlap_area,
            "center_distance": zero_center_distance,
        }

    def solved_wall_zero_velocity_geometry(self, particle, state):
        start_vx, start_vy = state.get("first_contact_velocity", (particle["vx"], particle["vy"]))
        nx, ny = state.get("first_contact_normal", (1.0, 0.0))
        incoming_speed = max(0.0, start_vx * nx + start_vy * ny)
        incoming_momentum = particle["mass"] * incoming_speed
        radius = particle["radius"]
        max_momentum = self.wall_overlap_momentum_at_center_distance(0.0, particle)
        max_overlap_area = self.circle_overlap_area(radius, radius, 0.0)
        if incoming_momentum <= 0.0:
            return {
                "overlap_area": 0.0,
                "center_distance": 2.0 * radius,
                "solution_source": "solved",
            }
        if incoming_momentum >= max_momentum:
            return {
                "overlap_area": max_overlap_area,
                "center_distance": 0.0,
                "solution_source": "solved_clamped",
            }

        lo = 0.0
        hi = 2.0 * radius
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            mid_momentum = self.wall_overlap_momentum_at_center_distance(mid, particle)
            if mid_momentum < incoming_momentum:
                hi = mid
            else:
                lo = mid
        center_distance = 0.5 * (lo + hi)
        return {
            "overlap_area": self.circle_overlap_area(radius, radius, center_distance),
            "center_distance": center_distance,
            "solution_source": "solved",
        }

    def neo_zero_velocity_state(
        self,
        source_particle,
        target_particle,
        rel_normal_velocity,
        current_overlap_area,
        current_center_distance,
    ):
        source_mass = source_particle["mass"]
        target_mass = target_particle["mass"]
        reduced_mass = (source_mass * target_mass) / (source_mass + target_mass)
        incoming_speed = max(0.0, -rel_normal_velocity)
        stiffness_q = self.contact_stiffness_q(source_particle, target_particle)
        radius_sum = source_particle["radius"] + target_particle["radius"]
        max_overlap_area = self.circle_overlap_area(
            source_particle["radius"],
            target_particle["radius"],
            0.0,
        )

        if incoming_speed <= 0.0:
            zero_center_distance = radius_sum
            zero_overlap_area = 0.0
            alpha_zero = 0.0
            solution_source = "force_law_zero_speed"
        else:
            alpha_zero = ((3.0 * reduced_mass * incoming_speed * incoming_speed) / (2.0 * stiffness_q)) ** (1.0 / 3.0)
            alpha_zero = max(0.0, min(radius_sum, alpha_zero))
            zero_center_distance = max(0.0, radius_sum - alpha_zero)
            zero_overlap_area = self.circle_overlap_area(
                source_particle["radius"],
                target_particle["radius"],
                zero_center_distance,
            )
            solution_source = "force_law"

        if zero_overlap_area + 1.0e-12 < current_overlap_area:
            zero_overlap_area = current_overlap_area
            zero_center_distance = current_center_distance
            alpha_zero = max(0.0, radius_sum - current_center_distance)
            solution_source = "force_law_promoted_to_current_overlap"

        return {
            "geo_zero_velocity_overlap_area": zero_overlap_area,
            "geo_zero_velocity_center_distance": zero_center_distance,
            "geo_zero_velocity_penetration_depth": alpha_zero,
            "geo_zero_velocity_overlap_fraction": (
                zero_overlap_area / max_overlap_area
                if max_overlap_area > 0.0
                else 0.0
            ),
            "geo_zero_velocity_solution_source": solution_source,
            "geo_zero_velocity_stiffness_q": stiffness_q,
            "geo_zero_velocity_reduced_mass": reduced_mass,
            "geo_zero_velocity_incoming_speed": incoming_speed,
        }

    def contact_stiffness_q(self, source_particle, target_particle):
        source_q = source_particle.get("collision_stiffness_q", self.collision_stiffness_q)
        target_q = target_particle.get("collision_stiffness_q", self.collision_stiffness_q)
        if source_q is None:
            source_q = self.collision_stiffness_q
        if target_q is None:
            target_q = self.collision_stiffness_q
        return max(1.0e-12, 0.5 * (float(source_q) + float(target_q)))

    def wall_overlap_momentum_at_center_distance(self, center_distance, particle):
        overlap_area = self.circle_overlap_area(
            particle["radius"],
            particle["radius"],
            center_distance,
        )
        return self.overlap_momentum(overlap_area, center_distance, particle)

    def center_distance_for_overlap_area(self, overlap_area, source_particle, target_particle):
        radius_sum = source_particle["radius"] + target_particle["radius"]
        if overlap_area <= 0.0:
            return radius_sum

        max_overlap_area = self.circle_overlap_area(
            source_particle["radius"],
            target_particle["radius"],
            0.0,
        )
        if overlap_area >= max_overlap_area:
            return 0.0

        lo = 0.0
        hi = radius_sum
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            mid_area = self.circle_overlap_area(
                source_particle["radius"],
                target_particle["radius"],
                mid,
            )
            if mid_area > overlap_area:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    def center_distance_for_wall_overlap_area(self, overlap_area, particle):
        radius_sum = 2.0 * particle["radius"]
        if overlap_area <= 0.0:
            return radius_sum

        max_overlap_area = self.circle_overlap_area(
            particle["radius"],
            particle["radius"],
            0.0,
        )
        if overlap_area >= max_overlap_area:
            return 0.0

        lo = 0.0
        hi = radius_sum
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            mid_area = self.circle_overlap_area(
                particle["radius"],
                particle["radius"],
                mid,
            )
            if mid_area > overlap_area:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    def update_configured_geo_phase(
        self,
        contact_state,
        overlap_area,
        center_distance,
        rel_normal_velocity,
        source_particle,
        target_particle,
        configured_zero,
    ):
        if contact_state.get("geo_phase") == "rebound":
            return

        zero_overlap_area = configured_zero["overlap_area"]
        zero_tolerance_area = zero_overlap_area * max(0.0, min(1.0, self.zero_velocity_overlap_tolerance))
        crossed_zero = overlap_area >= zero_overlap_area - zero_tolerance_area
        if not crossed_zero and rel_normal_velocity < 0.0:
            next_distance = center_distance + rel_normal_velocity * getattr(self, "current_step_dt", self.dt)
            next_area = self.circle_overlap_area(
                source_particle["radius"],
                target_particle["radius"],
                next_distance,
            )
            crossed_zero = overlap_area <= zero_overlap_area <= next_area

        if not crossed_zero:
            contact_state["geo_phase"] = "compression"
            return

        contact_state["geo_phase"] = "rebound"
        contact_state["geo_zero_velocity_overlap_area"] = zero_overlap_area
        contact_state["geo_zero_velocity_center_distance"] = configured_zero["center_distance"]

    def update_configured_geo_wall_phase(
        self,
        contact_state,
        overlap_area,
        center_distance,
        normal_velocity,
        particle,
        configured_zero,
    ):
        if contact_state.get("geo_phase") == "rebound":
            return

        zero_overlap_area = configured_zero["overlap_area"]
        zero_tolerance_area = zero_overlap_area * max(0.0, min(1.0, self.zero_velocity_overlap_tolerance))
        crossed_zero = overlap_area >= zero_overlap_area - zero_tolerance_area
        if not crossed_zero and normal_velocity > 0.0:
            next_distance = center_distance - 2.0 * normal_velocity * getattr(self, "current_step_dt", self.dt)
            next_area = self.circle_overlap_area(
                particle["radius"],
                particle["radius"],
                next_distance,
            )
            crossed_zero = overlap_area <= zero_overlap_area <= next_area

        if not crossed_zero:
            contact_state["geo_phase"] = "compression"
            return

        contact_state["geo_phase"] = "rebound"
        contact_state["geo_zero_velocity_overlap_area"] = zero_overlap_area
        contact_state["geo_zero_velocity_center_distance"] = configured_zero["center_distance"]

    @staticmethod
    def sync_velocity_mirror(particle):
        vx = particle["vx"]
        vy = particle["vy"]
        particle["VelRad"][0] = vx
        particle["VelRad"][1] = vy
        particle["VelRad"][3] = math.atan2(vy, vx) if vx != 0.0 or vy != 0.0 else 0.0

    def particle_contact(self, source_particle, target_particle):
        if not self.is_active_particle(source_particle) or not self.is_active_particle(target_particle):
            return None

        source_x, source_y = self.current_location(source_particle)
        target_x, target_y = self.current_location(target_particle)
        dx = target_x - source_x
        dy = target_y - source_y
        center_distance = math.hypot(dx, dy)
        source_radius = source_particle["radius"]
        target_radius = target_particle["radius"]
        radius_sum = source_radius + target_radius
        if center_distance >= radius_sum:
            return None

        if center_distance <= 1.0e-12:
            nx = 1.0
            ny = 0.0
        else:
            nx = dx / center_distance
            ny = dy / center_distance

        overlap_area = self.circle_overlap_area(source_radius, target_radius, center_distance)
        return nx, ny, overlap_area, center_distance

    def wall_contact(self, source_particle, wall_flag, walls):
        if walls is None:
            return None

        x, y = self.current_location(source_particle)
        radius = source_particle["radius"]

        if wall_flag == 1:
            distance_to_wall = x - walls["start_x"]
            nx, ny = -1.0, 0.0
        elif wall_flag == 2:
            distance_to_wall = walls["end_x"] - x
            nx, ny = 1.0, 0.0
        elif wall_flag == 3:
            distance_to_wall = y - walls["start_y"]
            nx, ny = 0.0, -1.0
        elif wall_flag == 4:
            distance_to_wall = walls["end_y"] - y
            nx, ny = 0.0, 1.0
        else:
            raise ValueError(f"Unknown wall flag: {wall_flag!r}")

        if distance_to_wall >= radius:
            return None

        center_distance = max(0.0, 2.0 * distance_to_wall)
        overlap_area = self.circle_overlap_area(radius, radius, center_distance)
        return nx, ny, overlap_area, center_distance

    def overlap_momentum(self, overlap_area, center_distance, source_particle):
        momentum_per_area = source_particle.get(
            "momentum_per_area",
            source_particle.get("repulsion_force_per_area", self.momentum_per_area),
        )
        if momentum_per_area is None:
            momentum_per_area = self.momentum_per_area
        return momentum_per_area * overlap_area * self.inverse_square_weight(center_distance)

    def inverse_square_weight(self, distance):
        softening = max(self.inverse_square_softening, 1.0e-12)
        return 1.0 / max(distance * distance, softening * softening)

    @staticmethod
    def circle_overlap_area(radius_i, radius_j, center_distance):
        if abs(radius_i - radius_j) > 1.0e-12:
            raise ValueError("circle_overlap_area currently assumes equal radii.")

        radius = radius_i
        distance = max(0.0, min(2.0 * radius, center_distance))
        return (
            2.0 * radius * radius * math.acos(distance / (2.0 * radius))
            - 0.5 * distance * math.sqrt(max(0.0, 4.0 * radius * radius - distance * distance))
        )

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
            if not self.is_active_particle(particle_i):
                continue
            for j in range(len(self.particles)):
                if i == j:
                    continue
                particle_j = self.particles[j]
                if not self.is_active_particle(particle_j):
                    continue
                if self.particle_contact(particle_i, particle_j) is not None:
                    self.add_particle_contact(i, j)
            self.detect_wall_contacts(i, particle_i)

    def detect_wall_contacts(self, particle_index, particle):
        if self.walls is None:
            return

        x, y = self.current_location(particle)
        radius = particle["radius"]
        walls = self.walls
        flow_type = self.flow_type

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
        for particle in self.particles:
            for state in particle.get("gcs", []):
                state["touched"] = False

        active_pairs = set()
        for source_index, source_particle in enumerate(self.particles):
            for slot in range(source_particle.get("sltnum", 0)):
                contact_record = source_particle["ccs"][slot]
                if contact_record.get("clflg", 0) == 0:
                    continue

                target_index = contact_record["pindex"]
                pair_key = tuple(sorted((source_index, target_index)))

                target_particle = self.particles[target_index]
                contact = self.particle_contact(source_particle, target_particle)
                if contact is None:
                    continue
                active_pairs.add(pair_key)

                nx, ny, overlap_area, center_distance = contact
                rel_vx = target_particle["vx"] - source_particle["vx"]
                rel_vy = target_particle["vy"] - source_particle["vy"]
                rel_normal_velocity = rel_vx * nx + rel_vy * ny
                reduced_mass = (
                    source_particle["mass"] * target_particle["mass"]
                ) / (source_particle["mass"] + target_particle["mass"])
                rel_normal_momentum = reduced_mass * abs(rel_normal_velocity)
                overlap_contact_momentum = self.overlap_momentum(
                    overlap_area,
                    center_distance,
                    source_particle,
                )
                state = self.source_geo_contact_state(source_particle, target_index)
                if state is None:
                    state = self.allocate_geo_contact_state(source_particle, target_index)
                    if state is None:
                        source_particle["contact_overflow"] = True
                        continue
                    state.update(
                        {
                            "internal_contact_momentum": 0.0,
                            "last_relative_normal_velocity": rel_normal_velocity,
                            "geo_phase": "compression",
                            "first_contact_velocities": {
                                source_index: (source_particle["vx"], source_particle["vy"]),
                                target_index: (target_particle["vx"], target_particle["vy"]),
                            },
                            "first_contact_normal": (nx, ny),
                            "first_contact_distance": center_distance,
                            "first_contact_overlap_area": overlap_area,
                        }
                    )
                    state.update(
                        self.neo_zero_velocity_state(
                            source_particle,
                            target_particle,
                            rel_normal_velocity,
                            overlap_area,
                            center_distance,
                        )
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
                state["touched"] = True

        finalized_pairs = set()
        for source_index, particle in enumerate(self.particles):
            for state in particle.get("gcs", []):
                if not state.get("active", False) or state.get("touched", False):
                    continue
                target_index = state.get("target_index")
                if target_index is None:
                    self.reset_geo_contact_state(state)
                    continue
                pair_key = tuple(sorted((source_index, target_index)))
                if pair_key not in active_pairs and pair_key not in finalized_pairs:
                    self.finalize_exited_geo_contact(source_index, target_index, state)
                    finalized_pairs.add(pair_key)
                self.reset_geo_contact_state(state)

    def update_wall_contact_state(self):
        active_walls = set()
        for particle_index, particle in enumerate(self.particles):
            if not self.is_active_particle(particle):
                continue
            for contact_record in particle.get("bcs", []):
                wall_flag = contact_record.get("clflg", 0)
                if wall_flag == 0:
                    continue

                contact = self.wall_contact(particle, wall_flag, self.walls)
                if contact is None:
                    continue

                nx, ny, overlap_area, center_distance = contact
                normal_velocity = particle["vx"] * nx + particle["vy"] * ny
                first_velocity = (particle["vx"], particle["vy"])
                if self.time == 0.0 and normal_velocity < 0.0:
                    first_velocity = (
                        particle["vx"] - 2.0 * normal_velocity * nx,
                        particle["vy"] - 2.0 * normal_velocity * ny,
                    )

                wall_key = (particle_index, wall_flag)
                state = self.wall_contact_state.setdefault(
                    wall_key,
                    {
                        "last_relative_normal_velocity": normal_velocity,
                        "geo_phase": "compression",
                        "first_contact_velocity": first_velocity,
                        "first_contact_normal": (nx, ny),
                        "first_contact_distance": center_distance,
                        "first_contact_overlap_area": overlap_area,
                    },
                )
                overlap_contact_momentum = self.overlap_momentum(
                    overlap_area,
                    center_distance,
                    particle,
                )
                state["relative_normal_momentum"] = particle["mass"] * abs(normal_velocity)
                state["overlap_contact_momentum"] = overlap_contact_momentum
                state["last_relative_normal_velocity"] = normal_velocity
                active_walls.add(wall_key)

        for wall_key in list(self.wall_contact_state):
            if wall_key not in active_walls:
                self.finalize_exited_geo_wall_contact(wall_key, self.wall_contact_state[wall_key])
                self.wall_contact_state.pop(wall_key, None)

    def finalize_exited_geo_contact(self, source_index, target_index, state):
        if state.get("geo_phase") != "rebound":
            return

        source_particle = self.particles[source_index]
        target_particle = self.particles[target_index]
        if source_particle.get("sltnum", 0) > 0 or target_particle.get("sltnum", 0) > 0:
            return

        first_contact_velocities = state.get("first_contact_velocities", {})
        if source_index not in first_contact_velocities or target_index not in first_contact_velocities:
            return
        if "first_contact_normal" not in state:
            return

        source_start_vx, source_start_vy = first_contact_velocities[source_index]
        target_start_vx, target_start_vy = first_contact_velocities[target_index]
        nx, ny = state["first_contact_normal"]
        source_mass = source_particle["mass"]
        target_mass = target_particle["mass"]
        reduced_mass = (source_mass * target_mass) / (source_mass + target_mass)
        start_rel_vx = target_start_vx - source_start_vx
        start_rel_vy = target_start_vy - source_start_vy
        incoming_relative_normal_momentum = max(0.0, -reduced_mass * (start_rel_vx * nx + start_rel_vy * ny))
        if incoming_relative_normal_momentum <= 0.0:
            return

        rebound_impulse = 2.0 * incoming_relative_normal_momentum
        source_particle["vx"] = source_start_vx - (rebound_impulse / source_mass) * nx
        source_particle["vy"] = source_start_vy - (rebound_impulse / source_mass) * ny
        target_particle["vx"] = target_start_vx + (rebound_impulse / target_mass) * nx
        target_particle["vy"] = target_start_vy + (rebound_impulse / target_mass) * ny
        self.sync_velocity_mirror(source_particle)
        self.sync_velocity_mirror(target_particle)

    def finalize_exited_geo_wall_contact(self, wall_key, state):
        if state.get("geo_phase") != "rebound":
            return
        particle_index, _wall_flag = wall_key
        particle = self.particles[particle_index]
        if self.boundary_contact_count(particle) > 0:
            return
        if "first_contact_velocity" not in state or "first_contact_normal" not in state:
            return

        start_vx, start_vy = state["first_contact_velocity"]
        nx, ny = state["first_contact_normal"]
        incoming_speed = start_vx * nx + start_vy * ny
        if incoming_speed <= 0.0:
            return

        particle["vx"] = start_vx - 2.0 * incoming_speed * nx
        particle["vy"] = start_vy - 2.0 * incoming_speed * ny
        self.sync_velocity_mirror(particle)

    @staticmethod
    def empty_particle_contact():
        return {"pindex": 0, "clflg": 0}

    @staticmethod
    def empty_boundary_contact():
        return {"clflg": 0}

    def empty_geo_contact_states(self):
        return [
            self.empty_geo_contact_state()
            for _ in range(self.max_contacts_per_particle)
        ]

    @staticmethod
    def empty_geo_contact_state():
        return {
            "active": False,
            "target_index": None,
            "touched": False,
        }

    def reset_geo_contact_state(self, state):
        state.clear()
        state.update(self.empty_geo_contact_state())

    @staticmethod
    def source_geo_contact_state(source_particle, target_index):
        for state in source_particle.get("gcs", []):
            if state.get("active", False) and state.get("target_index") == target_index:
                return state
        return None

    def allocate_geo_contact_state(self, source_particle, target_index):
        for state in source_particle.get("gcs", []):
            if state.get("active", False) and state.get("target_index") == target_index:
                return state
        for state in source_particle.get("gcs", []):
            if not state.get("active", False):
                state.clear()
                state.update(
                    {
                        "active": True,
                        "target_index": target_index,
                        "touched": False,
                    }
                )
                return state
        return None

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
            if not self.is_active_particle(particle):
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
                    "state_flg": particle.get("state_flg", self.STATE_ACTIVE),
                    "overlap_momentum_x": particle.get("overlap_momentum_x", 0.0),
                    "overlap_momentum_y": particle.get("overlap_momentum_y", 0.0),
                    "overlap_momentum": particle.get("overlap_momentum", 0.0),
                    "internal_momentum_x": particle.get("internal_momentum_x", 0.0),
                    "internal_momentum_y": particle.get("internal_momentum_y", 0.0),
                    "internal_momentum": particle.get("internal_momentum", 0.0),
                    "momentum_delta_x": particle.get("momentum_delta_x", 0.0),
                    "momentum_delta_y": particle.get("momentum_delta_y", 0.0),
                    "momentum_delta": particle.get("momentum_delta", 0.0),
                    "starting_uncorrected_vx": particle.get("starting_uncorrected_vx", particle["vx"]),
                    "starting_uncorrected_vy": particle.get("starting_uncorrected_vy", particle["vy"]),
                    "starting_corrected_vx": particle.get("starting_corrected_vx", particle["vx"]),
                    "starting_corrected_vy": particle.get("starting_corrected_vy", particle["vy"]),
                    "starting_velocity_correction_x": particle.get("starting_velocity_correction_x", 0.0),
                    "starting_velocity_correction_y": particle.get("starting_velocity_correction_y", 0.0),
                    "starting_uncorrected_speed": particle.get(
                        "starting_uncorrected_speed",
                        math.hypot(particle["vx"], particle["vy"]),
                    ),
                    "starting_corrected_speed": particle.get(
                        "starting_corrected_speed",
                        math.hypot(particle["vx"], particle["vy"]),
                    ),
                },
            )

