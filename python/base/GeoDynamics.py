class GeoDynamics:
    """GLSL-shaped dynamics functions for the Geo path."""

    GEO_EPSILON = 1.0e-12
    GEO_CONTACT_INACTIVE = 0
    GEO_CONTACT_PARTICLE = 1
    GEO_PHASE_INACTIVE = 0
    GEO_PHASE_COMPRESSION = 1
    GEO_PHASE_RETURNING = 2
    GEO_CONTACT_ACTIVE_THIS_FRAME = 1

    def GeoSetError(self, ErrorReturn):
        """Set the GLSL-style collIn error code and return False."""
        self.collIn.ErrorReturn = ErrorReturn
        return False

    def GeoValidParticleID(self, ParticleID):
        """Return True when ParticleID indexes the current particle buffer."""
        return 0 <= ParticleID < len(self.particles)

    def GeoCurrentLocation(self, ParticleID):
        """Read the current position from ShaderFlags.positionBuffer."""
        return self.particle_position(
            self.particles[ParticleID],
            int(self.ShaderFlags.positionBuffer),
        )

    def GeoMass(self, ParticleID):
        """Return the GLSL-shaped particle mass field."""
        return max(self.particles[ParticleID].parms.x, 1.0e-12)

    def GeoPairStiffness(self, SourceID, TargetID):
        """Return average source/target particle-owned stiffness."""
        source_q = self.particles[SourceID].Data.y or 0.0
        target_q = self.particles[TargetID].Data.y or 0.0
        return max(0.0, 0.5 * (source_q + target_q))

    def GeoContactSlots(self, SourceID):
        """Return the source-owned persistent contact slots."""
        particle = self.particles[SourceID]
        if hasattr(particle, "contacts"):
            return particle.contacts
        return particle.gcs

    def GeoClearContactSlot(self, contact_state):
        contact_state.ids = self.create_uvec4()
        contact_state.geom = self.create_vec4()
        contact_state.aux = self.create_vec4()

    def GeoBeginContactFrame(self, SourceID):
        """Reset current-frame contact flags while preserving active ledgers."""
        source = self.particles[SourceID]
        source.collision_list = []
        source.contactCount = 0
        source.colFlg = 0
        for contact_state in self.GeoContactSlots(SourceID):
            if contact_state.ids.w != self.GEO_CONTACT_ACTIVE_THIS_FRAME:
                self.GeoClearContactSlot(contact_state)
                continue
            contact_state.ids.w = 0
            contact_state.geom = self.create_vec4()
            contact_state.aux.x = 0.0
            contact_state.aux.y = 0.0
            contact_state.aux.w = 0.0

    def GeoFindContactSlot(self, SourceID, TargetID):
        for contact_state in self.GeoContactSlots(SourceID):
            if (
                contact_state.ids.x == TargetID
                and contact_state.ids.y == self.GEO_CONTACT_PARTICLE
            ):
                return contact_state
        return None

    def GeoAllocContactSlot(self, SourceID, TargetID):
        for contact_state in self.GeoContactSlots(SourceID):
            if contact_state.ids.y == self.GEO_CONTACT_INACTIVE:
                contact_state.ids.x = TargetID
                contact_state.ids.y = self.GEO_CONTACT_PARTICLE
                contact_state.ids.z = self.GEO_PHASE_COMPRESSION
                contact_state.ids.w = self.GEO_CONTACT_ACTIVE_THIS_FRAME
                contact_state.aux.z = 0.0
                return contact_state
        return None

    def GeoContactState(self, SourceID, TargetID):
        contact_state = self.GeoFindContactSlot(SourceID, TargetID)
        if contact_state is None:
            contact_state = self.GeoAllocContactSlot(SourceID, TargetID)
        if contact_state is not None:
            contact_state.ids.w = self.GEO_CONTACT_ACTIVE_THIS_FRAME
        return contact_state

    def GeoParticleGeometry(self, SourceID, TargetID):
        """Return current contact geometry or None when there is no contact."""
        source_position = self.GeoCurrentLocation(SourceID)
        target_position = self.GeoCurrentLocation(TargetID)
        dx = target_position.x - source_position.x
        dy = target_position.y - source_position.y
        dz = target_position.z - source_position.z
        center_distance = (dx * dx + dy * dy + dz * dz) ** 0.5
        source_radius = self.particles[SourceID].Data.x
        target_radius = self.particles[TargetID].Data.x
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
        return normal_x, normal_y, normal_z, overlap_area, center_distance

    def GeoVelocity(self, ParticleID):
        """Read frame-start velocity when GeoBase provides it."""
        if hasattr(self, "VelRadFrame") and self.VelRadFrame:
            return self.VelRadFrame[ParticleID]
        return self.particles[ParticleID].VelRad

    def GeoContactContext(self, SourceID):
        source_velocity = self.GeoVelocity(SourceID)
        total_overlap_area = 0.0
        available_source_momentum = 0.0
        for TargetID in range(len(self.particles)):
            if TargetID == SourceID:
                continue
            contact = self.GeoParticleGeometry(SourceID, TargetID)
            if contact is None:
                continue
            normal_x, normal_y, normal_z, overlap_area, _center_distance = contact
            target_velocity = self.GeoVelocity(TargetID)
            relative_normal_velocity = (
                (target_velocity.x - source_velocity.x) * normal_x
                + (target_velocity.y - source_velocity.y) * normal_y
                + (target_velocity.z - source_velocity.z) * normal_z
            )
            source_normal_velocity = (
                source_velocity.x * normal_x
                + source_velocity.y * normal_y
                + source_velocity.z * normal_z
            )
            total_overlap_area += max(0.0, overlap_area)
            if relative_normal_velocity < -self.GEO_EPSILON:
                available_source_momentum = max(
                    available_source_momentum,
                    self.GeoMass(SourceID) * max(0.0, source_normal_velocity),
                )
        return total_overlap_area, available_source_momentum

    def GeoAddParticleContact(self, SourceID, TargetID):
        """Record that SourceID is in contact with TargetID this frame.

        Contact detection and overlap-area calculation happen in GeoBase before
        this function is called.  This function records the current-frame
        contact list and binds it to a source-owned persistent contact slot.
        """
        if not self.GeoValidParticleID(SourceID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_SOURCE_ID)
        if not self.GeoValidParticleID(TargetID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_TARGET_ID)

        particle = self.particles[SourceID]
        if not hasattr(particle, "collision_list"):
            return self.GeoSetError(self.constants.GEO_ERROR_CONTACT_LIST_MISSING)

        if TargetID not in particle.collision_list:
            particle.collision_list.append(TargetID)
        contact_state = self.GeoContactState(SourceID, TargetID)
        if contact_state is None:
            return True
        particle.colFlg = 1
        particle.contactCount = len(particle.collision_list)
        particle.report_contacts = len(particle.collision_list)
        particle.report_target = TargetID
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
        """Apply source-owned geometric response with internal momentum."""
        if not self.GeoValidParticleID(SourceID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_SOURCE_ID)
        source = self.particles[SourceID]
        if not source.collision_list:
            return True

        source_velocity = self.GeoVelocity(SourceID)
        contact_entries = []
        total_overlap_area, available_source_momentum = self.GeoContactContext(SourceID)

        for TargetID in source.collision_list:
            if not self.GeoValidParticleID(TargetID):
                return self.GeoSetError(self.constants.GEO_ERROR_INVALID_TARGET_ID)
            contact = self.GeoParticleGeometry(SourceID, TargetID)
            if contact is None:
                continue
            contact_state = self.GeoContactState(SourceID, TargetID)
            if contact_state is None:
                continue

            normal_x, normal_y, normal_z, overlap_area, center_distance = contact
            target_velocity = self.GeoVelocity(TargetID)
            relative_normal_velocity = (
                (target_velocity.x - source_velocity.x) * normal_x
                + (target_velocity.y - source_velocity.y) * normal_y
                + (target_velocity.z - source_velocity.z) * normal_z
            )
            source_normal_velocity = (
                source_velocity.x * normal_x
                + source_velocity.y * normal_y
                + source_velocity.z * normal_z
            )
            contact_entries.append(
                (
                    TargetID,
                    contact_state,
                    normal_x,
                    normal_y,
                    normal_z,
                    overlap_area,
                    center_distance,
                    relative_normal_velocity,
                    source_normal_velocity,
                )
            )

        if not contact_entries or total_overlap_area <= self.GEO_EPSILON:
            return True

        delta_momentum_x = 0.0
        delta_momentum_y = 0.0
        delta_momentum_z = 0.0
        report_target = 0
        report_center_distance = 0.0
        report_normal_x = 0.0
        report_normal_y = 0.0
        report_stored_mom = 0.0
        report_rel_vn = 0.0
        report_closing_mom = 0.0
        report_stiffness_q = 0.0

        for entry_index, entry in enumerate(contact_entries):
            (
                TargetID,
                contact_state,
                normal_x,
                normal_y,
                normal_z,
                overlap_area,
                center_distance,
                relative_normal_velocity,
                _source_normal_velocity,
            ) = entry
            area_weight = max(0.0, overlap_area / total_overlap_area)
            target_total_overlap_area, target_available_momentum = self.GeoContactContext(TargetID)
            target_area_weight = (
                max(0.0, overlap_area / target_total_overlap_area)
                if target_total_overlap_area > self.GEO_EPSILON
                else 0.0
            )
            stiffness_q = self.GeoPairStiffness(SourceID, TargetID)
            raw_impulse = stiffness_q * overlap_area * self.ShaderFlags.dt
            source_available_share = available_source_momentum * area_weight
            target_available_share = target_available_momentum * target_area_weight
            weighted_available_momentum = min(source_available_share, target_available_share)
            stored_internal_momentum = max(0.0, contact_state.aux.z)
            applied_impulse = 0.0

            if (
                contact_state.ids.z != self.GEO_PHASE_RETURNING
                and relative_normal_velocity < -self.GEO_EPSILON
            ):
                compression_impulse = min(raw_impulse, weighted_available_momentum)
                applied_impulse += compression_impulse
                stored_internal_momentum += compression_impulse
                if compression_impulse < raw_impulse:
                    contact_state.ids.z = self.GEO_PHASE_RETURNING
                else:
                    contact_state.ids.z = self.GEO_PHASE_COMPRESSION

            if contact_state.ids.z == self.GEO_PHASE_RETURNING:
                release_impulse = min(raw_impulse, stored_internal_momentum)
                applied_impulse += release_impulse
                stored_internal_momentum -= release_impulse
                if stored_internal_momentum <= self.GEO_EPSILON:
                    stored_internal_momentum = 0.0

            contact_state.aux.z = stored_internal_momentum
            delta_momentum_x -= applied_impulse * normal_x
            delta_momentum_y -= applied_impulse * normal_y
            delta_momentum_z -= applied_impulse * normal_z

            contact_state.geom = self.create_vec4(normal_x, normal_y, normal_z, overlap_area)
            contact_state.aux.x = center_distance
            contact_state.aux.y = source.Data.x + self.particles[TargetID].Data.x - center_distance
            contact_state.aux.w = applied_impulse

            if entry_index == 0:
                report_target = TargetID
                report_center_distance = center_distance
                report_normal_x = normal_x
                report_normal_y = normal_y
                report_rel_vn = relative_normal_velocity
                report_stiffness_q = stiffness_q
            report_stored_mom += stored_internal_momentum
            report_closing_mom += applied_impulse

        source.VelRad.x += delta_momentum_x / self.GeoMass(SourceID)
        source.VelRad.y += delta_momentum_y / self.GeoMass(SourceID)
        source.VelRad.z += delta_momentum_z / self.GeoMass(SourceID)
        source.vx = source.VelRad.x
        source.vy = source.VelRad.y
        source.vz = source.VelRad.z

        source.report_contacts = len(source.collision_list)
        source.report_target = report_target
        source.report_center_distance = report_center_distance
        source.report_normal_x = report_normal_x
        source.report_normal_y = report_normal_y
        source.report_stored_mom = report_stored_mom
        source.report_alpha_zero = 0.0
        source.report_zero_area = 0.0
        source.report_compression_fraction = 0.0
        source.report_rel_vn = report_rel_vn
        source.report_closing_mom = report_closing_mom
        source.report_collision_stiffness_q = report_stiffness_q
        return True
