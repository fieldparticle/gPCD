import math


class Dynamics:
    """Collision dynamics kernel for the particle model.

    Base owns particle storage, contact detection, time stepping, and reporting.
    Dynamics owns the math that converts a particle's contact list into momentum
    changes.

    The important parallelization rule is that this class only writes to the
    particle currently being processed. Other particles may be read for current
    position, radius, velocity, and momentum-like state, but this pass must not
    update another particle's memory. That keeps the structure close to a future
    C++ or GLSL kernel where one thread owns one particle.

    Required particle fields:
        location:
            Double-buffered position dictionary:
            {"use": 0 or 1, "x1": ..., "y1": ..., "x2": ..., "y2": ...}
        radius:
            Disk radius. The current overlap-area shortcut assumes every
            particle has the same radius.
        mass:
            Particle mass used when converting momentum into velocity change.
        vx, vy:
            Current velocity components.
        PosLocA, PosLocB:
            GLSL-shaped position buffers mirrored from location.
        VelRad:
            GLSL-shaped velocity mirror. x/y are vx/vy, z is unused for now,
            and w stores the velocity angle in radians.
        Data:
            GLSL-shaped data mirror. x stores particle radius.
        parms:
            GLSL-shaped parameter/result mirror. x stores mass, y/z store
            overlap_momentum_x/y, and w stores scalar overlap momentum sum.
        sltnum:
            Number of valid particle-collision entries in ccs.
        ColFlg:
            1 when this source particle has any active ccs particle collision,
            otherwise 0. Python wall contacts do not make ColFlg shader-ready.
        ccs:
            Fixed-length particle contact list. Active slots have clflg != 0
            and pindex set to the target particle index.
        bcs:
            Python-only boundary contact list for the current wall demos.
            Active slots have clflg != 0, but this is not treated as
            GLSL-ready wall behavior yet.

    Written particle fields:
        overlap_momentum_x, overlap_momentum_y:
            Net collision momentum components computed from this particle's
            current contacts.
        overlap_momentum:
            Scalar sum of contact momentum magnitudes.
        internal_momentum_x, internal_momentum_y, internal_momentum:
            Same vector and magnitude currently used for reporting. Kept as a
            separate name because this is the internal collision response state
            we may want to inspect independently from the applied velocity.
    """

    def __init__(self):
        """Create default coefficients for the overlap momentum model."""
        self.momentum_per_area = 0.001
        self.inverse_square_softening = 1.0

    def process_collisions(self, particles, walls=None):
        """Compute collision momentum for every source particle.

        This is the Python convenience wrapper around the GLSL-shaped unit of
        work, process_source_collision(source_id). Contact detection is assumed
        to be complete before this method runs.

        This method intentionally does not apply the momentum to velocity. It
        only stores the calculated response on the particle. The separate
        apply_overlap_momentum() method performs the velocity update.
        """
        for source_id in range(len(particles)):
            self.process_source_collision(source_id, particles, walls)

    def process_source_collision(self, source_id, particles, walls=None):
        """Process the completed collision list for one source particle.

        This method mirrors the intended GLSL entry point:

            ProcessCollision(uint SourceID)

        It assumes ccs[0:sltnum] has already been filled by collision
        detection. It does not perform broad-phase search, cell lookup, corner
        list traversal, or duplicate filtering.
        """
        source_particle = particles[source_id]
        momentum_x = 0.0
        momentum_y = 0.0
        momentum_sum = 0.0

        for slot in range(source_particle.get("sltnum", 0)):
            contact_record = source_particle["ccs"][slot]
            if contact_record.get("clflg", 0) == 0:
                continue

            contact = self.ccs_contact_geometry(source_particle, contact_record, particles)
            if contact is None:
                continue

            momentum_x, momentum_y, momentum_sum = self.add_contact_momentum(
                source_particle,
                contact,
                momentum_x,
                momentum_y,
                momentum_sum,
            )

        for contact_record in source_particle.get("bcs", []):
            if contact_record.get("clflg", 0) == 0:
                continue

            contact = self.bcs_contact_geometry(source_particle, contact_record, walls)
            if contact is None:
                continue

            momentum_x, momentum_y, momentum_sum = self.add_contact_momentum(
                source_particle,
                contact,
                momentum_x,
                momentum_y,
                momentum_sum,
            )

        source_particle["overlap_momentum_x"] = momentum_x
        source_particle["overlap_momentum_y"] = momentum_y
        source_particle["overlap_momentum"] = momentum_sum
        source_particle["parms"][1] = momentum_x
        source_particle["parms"][2] = momentum_y
        source_particle["parms"][3] = momentum_sum
        source_particle["internal_momentum_x"] = momentum_x
        source_particle["internal_momentum_y"] = momentum_y
        source_particle["internal_momentum"] = math.hypot(momentum_x, momentum_y)

    def apply_overlap_momentum(self, particles):
        """Convert each particle's stored overlap momentum into velocity.

        This is the only place where collision response changes velocity:

            dv = p / m

        The position update is handled by Base before collision processing, so
        this velocity change affects the next Base.step() movement.
        """
        for particle in particles:
            particle["vx"] += particle.get("overlap_momentum_x", 0.0) / particle["mass"]
            particle["vy"] += particle.get("overlap_momentum_y", 0.0) / particle["mass"]
            self.sync_velocity_mirror(particle)

    @staticmethod
    def sync_velocity_mirror(particle):
        """Keep the GLSL-shaped velocity vector aligned with vx/vy."""
        vx = particle["vx"]
        vy = particle["vy"]
        particle["VelRad"][0] = vx
        particle["VelRad"][1] = vy
        particle["VelRad"][3] = math.atan2(vy, vx) if vx != 0.0 or vy != 0.0 else 0.0

    def particle_contact(self, source_particle, target_particle):
        """Return contact geometry for two overlapping source/target disks.

        Returns None when the disks do not overlap.

        When they overlap, returns:

            nx, ny:
                Unit vector from source_particle center to target_particle
                center.
            overlap_area:
                Area of intersection between the two equal-radius disks.
            center_distance:
                Distance between the two particle centers.

        The zero-distance branch chooses an arbitrary normal of (1, 0). That
        avoids division by zero while keeping the response deterministic.
        """
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

        delta = min(radius_sum - center_distance, min(source_radius, target_radius))
        contact_distance = radius_sum - delta
        overlap_area = self.circle_overlap_area(source_radius, target_radius, contact_distance)
        return nx, ny, overlap_area, center_distance

    def add_contact_momentum(self, source_particle, contact, momentum_x, momentum_y, momentum_sum):
        """Accumulate response momentum from one contact geometry tuple."""
        nx, ny, overlap_area, center_distance = contact
        momentum = self.overlap_momentum(
            overlap_area,
            center_distance,
            source_particle,
        )
        # nx, ny points from the source toward the target. The response for the
        # source is in the opposite direction, so subtract it.
        return (
            momentum_x - nx * momentum,
            momentum_y - ny * momentum,
            momentum_sum + momentum,
        )

    def ccs_contact_geometry(self, source_particle, contact_record, particles):
        """Return geometry for one active ccs particle contact record."""
        target_particle = particles[contact_record["pindex"]]
        return self.particle_contact(source_particle, target_particle)

    def bcs_contact_geometry(self, source_particle, contact_record, walls):
        """Return geometry for one active bcs boundary contact record."""
        return self.wall_contact(source_particle, contact_record["clflg"], walls)

    def wall_contact(self, source_particle, wall_flag, walls):
        """Return contact geometry for the current flat wall box.

        This function is intentionally the wall-specific geometry hook. The
        current implementation handles the rectangular wall box, while future
        profiles can return the same nx, ny, overlap_area, distance tuple from
        curved or segmented boundaries.
        """
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
        delta = min(2.0 * radius - center_distance, radius)
        contact_distance = 2.0 * radius - delta
        overlap_area = self.circle_overlap_area(radius, radius, contact_distance)
        return nx, ny, overlap_area, center_distance

    def overlap_momentum(self, overlap_area, center_distance, source_particle):
        """Convert overlap area into a scalar momentum amount.

        This follows the legacy Mom idea: overlap area is the source of a
        momentum amount, not a force integrated through dt. The current formula
        is:

            momentum = momentum_per_area * overlap_area * inverse_square_weight

        source_particle may override momentum_per_area. The target particle is
        not queried for optional configuration so this source-owned calculation
        stays friendly to one-thread-per-particle execution.
        """
        # Legacy Mom model: overlap area is treated as the source of a momentum
        # amount, not as a force that gets multiplied by dt.
        momentum_per_area = source_particle.get(
            "momentum_per_area",
            source_particle.get("repulsion_force_per_area", self.momentum_per_area),
        )
        return momentum_per_area * overlap_area * self.inverse_square_weight(center_distance)

    def inverse_square_weight(self, distance):
        """Return softened inverse-square contact weighting.

        The softening value caps the denominator from below, avoiding singular
        momentum when two particle centers are extremely close or identical.
        """
        softening = max(self.inverse_square_softening, 1.0e-12)
        return 1.0 / max(distance * distance, softening * softening)

    @staticmethod
    def circle_overlap_area(radius_i, radius_j, center_distance):
        """Return the intersection area of two equal-radius disks.

        The simplified code path assumes all particles have the same radius.
        For equal radius r and center distance d, the overlap area is:

            2 r^2 acos(d / 2r) - 0.5 d sqrt(4 r^2 - d^2)

        d is clamped to [0, 2r] so small floating-point drift cannot push the
        formula outside its valid range.
        """
        if abs(radius_i - radius_j) > 1.0e-12:
            raise ValueError("circle_overlap_area currently assumes equal radii.")

        radius = radius_i
        distance = max(0.0, min(2.0 * radius, center_distance))
        return (
            2.0 * radius * radius * math.acos(distance / (2.0 * radius))
            - 0.5 * distance * math.sqrt(max(0.0, 4.0 * radius * radius - distance * distance))
        )

    @staticmethod
    def current_location(particle):
        """Read the active position from a particle's double-buffered location."""
        location = particle["location"]
        if int(location["use"]) == 0:
            return location["x1"], location["y1"]
        return location["x2"], location["y2"]
