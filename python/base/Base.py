import math

from base.NeoDynamics import NeoDynamics
from base.Report import Report
from base.SimCalc import SimCalc


class Base:
    """Minimal particle motion model.

    This clean step has motion, contact detection, and minimal Mom-style
    overlap momentum tracking. It has no bonding, tracing, or exports.
    """

    ESCAPE_MODE_RESERVOIR = SimCalc.ESCAPE_MODE_RESERVOIR
    ESCAPE_MODE_ESCAPED = SimCalc.ESCAPE_MODE_ESCAPED
    ESCAPE_MODE_RETAINED = SimCalc.ESCAPE_MODE_RETAINED

    STATE_RESERVOIR = SimCalc.STATE_RESERVOIR
    STATE_ACTIVE = SimCalc.STATE_ACTIVE
    STATE_ESCAPED = SimCalc.STATE_ESCAPED
    STATE_RETAINED = SimCalc.STATE_RETAINED

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
        self.zero_velocity_overlap_tolerance = 0.01
        self.neo_velocity_tolerance = 1.0e-12
        self.geo_rebound_min_fraction = 0.02
        self.collision_stiffness_q = 1.0
        self.momentum_per_area = 0.001
        self.inverse_square_softening = 1.0
        self.wall_ghost_mass_multiplier = 1.0e12
        self.sim_calc = SimCalc(self)
        self.report = Report()
        self.wall_contact_state = {}

    def configure_flow(self, config):
        self.sim_calc.configure_flow(config)

    def begin_step(self, particles, dt, set_location):
        self.sim_calc.begin_step(particles, dt, set_location)

    def end_step(self, particles, set_location):
        self.sim_calc.end_step(particles, set_location)

    def is_active_particle(self, particle):
        return self.sim_calc.is_active_particle(particle)

    def is_reservoir_particle(self, particle):
        return self.sim_calc.is_reservoir_particle(particle)

    @classmethod
    def normalize_escape_mode(cls, escape_mode):
        return SimCalc.normalize_escape_mode(escape_mode)

    @property
    def flow_type(self):
        return self.sim_calc.flow_type

    @property
    def released_count(self):
        return self.sim_calc.released_count

    @property
    def recycled_count(self):
        return self.sim_calc.recycled_count

    @property
    def escaped_count(self):
        return self.sim_calc.escaped_count

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
        self.update_neo_internal_momentum_report()
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
            contact = self.wall_ghost_contact(particle, wall_flag, self.walls)
            if contact is None:
                continue

            nx, ny = contact["normal"]
            overlap_area = contact["overlap_area"]
            center_distance = contact["center_distance"]
            first_vx, first_vy = state.get("first_contact_velocity", (particle["vx"], particle["vy"]))
            normal_velocity = first_vx * nx + first_vy * ny
            zero_state = self.new_neo_model().particle_zero_velocity_state(
                particle,
                contact["ghost_particle"],
                -normal_velocity,
                overlap_area,
                center_distance,
            )
            zero_geometry = {
                "overlap_area": zero_state["geo_zero_velocity_overlap_area"],
                "center_distance": zero_state["geo_zero_velocity_center_distance"],
                "solution_source": zero_state["geo_zero_velocity_solution_source"],
            }
            if zero_geometry["overlap_area"] + 1.0e-12 < overlap_area:
                zero_geometry = {
                    "overlap_area": overlap_area,
                    "center_distance": center_distance,
                    "solution_source": "force_law_promoted_to_current_overlap",
                }

            state["geo_phase"] = "rebound"
            state["geo_zero_velocity_overlap_area"] = zero_geometry["overlap_area"]
            state["geo_zero_velocity_center_distance"] = zero_geometry["center_distance"]
            state["geo_zero_velocity_source"] = zero_geometry["solution_source"]
            state["geo_zero_velocity_penetration_depth"] = zero_state.get("geo_zero_velocity_penetration_depth")
            state["geo_zero_velocity_overlap_fraction"] = zero_state.get("geo_zero_velocity_overlap_fraction")
            state["geo_zero_velocity_stiffness_q"] = zero_state.get("geo_zero_velocity_stiffness_q")
            state["geo_zero_velocity_incoming_speed"] = zero_state.get("geo_zero_velocity_incoming_speed")
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
            particle["neo_internal_momentum_x"] = 0.0
            particle["neo_internal_momentum_y"] = 0.0
            particle["neo_internal_momentum"] = 0.0
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
        self.clip_zero_velocity_overlaps()
        self.clip_zero_velocity_wall_overlaps()
        self.end_step(self.particles, self.set_location)
        self.update_neo_internal_momentum_report()
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
        self.clip_zero_velocity_overlaps()
        self.clip_zero_velocity_wall_overlaps()

    def has_pair_zero_velocity_model(self):
        return True

    def new_neo_model(self):
        neo_model = NeoDynamics()
        neo_model.collision_stiffness_q = self.collision_stiffness_q
        return neo_model

    def clip_zero_velocity_overlaps(self):
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

    def clip_zero_velocity_wall_overlaps(self):
        for wall_key, state in self.wall_contact_state.items():
            if state.get("geo_phase") != "rebound":
                continue

            particle_index, wall_flag = wall_key
            particle = self.particles[particle_index]
            zero_geometry = self.contact_state_zero_velocity_geometry(state)
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
        active_pairs = []
        active_pair_set = set()
        for source_index, source_particle in enumerate(self.particles):
            if not self.is_active_particle(source_particle):
                continue
            for slot in range(source_particle.get("sltnum", 0)):
                contact_record = source_particle["ccs"][slot]
                if contact_record.get("clflg", 0) == 0:
                    continue
                target_index = contact_record["pindex"]
                pair_key = tuple(sorted((source_index, target_index)))
                if pair_key not in active_pair_set:
                    active_pair_set.add(pair_key)
                    active_pairs.append(pair_key)

        if not active_pairs:
            return None

        if len(active_pairs) != 1 and not self.has_pair_zero_velocity_model():
            return None

        predictions = {}
        for cluster in self.pair_contact_clusters(active_pairs):
            cluster_predictions = self.geo_cluster_velocity_predictions(cluster, active_pairs)
            if cluster_predictions is None:
                return None
            predictions.update(cluster_predictions)

        return predictions

    @staticmethod
    def pair_contact_clusters(active_pairs):
        neighbors = {}
        for source_index, target_index in active_pairs:
            neighbors.setdefault(source_index, set()).add(target_index)
            neighbors.setdefault(target_index, set()).add(source_index)

        clusters = []
        visited = set()
        for particle_index in neighbors:
            if particle_index in visited:
                continue
            stack = [particle_index]
            cluster = set()
            visited.add(particle_index)
            while stack:
                current = stack.pop()
                cluster.add(current)
                for neighbor in neighbors.get(current, ()):
                    if neighbor in visited:
                        continue
                    visited.add(neighbor)
                    stack.append(neighbor)
            clusters.append(cluster)
        return clusters

    def geo_cluster_velocity_predictions(self, cluster, active_pairs):
        cluster_pairs = [
            pair for pair in active_pairs if pair[0] in cluster and pair[1] in cluster
        ]
        if not cluster_pairs:
            return None

        if len(cluster_pairs) == 1:
            source_index, target_index = cluster_pairs[0]
            source_prediction = self.geo_pair_prediction(source_index, target_index)
            target_prediction = self.geo_pair_prediction(target_index, source_index)
            if source_prediction is None or target_prediction is None:
                return None
            return {
                source_index: source_prediction["predicted_velocity"],
                target_index: target_prediction["predicted_velocity"],
            }

        return self.geo_multi_pair_cluster_prediction(cluster, cluster_pairs)

    def geo_multi_pair_cluster_prediction(self, cluster, cluster_pairs):
        cluster_indices = sorted(cluster)
        velocities = {
            index: [self.particles[index]["vx"], self.particles[index]["vy"]]
            for index in cluster_indices
        }
        contacts = []

        for source_index, target_index in cluster_pairs:
            source_particle = self.particles[source_index]
            target_particle = self.particles[target_index]
            contact = self.particle_contact(source_particle, target_particle)
            if contact is None:
                return None

            nx, ny, _overlap_area, _center_distance = contact
            source_prediction = self.geo_pair_prediction(source_index, target_index)
            target_prediction = self.geo_pair_prediction(target_index, source_index)
            if source_prediction is None or target_prediction is None:
                return None

            current_relative_normal_velocity = (
                (target_particle["vx"] - source_particle["vx"]) * nx
                + (target_particle["vy"] - source_particle["vy"]) * ny
            )
            desired_relative_normal_velocity = (
                (
                    target_prediction["predicted_velocity"][0]
                    - source_prediction["predicted_velocity"][0]
                )
                * nx
                + (
                    target_prediction["predicted_velocity"][1]
                    - source_prediction["predicted_velocity"][1]
                )
                * ny
            )
            contacts.append(
                {
                    "source_index": source_index,
                    "target_index": target_index,
                    "normal": (nx, ny),
                    "delta_relative_normal_velocity": (
                        desired_relative_normal_velocity - current_relative_normal_velocity
                    ),
                }
            )

        impulses = self.solve_cluster_contact_impulses(contacts)
        if impulses is None:
            return None

        for impulse, contact in zip(impulses, contacts):
            source_index = contact["source_index"]
            target_index = contact["target_index"]
            source_particle = self.particles[source_index]
            target_particle = self.particles[target_index]
            nx, ny = contact["normal"]
            velocities[source_index][0] -= impulse * nx / source_particle["mass"]
            velocities[source_index][1] -= impulse * ny / source_particle["mass"]
            velocities[target_index][0] += impulse * nx / target_particle["mass"]
            velocities[target_index][1] += impulse * ny / target_particle["mass"]

        return {
            index: (velocity[0], velocity[1])
            for index, velocity in velocities.items()
        }

    def solve_cluster_contact_impulses(self, contacts):
        contact_count = len(contacts)
        if contact_count == 0:
            return []

        matrix = [
            [self.cluster_relative_velocity_impulse_coefficient(row, column)
             for column in contacts]
            for row in contacts
        ]
        target = [
            contact["delta_relative_normal_velocity"]
            for contact in contacts
        ]

        return self.solve_linear_system(matrix, target)

    def cluster_relative_velocity_impulse_coefficient(self, row_contact, column_contact):
        row_source = row_contact["source_index"]
        row_target = row_contact["target_index"]
        row_nx, row_ny = row_contact["normal"]
        column_source = column_contact["source_index"]
        column_target = column_contact["target_index"]
        column_nx, column_ny = column_contact["normal"]
        normal_dot = row_nx * column_nx + row_ny * column_ny

        coefficient = 0.0
        source_mass = self.particles[column_source]["mass"]
        target_mass = self.particles[column_target]["mass"]
        if row_target == column_source:
            coefficient -= normal_dot / source_mass
        if row_target == column_target:
            coefficient += normal_dot / target_mass
        if row_source == column_source:
            coefficient += normal_dot / source_mass
        if row_source == column_target:
            coefficient -= normal_dot / target_mass
        return coefficient

    @staticmethod
    def solve_linear_system(matrix, target):
        size = len(target)
        augmented = [
            [float(value) for value in row] + [float(target[index])]
            for index, row in enumerate(matrix)
        ]
        for pivot_index in range(size):
            pivot_row = max(
                range(pivot_index, size),
                key=lambda row_index: abs(augmented[row_index][pivot_index]),
            )
            if abs(augmented[pivot_row][pivot_index]) <= 1.0e-12:
                augmented[pivot_index][pivot_index] += 1.0e-12
                pivot_row = pivot_index
            if pivot_row != pivot_index:
                augmented[pivot_index], augmented[pivot_row] = (
                    augmented[pivot_row],
                    augmented[pivot_index],
                )

            pivot = augmented[pivot_index][pivot_index]
            if abs(pivot) <= 1.0e-24:
                return None
            for column_index in range(pivot_index, size + 1):
                augmented[pivot_index][column_index] /= pivot

            for row_index in range(size):
                if row_index == pivot_index:
                    continue
                factor = augmented[row_index][pivot_index]
                if factor == 0.0:
                    continue
                for column_index in range(pivot_index, size + 1):
                    augmented[row_index][column_index] -= (
                        factor * augmented[pivot_index][column_index]
                    )

        return [augmented[index][size] for index in range(size)]

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
                continue
            particle_index = wall_key[0]
            start_velocity = prediction["start_velocity"]
            predicted_velocity = prediction["predicted_velocity"]
            if particle_index not in combined_velocities:
                combined_velocities[particle_index] = [start_velocity[0], start_velocity[1]]
            combined_velocities[particle_index][0] += predicted_velocity[0] - start_velocity[0]
            combined_velocities[particle_index][1] += predicted_velocity[1] - start_velocity[1]

        if not combined_velocities:
            return None

        return {
            particle_index: (velocity[0], velocity[1])
            for particle_index, velocity in combined_velocities.items()
        }

    def geo_wall_prediction(self, wall_key):
        particle_index, wall_flag = wall_key
        particle = self.particles[particle_index]
        contact = self.wall_ghost_contact(particle, wall_flag, self.walls)
        if contact is None:
            return None

        nx, ny = contact["normal"]
        overlap_area = contact["overlap_area"]
        center_distance = contact["center_distance"]
        normal_velocity = particle["vx"] * nx + particle["vy"] * ny
        phase = "compression" if normal_velocity > 0.0 else "rebound"
        state = self.wall_contact_state.get(wall_key, {})
        state_zero = self.contact_state_zero_velocity_geometry(state)
        if state_zero is not None:
            ghost_particle = contact["ghost_particle"]
            self.update_neo_phase(
                state,
                overlap_area=overlap_area,
                center_distance=center_distance,
                rel_normal_velocity=-2.0 * normal_velocity,
                source_particle=particle,
                target_particle=ghost_particle,
                zero_geometry=state_zero,
                release_at_zero_while_accumulating=False,
            )
            phase = state.get("geo_phase", "rebound")
        elif state.get("geo_phase") != "rebound":
            return None

        prediction = self.geo_contact_prediction(
            particle,
            contact["ghost_particle"],
            (nx, ny, overlap_area, center_distance),
            state,
            source_index=particle_index,
            target_index=("wall", wall_flag),
            phase=phase,
            fixed_target=True,
        )
        if prediction is None:
            return None

        if phase == "rebound":
            prediction["predicted_velocity"] = self.fixed_target_rebound_clamped_velocity(
                prediction["predicted_velocity"],
                (nx, ny),
                prediction["start_velocity"],
                self.geo_rebound_min_fraction,
            )

        current_velocity = (particle["vx"], particle["vy"])
        predicted_normal_velocity = (
            prediction["predicted_velocity"][0] * nx
            + prediction["predicted_velocity"][1] * ny
        )
        current_normal_velocity = current_velocity[0] * nx + current_velocity[1] * ny
        current_tangent_velocity = (
            current_velocity[0] - current_normal_velocity * nx,
            current_velocity[1] - current_normal_velocity * ny,
        )
        prediction["start_velocity"] = current_velocity
        prediction["predicted_velocity"] = (
            current_tangent_velocity[0] + predicted_normal_velocity * nx,
            current_tangent_velocity[1] + predicted_normal_velocity * ny,
        )

        return prediction

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
        if state_zero is not None:
            self.update_neo_phase(
                contact_state,
                overlap_area=_overlap_area,
                center_distance=_center_distance,
                rel_normal_velocity=rel_normal_velocity,
                source_particle=source_particle,
                target_particle=target_particle,
                zero_geometry=state_zero,
                release_at_zero_while_accumulating=True,
            )
            phase = contact_state.get("geo_phase", "rebound")
        elif contact_state.get("geo_phase") != "rebound":
            return None

        return self.geo_contact_prediction(
            source_particle,
            target_particle,
            contact,
            contact_state,
            source_index=source_index,
            target_index=target_index,
            phase=phase,
            fixed_target=False,
        )

    def geo_contact_prediction(
        self,
        source_particle,
        target_particle,
        contact,
        contact_state,
        source_index,
        target_index,
        phase,
        fixed_target=False,
    ):
        nx, ny, overlap_area, center_distance = contact
        state_zero = self.contact_state_zero_velocity_geometry(contact_state)
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
                else contact_state.get("geo_zero_velocity_overlap_area")
            ),
            zero_velocity_center_distance=(
                state_zero["center_distance"]
                if state_zero is not None
                else contact_state.get("geo_zero_velocity_center_distance")
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
        report = neo_model.starting_overlap_report(
            0,
            neo_model.particles[0],
            1,
            neo_model.particles[1],
            (nx, ny, overlap_area, center_distance),
        )
        if report is None:
            return None

        self.update_contact_internal_momentum_report(contact_state, report, phase)

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
            source_velocity, target_velocity = self.new_neo_model().outward_clamped_rebound_velocities(
                source_velocity,
                target_velocity,
                (nx, ny),
                (source_start_vx, source_start_vy),
                (target_start_vx, target_start_vy),
                self.geo_rebound_min_fraction,
            )

        if not fixed_target:
            current_normal_velocity = source_particle["vx"] * nx + source_particle["vy"] * ny
            predicted_normal_velocity = source_velocity[0] * nx + source_velocity[1] * ny
            current_tangent_velocity = (
                source_particle["vx"] - current_normal_velocity * nx,
                source_particle["vy"] - current_normal_velocity * ny,
            )
            source_velocity = (
                current_tangent_velocity[0] + predicted_normal_velocity * nx,
                current_tangent_velocity[1] + predicted_normal_velocity * ny,
            )

        return {
            "start_velocity": (source_start_vx, source_start_vy),
            "predicted_velocity": source_velocity,
        }

    @staticmethod
    def update_contact_internal_momentum_report(contact_state, report, phase):
        zero_momentum = report.get("zero_internal_normal_momentum", 0.0)
        compression_stored = report.get("compression_stored_internal_momentum", 0.0)
        rebound_released = report.get("rebound_released_internal_momentum", 0.0)
        rebound_remaining = report.get("rebound_remaining_internal_momentum", 0.0)

        contact_state["neo_zero_internal_normal_momentum"] = zero_momentum
        contact_state["neo_rebound_released_normal_momentum"] = (
            rebound_released if phase == "rebound" else 0.0
        )
        contact_state["neo_rebound_remaining_normal_momentum"] = (
            rebound_remaining if phase == "rebound" else zero_momentum
        )
        contact_state["neo_stored_internal_normal_momentum"] = (
            rebound_remaining if phase == "rebound" else compression_stored
        )

    @staticmethod
    def fixed_target_rebound_clamped_velocity(
        source_velocity,
        normal,
        source_start_velocity,
        rebound_min_fraction,
    ):
        nx, ny = normal
        incoming_speed = max(0.0, source_start_velocity[0] * nx + source_start_velocity[1] * ny)
        minimum_outward_speed = max(0.0, rebound_min_fraction) * incoming_speed
        predicted_normal_velocity = source_velocity[0] * nx + source_velocity[1] * ny
        if predicted_normal_velocity <= -minimum_outward_speed:
            return source_velocity

        correction = predicted_normal_velocity + minimum_outward_speed
        return (
            source_velocity[0] - correction * nx,
            source_velocity[1] - correction * ny,
        )

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

    @staticmethod
    def neo_internal_normal_momentum(contact_state, source_index, source_particle, normal):
        first_velocities = contact_state.get("first_contact_velocities", {})
        start_velocity = first_velocities.get(source_index)
        if start_velocity is None:
            return 0.0

        nx, ny = normal
        start_normal_momentum = source_particle["mass"] * (
            start_velocity[0] * nx + start_velocity[1] * ny
        )
        current_normal_momentum = source_particle["mass"] * (
            source_particle["vx"] * nx + source_particle["vy"] * ny
        )
        return start_normal_momentum - current_normal_momentum

    @staticmethod
    def accumulate_particle_neo_internal_momentum(particle, internal_momentum, normal):
        nx, ny = normal
        particle["neo_internal_momentum_x"] = particle.get("neo_internal_momentum_x", 0.0) + internal_momentum * nx
        particle["neo_internal_momentum_y"] = particle.get("neo_internal_momentum_y", 0.0) + internal_momentum * ny
        particle["neo_internal_momentum"] = math.hypot(
            particle["neo_internal_momentum_x"],
            particle["neo_internal_momentum_y"],
        )

    def update_neo_internal_momentum_report(self):
        for particle in self.particles:
            particle["neo_internal_momentum_x"] = 0.0
            particle["neo_internal_momentum_y"] = 0.0
            particle["neo_internal_momentum"] = 0.0

        for source_index, source_particle in enumerate(self.particles):
            for slot in range(source_particle.get("sltnum", 0)):
                contact_record = source_particle["ccs"][slot]
                if contact_record.get("clflg", 0) == 0:
                    continue

                target_index = contact_record["pindex"]
                target_particle = self.particles[target_index]
                contact = self.particle_contact(source_particle, target_particle)
                if contact is None:
                    continue

                nx, ny, _overlap_area, _center_distance = contact
                state = self.source_geo_contact_state(source_particle, target_index)
                if state is None:
                    continue

                state["neo_internal_normal_momentum"] = self.neo_internal_normal_momentum(
                    state,
                    source_index,
                    source_particle,
                    (nx, ny),
                )
                self.accumulate_particle_neo_internal_momentum(
                    source_particle,
                    state["neo_internal_normal_momentum"],
                    (nx, ny),
                )

    def update_neo_phase(
        self,
        contact_state,
        overlap_area,
        center_distance,
        rel_normal_velocity,
        source_particle,
        target_particle,
        zero_geometry,
        release_at_zero_while_accumulating=True,
    ):
        mode = self.update_neo_motion_state(
            contact_state,
            overlap_area,
            center_distance,
            rel_normal_velocity,
            release_at_zero_while_accumulating=release_at_zero_while_accumulating,
        )
        if mode != "releasing":
            return

        zero_overlap_area = zero_geometry["overlap_area"]
        zero_tolerance_area = zero_overlap_area * max(0.0, min(1.0, self.zero_velocity_overlap_tolerance))
        crossed_zero = overlap_area >= zero_overlap_area - zero_tolerance_area
        zero_source = "force_law"
        previous_rel_normal_velocity = contact_state.get("last_neo_relative_normal_velocity")
        if (
            not crossed_zero
            and previous_rel_normal_velocity is not None
            and previous_rel_normal_velocity < 0.0
            and rel_normal_velocity >= 0.0
        ):
            crossed_zero = True
            zero_overlap_area = overlap_area
            zero_geometry = {
                "overlap_area": overlap_area,
                "center_distance": center_distance,
            }
            zero_source = "velocity_reversal_promoted_to_current_overlap"
        if not crossed_zero and rel_normal_velocity < 0.0:
            next_distance = center_distance + rel_normal_velocity * getattr(self, "current_step_dt", self.dt)
            next_area = self.circle_overlap_area(
                source_particle["radius"],
                target_particle["radius"],
                next_distance,
            )
            crossed_zero = overlap_area <= zero_overlap_area <= next_area

        if not crossed_zero and mode != "releasing":
            contact_state["geo_phase"] = "compression"
            return
        if not crossed_zero:
            contact_state["geo_phase"] = "rebound"
            return

        contact_state["geo_phase"] = "rebound"
        contact_state["geo_zero_velocity_overlap_area"] = zero_overlap_area
        contact_state["geo_zero_velocity_center_distance"] = zero_geometry["center_distance"]
        contact_state["geo_zero_velocity_source"] = zero_source

    def update_neo_motion_state(
        self,
        contact_state,
        overlap_area,
        center_distance,
        rel_normal_velocity,
        release_at_zero_while_accumulating=True,
    ):
        tolerance = self.neo_velocity_tolerance
        previous_rel_normal_velocity = contact_state.get("last_neo_relative_normal_velocity")
        if rel_normal_velocity < -tolerance:
            mode = "accumulating"
        elif rel_normal_velocity > tolerance:
            mode = "releasing"
        else:
            mode = "blocked"

        zero_overlap_area = contact_state.get("geo_zero_velocity_overlap_area")
        zero_reached = False
        before_zero = False
        if zero_overlap_area is not None:
            zero_tolerance_area = zero_overlap_area * max(0.0, min(1.0, self.zero_velocity_overlap_tolerance))
            zero_reached = overlap_area >= zero_overlap_area - zero_tolerance_area
            before_zero = overlap_area < zero_overlap_area - zero_tolerance_area
            reversed_outward = (
                previous_rel_normal_velocity is not None
                and previous_rel_normal_velocity < -tolerance
                and rel_normal_velocity > tolerance
                and contact_state.get("geo_phase") != "rebound"
            )
            if before_zero and reversed_outward:
                contact_state["geo_zero_velocity_overlap_area"] = overlap_area
                contact_state["geo_zero_velocity_center_distance"] = center_distance
                contact_state["geo_zero_velocity_source"] = "velocity_reversal_promoted_to_current_overlap"
                zero_reached = True

        if zero_reached and (mode != "accumulating" or release_at_zero_while_accumulating):
            mode = "releasing"
            if contact_state.get("geo_zero_velocity_source") is None:
                contact_state["geo_zero_velocity_source"] = contact_state.get(
                    "geo_zero_velocity_solution_source",
                    "force_law",
                )

        contact_state["neo_motion_mode"] = mode

        if mode == "accumulating":
            contact_state["geo_phase"] = "compression"
        elif mode == "releasing":
            contact_state["geo_phase"] = "rebound"
        return mode

    def promote_neo_velocity_reversal_zero(
        self,
        contact_state,
        overlap_area,
        center_distance,
        rel_normal_velocity,
    ):
        if contact_state.get("geo_phase") == "rebound":
            return
        if contact_state.get("geo_zero_velocity_overlap_area") is None:
            return

        previous_rel_normal_velocity = contact_state.get("last_neo_relative_normal_velocity")
        if previous_rel_normal_velocity is None:
            return
        if (
            previous_rel_normal_velocity < 0.0
            and rel_normal_velocity >= 0.0
            and contact_state.get("geo_phase") != "rebound"
        ):
            contact_state["geo_phase"] = "rebound"
            contact_state["geo_zero_velocity_overlap_area"] = overlap_area
            contact_state["geo_zero_velocity_center_distance"] = center_distance
            contact_state["geo_zero_velocity_source"] = "velocity_reversal_promoted_to_current_overlap"

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

    def wall_ghost_contact(self, source_particle, wall_flag, walls):
        if walls is None:
            return None

        x, y = self.current_location(source_particle)
        radius = source_particle["radius"]

        if wall_flag == 1:
            distance_to_wall = x - walls["start_x"]
            nx, ny = -1.0, 0.0
            ghost_x, ghost_y = walls["start_x"], y
        elif wall_flag == 2:
            distance_to_wall = walls["end_x"] - x
            nx, ny = 1.0, 0.0
            ghost_x, ghost_y = walls["end_x"], y
        elif wall_flag == 3:
            distance_to_wall = y - walls["start_y"]
            nx, ny = 0.0, -1.0
            ghost_x, ghost_y = x, walls["start_y"]
        elif wall_flag == 4:
            distance_to_wall = walls["end_y"] - y
            nx, ny = 0.0, 1.0
            ghost_x, ghost_y = x, walls["end_y"]
        else:
            raise ValueError(f"Unknown wall flag: {wall_flag!r}")

        if distance_to_wall >= radius:
            return None

        # The ghost center lives on the wall, but the equal-radius overlap uses
        # the mirrored pair distance so contact begins at one particle radius.
        center_distance = max(0.0, 2.0 * distance_to_wall)
        overlap_area = self.circle_overlap_area(radius, radius, center_distance)
        ghost_particle = self.wall_ghost_particle(
            source_particle,
            ghost_x,
            ghost_y,
            wall_flag,
            (nx, ny),
        )
        return {
            "normal": (nx, ny),
            "overlap_area": overlap_area,
            "center_distance": center_distance,
            "distance_to_wall": distance_to_wall,
            "ghost_particle": ghost_particle,
            "ghost_location": (ghost_x, ghost_y),
        }

    def wall_ghost_particle(self, source_particle, ghost_x, ghost_y, wall_flag, normal):
        return {
            "wall_flag": wall_flag,
            "wall_ghost": True,
            "location": {
                "use": 0,
                "x1": ghost_x,
                "y1": ghost_y,
                "z1": source_particle.get("location", {}).get("z1", 0.0),
                "x2": ghost_x,
                "y2": ghost_y,
                "z2": source_particle.get("location", {}).get("z2", 0.0),
            },
            "vx": 0.0,
            "vy": 0.0,
            "mass": max(source_particle["mass"], 1.0e-12) * self.wall_ghost_mass_multiplier,
            "source_mass": source_particle["mass"],
            "effective_mass": source_particle["mass"],
            "radius": source_particle["radius"],
            "normal": normal,
            "collision_stiffness_q": source_particle.get("collision_stiffness_q"),
        }

    def wall_contact(self, source_particle, wall_flag, walls):
        contact = self.wall_ghost_contact(source_particle, wall_flag, walls)
        if contact is None:
            return None
        nx, ny = contact["normal"]
        return nx, ny, contact["overlap_area"], contact["center_distance"]

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
            particle["neo_internal_momentum_x"] = 0.0
            particle["neo_internal_momentum_y"] = 0.0
            particle["neo_internal_momentum"] = 0.0

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
                            "neo_internal_normal_momentum": 0.0,
                            "last_relative_normal_velocity": rel_normal_velocity,
                            "last_neo_relative_normal_velocity": rel_normal_velocity,
                            "neo_motion_mode": "accumulating",
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
                        self.new_neo_model().particle_zero_velocity_state(
                            source_particle,
                            target_particle,
                            rel_normal_velocity,
                            overlap_area,
                            center_distance,
                        )
                    )
                if (
                    source_particle.get("sltnum", 0) > 1
                    or target_particle.get("sltnum", 0) > 1
                ):
                    state["multi_contact_cluster"] = True
                self.update_neo_motion_state(
                    state,
                    overlap_area,
                    center_distance,
                    rel_normal_velocity,
                    release_at_zero_while_accumulating=True,
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
                state["current_neo_relative_normal_velocity"] = rel_normal_velocity
                state["last_relative_normal_velocity"] = rel_normal_velocity
                state["last_neo_relative_normal_velocity"] = rel_normal_velocity
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
        self.update_neo_internal_momentum_report()

    def update_wall_contact_state(self):
        active_walls = set()
        for particle_index, particle in enumerate(self.particles):
            if not self.is_active_particle(particle):
                continue
            for contact_record in particle.get("bcs", []):
                wall_flag = contact_record.get("clflg", 0)
                if wall_flag == 0:
                    continue

                contact = self.wall_ghost_contact(particle, wall_flag, self.walls)
                if contact is None:
                    continue

                nx, ny = contact["normal"]
                overlap_area = contact["overlap_area"]
                center_distance = contact["center_distance"]
                normal_velocity = particle["vx"] * nx + particle["vy"] * ny
                first_velocity = (particle["vx"], particle["vy"])
                if self.time == 0.0 and normal_velocity < 0.0:
                    first_velocity = (
                        particle["vx"] - 2.0 * normal_velocity * nx,
                        particle["vy"] - 2.0 * normal_velocity * ny,
                    )

                wall_key = (particle_index, wall_flag)
                state = self.wall_contact_state.get(wall_key)
                if state is None:
                    ghost_particle = contact["ghost_particle"]
                    state = {
                        "last_relative_normal_velocity": normal_velocity,
                        "last_neo_relative_normal_velocity": -2.0 * normal_velocity,
                        "neo_motion_mode": "accumulating",
                        "geo_phase": "compression",
                        "first_contact_velocity": first_velocity,
                        "first_contact_velocities": {
                            particle_index: first_velocity,
                            ("wall", wall_flag): (ghost_particle["vx"], ghost_particle["vy"]),
                        },
                        "first_contact_normal": (nx, ny),
                        "first_contact_distance": center_distance,
                        "first_contact_overlap_area": overlap_area,
                        "wall_ghost_location": contact["ghost_location"],
                        "wall_ghost_particle": dict(ghost_particle),
                    }
                    self.wall_contact_state[wall_key] = state
                else:
                    state["wall_ghost_location"] = contact["ghost_location"]
                    state["wall_ghost_particle"] = dict(contact["ghost_particle"])
                if "geo_zero_velocity_overlap_area" not in state:
                    state.update(
                        self.new_neo_model().particle_zero_velocity_state(
                            particle,
                            contact["ghost_particle"],
                            -normal_velocity,
                            overlap_area,
                            center_distance,
                        )
                    )
                wall_rel_normal_velocity = -2.0 * normal_velocity
                self.update_neo_motion_state(
                    state,
                    overlap_area,
                    center_distance,
                    wall_rel_normal_velocity,
                    release_at_zero_while_accumulating=False,
                )
                overlap_contact_momentum = self.overlap_momentum(
                    overlap_area,
                    center_distance,
                    particle,
                )
                state["relative_normal_momentum"] = particle["mass"] * abs(normal_velocity)
                state["overlap_contact_momentum"] = overlap_contact_momentum
                state["current_neo_relative_normal_velocity"] = wall_rel_normal_velocity
                state["last_relative_normal_velocity"] = normal_velocity
                state["last_neo_relative_normal_velocity"] = wall_rel_normal_velocity
                active_walls.add(wall_key)

        exited_wall_contacts = {}
        for wall_key in list(self.wall_contact_state):
            if wall_key not in active_walls:
                particle_index, _wall_flag = wall_key
                exited_wall_contacts.setdefault(particle_index, []).append(
                    (wall_key, self.wall_contact_state[wall_key])
                )

        for particle_index, wall_contacts in exited_wall_contacts.items():
            self.finalize_exited_geo_wall_contacts(particle_index, wall_contacts)
            for wall_key, _state in wall_contacts:
                self.wall_contact_state.pop(wall_key, None)

    def finalize_exited_geo_contact(self, source_index, target_index, state):
        if state.get("geo_phase") != "rebound":
            return

        source_particle = self.particles[source_index]
        target_particle = self.particles[target_index]
        if source_particle.get("sltnum", 0) > 0 or target_particle.get("sltnum", 0) > 0:
            return
        if (
            self.active_geo_contact_state_count(source_particle) > 1
            or self.active_geo_contact_state_count(target_particle) > 1
            or state.get("multi_contact_cluster", False)
        ):
            return

        first_contact_velocities = state.get("first_contact_velocities", {})
        if source_index not in first_contact_velocities or target_index not in first_contact_velocities:
            return
        if "first_contact_normal" not in state:
            return

        source_start_vx, source_start_vy = first_contact_velocities[source_index]
        target_start_vx, target_start_vy = first_contact_velocities[target_index]
        velocities = self.new_neo_model().final_pair_rebound_velocities(
            (source_start_vx, source_start_vy),
            (target_start_vx, target_start_vy),
            source_particle["mass"],
            target_particle["mass"],
            state["first_contact_normal"],
        )
        if velocities is None:
            return

        source_velocity, target_velocity = velocities
        source_velocity = self.velocity_with_current_tangent(
            source_particle,
            source_velocity,
            state["first_contact_normal"],
        )
        target_velocity = self.velocity_with_current_tangent(
            target_particle,
            target_velocity,
            state["first_contact_normal"],
        )
        source_particle["vx"], source_particle["vy"] = source_velocity
        target_particle["vx"], target_particle["vy"] = target_velocity
        self.sync_velocity_mirror(source_particle)
        self.sync_velocity_mirror(target_particle)

    @staticmethod
    def active_geo_contact_state_count(particle):
        return sum(
            1
            for state in particle.get("gcs", [])
            if state.get("active", False)
        )

    def finalize_exited_geo_wall_contact(self, wall_key, state):
        particle_index, _wall_flag = wall_key
        self.finalize_exited_geo_wall_contacts(particle_index, [(wall_key, state)])

    def finalize_exited_geo_wall_contacts(self, particle_index, wall_contacts):
        particle = self.particles[particle_index]
        if self.boundary_contact_count(particle) > 0:
            return

        combined_velocity = None
        applied_rebound = False
        for wall_key, state in wall_contacts:
            if state.get("geo_phase") != "rebound":
                continue
            if "first_contact_velocity" not in state or "first_contact_normal" not in state:
                continue

            _particle_index, wall_flag = wall_key
            start_velocity = state["first_contact_velocity"]
            ghost_particle = state.get("wall_ghost_particle")
            if ghost_particle is None:
                ghost_particle = self.wall_ghost_particle(
                    particle,
                    *state.get("wall_ghost_location", self.current_location(particle)),
                    wall_flag,
                    state["first_contact_normal"],
                )
            ghost_start_velocity = state.get("first_contact_velocities", {}).get(
                ("wall", wall_flag),
                (ghost_particle.get("vx", 0.0), ghost_particle.get("vy", 0.0)),
            )
            velocities = self.new_neo_model().final_pair_rebound_velocities(
                start_velocity,
                ghost_start_velocity,
                particle["mass"],
                ghost_particle["mass"],
                state["first_contact_normal"],
            )
            if velocities is None:
                continue
            velocity, _ghost_velocity = velocities
            velocity = self.velocity_with_current_tangent(
                particle,
                velocity,
                state["first_contact_normal"],
            )

            if combined_velocity is None:
                combined_velocity = [particle["vx"], particle["vy"]]
            current_normal_velocity = (
                combined_velocity[0] * state["first_contact_normal"][0]
                + combined_velocity[1] * state["first_contact_normal"][1]
            )
            predicted_normal_velocity = (
                velocity[0] * state["first_contact_normal"][0]
                + velocity[1] * state["first_contact_normal"][1]
            )
            combined_velocity[0] += (
                predicted_normal_velocity - current_normal_velocity
            ) * state["first_contact_normal"][0]
            combined_velocity[1] += (
                predicted_normal_velocity - current_normal_velocity
            ) * state["first_contact_normal"][1]
            applied_rebound = True

        if not applied_rebound:
            return

        particle["vx"], particle["vy"] = combined_velocity
        self.sync_velocity_mirror(particle)

    @staticmethod
    def velocity_with_current_tangent(particle, predicted_velocity, normal):
        nx, ny = normal
        current_normal_velocity = particle["vx"] * nx + particle["vy"] * ny
        predicted_normal_velocity = predicted_velocity[0] * nx + predicted_velocity[1] * ny
        current_tangent_velocity = (
            particle["vx"] - current_normal_velocity * nx,
            particle["vy"] - current_normal_velocity * ny,
        )
        return (
            current_tangent_velocity[0] + predicted_normal_velocity * nx,
            current_tangent_velocity[1] + predicted_normal_velocity * ny,
        )

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
                    "neo_internal_momentum_x": particle.get("neo_internal_momentum_x", 0.0),
                    "neo_internal_momentum_y": particle.get("neo_internal_momentum_y", 0.0),
                    "neo_internal_momentum": particle.get("neo_internal_momentum", 0.0),
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

