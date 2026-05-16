import math

from base.Dynamics import Dynamics
from base.ExperimentalBase import ExperimentalBase
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
        self.use_experimental_starting_overlap = False
        self.use_experimental_geometry_dynamics = False
        self.zero_velocity_overlap_area = None
        self.zero_velocity_overlap_fraction = None
        self.zero_velocity_overlap_tolerance = 0.01
        self.experimental_rebound_min_fraction = 0.02
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
        if self.use_experimental_starting_overlap:
            self.apply_experimental_starting_overlap()
            self.detect_contacts()
        self.update_contact_state()
        self.dynamics.process_collisions(self.particles, self.walls)
        self.dynamics.resolve_starting_collisions(self.particles)
        self.record_step_report()

    def apply_experimental_starting_overlap(self):
        experimental_base = ExperimentalBase()
        experimental_base.momentum_per_area = self.dynamics.momentum_per_area
        experimental_base.inverse_square_softening = self.dynamics.inverse_square_softening

        for particle_config in self.particle_configs:
            particle = dict(particle_config)
            particle["location"] = dict(particle["location"])
            experimental_base.add_particle(**particle)
        experimental_base.reset()

        for index, experimental_particle in enumerate(experimental_base.particles):
            if index >= len(self.particles):
                continue
            if not self.particle_has_starting_overlap(index):
                continue

            particle = self.particles[index]
            particle["vx"] = experimental_particle["velocity_at_current_overlap_rebound_x"]
            particle["vy"] = experimental_particle["velocity_at_current_overlap_rebound_y"]
            self.dynamics.sync_velocity_mirror(particle)

    def particle_has_starting_overlap(self, particle_index):
        if particle_index >= len(self.particles):
            return False
        particle = self.particles[particle_index]
        return particle.get("sltnum", 0) > 0 or self.boundary_contact_count(particle) > 0

    def step(self, dt):
        self.current_step_dt = dt
        self.dynamics.begin_step(self.particles, dt, self.set_location)
        self.detect_contacts()
        self.update_contact_state()
        self.dynamics.process_collisions(self.particles, self.walls)
        if self.use_experimental_geometry_dynamics:
            self.apply_experimental_geometry_dynamics()
        else:
            self.dynamics.apply_overlap_momentum(self.particles)
        self.move(dt)
        if self.use_experimental_geometry_dynamics and self.has_configured_zero_velocity_overlap():
            self.detect_contacts()
            self.clip_configured_zero_velocity_overlaps()
        self.dynamics.end_step(self.particles, self.set_location)
        self.time += dt
        self.record_step_report()

    def apply_experimental_geometry_dynamics(self):
        if self.has_configured_zero_velocity_overlap():
            predictions = self.experimental_geometry_velocity_predictions()
            if predictions is None:
                self.dynamics.apply_overlap_momentum(self.particles)
                return
            self.apply_experimental_velocity_predictions(predictions)
            return

        if not self.experimental_geometry_has_rebound_pair():
            self.dynamics.apply_overlap_momentum(self.particles)
            self.update_experimental_geometry_turnaround()
            return

        predictions = self.experimental_geometry_velocity_predictions()
        if predictions is None:
            self.dynamics.apply_overlap_momentum(self.particles)
            self.update_experimental_geometry_turnaround()
            return

        self.apply_experimental_velocity_predictions(predictions)

    def apply_experimental_velocity_predictions(self, predictions):
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
            self.dynamics.sync_velocity_mirror(particle)
        self.clip_configured_zero_velocity_overlaps()

    def has_configured_zero_velocity_overlap(self):
        return self.zero_velocity_overlap_area is not None or self.zero_velocity_overlap_fraction is not None

    def clip_configured_zero_velocity_overlaps(self):
        if not self.has_configured_zero_velocity_overlap():
            return

        for pair_key, state in self.contact_state.items():
            if state.get("experimental_phase") != "rebound":
                continue

            source_index, target_index = pair_key
            source_particle = self.particles[source_index]
            target_particle = self.particles[target_index]
            configured_zero = self.configured_zero_velocity_geometry(source_particle, target_particle)
            if configured_zero is None:
                continue

            contact = self.dynamics.particle_contact(source_particle, target_particle)
            if contact is None:
                continue

            nx, ny, overlap_area, center_distance = contact
            if overlap_area <= configured_zero["overlap_area"]:
                continue

            self.set_pair_center_distance(
                source_particle,
                target_particle,
                nx,
                ny,
                configured_zero["center_distance"],
            )
            state["experimental_zero_velocity_clipped"] = True

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

    def experimental_geometry_has_rebound_pair(self):
        return any(
            state.get("experimental_phase") == "rebound"
            for state in self.contact_state.values()
        )

    def update_experimental_geometry_turnaround(self):
        for pair_key, state in self.contact_state.items():
            if state.get("experimental_phase") == "rebound":
                continue

            source_index, target_index = pair_key
            source_particle = self.particles[source_index]
            target_particle = self.particles[target_index]
            contact = self.dynamics.particle_contact(source_particle, target_particle)
            if contact is None:
                continue

            nx, ny, overlap_area, center_distance = contact
            rel_vx = target_particle["vx"] - source_particle["vx"]
            rel_vy = target_particle["vy"] - source_particle["vy"]
            rel_normal_velocity = rel_vx * nx + rel_vy * ny
            if rel_normal_velocity < 0.0:
                state["experimental_previous_center_distance"] = center_distance
                state["experimental_previous_overlap_area"] = overlap_area
                state["experimental_previous_relative_normal_velocity"] = rel_normal_velocity
                continue

            zero_prediction = self.predict_experimental_zero_velocity_geometry(
                state,
                center_distance,
                overlap_area,
                rel_normal_velocity,
                source_particle,
                target_particle,
            )
            state["experimental_phase"] = "rebound"
            state["experimental_zero_velocity_overlap_area"] = zero_prediction["overlap_area"]
            state["experimental_zero_velocity_center_distance"] = zero_prediction["center_distance"]
            state["experimental_zero_velocity_relative_normal_velocity"] = rel_normal_velocity
            state["experimental_zero_velocity_interpolation_alpha"] = zero_prediction["alpha"]
            state["experimental_zero_velocity_interpolated"] = zero_prediction["interpolated"]

    def predict_experimental_zero_velocity_geometry(
        self,
        state,
        center_distance,
        overlap_area,
        rel_normal_velocity,
        source_particle,
        target_particle,
    ):
        previous_velocity = state.get("experimental_previous_relative_normal_velocity")
        previous_distance = state.get("experimental_previous_center_distance")
        previous_overlap_area = state.get("experimental_previous_overlap_area")
        if (
            previous_velocity is None
            or previous_distance is None
            or previous_overlap_area is None
            or previous_velocity >= 0.0
            or rel_normal_velocity <= 0.0
        ):
            return {
                "center_distance": center_distance,
                "overlap_area": overlap_area,
                "alpha": 1.0,
                "interpolated": False,
            }

        denominator = rel_normal_velocity - previous_velocity
        if abs(denominator) <= 1.0e-12:
            alpha = 1.0
        else:
            alpha = -previous_velocity / denominator
        alpha = max(0.0, min(1.0, alpha))
        zero_distance = previous_distance + alpha * (center_distance - previous_distance)
        zero_overlap_area = self.dynamics.circle_overlap_area(
            source_particle["radius"],
            target_particle["radius"],
            zero_distance,
        )
        return {
            "center_distance": zero_distance,
            "overlap_area": zero_overlap_area,
            "alpha": alpha,
            "interpolated": True,
        }

    def experimental_geometry_velocity_predictions(self):
        active_pairs = []
        for source_index, source_particle in enumerate(self.particles):
            if not self.dynamics.is_active_particle(source_particle):
                continue
            for slot in range(source_particle.get("sltnum", 0)):
                contact_record = source_particle["ccs"][slot]
                if contact_record.get("clflg", 0) == 0:
                    continue
                target_index = contact_record["pindex"]
                pair_key = tuple(sorted((source_index, target_index)))
                if pair_key not in active_pairs:
                    active_pairs.append(pair_key)

        if not active_pairs:
            return None

        if len(active_pairs) != 1 and not self.has_configured_zero_velocity_overlap():
            return None

        combined_velocities = {}
        for pair_key in active_pairs:
            pair_prediction = self.experimental_geometry_pair_prediction(pair_key)
            if pair_prediction is None:
                return None

            for particle_index, prediction in pair_prediction.items():
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

    def experimental_geometry_pair_prediction(self, pair_key):
        source_index, target_index = pair_key
        source_particle = self.particles[source_index]
        target_particle = self.particles[target_index]
        contact = self.dynamics.particle_contact(source_particle, target_particle)
        if contact is None:
            return None

        nx, ny, _overlap_area, _center_distance = contact
        rel_vx = target_particle["vx"] - source_particle["vx"]
        rel_vy = target_particle["vy"] - source_particle["vy"]
        rel_normal_velocity = rel_vx * nx + rel_vy * ny
        phase = "compression" if rel_normal_velocity < 0.0 else "rebound"
        contact_state = self.contact_state.get(pair_key, {})
        configured_zero = self.configured_zero_velocity_geometry(source_particle, target_particle)
        if configured_zero is not None:
            self.update_configured_experimental_phase(
                contact_state,
                overlap_area=_overlap_area,
                center_distance=_center_distance,
                rel_normal_velocity=rel_normal_velocity,
                source_particle=source_particle,
                target_particle=target_particle,
                configured_zero=configured_zero,
            )
            phase = contact_state.get("experimental_phase", phase)
        elif contact_state.get("experimental_phase") != "rebound":
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
        experimental_base = ExperimentalBase()
        experimental_base.momentum_per_area = self.dynamics.momentum_per_area
        experimental_base.inverse_square_softening = self.dynamics.inverse_square_softening
        experimental_base.add_particle(
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
                configured_zero["overlap_area"]
                if configured_zero is not None
                else contact_state.get("experimental_zero_velocity_overlap_area")
            ),
            zero_velocity_center_distance=(
                configured_zero["center_distance"]
                if configured_zero is not None
                else contact_state.get("experimental_zero_velocity_center_distance")
            ),
        )
        experimental_base.add_particle(
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
        experimental_base.reset()
        report = next(
            (
                contact_report
                for contact_report in experimental_base.contact_reports
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
            source_index: {
                "start_velocity": (source_start_vx, source_start_vy),
                "predicted_velocity": source_velocity,
            },
            target_index: {
                "start_velocity": (target_start_vx, target_start_vy),
                "predicted_velocity": target_velocity,
            },
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
        minimum_outward_speed = self.experimental_rebound_min_fraction * start_closing_speed
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

        max_overlap_area = self.dynamics.circle_overlap_area(
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

    def center_distance_for_overlap_area(self, overlap_area, source_particle, target_particle):
        radius_sum = source_particle["radius"] + target_particle["radius"]
        if overlap_area <= 0.0:
            return radius_sum

        max_overlap_area = self.dynamics.circle_overlap_area(
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
            mid_area = self.dynamics.circle_overlap_area(
                source_particle["radius"],
                target_particle["radius"],
                mid,
            )
            if mid_area > overlap_area:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    def update_configured_experimental_phase(
        self,
        contact_state,
        overlap_area,
        center_distance,
        rel_normal_velocity,
        source_particle,
        target_particle,
        configured_zero,
    ):
        if contact_state.get("experimental_phase") == "rebound":
            return

        zero_overlap_area = configured_zero["overlap_area"]
        zero_tolerance_area = zero_overlap_area * max(0.0, min(1.0, self.zero_velocity_overlap_tolerance))
        crossed_zero = overlap_area >= zero_overlap_area - zero_tolerance_area
        if not crossed_zero and rel_normal_velocity < 0.0:
            next_distance = center_distance + rel_normal_velocity * getattr(self, "current_step_dt", self.dt)
            next_area = self.dynamics.circle_overlap_area(
                source_particle["radius"],
                target_particle["radius"],
                next_distance,
            )
            crossed_zero = overlap_area <= zero_overlap_area <= next_area

        if not crossed_zero:
            contact_state["experimental_phase"] = "compression"
            return

        contact_state["experimental_phase"] = "rebound"
        contact_state["experimental_zero_velocity_overlap_area"] = zero_overlap_area
        contact_state["experimental_zero_velocity_center_distance"] = configured_zero["center_distance"]
        contact_state["experimental_zero_velocity_interpolated"] = False
        contact_state["experimental_zero_velocity_interpolation_alpha"] = 1.0

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
                        "experimental_phase": "compression",
                        "first_contact_velocities": {
                            source_index: (source_particle["vx"], source_particle["vy"]),
                            target_index: (target_particle["vx"], target_particle["vy"]),
                        },
                        "first_contact_normal": (nx, ny),
                        "first_contact_distance": center_distance,
                        "first_contact_overlap_area": overlap_area,
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

        for pair_key in list(self.contact_state):
            if pair_key not in active_pairs:
                self.contact_state.pop(pair_key, None)

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
