class GeoDynamics:
    """GLSL-shaped dynamics functions for the Geo path.

    This class is intentionally kept close to the shader-side function layout.
    Python-only setup, cfg parsing, drawing, and reporting belong outside this
    file.  The active particle/contact data is owned by GeoBase, but the fields
    are named to match the GLSL buffers where possible.

    Contact state convention used here:
        state.ids.x = target particle id
        state.ids.y = contact type
        state.ids.z = phase
        state.ids.w = active/pending flag for the current frame
        state.vel   = first/contact velocity snapshot fields
        state.geom  = normal.xy, current overlap area, current center distance
        state.mom.x = source-owned stored normal contact momentum
        state.mom.y = normal contact momentum already applied to velocity

    Important: alpha_zero is not stored as immutable contact history in this
    path.  It is derived from state.mom.x when needed.  Velocity changes use
    deltas in state.mom.y so a small first overlap does not apply the full
    contact reservoir immediately.
    """

    NEO_EPSILON = 1.0e-12

    def GeoSetError(self, ErrorReturn):
        """Set the GLSL-style collIn error code and return False."""
        self.collIn.ErrorReturn = ErrorReturn
        return False

    def GeoValidParticleID(self, ParticleID):
        """Return True when ParticleID indexes the current particle buffer."""
        return 0 <= ParticleID < len(self.particles)

    def GeoCurrentLocation(self, ParticleID):
        """Read the current position using ShaderFlags.positionBuffer."""
        return self.particle_position(
            self.particles[ParticleID],
            int(self.ShaderFlags.positionBuffer),
        )

    def GeoRadius(self, ParticleID):
        """Return GLSL-style radius field P[id].Data.x."""
        return self.particles[ParticleID].Data.x

    def GeoMass(self, ParticleID):
        """Return GLSL-style mass field P[id].parms.x."""
        return max(self.particles[ParticleID].parms.x, self.NEO_EPSILON)

    def GeoVelocity(self, ParticleID):
        """Read the frame-start velocity when available.

        GeoBase creates VelRadFrame at the start of CollisionRun so every
        source particle resolves against the same velocity snapshot, matching
        the parallel GLSL model more closely than sequential Python mutation.
        """
        if hasattr(self, "VelRadFrame") and self.VelRadFrame:
            return self.VelRadFrame[ParticleID]
        return self.particles[ParticleID].VelRad

    def GeoPairStiffness(self, SourceID, TargetID):
        """Return average source/target stiffness with cfg fallback."""
        source_q = self.particles[SourceID].Data.y or 0.0
        target_q = self.particles[TargetID].Data.y or 0.0
        default_q = float(self.run_configuration.get("collision_stiffness_q", 1.0))
        if source_q <= 0.0:
            source_q = default_q
        if target_q <= 0.0:
            target_q = default_q
        return max(self.NEO_EPSILON, 0.5 * (source_q + target_q))

    def GeoParticleGeometry(self, SourceID, TargetID):
        """Compute pair contact geometry from the current read position buffer.

        Returns (normal_x, normal_y, overlap_area, center_distance), or None
        when the pair is not in contact.
        """
        source_position = self.GeoCurrentLocation(SourceID)
        target_position = self.GeoCurrentLocation(TargetID)
        dx = target_position.x - source_position.x
        dy = target_position.y - source_position.y
        center_distance = (dx * dx + dy * dy) ** 0.5
        source_radius = self.GeoRadius(SourceID)
        target_radius = self.GeoRadius(TargetID)
        if center_distance >= source_radius + target_radius:
            return None
        if center_distance <= self.NEO_EPSILON:
            normal_x = 1.0
            normal_y = 0.0
        else:
            normal_x = dx / center_distance
            normal_y = dy / center_distance
        overlap_area = self.particle_overlap_area(
            source_radius,
            target_radius,
            center_distance,
        )
        return normal_x, normal_y, overlap_area, center_distance

    def GeoFindContactSlot(self, SourceID, TargetID, contact_type):
        """Find an existing source-owned contact slot for target/type."""
        source = self.particles[SourceID]
        tracked_count = min(source.contactCount, self.constants.MAX_CONTACTS)
        for slot in range(tracked_count):
            state = source.gcs[slot]
            if state.ids.x == TargetID and state.ids.y == contact_type:
                return slot
        return -1

    def GeoFindReusableContactSlot(self, SourceID):
        """Find or allocate a reusable source-owned contact slot."""
        source = self.particles[SourceID]
        tracked_count = min(source.contactCount, self.constants.MAX_CONTACTS)
        for slot in range(tracked_count):
            if source.gcs[slot].ids.y == self.constants.NEO_CONTACT_INACTIVE:
                return slot
        if tracked_count < self.constants.MAX_CONTACTS:
            source.contactCount = tracked_count + 1
            return tracked_count
        return -1

    def GeoDeactivateContact(self, SourceID, slot):
        """Mark a source-owned contact slot inactive."""
        state = self.particles[SourceID].gcs[slot]
        state.ids.y = self.constants.NEO_CONTACT_INACTIVE
        state.ids.z = self.constants.NEO_PHASE_INACTIVE
        state.ids.w = 0
        state.mom.x = 0.0
        state.mom.y = 0.0

    def GeoStoredMomentumAlphaZero(self, SourceID, TargetID, stored_momentum):
        """Derive alpha_zero from source-owned stored contact momentum.

        This replaces the older idea that alpha_zero is fixed forever from the
        first contact velocity.  The formula is:

            alpha_zero = ((3 * p^2) / (2 * q * reduced_mass)) ** (1/3)

        where p is the stored source-owned normal contact momentum.
        """
        if stored_momentum <= 0.0:
            return 0.0
        reduced_mass = (
            self.GeoMass(SourceID) * self.GeoMass(TargetID)
        ) / max(self.GeoMass(SourceID) + self.GeoMass(TargetID), self.NEO_EPSILON)
        stiffness_q = self.GeoPairStiffness(SourceID, TargetID)
        return (
            (3.0 * stored_momentum * stored_momentum)
            / (2.0 * stiffness_q * reduced_mass)
        ) ** (1.0 / 3.0)

    def GeoStoredMomentumZeroArea(self, SourceID, TargetID, stored_momentum):
        """Derive zero-area geometry from stored contact momentum."""
        radius_sum = self.GeoRadius(SourceID) + self.GeoRadius(TargetID)
        alpha_zero = self.GeoStoredMomentumAlphaZero(SourceID, TargetID, stored_momentum)
        center_distance = max(0.0, radius_sum - alpha_zero)
        zero_area = self.particle_overlap_area(
            self.GeoRadius(SourceID),
            self.GeoRadius(TargetID),
            center_distance,
        )
        return zero_area, center_distance, alpha_zero

    def GeoAddParticleContact(self, SourceID, TargetID):
        """Add/update a source-owned particle contact for the current frame."""
        if not self.GeoValidParticleID(SourceID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_SOURCE_ID)
        if not self.GeoValidParticleID(TargetID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_TARGET_ID)

        particle = self.particles[SourceID]
        if not hasattr(particle, "collision_list"):
            return self.GeoSetError(self.constants.GEO_ERROR_CONTACT_LIST_MISSING)

        if TargetID not in particle.collision_list:
            particle.collision_list.append(TargetID)
        contact = self.GeoParticleGeometry(SourceID, TargetID)
        if contact is None:
            return True
        found_slot = self.GeoFindContactSlot(
            SourceID,
            TargetID,
            self.constants.NEO_CONTACT_PARTICLE,
        )
        slot = found_slot if found_slot >= 0 else self.GeoFindReusableContactSlot(SourceID)
        if slot < 0:
            return self.GeoSetError(self.constants.GEO_ERROR_CONTACT_LIST_MISSING)
        state = particle.gcs[slot]
        normal_x, normal_y, overlap_area, center_distance = contact
        source_velocity = self.GeoVelocity(SourceID)
        target_velocity = self.GeoVelocity(TargetID)
        relative_normal_velocity = (
            (target_velocity.x - source_velocity.x) * normal_x
            + (target_velocity.y - source_velocity.y) * normal_y
        )
        if found_slot < 0 or state.ids.y == self.constants.NEO_CONTACT_INACTIVE:
            state.ids.x = TargetID
            state.ids.y = self.constants.NEO_CONTACT_PARTICLE
            state.ids.z = (
                self.constants.NEO_PHASE_COMPRESSION
                if relative_normal_velocity < -self.NEO_EPSILON
                else self.constants.NEO_PHASE_REBOUND
            )
            state.vel.x = source_velocity.x
            state.vel.y = source_velocity.y
            state.vel.z = target_velocity.x
            state.vel.w = target_velocity.y
            state.mom.x = 0.0
            state.mom.y = 0.0
        state.ids.w = self.constants.NEO_CONTACT_ACTIVE_THIS_FRAME
        state.geom.x = normal_x
        state.geom.y = normal_y
        state.geom.z = overlap_area
        state.geom.w = center_distance
        particle.colFlg = 1
        return True

    def GeoMoveParticle(self, SourceID, positionBuffer, dt):
        """Move one source particle using GLSL-style position double buffering."""
        if not self.GeoValidParticleID(SourceID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_SOURCE_ID)
        if dt <= 0.0:
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_DT)

        particle = self.particles[SourceID]
        velocity = particle.VelRad
        if int(positionBuffer) == 0:
            particle.PosLocB.x = particle.PosLocA.x + velocity.x * dt
            particle.PosLocB.y = particle.PosLocA.y + velocity.y * dt
            particle.PosLocB.z = particle.PosLocA.z + velocity.z * dt
            particle.PosLocA.w = 1.0
            particle.PosLocB.w = 0.0
            output_position = particle.PosLocB
        else:
            particle.PosLocA.x = particle.PosLocB.x + velocity.x * dt
            particle.PosLocA.y = particle.PosLocB.y + velocity.y * dt
            particle.PosLocA.z = particle.PosLocB.z + velocity.z * dt
            particle.PosLocA.w = 0.0
            particle.PosLocB.w = 1.0
            output_position = particle.PosLocA
        if output_position.x < 1.0 or output_position.y < 1.0:
            return self.GeoSetError(self.constants.GEO_ERROR_PARTICLE_OUT_OF_BOUNDS)
        return True

    def GeoProcessCollisions(self, SourceID):
        """Process source-owned contacts for one particle.

        Current first-pass behavior:
            1. use frame-start relative normal velocity;
            2. keep source-owned stored momentum in state.mom.x;
            3. derive alpha_zero and zero_area from state.mom.x;
            4. use overlap progress to compute target applied momentum;
            5. change source velocity only by the applied-momentum delta.

        state.mom.x is the source-owned contact reservoir.
        state.mom.y is the portion of that reservoir already applied to the
        source velocity for the current overlap path.
        """
        if not self.GeoValidParticleID(SourceID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_SOURCE_ID)
        source = self.particles[SourceID]
        source_delta_vx = 0.0
        source_delta_vy = 0.0
        tracked_count = min(source.contactCount, self.constants.MAX_CONTACTS)
        for slot in range(tracked_count):
            state = source.gcs[slot]
            if state.ids.y != self.constants.NEO_CONTACT_PARTICLE:
                continue
            if state.ids.w != self.constants.NEO_CONTACT_ACTIVE_THIS_FRAME:
                self.GeoDeactivateContact(SourceID, slot)
                continue
            TargetID = state.ids.x
            contact = self.GeoParticleGeometry(SourceID, TargetID)
            if contact is None:
                self.GeoDeactivateContact(SourceID, slot)
                continue
            normal_x, normal_y, overlap_area, _center_distance = contact
            target_velocity = self.GeoVelocity(TargetID)
            source_velocity = self.GeoVelocity(SourceID)
            relative_normal_velocity = (
                (target_velocity.x - source_velocity.x) * normal_x
                + (target_velocity.y - source_velocity.y) * normal_y
            )
            reduced_mass = (
                self.GeoMass(SourceID) * self.GeoMass(TargetID)
            ) / max(self.GeoMass(SourceID) + self.GeoMass(TargetID), self.NEO_EPSILON)
            closing_momentum = reduced_mass * max(0.0, -relative_normal_velocity)
            zero_area, _zero_distance, alpha_zero = self.GeoStoredMomentumZeroArea(
                SourceID,
                TargetID,
                state.mom.x,
            )
            compression_fraction = (
                max(0.0, min(1.0, overlap_area / zero_area))
                if zero_area > self.NEO_EPSILON
                else 0.0
            )
            if state.ids.z == self.constants.NEO_PHASE_COMPRESSION:
                if relative_normal_velocity >= -self.NEO_EPSILON:
                    state.ids.z = self.constants.NEO_PHASE_REBOUND
                    continue
                state.mom.x = max(state.mom.x, closing_momentum)
                zero_area, _zero_distance, alpha_zero = self.GeoStoredMomentumZeroArea(
                    SourceID,
                    TargetID,
                    state.mom.x,
                )
                compression_fraction = (
                    max(0.0, min(1.0, overlap_area / zero_area))
                    if zero_area > self.NEO_EPSILON
                    else 0.0
                )
                compression_progress = 1.0 - max(
                    0.0,
                    1.0 - compression_fraction,
                ) ** 0.5
                target_applied_momentum = state.mom.x * compression_progress
                delta_momentum = max(0.0, target_applied_momentum - state.mom.y)
                state.mom.y = max(state.mom.y, target_applied_momentum)
                if zero_area > self.NEO_EPSILON and overlap_area >= zero_area:
                    state.ids.z = self.constants.NEO_PHASE_REBOUND
                if delta_momentum > 0.0:
                    source_delta_vx -= (delta_momentum / self.GeoMass(SourceID)) * normal_x
                    source_delta_vy -= (delta_momentum / self.GeoMass(SourceID)) * normal_y
            else:
                zero_area, _zero_distance, alpha_zero = self.GeoStoredMomentumZeroArea(
                    SourceID,
                    TargetID,
                    state.mom.x,
                )
                if zero_area <= self.NEO_EPSILON:
                    continue
                compression_fraction = max(0.0, min(1.0, overlap_area / zero_area))
                if (
                    compression_fraction >= 1.0 - self.NEO_EPSILON
                    and abs(relative_normal_velocity) <= self.NEO_EPSILON
                ):
                    release_momentum = state.mom.y
                    state.mom.y = 0.0
                    state.mom.x = 0.0
                else:
                    target_applied_momentum = state.mom.x * compression_fraction
                    release_momentum = max(0.0, state.mom.y - target_applied_momentum)
                    state.mom.y = target_applied_momentum
                if release_momentum > 0.0:
                    source_delta_vx -= (release_momentum / self.GeoMass(SourceID)) * normal_x
                    source_delta_vy -= (release_momentum / self.GeoMass(SourceID)) * normal_y
            source.report_contacts = len(source.collision_list)
            source.report_phase = state.ids.z
            source.report_target = TargetID
            source.report_center_distance = state.geom.w
            source.report_normal_x = normal_x
            source.report_normal_y = normal_y
            source.report_stored_mom = state.mom.x
            source.report_alpha_zero = alpha_zero
            source.report_zero_area = zero_area
            source.report_compression_fraction = compression_fraction
            source.report_rel_vn = relative_normal_velocity
            source.report_closing_mom = closing_momentum
        source.VelRad.x += source_delta_vx
        source.VelRad.y += source_delta_vy
        source.vx = source.VelRad.x
        source.vy = source.VelRad.y
        return True
