import math


class NeoDynamics:
    """Independent force-law geometry collision model.

    NeoDynamics computes the zero-velocity penetration depth from:

        F(alpha) = Q * alpha^2

    The turnaround penetration depth is:

        alpha_0 = ((3 * reduced_mass * v_in^2) / (2 * Q)) ** (1 / 3)

    The zero-velocity overlap area is then A(alpha_0). This class is kept
    independent from the retired collision models so changes to old code cannot
    alter the Neo report path.
    """

    POSITION_BUFFER_A = 0
    POSITION_BUFFER_B = 1

    def __init__(self):
        self.particle_configs = []
        self.particles = []
        self.contact_reports = []
        self.momentum_per_area = 0.001
        self.inverse_square_softening = 1.0
        self.collision_stiffness_q = 1.0

    def clear_particles(self):
        self.particle_configs = []
        self.particles = []
        self.contact_reports = []

    def add_particle(self, vx, vy, mass, radius, location=None, x=None, y=None, **display):
        if location is None:
            if x is None or y is None:
                raise ValueError("Particle requires either location or x/y.")
            location = {
                "use": self.POSITION_BUFFER_A,
                "x1": float(x),
                "y1": float(y),
                "x2": float(x),
                "y2": float(y),
            }

        self.particle_configs.append(
            {
                "vx": float(vx),
                "vy": float(vy),
                "mass": float(mass),
                "radius": float(radius),
                "location": self.normalized_location(location),
                **display,
            }
        )

    def reset(self):
        self.particles = []
        self.contact_reports = []
        for config in self.particle_configs:
            particle = dict(config)
            particle["location"] = dict(particle["location"])
            starting_vx = particle.get("velocity_at_starting_contact_x", particle["vx"])
            starting_vy = particle.get("velocity_at_starting_contact_y", particle["vy"])
            particle["velocity_at_starting_contact_x"] = starting_vx
            particle["velocity_at_starting_contact_y"] = starting_vy
            particle["starting_momentum_x"] = particle["mass"] * starting_vx
            particle["starting_momentum_y"] = particle["mass"] * starting_vy
            particle["starting_momentum"] = particle["mass"] * math.hypot(starting_vx, starting_vy)
            self.particles.append(particle)

        self.contact_reports = self.starting_overlap_reports()
        self.apply_rebound_report_velocities()

    def starting_overlap_reports(self):
        reports = []
        for source_index, source_particle in enumerate(self.particles):
            for target_index, target_particle in enumerate(self.particles):
                if source_index == target_index:
                    continue

                contact = self.particle_contact(source_particle, target_particle)
                if contact is None:
                    continue

                reports.append(
                    self.starting_overlap_report(
                        source_index,
                        source_particle,
                        target_index,
                        target_particle,
                        contact,
                    )
                )
        return reports

    def starting_overlap_report(self, source_index, source_particle, target_index, target_particle, contact):
        nx, ny, overlap_area, center_distance = contact
        source_vx = source_particle["velocity_at_starting_contact_x"]
        source_vy = source_particle["velocity_at_starting_contact_y"]
        target_vx = target_particle["velocity_at_starting_contact_x"]
        target_vy = target_particle["velocity_at_starting_contact_y"]
        source_mass = source_particle["mass"]
        target_mass = target_particle["mass"]

        rel_vx = target_vx - source_vx
        rel_vy = target_vy - source_vy
        rel_normal_velocity = rel_vx * nx + rel_vy * ny
        reduced_mass = (source_mass * target_mass) / (source_mass + target_mass)

        incoming_relative_normal_momentum = max(0.0, -reduced_mass * rel_normal_velocity)
        zero_geometry = self.zero_velocity_overlap_geometry(
            incoming_relative_normal_momentum,
            source_particle,
            target_particle,
        )
        if source_particle.get("zero_velocity_overlap_area") is not None:
            zero_geometry = dict(zero_geometry)
            zero_geometry["overlap_area"] = float(source_particle["zero_velocity_overlap_area"])
            zero_geometry["center_distance"] = float(
                source_particle.get("zero_velocity_center_distance", zero_geometry["center_distance"])
            )
            zero_geometry["overlap_momentum"] = incoming_relative_normal_momentum
            zero_geometry["penetration_depth"] = max(
                0.0,
                source_particle["radius"] + target_particle["radius"] - zero_geometry["center_distance"],
            )
            max_overlap_area = self.circle_overlap_area(
                source_particle["radius"],
                target_particle["radius"],
                0.0,
            )
            zero_geometry["overlap_fraction"] = (
                zero_geometry["overlap_area"] / max_overlap_area
                if max_overlap_area > 0.0
                else 0.0
            )
            zero_geometry["solution_clamped"] = False
            zero_geometry["solution_source"] = "stored_contact_state"

        if zero_geometry["overlap_area"] + 1.0e-12 < overlap_area:
            zero_geometry = dict(zero_geometry)
            zero_geometry["center_distance"] = center_distance
            zero_geometry["overlap_area"] = overlap_area
            zero_geometry["overlap_momentum"] = incoming_relative_normal_momentum
            zero_geometry["penetration_depth"] = max(
                0.0,
                source_particle["radius"] + target_particle["radius"] - center_distance,
            )
            zero_geometry["solution_clamped"] = True
            zero_geometry["solution_source"] = "force_law_promoted_to_current_overlap"

        zero_overlap_area = zero_geometry["overlap_area"]
        if zero_overlap_area > 1.0e-12:
            compression_fraction = overlap_area / zero_overlap_area
            compression_fraction = max(0.0, min(1.0, compression_fraction))
            rebound_fraction = 1.0 - compression_fraction
            rebound_fraction = max(0.0, min(1.0, rebound_fraction))
        else:
            compression_fraction = 0.0
            rebound_fraction = 0.0

        compression_velocity_fraction = math.sqrt(max(0.0, 1.0 - compression_fraction))
        compression_progress = 1.0 - compression_velocity_fraction
        rebound_velocity_fraction = math.sqrt(rebound_fraction)

        turn_impulse = incoming_relative_normal_momentum
        rebound_impulse = 2.0 * incoming_relative_normal_momentum
        zero_internal_normal_momentum = incoming_relative_normal_momentum
        compression_stored_internal_momentum = zero_internal_normal_momentum * compression_progress
        rebound_released_internal_momentum = zero_internal_normal_momentum * rebound_velocity_fraction
        rebound_remaining_internal_momentum = max(
            0.0,
            zero_internal_normal_momentum - rebound_released_internal_momentum,
        )

        source_turn_vx = source_vx - (turn_impulse / source_mass) * nx
        source_turn_vy = source_vy - (turn_impulse / source_mass) * ny
        target_turn_vx = target_vx + (turn_impulse / target_mass) * nx
        target_turn_vy = target_vy + (turn_impulse / target_mass) * ny

        source_compression_vx = source_vx + compression_progress * (source_turn_vx - source_vx)
        source_compression_vy = source_vy + compression_progress * (source_turn_vy - source_vy)
        target_compression_vx = target_vx + compression_progress * (target_turn_vx - target_vx)
        target_compression_vy = target_vy + compression_progress * (target_turn_vy - target_vy)

        source_rebound_vx = source_vx - (rebound_impulse / source_mass) * nx
        source_rebound_vy = source_vy - (rebound_impulse / source_mass) * ny
        target_rebound_vx = target_vx + (rebound_impulse / target_mass) * nx
        target_rebound_vy = target_vy + (rebound_impulse / target_mass) * ny

        source_current_rebound_vx = source_turn_vx - (
            rebound_released_internal_momentum / source_mass
        ) * nx
        source_current_rebound_vy = source_turn_vy - (
            rebound_released_internal_momentum / source_mass
        ) * ny
        target_current_rebound_vx = target_turn_vx + (
            rebound_released_internal_momentum / target_mass
        ) * nx
        target_current_rebound_vy = target_turn_vy + (
            rebound_released_internal_momentum / target_mass
        ) * ny

        return {
            "source_index": source_index,
            "target_index": target_index,
            "phase_assumption": "rebound"
            if center_distance < source_particle["radius"] + target_particle["radius"]
            else "contact",
            "center_distance": center_distance,
            "overlap_area": overlap_area,
            "normal_x": nx,
            "normal_y": ny,
            "relative_normal_velocity_at_starting_contact": rel_normal_velocity,
            "reduced_mass": reduced_mass,
            "incoming_relative_normal_momentum": incoming_relative_normal_momentum,
            "zero_velocity_center_distance": zero_geometry["center_distance"],
            "zero_velocity_overlap_area": zero_overlap_area,
            "zero_velocity_overlap_momentum": zero_geometry["overlap_momentum"],
            "zero_velocity_penetration_depth": zero_geometry["penetration_depth"],
            "zero_velocity_overlap_fraction": zero_geometry["overlap_fraction"],
            "zero_velocity_solution_clamped": zero_geometry["solution_clamped"],
            "zero_velocity_solution_source": zero_geometry["solution_source"],
            "zero_velocity_stiffness_q": zero_geometry["stiffness_q"],
            "zero_velocity_incoming_speed": zero_geometry["incoming_speed"],
            "compression_fraction": compression_fraction,
            "rebound_fraction": rebound_fraction,
            "compression_velocity_fraction": compression_velocity_fraction,
            "compression_progress": compression_progress,
            "rebound_velocity_fraction": rebound_velocity_fraction,
            "turn_impulse": turn_impulse,
            "rebound_impulse": rebound_impulse,
            "zero_internal_normal_momentum": zero_internal_normal_momentum,
            "compression_stored_internal_momentum": compression_stored_internal_momentum,
            "rebound_released_internal_momentum": rebound_released_internal_momentum,
            "rebound_remaining_internal_momentum": rebound_remaining_internal_momentum,
            "source_velocity_at_starting_contact_x": source_vx,
            "source_velocity_at_starting_contact_y": source_vy,
            "target_velocity_at_starting_contact_x": target_vx,
            "target_velocity_at_starting_contact_y": target_vy,
            "source_velocity_at_zero_velocity_point_x": source_turn_vx,
            "source_velocity_at_zero_velocity_point_y": source_turn_vy,
            "target_velocity_at_zero_velocity_point_x": target_turn_vx,
            "target_velocity_at_zero_velocity_point_y": target_turn_vy,
            "source_velocity_at_current_overlap_compression_x": source_compression_vx,
            "source_velocity_at_current_overlap_compression_y": source_compression_vy,
            "target_velocity_at_current_overlap_compression_x": target_compression_vx,
            "target_velocity_at_current_overlap_compression_y": target_compression_vy,
            "source_velocity_at_full_rebound_x": source_rebound_vx,
            "source_velocity_at_full_rebound_y": source_rebound_vy,
            "target_velocity_at_full_rebound_x": target_rebound_vx,
            "target_velocity_at_full_rebound_y": target_rebound_vy,
            "source_velocity_at_current_overlap_rebound_x": source_current_rebound_vx,
            "source_velocity_at_current_overlap_rebound_y": source_current_rebound_vy,
            "target_velocity_at_current_overlap_rebound_x": target_current_rebound_vx,
            "target_velocity_at_current_overlap_rebound_y": target_current_rebound_vy,
        }

    def zero_velocity_overlap_geometry(self, incoming_relative_normal_momentum, source_particle, target_particle):
        source_vx = source_particle["velocity_at_starting_contact_x"]
        source_vy = source_particle["velocity_at_starting_contact_y"]
        target_vx = target_particle["velocity_at_starting_contact_x"]
        target_vy = target_particle["velocity_at_starting_contact_y"]
        contact = self.particle_contact(source_particle, target_particle)
        radius_sum = source_particle["radius"] + target_particle["radius"]
        max_overlap_area = self.circle_overlap_area(source_particle["radius"], target_particle["radius"], 0.0)

        if contact is None:
            return {
                "center_distance": radius_sum,
                "overlap_area": 0.0,
                "overlap_momentum": 0.0,
                "penetration_depth": 0.0,
                "overlap_fraction": 0.0,
                "solution_clamped": False,
                "solution_source": "force_law_no_contact",
                "stiffness_q": self.contact_stiffness_q(source_particle, target_particle),
                "incoming_speed": 0.0,
            }

        nx, ny, _overlap_area, _center_distance = contact
        rel_vx = target_vx - source_vx
        rel_vy = target_vy - source_vy
        incoming_speed = max(0.0, -(rel_vx * nx + rel_vy * ny))
        source_mass = source_particle["mass"]
        target_mass = target_particle["mass"]
        reduced_mass = (source_mass * target_mass) / (source_mass + target_mass)
        stiffness_q = self.contact_stiffness_q(source_particle, target_particle)

        if incoming_speed <= 0.0:
            return {
                "center_distance": radius_sum,
                "overlap_area": 0.0,
                "overlap_momentum": 0.0,
                "penetration_depth": 0.0,
                "overlap_fraction": 0.0,
                "solution_clamped": False,
                "solution_source": "force_law_zero_speed",
                "stiffness_q": stiffness_q,
                "incoming_speed": incoming_speed,
            }

        alpha_zero = ((3.0 * reduced_mass * incoming_speed * incoming_speed) / (2.0 * stiffness_q)) ** (1.0 / 3.0)
        alpha_zero = max(0.0, min(radius_sum, alpha_zero))
        center_distance = max(0.0, radius_sum - alpha_zero)
        overlap_area = self.circle_overlap_area(source_particle["radius"], target_particle["radius"], center_distance)
        return {
            "center_distance": center_distance,
            "overlap_area": overlap_area,
            "overlap_momentum": incoming_relative_normal_momentum,
            "penetration_depth": alpha_zero,
            "overlap_fraction": overlap_area / max_overlap_area if max_overlap_area > 0.0 else 0.0,
            "solution_clamped": alpha_zero >= radius_sum,
            "solution_source": "force_law",
            "stiffness_q": stiffness_q,
            "incoming_speed": incoming_speed,
        }

    def contact_stiffness_q(self, source_particle, target_particle):
        source_q = source_particle.get("collision_stiffness_q", self.collision_stiffness_q)
        target_q = target_particle.get("collision_stiffness_q", self.collision_stiffness_q)
        if source_q is None:
            source_q = self.collision_stiffness_q
        if target_q is None:
            target_q = self.collision_stiffness_q
        return max(1.0e-12, 0.5 * (float(source_q) + float(target_q)))

    def particle_zero_velocity_state(
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
            alpha_zero = ((3.0 * reduced_mass * incoming_speed * incoming_speed) / (2.0 * stiffness_q)) ** (
                1.0 / 3.0
            )
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

        return self.zero_state_dict(
            zero_overlap_area,
            zero_center_distance,
            alpha_zero,
            max_overlap_area,
            solution_source,
            stiffness_q,
            reduced_mass,
            incoming_speed,
        )

    def wall_zero_velocity_state(
        self,
        particle,
        normal_velocity,
        current_overlap_area,
        current_center_distance,
    ):
        incoming_speed = max(0.0, normal_velocity)
        stiffness_q = max(1.0e-12, float(particle.get("collision_stiffness_q", self.collision_stiffness_q)))
        radius = particle["radius"]
        max_overlap_area = self.circle_overlap_area(radius, radius, 0.0)

        if incoming_speed <= 0.0:
            zero_center_distance = 2.0 * radius
            zero_overlap_area = 0.0
            alpha_zero = 0.0
            solution_source = "force_law_zero_speed"
        else:
            alpha_zero = ((3.0 * particle["mass"] * incoming_speed * incoming_speed) / (2.0 * stiffness_q)) ** (
                1.0 / 3.0
            )
            alpha_zero = max(0.0, min(2.0 * radius, alpha_zero))
            zero_center_distance = max(0.0, 2.0 * radius - alpha_zero)
            zero_overlap_area = self.circle_overlap_area(radius, radius, zero_center_distance)
            solution_source = "force_law_wall"

        if zero_overlap_area + 1.0e-12 < current_overlap_area:
            zero_overlap_area = current_overlap_area
            zero_center_distance = current_center_distance
            alpha_zero = max(0.0, 2.0 * radius - current_center_distance)
            solution_source = "force_law_wall_promoted_to_current_overlap"

        return self.zero_state_dict(
            zero_overlap_area,
            zero_center_distance,
            alpha_zero,
            max_overlap_area,
            solution_source,
            stiffness_q,
            particle["mass"],
            incoming_speed,
        )

    @staticmethod
    def zero_state_dict(
        zero_overlap_area,
        zero_center_distance,
        alpha_zero,
        max_overlap_area,
        solution_source,
        stiffness_q,
        reduced_mass,
        incoming_speed,
    ):
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

    @staticmethod
    def apply_internal_contact_momentum_feedback(
        source_particle,
        target_particle,
        contact_state,
        source_velocity,
        normal,
    ):
        internal_momentum = contact_state.get("internal_contact_momentum", 0.0)
        if internal_momentum <= 0.0:
            return source_velocity

        source_mass = source_particle.get("mass", 0.0)
        target_mass = target_particle.get("mass", 0.0)
        total_mass = source_mass + target_mass
        if total_mass <= 0.0:
            return source_velocity

        reduced_mass = (source_mass * target_mass) / total_mass
        if reduced_mass <= 0.0:
            return source_velocity

        delta_velocity = internal_momentum / reduced_mass
        nx, ny = normal

        return (
            source_velocity[0] - delta_velocity * nx,
            source_velocity[1] - delta_velocity * ny,
        )

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

    @staticmethod
    def outward_escape_velocities(
        source_velocity,
        target_velocity,
        normal,
        source_start_velocity,
        target_start_velocity,
        escape_fraction,
    ):
        nx, ny = normal
        rel_vx = target_velocity[0] - source_velocity[0]
        rel_vy = target_velocity[1] - source_velocity[1]
        rel_normal_velocity = rel_vx * nx + rel_vy * ny

        start_rel_vx = target_start_velocity[0] - source_start_velocity[0]
        start_rel_vy = target_start_velocity[1] - source_start_velocity[1]
        start_closing_speed = max(0.0, -(start_rel_vx * nx + start_rel_vy * ny))
        minimum_outward_speed = max(0.0, escape_fraction) * start_closing_speed
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

    @staticmethod
    def final_pair_rebound_velocities(
        source_start_velocity,
        target_start_velocity,
        source_mass,
        target_mass,
        normal,
    ):
        nx, ny = normal
        source_start_vx, source_start_vy = source_start_velocity
        target_start_vx, target_start_vy = target_start_velocity
        reduced_mass = (source_mass * target_mass) / (source_mass + target_mass)
        start_rel_vx = target_start_vx - source_start_vx
        start_rel_vy = target_start_vy - source_start_vy
        incoming_relative_normal_momentum = max(0.0, -reduced_mass * (start_rel_vx * nx + start_rel_vy * ny))
        if incoming_relative_normal_momentum <= 0.0:
            return None

        rebound_impulse = 2.0 * incoming_relative_normal_momentum
        return (
            (
                source_start_vx - (rebound_impulse / source_mass) * nx,
                source_start_vy - (rebound_impulse / source_mass) * ny,
            ),
            (
                target_start_vx + (rebound_impulse / target_mass) * nx,
                target_start_vy + (rebound_impulse / target_mass) * ny,
            ),
        )

    @staticmethod
    def final_wall_rebound_velocity(start_velocity, normal):
        start_vx, start_vy = start_velocity
        nx, ny = normal
        incoming_speed = start_vx * nx + start_vy * ny
        if incoming_speed <= 0.0:
            return None
        return (
            start_vx - 2.0 * incoming_speed * nx,
            start_vy - 2.0 * incoming_speed * ny,
        )

    def apply_rebound_report_velocities(self):
        for particle in self.particles:
            particle["velocity_at_current_overlap_rebound_x"] = particle["vx"]
            particle["velocity_at_current_overlap_rebound_y"] = particle["vy"]

        for report in self.contact_reports:
            source_particle = self.particles[report["source_index"]]
            source_particle["velocity_at_current_overlap_rebound_x"] = report[
                "source_velocity_at_current_overlap_rebound_x"
            ]
            source_particle["velocity_at_current_overlap_rebound_y"] = report[
                "source_velocity_at_current_overlap_rebound_y"
            ]

    def particle_contact(self, source_particle, target_particle):
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

    @classmethod
    def normalized_location(cls, location):
        location = dict(location)
        use = int(location["use"])
        if use not in (cls.POSITION_BUFFER_A, cls.POSITION_BUFFER_B):
            raise ValueError(f"Unknown position buffer: {location['use']!r}")
        location["use"] = use
        if "x2" not in location and "x1" in location:
            location["x2"] = location["x1"]
        if "y2" not in location and "y1" in location:
            location["y2"] = location["y1"]
        return location

    @classmethod
    def current_location(cls, particle):
        location = particle["location"]
        if int(location["use"]) == cls.POSITION_BUFFER_A:
            return location["x1"], location["y1"]
        return location["x2"], location["y2"]

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
