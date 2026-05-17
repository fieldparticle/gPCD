import math


class GeoDynamics:
    """Pair-level geometry collision model.

    This class is intentionally separate from Base/Dynamics. It is for testing
    the starting-overlap model from Rules.txt:

    - cfg velocity is the incoming velocity at starting contact.
    - if t=0 is overlapped, the pair is treated as rebound phase.
    - the reported rebound velocity is the velocity implied by the incoming
      relative normal momentum at the current overlap geometry.

    It does not step the simulation. It builds diagnostics from the current
    particle geometry.
    """

    POSITION_BUFFER_A = 0
    POSITION_BUFFER_B = 1

    def __init__(self):
        self.particle_configs = []
        self.particles = []
        self.contact_reports = []
        self.momentum_per_area = 0.001
        self.inverse_square_softening = 1.0

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
            zero_geometry["overlap_momentum"] = float(
                source_particle.get("zero_velocity_overlap_momentum", zero_geometry["overlap_momentum"])
            )
            zero_geometry["solution_clamped"] = False
            zero_geometry["solution_source"] = "provided"
        else:
            zero_geometry["solution_source"] = "solved"
        if zero_geometry["overlap_area"] + 1.0e-12 < overlap_area:
            zero_geometry = dict(zero_geometry)
            zero_geometry["center_distance"] = center_distance
            zero_geometry["overlap_area"] = overlap_area
            zero_geometry["overlap_momentum"] = self.overlap_momentum_at_distance(
                center_distance,
                source_particle,
                target_particle,
            )
            zero_geometry["solution_clamped"] = True
            zero_geometry["solution_source"] = "promoted_to_current_overlap"
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

        source_current_rebound_vx = source_turn_vx + rebound_velocity_fraction * (source_rebound_vx - source_turn_vx)
        source_current_rebound_vy = source_turn_vy + rebound_velocity_fraction * (source_rebound_vy - source_turn_vy)
        target_current_rebound_vx = target_turn_vx + rebound_velocity_fraction * (target_rebound_vx - target_turn_vx)
        target_current_rebound_vy = target_turn_vy + rebound_velocity_fraction * (target_rebound_vy - target_turn_vy)

        return {
            "source_index": source_index,
            "target_index": target_index,
            "phase_assumption": "rebound" if center_distance < source_particle["radius"] + target_particle["radius"] else "contact",
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
            "zero_velocity_solution_clamped": zero_geometry["solution_clamped"],
            "zero_velocity_solution_source": zero_geometry["solution_source"],
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
        radius_sum = source_particle["radius"] + target_particle["radius"]
        if incoming_relative_normal_momentum <= 0.0:
            return {
                "center_distance": radius_sum,
                "overlap_area": 0.0,
                "overlap_momentum": 0.0,
                "solution_clamped": False,
            }

        max_momentum = self.overlap_momentum_at_distance(0.0, source_particle, target_particle)
        if incoming_relative_normal_momentum >= max_momentum:
            return {
                "center_distance": 0.0,
                "overlap_area": self.circle_overlap_area(source_particle["radius"], target_particle["radius"], 0.0),
                "overlap_momentum": max_momentum,
                "solution_clamped": True,
            }

        lo = 0.0
        hi = radius_sum
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            mid_momentum = self.overlap_momentum_at_distance(mid, source_particle, target_particle)
            if mid_momentum < incoming_relative_normal_momentum:
                hi = mid
            else:
                lo = mid

        center_distance = 0.5 * (lo + hi)
        overlap_area = self.circle_overlap_area(
            source_particle["radius"],
            target_particle["radius"],
            center_distance,
        )
        return {
            "center_distance": center_distance,
            "overlap_area": overlap_area,
            "overlap_momentum": self.overlap_momentum_at_distance(center_distance, source_particle, target_particle),
            "solution_clamped": False,
        }

    def overlap_momentum_at_distance(self, center_distance, source_particle, target_particle):
        overlap_area = self.circle_overlap_area(
            source_particle["radius"],
            target_particle["radius"],
            center_distance,
        )
        momentum_per_area = source_particle.get(
            "momentum_per_area",
            source_particle.get("repulsion_force_per_area", self.momentum_per_area),
        )
        if momentum_per_area is None:
            momentum_per_area = source_particle.get("repulsion_force_per_area", self.momentum_per_area)
        if momentum_per_area is None:
            momentum_per_area = self.momentum_per_area
        return momentum_per_area * overlap_area * self.inverse_square_weight(center_distance)

    def inverse_square_weight(self, distance):
        softening = max(self.inverse_square_softening, 1.0e-12)
        return 1.0 / max(distance * distance, softening * softening)

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

    @staticmethod
    def normalized_location(location):
        location = dict(location)
        use = int(location["use"])
        if use not in (GeoDynamics.POSITION_BUFFER_A, GeoDynamics.POSITION_BUFFER_B):
            raise ValueError(f"Unknown position buffer: {location['use']!r}")
        location["use"] = use
        if "x2" not in location and "x1" in location:
            location["x2"] = location["x1"]
        if "y2" not in location and "y1" in location:
            location["y2"] = location["y1"]
        return location

    @staticmethod
    def current_location(particle):
        location = particle["location"]
        if int(location["use"]) == GeoDynamics.POSITION_BUFFER_A:
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
