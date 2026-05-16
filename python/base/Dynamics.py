import math
import random


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
        momentum_delta_x, momentum_delta_y:
            Per-step vector momentum change caused by the stored overlap
            momentum. Contact-level internal state owns unresolved collision
            storage.
    """

    def __init__(self):
        """Create default coefficients for the overlap momentum model."""
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
        self.escape_mode = 0

    ESCAPE_MODE_RESERVOIR = 0
    ESCAPE_MODE_ESCAPED = 1
    ESCAPE_MODE_RETAINED = 2

    STATE_RESERVOIR = 0
    STATE_ACTIVE = 1
    STATE_ESCAPED = 2
    STATE_RETAINED = 3

    def configure_flow(self, config):
        """Load optional reservoir/periodic/open-boundary dynamics settings."""
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
        """Apply non-collision lifecycle work before contact detection."""
        if self.flow_type in ("pipe_reservoir_entry", "reservoir_release"):
            self.release_from_reservoir(particles, dt, set_location)

    def end_step(self, particles, set_location):
        """Apply boundary lifecycle work after particle motion."""
        if self.flow_type == "periodic":
            self.apply_periodic_boundary(particles, set_location)
        elif self.flow_type in ("pipe_reservoir_entry", "reservoir_release", "open_escape"):
            self.apply_outlet_boundary(particles, set_location)

    def release_from_reservoir(self, particles, dt, set_location):
        """Activate inactive particles at the configured inlet rate."""
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
            if not self.is_active_particle(particles[source_id]):
                continue
            self.process_source_collision(source_id, particles, walls)

    def resolve_starting_collisions(self, particles):
        """Record reset-time collision correction diagnostics.

        Some tests intentionally begin with overlapping particles. At reset
        time, process_collisions() has already computed the instantaneous
        overlap momentum for that starting geometry. For now this method only
        reports what the velocity would be after applying that overlap
        momentum; it does not alter the live dynamics velocity.
        """
        for particle in particles:
            if not self.is_active_particle(particle):
                continue

            uncorrected_vx = particle["vx"]
            uncorrected_vy = particle["vy"]
            overlap_momentum_x = particle.get("overlap_momentum_x", 0.0)
            overlap_momentum_y = particle.get("overlap_momentum_y", 0.0)
            corrected_vx = uncorrected_vx + overlap_momentum_x / particle["mass"]
            corrected_vy = uncorrected_vy + overlap_momentum_y / particle["mass"]

            linear_momentum_x = particle["mass"] * particle["vx"]
            linear_momentum_y = particle["mass"] * particle["vy"]
            particle["starting_momentum_x"] = linear_momentum_x
            particle["starting_momentum_y"] = linear_momentum_y
            particle["starting_momentum"] = math.hypot(linear_momentum_x, linear_momentum_y)
            particle["starting_uncorrected_vx"] = uncorrected_vx
            particle["starting_uncorrected_vy"] = uncorrected_vy
            particle["starting_corrected_vx"] = corrected_vx
            particle["starting_corrected_vy"] = corrected_vy
            particle["starting_velocity_correction_x"] = corrected_vx - uncorrected_vx
            particle["starting_velocity_correction_y"] = corrected_vy - uncorrected_vy
            particle["starting_uncorrected_speed"] = math.hypot(uncorrected_vx, uncorrected_vy)
            particle["starting_corrected_speed"] = math.hypot(corrected_vx, corrected_vy)
            particle["internal_momentum_x"] = 0.0
            particle["internal_momentum_y"] = 0.0
            particle["internal_momentum"] = 0.0
            particle["momentum_delta_x"] = 0.0
            particle["momentum_delta_y"] = 0.0
            particle["momentum_delta"] = 0.0

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

    def apply_overlap_momentum(self, particles):
        """Convert each particle's stored overlap momentum into velocity.

        This is the only place where collision response changes velocity:

            dv = p / m

        The position update is handled by Base before collision processing, so
        this velocity change affects the next Base.step() movement.
        """
        for particle in particles:
            if not self.is_active_particle(particle):
                continue
            overlap_momentum_x = particle.get("overlap_momentum_x", 0.0)
            overlap_momentum_y = particle.get("overlap_momentum_y", 0.0)
            old_momentum_x = particle["mass"] * particle["vx"]
            old_momentum_y = particle["mass"] * particle["vy"]
            candidate_vx = particle["vx"] + overlap_momentum_x / particle["mass"]
            candidate_vy = particle["vy"] + overlap_momentum_y / particle["mass"]

            particle["vx"] = candidate_vx
            particle["vy"] = candidate_vy
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

    @staticmethod
    def sync_velocity_mirror(particle):
        """Keep the GLSL-shaped velocity vector aligned with vx/vy."""
        vx = particle["vx"]
        vy = particle["vy"]
        particle["VelRad"][0] = vx
        particle["VelRad"][1] = vy
        particle["VelRad"][3] = math.atan2(vy, vx) if vx != 0.0 or vy != 0.0 else 0.0

    @staticmethod
    def velocity_direction(particle):
        speed = math.hypot(particle["vx"], particle["vy"])
        if speed <= 1.0e-12:
            return 0.0, 0.0
        return particle["vx"] / speed, particle["vy"] / speed

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
        if not self.is_active_particle(source_particle) or not self.is_active_particle(target_particle):
            return None
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
