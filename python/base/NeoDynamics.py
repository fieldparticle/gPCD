import math


class NeoDynamics:
    """Independent force-law geometry collision model.

    NeoDynamics computes the zero-velocity penetration depth from:

        F(alpha) = Q * alpha^2

    The turnaround penetration depth is:

        alpha_0 = ((3 * reduced_mass * v_in^2) / (2 * Q)) ** (1 / 3)

    The zero-velocity overlap area is then A(alpha_0). This class is kept
    independent from GeoDynamics and Dynamics so changes to either older model
    cannot alter the Neo report path.
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

        source_current_rebound_vx = source_turn_vx + rebound_velocity_fraction * (
            source_rebound_vx - source_turn_vx
        )
        source_current_rebound_vy = source_turn_vy + rebound_velocity_fraction * (
            source_rebound_vy - source_turn_vy
        )
        target_current_rebound_vx = target_turn_vx + rebound_velocity_fraction * (
            target_rebound_vx - target_turn_vx
        )
        target_current_rebound_vy = target_turn_vy + rebound_velocity_fraction * (
            target_rebound_vy - target_turn_vy
        )

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
