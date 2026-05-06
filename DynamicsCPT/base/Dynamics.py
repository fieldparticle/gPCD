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
            {"use": 1 or 2, "x1": ..., "y1": ..., "x2": ..., "y2": ...}
        radius:
            Disk radius. The current overlap-area shortcut assumes every
            particle has the same radius.
        mass:
            Particle mass used when converting momentum into velocity change.
        vx, vy:
            Current velocity components.
        contact_count:
            Number of valid entries in contacts.
        contacts:
            Fixed-length list of contact-particle indices found by
            Base.detect_contacts. The contact-particle array contains all real
            particles plus any wall ghost particles created for this step.

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

    def process_collisions(self, particles, contact_particles=None):
        """Compute collision momentum for each particle from its contacts.

        Base.detect_contacts fills each particle's contact array before this
        method runs. For every particle_i, this method loops only over
        particle_i["contacts"], computes the overlap with each listed
        particle_j, and accumulates the resulting momentum vector into
        particle_i. Contact entries index into contact_particles, which is the
        real particle list plus any wall ghost particles for the current step.

        This method intentionally does not apply the momentum to velocity. It
        only stores the calculated response on the particle. The separate
        apply_overlap_momentum() method performs the velocity update.
        """
        
        if contact_particles is None:
            contact_particles = particles

        #JMB# If contact particles is none then why is it iterating over particles instead 
        # of contact_particles? It seems like it should be iterating over contact_particles instead. 
        # if contact_particles is None then there are no more collisons for this particle and 
        # we should return.
        for particle_i in particles:
            momentum_x = 0.0
            momentum_y = 0.0
            momentum_sum = 0.0

            for slot in range(particle_i["contact_count"]):
                j = particle_i["contacts"][slot]
                if j is None:
                    continue

                particle_j = contact_particles[j]
                contact = self.particle_contact(particle_i, particle_j)
                if contact is None:
                    continue

                nx, ny, overlap_area, center_distance = contact
                momentum = self.overlap_momentum(
                    overlap_area,
                    center_distance,
                    particle_i,
                )
                # nx, ny points from particle_i toward particle_j. The response
                # for particle_i is in the opposite direction, so subtract it.
                momentum_x -= nx * momentum
                momentum_y -= ny * momentum
                momentum_sum += momentum

            particle_i["overlap_momentum_x"] = momentum_x
            particle_i["overlap_momentum_y"] = momentum_y
            particle_i["overlap_momentum"] = momentum_sum
            particle_i["internal_momentum_x"] = momentum_x
            particle_i["internal_momentum_y"] = momentum_y
            particle_i["internal_momentum"] = math.hypot(momentum_x, momentum_y)

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

    def particle_contact(self, particle_i, particle_j):
        """Return contact geometry for two overlapping disks.

        Returns None when the disks do not overlap.

        When they overlap, returns:

            nx, ny:
                Unit vector from particle_i center to particle_j center.
            overlap_area:
                Area of intersection between the two equal-radius disks.
            center_distance:
                Distance between the two particle centers.

        The zero-distance branch chooses an arbitrary normal of (1, 0). That
        avoids division by zero while keeping the response deterministic.
        """
        xi, yi = self.current_location(particle_i)
        xj, yj = self.current_location(particle_j)
        dx = xj - xi
        dy = yj - yi
        center_distance = math.hypot(dx, dy)
        radius_i = particle_i["radius"]
        radius_j = particle_j["radius"]
        radius_sum = radius_i + radius_j
        if center_distance >= radius_sum:
            return None

        if center_distance <= 1.0e-12:
            nx = 1.0
            ny = 0.0
        else:
            nx = dx / center_distance
            ny = dy / center_distance

        delta = min(radius_sum - center_distance, min(radius_i, radius_j))
        contact_distance = radius_sum - delta
        overlap_area = self.circle_overlap_area(radius_i, radius_j, contact_distance)
        return nx, ny, overlap_area, center_distance

    def overlap_momentum(self, overlap_area, center_distance, particle_i):
        """Convert overlap area into a scalar momentum amount.

        This follows the legacy Mom idea: overlap area is the source of a
        momentum amount, not a force integrated through dt. The current formula
        is:

            momentum = momentum_per_area * overlap_area * inverse_square_weight

        particle_i may override momentum_per_area. The other particle is not
        queried for optional configuration so this particle-owned calculation
        stays friendly to one-thread-per-particle execution.
        """
        # Legacy Mom model: overlap area is treated as the source of a momentum
        # amount, not as a force that gets multiplied by dt.
        momentum_per_area = particle_i.get(
            "momentum_per_area",
            particle_i.get("repulsion_force_per_area", self.momentum_per_area),
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
        if int(location["use"]) == 1:
            return location["x1"], location["y1"]
        return location["x2"], location["y2"]
