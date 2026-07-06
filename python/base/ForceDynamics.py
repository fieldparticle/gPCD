import math
import itertools

from gbase.ParametricCurve import closest_point
from gbase.ParametricCurve import evaluate_tangent


class ForceContactDynamics:
    """Apply overlap-area central forces through a source-owned linear chain."""

    EPSILON = 1.0e-12
    CONTACT_PARTICLE = 1
    CONTACT_WALL = 2
    CONTACT_ACTIVE_THIS_FRAME = 1
    MAXIMUM_PENETRATION_FRACTION = 0.5
    BOUNDARY_EVALUATOR_PARAMETRIC = 5

    @staticmethod
    def VelocityAngle(vx, vy):
        """Return the GLSL VelRad.w velocity angle for an xy velocity."""
        return math.atan2(vy, vx) if vx != 0.0 or vy != 0.0 else 0.0

    @staticmethod
    def particle_position(particle, positionBuffer):
        """Return the currently selected position buffer for one particle."""
        if int(positionBuffer) == 0:
            return particle.PosLocA
        return particle.PosLocB

    @staticmethod
    def particle_overlap_area(source_radius, target_radius, center_distance):
        """Return the circular overlap area of two particles."""
        if center_distance <= 0.0:
            return math.pi * min(source_radius, target_radius) ** 2
        if center_distance >= source_radius + target_radius:
            return 0.0
        if center_distance <= abs(source_radius - target_radius):
            return math.pi * min(source_radius, target_radius) ** 2

        source_term = (
            center_distance * center_distance
            + source_radius * source_radius
            - target_radius * target_radius
        ) / (2.0 * center_distance * source_radius)
        target_term = (
            center_distance * center_distance
            + target_radius * target_radius
            - source_radius * source_radius
        ) / (2.0 * center_distance * target_radius)
        source_term = max(-1.0, min(1.0, source_term))
        target_term = max(-1.0, min(1.0, target_term))
        source_area = source_radius * source_radius * math.acos(source_term)
        target_area = target_radius * target_radius * math.acos(target_term)
        triangle_area = 0.5 * math.sqrt(
            max(
                0.0,
                (-center_distance + source_radius + target_radius)
                * (center_distance + source_radius - target_radius)
                * (center_distance - source_radius + target_radius)
                * (center_distance + source_radius + target_radius),
            )
        )
        return source_area + target_area - triangle_area

    def ProcessParticleCollision(self, TargetID, SourceID, totalForce):
        """Calculate and accumulate one particle-contact force."""
        contact_state = self.InitializeContactState(SourceID, TargetID)
        if contact_state is None:
            return self.collIn.ErrorReturn == self.constants.ERROR_NONE
        return self.AccumulateContactForce(SourceID, contact_state, totalForce)

    def CheckWallMaximumDepth(
        self,
        SourceID,
        center_distance,
        particle_radius,
        wall_flag,
    ):
        """Reject a wall ghost whose leading edge passed the source center."""
        maximum_depth_distance = (
            float(particle_radius)
            - self.WallContactOffsetDistance(particle_radius)
        )
        wall_proximity = float(center_distance) - maximum_depth_distance
        if wall_proximity < -self.EPSILON:
            return self.SetError(
                self.constants.ERROR_WALL_TUNNELING,
                error_kind="particle-wall",
                source_id=SourceID,
                wall_flag=wall_flag,
            )
        return True

    def CheckPenetrationStepResolution(
        self,
        SourceID,
        normal,
        source_radius,
        target_velocity,
        error_kind,
        target_id=None,
        wall_flag=None,
    ):
        """Require one step to consume no more than the penetration reserve."""
        source_velocity = self.GetStartFrameVelocity(SourceID)
        relative_normal_velocity = (
            (float(target_velocity.x) - float(source_velocity.x)) * normal[0]
            + (float(target_velocity.y) - float(source_velocity.y)) * normal[1]
            + (float(target_velocity.z) - float(source_velocity.z)) * normal[2]
        )
        inward_displacement = max(
            0.0,
            -relative_normal_velocity * float(self.ShaderFlags.dt),
        )
        penetration_reserve = (
            (1.0 - self.MAXIMUM_PENETRATION_FRACTION)
            * float(source_radius)
        )
        if inward_displacement > penetration_reserve + self.EPSILON:
            return self.SetError(
                self.constants.ERROR_PENETRATION_STEP_TOO_LARGE,
                error_kind=error_kind,
                source_id=SourceID,
                target_id=target_id,
                wall_flag=wall_flag,
            )
        return True

    def EvaluateParametricWallSegment(self, SourceID, segment):
        """Evaluate one configured parametric wall against a mobile source."""
        source_position = self.GetParticlePosition(SourceID)
        source_point = (
            float(source_position.x),
            float(source_position.y),
        )
        parameter, wall_point_2d, _distance_squared = closest_point(
            segment,
            source_point,
        )
        tangent_x, tangent_y = evaluate_tangent(segment, parameter)
        tangent_magnitude = math.hypot(tangent_x, tangent_y)
        if tangent_magnitude <= self.EPSILON:
            return None

        wall_flag = int(round(float(segment[8])))
        if wall_flag <= 0:
            return None
        normal = (
            tangent_y / tangent_magnitude,
            -tangent_x / tangent_magnitude,
            0.0,
        )

        radius = float(self.particles[SourceID].Data.x)
        offset = self.WallContactOffsetDistance(radius)
        ghost = (
            wall_point_2d[0] + normal[0] * (radius - offset),
            wall_point_2d[1] + normal[1] * (radius - offset),
            float(source_position.z),
        )
        dx = ghost[0] - float(source_position.x)
        dy = ghost[1] - float(source_position.y)
        dz = ghost[2] - float(source_position.z)
        center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        if center_distance >= 2.0 * radius:
            return None
        overlap_area = self.particle_overlap_area(
            radius,
            radius,
            center_distance,
        )
        return (*normal, overlap_area, center_distance, wall_flag)

    def EvaluateParametricWallContacts(self, SourceID):
        """Return the deepest current contact for each physical wall."""
        radius = float(self.particles[SourceID].Data.x)
        contacts = {}
        for segment in self.run_configuration.get("curve_wall_segments", ()):
            contact = self.EvaluateParametricWallSegment(SourceID, segment)
            if contact is None:
                continue
            wall_flag = int(contact[-1])
            penetration_depth = self.ParticlePenetrationDepth(
                radius,
                radius,
                float(contact[-2]),
            )
            previous = contacts.get(wall_flag)
            if previous is None or penetration_depth > previous[0]:
                contacts[wall_flag] = (penetration_depth, contact)
        return contacts

    def GetPistonPosition(self, frame):
        """Return the piston x position for the specified simulation frame."""
        bounds = self.run_configuration["chamber_bounds"]
        start_x = float(bounds[0])
        stop_x = float(bounds[1])
        start_frame = int(self.run_configuration["piston_start_frame"])
        velocity_x = float(self.run_configuration["piston_velocity"][0])

        elapsed_frames = max(0, int(frame) - start_frame)
        position = start_x + elapsed_frames * float(self.ShaderFlags.dt) * velocity_x
        return min(position, stop_x)

    def PistonEnabled(self):
        """Return whether this scenario defines the analytic piston model."""
        return all(
            key in self.run_configuration
            for key in (
                "chamber_bounds",
                "piston_velocity",
                "piston_start_frame",
            )
        )

    def GetPistonVelocity(self, frame):
        """Return zero while parked and the configured velocity while moving."""
        start_frame = int(self.run_configuration["piston_start_frame"])
        stop_x = float(self.run_configuration["chamber_bounds"][1])
        if int(frame) < start_frame or self.GetPistonPosition(frame) >= stop_x:
            return self.create_vec4()

        velocity = self.run_configuration["piston_velocity"]
        vx, vy, vz = (float(value) for value in velocity)
        return self.create_vec4(vx, vy, vz, self.VelocityAngle(vx, vy))

    def EvaluatePistonWall(self, SourceID):
        """Evaluate the analytic vertical piston plane for one mobile source."""
        source_position = self.GetParticlePosition(SourceID)
        radius = float(self.particles[SourceID].Data.x)
        bounds = self.run_configuration["chamber_bounds"]
        if not (
            float(bounds[2]) <= float(source_position.y) <= float(bounds[3])
            and float(bounds[4]) <= float(source_position.z) <= float(bounds[5])
        ):
            return None

        offset = self.WallContactOffsetDistance(radius)
        piston_x = self.GetPistonPosition(self.ShaderFlags.frameNum)
        ghost = (
            piston_x - radius + offset,
            source_position.y,
            source_position.z,
        )
        normal = (-1.0, 0.0, 0.0)
        center_distance = abs(ghost[0] - source_position.x)
        if center_distance >= 2.0 * radius:
            return None
        overlap_area = self.particle_overlap_area(radius, radius, center_distance)
        return (*normal, overlap_area, center_distance, 1)

    def ProcessPistonCollision(self, SourceID, totalForce):
        """Evaluate and accumulate the single analytic piston contact."""
        if not self.PistonEnabled():
            return True
        segment = self.EvaluatePistonWall(SourceID)
        if segment is None:
            return True

        normal_x, normal_y, normal_z, overlap_area, center_distance, wall_flag = segment
        radius = float(self.particles[SourceID].Data.x)
        if not self.CheckPenetrationStepResolution(
            SourceID,
            (normal_x, normal_y, normal_z),
            radius,
            self.GetPistonVelocity(self.ShaderFlags.frameNum),
            "particle-wall",
            wall_flag=wall_flag,
        ):
            return False
        if not self.CheckWallMaximumDepth(
            SourceID,
            center_distance,
            radius,
            wall_flag,
        ):
            return False

        geometry = (
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
            center_distance,
            radius,
            2.0 * radius,
            0.0,
            0.0,
        )
        contact_state = self.AppendWallContactSlot(SourceID, wall_flag, geometry)
        if contact_state is None:
            return False
        contact_state.wall_target_velocity = self.GetPistonVelocity(
            self.ShaderFlags.frameNum
        )
        contact_state.is_piston_contact = 1.0
        if hasattr(self, "RecordContactParameters"):
            self.RecordContactParameters(SourceID, wall_flag, contact_state)
        return self.AccumulateContactForce(SourceID, contact_state, totalForce)

    def ProcessParametricWallCollision(self, SourceID, contact, totalForce):
        """Apply one source-owned parametric wall contact."""
        contact_state = self.InitializeParametricWallContactState(SourceID, contact)
        if contact_state is None:
            if self.collIn.ErrorReturn != self.constants.ERROR_NONE:
                return False
            return True
        if hasattr(self, "RecordContactParameters"):
            self.RecordContactParameters(
                SourceID,
                int(contact_state.ids.x),
                contact_state,
            )
        return self.AccumulateContactForce(SourceID, contact_state, totalForce)

    def InitializeParametricWallContactState(self, SourceID, contact):
        """Initialize one current-frame source-parametric-wall contact."""
        normal_x, normal_y, normal_z, overlap_area, center_distance, wall_flag = contact
        radius = float(self.particles[SourceID].Data.x)
        if not self.CheckPenetrationStepResolution(
            SourceID,
            (normal_x, normal_y, normal_z),
            radius,
            self.create_vec4(),
            "particle-wall",
            wall_flag=wall_flag,
        ):
            return None
        if not self.CheckWallMaximumDepth(
            SourceID,
            center_distance,
            radius,
            wall_flag,
        ):
            return None
        geometry = (
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
            center_distance,
            radius,
            2.0 * radius,
            0.0,
            0.0,
        )
        return self.AppendWallContactSlot(SourceID, wall_flag, geometry)

    def ParametricBoundaryMarkerApplies(self, SourceID, BoundaryID):
        """Return True when a parametric boundary marker is local to a source."""
        source_position = self.GetParticlePosition(SourceID)
        boundary_position = self.GetParticlePosition(BoundaryID)
        evaluator_id = int(round(float(self.particles[BoundaryID].Data.z)))
        if evaluator_id != self.BOUNDARY_EVALUATOR_PARAMETRIC:
            return False
        return (
            abs(source_position.x - boundary_position.x) <= 1.0
            and abs(source_position.y - boundary_position.y) <= 1.0
            and abs(source_position.z - boundary_position.z) <= 1.0
        )

    def InitializeContactState(self, SourceID, TargetID):
        """Initialize one current-frame source-target contact."""
        source = self.particles[SourceID]
        contact_state = self.GetContactState(SourceID, TargetID)
        if contact_state is None:
            return None
        source.colFlg = 1
        return contact_state

    def GetContactState(self, SourceID, TargetID):
        """Create and populate one current-frame source-owned contact slot.

        The slot first receives its target ID and current collision state.
        Current geometry is then calculated and stored in the slot. Returning
        a slot with no geometry is allowed when no current overlap is found;
        returning None means no contact slot was available.
        """
        contact = self.GetParticleGeometry(SourceID, TargetID)
        if contact is None:
            return None

        contact_state = self.AppendContactSlot(SourceID, TargetID)
        if contact_state is None:
            self.SetError(
                self.constants.ERROR_CONTACT_LIST_MISSING,
                error_kind="contact-slot-capacity",
                source_id=SourceID,
                target_id=TargetID,
            )
            return None

        (
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
            center_distance,
            effective_source_radius,
            effective_target_radius,
            physical_separation_limit,
            starting_contact,
            starting_resolved,
        ) = contact
        source = self.particles[SourceID]
        target = self.particles[TargetID]
        contact_state.geom = self.create_vec4(
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
        )
        contact_state.aux.x = center_distance
        contact_state.aux.y = self.ParticlePenetrationDepth(
            effective_source_radius,
            effective_target_radius,
            center_distance,
        )
        contact_state.aux.z = 0.0
        contact_state.effective_source_radius = effective_source_radius
        contact_state.effective_target_radius = effective_target_radius
        contact_state.effective_separation_limit = (
            effective_source_radius + effective_target_radius
        )
        contact_state.physical_separation_limit = physical_separation_limit
        contact_state.starting_contact = starting_contact
        contact_state.starting_resolved = starting_resolved
        return contact_state

    def GetParticleGeometry(self, SourceID, TargetID):
        """Calculate current-frame geometry for one source-target pair.

        Positions come from the frame-start snapshot.  When the particle radii
        overlap, return the source-to-target unit normal, circular overlap area,
        center distance, and effective radii.  In depth mode, penetration is
        the source orientation magnitude minus the source-to-target-leading-edge
        proximity magnitude.  Return None when no overlap exists.  Coincident
        centers use +x as a deterministic fallback normal.
        """
        source_position = self.GetParticlePosition(SourceID)
        target_position = self.GetParticlePosition(TargetID)
        dx = target_position.x - source_position.x
        dy = target_position.y - source_position.y
        dz = target_position.z - source_position.z
        center_distance = (dx * dx + dy * dy + dz * dz) ** 0.5

        (
            source_radius,
            target_radius,
            physical_separation_limit,
            starting_contact,
            starting_resolved,
            suppress_contact,
        ) = self.GetParticleEffectiveContactGeometry(
            SourceID,
            TargetID,
            center_distance,
        )
        if suppress_contact:
            return None
        if center_distance >= source_radius + target_radius:
            return None

        if center_distance <= 1.0e-12:
            normal_x = 1.0
            normal_y = 0.0
            normal_z = 0.0
        else:
            normal_x = dx / center_distance
            normal_y = dy / center_distance
            normal_z = dz / center_distance

        overlap_area = self.particle_overlap_area(
            source_radius,
            target_radius,
            center_distance,
        )
        return (
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
            center_distance,
            source_radius,
            target_radius,
            physical_separation_limit,
            starting_contact,
            starting_resolved,
        )

    @staticmethod
    def ParticleProximityMagnitude(source_radius, target_radius, center_distance):
        """Distance from source center to target leading edge along the normal."""
        return max(0.0, center_distance - target_radius)

    @classmethod
    def ParticlePenetrationDepth(cls, source_radius, target_radius, center_distance):
        """Return orientation magnitude minus proximity magnitude."""
        orientation_magnitude = source_radius
        proximity_magnitude = cls.ParticleProximityMagnitude(
            source_radius,
            target_radius,
            center_distance,
        )
        return orientation_magnitude - proximity_magnitude

    @staticmethod
    def SolveSmallLinearSystem(matrix, values, epsilon=1.0e-12):
        """Solve a dense system of at most three equations."""
        size = len(values)
        augmented = [
            [float(matrix[row][column]) for column in range(size)]
            + [float(values[row])]
            for row in range(size)
        ]
        for pivot in range(size):
            pivot_row = max(
                range(pivot, size),
                key=lambda row: abs(augmented[row][pivot]),
            )
            if abs(augmented[pivot_row][pivot]) <= epsilon:
                return None
            augmented[pivot], augmented[pivot_row] = (
                augmented[pivot_row],
                augmented[pivot],
            )
            divisor = augmented[pivot][pivot]
            for column in range(pivot, size + 1):
                augmented[pivot][column] /= divisor
            for row in range(size):
                if row == pivot:
                    continue
                factor = augmented[row][pivot]
                for column in range(pivot, size + 1):
                    augmented[row][column] -= factor * augmented[pivot][column]
        return [augmented[row][size] for row in range(size)]

    def ProjectSourceVelocityToContactSet(self, candidate_velocity, constraints):
        """Return the closest velocity satisfying all source half-spaces."""
        candidate = tuple(float(value) for value in candidate_velocity)

        def dot(left, right):
            return sum(left[axis] * right[axis] for axis in range(3))

        def satisfies(velocity):
            return all(
                dot(normal, velocity) <= limit + self.EPSILON
                for normal, limit, _contact_state in constraints
            )

        if satisfies(candidate):
            return candidate

        best_velocity = None
        best_distance_sq = None
        maximum_active = min(3, len(constraints))
        for active_count in range(1, maximum_active + 1):
            for active_indices in itertools.combinations(
                range(len(constraints)),
                active_count,
            ):
                active = [constraints[index] for index in active_indices]
                gram = [
                    [dot(left[0], right[0]) for right in active]
                    for left in active
                ]
                residual = [
                    dot(normal, candidate) - limit
                    for normal, limit, _contact_state in active
                ]
                multipliers = self.SolveSmallLinearSystem(
                    gram,
                    residual,
                    self.EPSILON,
                )
                if multipliers is None or any(
                    multiplier < -self.EPSILON
                    for multiplier in multipliers
                ):
                    continue
                velocity = tuple(
                    candidate[axis]
                    - sum(
                        multipliers[index] * active[index][0][axis]
                        for index in range(active_count)
                    )
                    for axis in range(3)
                )
                if not satisfies(velocity):
                    continue
                distance_sq = sum(
                    (candidate[axis] - velocity[axis]) ** 2
                    for axis in range(3)
                )
                if best_distance_sq is None or distance_sq < best_distance_sq:
                    best_velocity = velocity
                    best_distance_sq = distance_sq
        return best_velocity

    def ApplySourceMaximumDepth(self, SourceID):
        """Stop current inward source motion at observed maximum compression."""
        source = self.particles[SourceID]
        candidate = (
            float(source.VelRad.x),
            float(source.VelRad.y),
            float(source.VelRad.z),
        )
        constraints = []
        for contact_index in range(int(source.contactCount)):
            contact_state = self.GetContactSlots(SourceID)[contact_index]
            contact_type = int(contact_state.ids.y)
            if contact_type not in (self.CONTACT_PARTICLE, self.CONTACT_WALL):
                continue

            source_radius = float(contact_state.effective_source_radius)
            maximum_depth = self.MAXIMUM_PENETRATION_FRACTION * source_radius
            penetration_depth = max(0.0, float(contact_state.aux.y))
            contact_state.maximum_depth = maximum_depth
            contact_state.remaining_depth = max(
                0.0,
                maximum_depth - penetration_depth,
            )
            contact_state.maximum_depth_reached = (
                1.0
                if penetration_depth >= maximum_depth - self.EPSILON
                else 0.0
            )
            if penetration_depth < maximum_depth - self.EPSILON:
                continue

            normal = (
                float(contact_state.geom.x),
                float(contact_state.geom.y),
                float(contact_state.geom.z),
            )
            if contact_type == self.CONTACT_WALL:
                target_velocity = getattr(
                    contact_state,
                    "wall_target_velocity",
                    self.create_vec4(),
                )
            else:
                target_velocity = self.GetStartFrameVelocity(
                    int(contact_state.ids.x)
                )
            source_normal_limit = (
                float(target_velocity.x) * normal[0]
                + float(target_velocity.y) * normal[1]
                + float(target_velocity.z) * normal[2]
            )
            constraints.append((normal, source_normal_limit, contact_state))

        if not constraints:
            return True

        contained = self.ProjectSourceVelocityToContactSet(candidate, constraints)
        if contained is None:
            first_contact = constraints[0][2]
            first_contact_type = int(first_contact.ids.y)
            target_id = (
                int(first_contact.ids.x)
                if first_contact_type == self.CONTACT_PARTICLE
                else None
            )
            wall_flag = (
                int(first_contact.ids.x)
                if first_contact_type == self.CONTACT_WALL
                else None
            )
            return self.SetError(
                self.constants.ERROR_MAX_DEPTH_CONSTRAINT,
                error_kind="source-contact-set",
                source_id=SourceID,
                target_id=target_id,
                wall_flag=wall_flag,
            )

        source_mass = self.GetParticleMass(SourceID)
        blocked_momentum = tuple(
            source_mass * (candidate[axis] - contained[axis])
            for axis in range(3)
        )
        source.parms.y += blocked_momentum[0]
        source.parms.z += blocked_momentum[1]
        source.parms.w += blocked_momentum[2]
        self.SyncInternalMomentumMagnitude(source)
        source.VelRad.x, source.VelRad.y, source.VelRad.z = contained
        source.VelRad.w = self.VelocityAngle(contained[0], contained[1])
        return True

    def GetParticlePosition(self, ParticleID):
        """Return a particle's frame-start position.

        Prefer PosLocFrame so every source reads the same immutable frame
        snapshot.  Fall back to the currently active position buffer when a
        snapshot is not available.
        """
        if hasattr(self, "PosLocFrame") and self.PosLocFrame:
            return self.PosLocFrame[ParticleID]
        return self.particle_position(
            self.particles[ParticleID],
            int(self.ShaderFlags.positionBuffer),
        )

    def IsBoundaryParticle(self, ParticleID):
        """Return True when a particle is an occupancy-only boundary marker."""
        return float(getattr(self.particles[ParticleID], "ptype", 0.0)) > 0.5

    def IsNullParticle(self, ParticleID):
        """Return True only for the reserved ABI particle at index zero."""
        particle = self.particles[ParticleID]
        return (
            int(ParticleID) == 0
            and int(getattr(particle, "pnum", -1)) == 0
            and float(getattr(particle, "ptype", 0.0)) < -0.5
        )

    def IsMobileParticleActiveForDynamics(self, ParticleID):
        """Return True when a particle is a mobile dynamics source."""
        return (
            not self.IsNullParticle(ParticleID)
            and not self.IsBoundaryParticle(ParticleID)
            and float(self.particles[ParticleID].Data.w) >= 0.0
        )

    def StartingParticleKey(self, SourceID, TargetID):
        """Return the unordered key for a particle starting contact."""
        low_id = min(int(SourceID), int(TargetID))
        high_id = max(int(SourceID), int(TargetID))
        return ("particle", low_id, high_id)

    def InitializeStartingContactState(self):
        """Record contacts that already overlap at the initial configuration."""
        if self.starting_contacts_initialized:
            return

        self.starting_contacts_initialized = True
        self.starting_contact_states = {}

        for source_id in range(len(self.particles)):
            if not self.IsMobileParticleActiveForDynamics(source_id):
                continue
            source_radius = float(self.particles[source_id].Data.x)
            for target_id in range(source_id + 1, len(self.particles)):
                if not self.IsMobileParticleActiveForDynamics(target_id):
                    continue
                target_radius = float(self.particles[target_id].Data.x)
                center_distance = self.ParticleCenterDistance(source_id, target_id)
                physical_limit = source_radius + target_radius
                if center_distance >= physical_limit - self.EPSILON:
                    continue
                if center_distance <= self.EPSILON or physical_limit <= self.EPSILON:
                    continue

                radius_scale = center_distance / physical_limit
                self.starting_contact_states[
                    self.StartingParticleKey(source_id, target_id)
                ] = {
                    "kind": "particle",
                    "status": "active",
                    "start_center_distance": center_distance,
                    "physical_separation_limit": physical_limit,
                    "effective_source_radius": source_radius * radius_scale,
                    "effective_target_radius": target_radius * radius_scale,
                    "compressed": False,
                }

    def ParticleCenterDistance(self, SourceID, TargetID):
        """Return frame-snapshot center distance for one particle pair."""
        source_position = self.GetParticlePosition(SourceID)
        target_position = self.GetParticlePosition(TargetID)
        dx = target_position.x - source_position.x
        dy = target_position.y - source_position.y
        dz = target_position.z - source_position.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def GetParticleEffectiveContactGeometry(self, SourceID, TargetID, center_distance):
        """Return radii and suppression state for a particle contact."""
        source_radius = float(self.particles[SourceID].Data.x)
        target_radius = float(self.particles[TargetID].Data.x)
        physical_limit = source_radius + target_radius
        key = self.StartingParticleKey(SourceID, TargetID)
        state = self.starting_contact_states.get(key)
        if state is None:
            return source_radius, target_radius, physical_limit, 0.0, 0.0, False

        start_distance = float(state["start_center_distance"])
        if state["status"] == "active":
            if center_distance < start_distance - self.EPSILON:
                state["compressed"] = True
            elif (
                center_distance > start_distance + self.EPSILON
                or (
                    bool(state.get("compressed", False))
                    and center_distance >= start_distance - self.EPSILON
                )
            ):
                state["status"] = "resolved"

        if state["status"] == "resolved":
            if center_distance >= physical_limit - self.EPSILON:
                self.starting_contact_states.pop(key, None)
                return source_radius, target_radius, physical_limit, 0.0, 1.0, False
            return source_radius, target_radius, physical_limit, 1.0, 1.0, True

        return (
            float(state["effective_source_radius"]),
            float(state["effective_target_radius"]),
            physical_limit,
            1.0,
            0.0,
            False,
        )

    def GetParticlePotentialGeometry(self, SourceID, TargetID, center_distance):
        """Return geometry used by force and potential diagnostics."""
        (
            source_radius,
            target_radius,
            _physical_limit,
            _starting_contact,
            _starting_resolved,
            suppress_contact,
        ) = self.GetParticleEffectiveContactGeometry(
            SourceID,
            TargetID,
            center_distance,
        )
        if suppress_contact:
            return None
        if center_distance >= source_radius + target_radius:
            return None
        return source_radius, target_radius

    def AppendContactSlot(self, SourceID, TargetID):
        """Allocate and initialize the next source-owned contact slot.

        The slot records the target ID, contact type, and active-this-frame flag.
        Increment source.contactCount only after a slot is successfully filled.
        Return None when the source has no remaining slot capacity.
        """
        source = self.particles[SourceID]
        contact_slots = self.GetContactSlots(SourceID)
        if source.contactCount >= len(contact_slots):
            return None

        contact_state = contact_slots[source.contactCount]
        contact_state.ids.x = TargetID
        contact_state.ids.y = self.CONTACT_PARTICLE
        contact_state.ids.z = 0
        contact_state.ids.w = self.CONTACT_ACTIVE_THIS_FRAME
        contact_state.aux.z = 0.0
        source.contactCount += 1
        return contact_state

    def GetContactSlots(self, SourceID):
        """Return the fixed contact-slot array owned by the source particle."""
        return self.particles[SourceID].contacts

    def GetStartFrameVelocity(self, ParticleID):
        """Return a particle's immutable frame-start velocity.

        Prefer VelRadFrame so contact calculations cannot observe velocity
        writes made earlier in the frame.  Fall back to the particle velocity
        when a frame snapshot is unavailable.
        """
        if hasattr(self, "VelRadFrame") and self.VelRadFrame:
            return self.VelRadFrame[ParticleID]
        return self.particles[ParticleID].VelRad

    def AccumulateContactForce(self, SourceID, contact_state, totalForce):
        """Calculate one contact force and add it to source-local totalForce."""
        TargetID = int(contact_state.ids.x)
        contact_type = int(contact_state.ids.y)
        pair_stiffness = self.GetContactStiffness(
            SourceID,
            TargetID,
            contact_type,
        )
        if self.contact_force_measure == "depth":
            contact_measure = float(contact_state.aux.y)
        else:
            contact_measure = float(contact_state.geom.w)
        force_magnitude = pair_stiffness * max(0.0, contact_measure)
        contact_state.force_magnitude = force_magnitude
        totalForce.x -= force_magnitude * float(contact_state.geom.x)
        totalForce.y -= force_magnitude * float(contact_state.geom.y)
        totalForce.z -= force_magnitude * float(contact_state.geom.z)
        return True

    def GetPairStiffness(self, SourceID, TargetID):
        """Return the nonnegative mean particle-owned stiffness for a contact."""
        source_q = self.particles[SourceID].Data.y or 0.0
        target_q = self.particles[TargetID].Data.y or 0.0
        return max(0.0, 0.5 * (source_q + target_q))

    def GetContactStiffness(self, SourceID, TargetID, contact_type):
        """Return contact stiffness for a particle or equal-material wall ghost."""
        if contact_type == self.CONTACT_WALL:
            return max(0.0, float(self.particles[SourceID].Data.y or 0.0))
        return self.GetPairStiffness(SourceID, TargetID)

    def WallContactOffsetDistance(self, radius):
        """Return configured wall offset as a bounded fraction of radius."""
        return min(float(radius), float(radius) * self.wall_contact_offset)

    def AppendWallContactSlot(self, SourceID, wall_flag, geometry):
        """Append one source-owned stationary wall-ghost contact slot."""
        source = self.particles[SourceID]
        slots = self.GetContactSlots(SourceID)
        if source.contactCount >= len(slots):
            return None
        contact_state = slots[source.contactCount]
        (
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
            center_distance,
            effective_radius,
            physical_limit,
            starting_contact,
            starting_resolved,
        ) = geometry
        contact_state.ids.x = int(wall_flag)
        contact_state.ids.y = self.CONTACT_WALL
        contact_state.ids.z = int(wall_flag)
        contact_state.ids.w = self.CONTACT_ACTIVE_THIS_FRAME
        contact_state.geom = self.create_vec4(
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
        )
        contact_state.aux.x = center_distance
        contact_state.aux.y = self.ParticlePenetrationDepth(
            effective_radius,
            effective_radius,
            center_distance,
        )
        contact_state.aux.z = 0.0
        contact_state.effective_source_radius = effective_radius
        contact_state.effective_target_radius = effective_radius
        contact_state.effective_separation_limit = 2.0 * effective_radius
        contact_state.physical_separation_limit = physical_limit
        contact_state.starting_contact = starting_contact
        contact_state.starting_resolved = starting_resolved
        contact_state.wall_ghost_mass = self.GetParticleMass(SourceID)
        contact_state.wall_target_velocity = self.create_vec4()
        contact_state.is_piston_contact = 0.0
        source.contactCount += 1
        source.colFlg = 1
        source.report_contacts = source.contactCount
        return contact_state

    def CalcVelocity(self, SourceID, totalForce):
        """Apply source-local total force directly to the source velocity."""
        dt = float(self.ShaderFlags.dt)
        if dt <= 0.0:
            return self.SetError(self.constants.ERROR_INVALID_DT)

        source = self.particles[SourceID]
        source_mass = self.GetParticleMass(SourceID)

        start_velocity = self.GetStartFrameVelocity(SourceID)
        source.VelRad.x = start_velocity.x + totalForce.x * dt / source_mass
        source.VelRad.y = start_velocity.y + totalForce.y * dt / source_mass
        source.VelRad.z = start_velocity.z + totalForce.z * dt / source_mass
        source.VelRad.w = self.VelocityAngle(source.VelRad.x, source.VelRad.y)
        return True

    def GetParticleMass(self, ParticleID):
        """Return particle mass from parms.x with an EPSILON lower bound."""
        return max(self.particles[ParticleID].parms.x, self.EPSILON)

    def CalcPosition(self, SourceID):
        """Move one source using its newly calculated velocity."""
        position_buffer = int(self.ShaderFlags.positionBuffer)
        dt = self.ShaderFlags.dt
        if dt <= 0.0:
            return self.SetError(self.constants.ERROR_INVALID_DT)

        particle = self.particles[SourceID]
        position = self.GetParticlePosition(SourceID)
        velocity = particle.VelRad
        if position_buffer == 0:
            particle.PosLocB.x = position.x + velocity.x * dt
            particle.PosLocB.y = position.y + velocity.y * dt
            particle.PosLocB.z = position.z + velocity.z * dt
            particle.PosLocA.w = 1.0
            particle.PosLocB.w = 0.0
            output_position = particle.PosLocB
        else:
            particle.PosLocA.x = position.x + velocity.x * dt
            particle.PosLocA.y = position.y + velocity.y * dt
            particle.PosLocA.z = position.z + velocity.z * dt
            particle.PosLocA.w = 0.0
            particle.PosLocB.w = 1.0
            output_position = particle.PosLocA

        if (
            output_position.x < 0.0
            or output_position.x >= float(self.ShaderFlags.CellAryW)
            or output_position.y < 0.0
            or output_position.y >= float(self.ShaderFlags.CellAryH)
            or output_position.z < 0.0
            or output_position.z >= float(self.ShaderFlags.CellAryL)
        ):
            return self.SetError(
                self.constants.ERROR_PARTICLE_OUT_OF_BOUNDS,
                error_kind="cell-boundary",
                source_id=SourceID,
            )

        death_bounds = self.run_configuration.get("death_bounds")
        if death_bounds is not None and len(death_bounds) == 6:
            if (
                output_position.x < float(death_bounds[0])
                or output_position.x > float(death_bounds[1])
                or output_position.y < float(death_bounds[2])
                or output_position.y > float(death_bounds[3])
                or output_position.z < float(death_bounds[4])
                or output_position.z > float(death_bounds[5])
            ):
                particle.Data.w = -1.0
                particle.state_flg = -1.0
        return True

    def isParticleContact(self, Frame, SourceID, TargetID, positionBuffer):
        source = self.particles[SourceID]
        target = self.particles[TargetID]
        if hasattr(self, "PosLocFrame") and self.PosLocFrame:
            source_position = self.PosLocFrame[SourceID]
            target_position = self.PosLocFrame[TargetID]
        else:
            source_position = self.particle_position(source, positionBuffer)
            target_position = self.particle_position(target, positionBuffer)
        dx = target_position.x - source_position.x
        dy = target_position.y - source_position.y
        dz = target_position.z - source_position.z
        center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        source_radius = source.Data.x
        target_radius = target.Data.x
        contact = center_distance <= source_radius + target_radius
        if not contact:
            return False

        physical_proximity = center_distance - target_radius
        if physical_proximity < -self.EPSILON:
            return self.SetError(
                self.constants.ERROR_PARTICLE_TUNNELING,
                error_kind="particle-particle",
                source_id=SourceID,
                target_id=TargetID,
            )

        if center_distance <= self.EPSILON:
            normal = (1.0, 0.0, 0.0)
        else:
            normal = (
                dx / center_distance,
                dy / center_distance,
                dz / center_distance,
            )
        if not self.CheckPenetrationStepResolution(
            SourceID,
            normal,
            source_radius,
            self.GetStartFrameVelocity(TargetID),
            "particle-particle",
            target_id=TargetID,
        ):
            return True
        (
            effective_source_radius,
            _effective_target_radius,
            _physical_limit,
            _starting_contact,
            _starting_resolved,
            suppress_contact,
        ) = self.GetParticleEffectiveContactGeometry(
            SourceID,
            TargetID,
            center_distance,
        )

        overlap_area = self.particle_overlap_area(
            effective_source_radius,
            _effective_target_radius,
            center_distance,
        )
        source.oa = max(source.oa, overlap_area)
        penetration_depth = self.ParticlePenetrationDepth(
            effective_source_radius,
            _effective_target_radius,
            center_distance,
        )
        source.max_penetration_depth = max(
            source.max_penetration_depth,
            penetration_depth,
        )
        if suppress_contact and TargetID not in source.suppressed_contacts:
            source.suppressed_contacts.append(TargetID)
        return True

    def DetectContacts(self, total_forces):
        """Run naive contact detection and overlap-area forces for every source."""
        return self.NaiveContactDetermination(total_forces)

    def NaiveContactDetermination(self, total_forces):
        """Fully process each source after scanning its possible targets."""
        position_buffer = int(self.ShaderFlags.positionBuffer)
        for source_id in range(len(self.particles)):
            if not self.IsMobileParticleActiveForDynamics(source_id):
                continue
            if not self.ProcessPistonCollision(
                source_id,
                total_forces[source_id],
            ):
                return False
            has_local_boundary_marker = False
            for target_id in range(len(self.particles)):
                if source_id == target_id:
                    continue
                if self.IsBoundaryParticle(target_id):
                    has_local_boundary_marker = (
                        has_local_boundary_marker
                        or self.ParametricBoundaryMarkerApplies(
                            source_id,
                            target_id,
                        )
                    )
                    continue
                if not self.IsMobileParticleActiveForDynamics(target_id):
                    continue
                if self.isParticleContact(
                    self.ShaderFlags.frameNum,
                    source_id,
                    target_id,
                    position_buffer,
                ):
                    if not self.AddContactTargetID(source_id, target_id):
                        return False
                    if not self.ProcessParticleCollision(
                        target_id,
                        source_id,
                        total_forces[source_id],
                    ):
                        return False
                if self.collIn.ErrorReturn != self.constants.ERROR_NONE:
                    return False
            if not has_local_boundary_marker:
                continue
            boundary_contacts = self.EvaluateParametricWallContacts(source_id)
            for wall_flag in sorted(boundary_contacts):
                _penetration_depth, contact = boundary_contacts[wall_flag]
                if not self.ProcessParametricWallCollision(
                    source_id,
                    contact,
                    total_forces[source_id],
                ):
                    return False
        return True

    def AddContactTargetID(self, SourceID, TargetID):
        """Add only the target id to the source contact list."""
        source = self.particles[SourceID]
        if TargetID not in source.collision_list:
            source.collision_list.append(TargetID)
        return True

    def CalculateVelocities(self, total_forces):
        """Calculate each source velocity after all source contacts are known."""
        for SourceID in range(len(self.particles)):
            if not self.IsMobileParticleActiveForDynamics(SourceID):
                continue
            if not self.CalcVelocity(SourceID, total_forces[SourceID]):
                return False
        return True

    def CalculatePositions(self):
        """Move every source using its newly calculated velocity."""
        for SourceID in range(len(self.particles)):
            if not self.IsMobileParticleActiveForDynamics(SourceID):
                continue
            if not self.CalcPosition(SourceID):
                return False
        return True

    def SetError(
        self,
        error_code,
        error_kind=None,
        source_id=None,
        target_id=None,
        wall_flag=None,
    ):
        """Set the shared collision error state and return failure."""
        self.collIn.ErrorReturn = error_code
        if error_kind is not None:
            self.collIn.ErrorKind = str(error_kind)
        if source_id is not None:
            self.collIn.ErrorSourceID = int(source_id)
            self.collIn.particleNumber = int(source_id)
        if target_id is not None:
            self.collIn.ErrorTargetID = int(target_id)
            self.collIn.ReadWriteConflict = int(target_id)
        if wall_flag is not None:
            self.collIn.ErrorWallFlag = int(wall_flag)
        return False
