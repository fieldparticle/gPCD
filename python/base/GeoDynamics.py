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
        """Read the frame-start position when GeoBase provides it."""
        if hasattr(self, "PosLocFrame") and self.PosLocFrame:
            return self.PosLocFrame[ParticleID]
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

    def GeoReducedMass(self, SourceID, TargetID):
        source_mass = self.GeoMass(SourceID)
        target_mass = self.GeoMass(TargetID)
        return (source_mass * target_mass) / (source_mass + target_mass)

    def GeoContactSlots(self, SourceID):
        """Return the source-owned current-frame contact slots."""
        particle = self.particles[SourceID]
        if hasattr(particle, "contacts"):
            return particle.contacts
        return particle.gcs

    def GeoClearContactDiagnostics(self, contact_state):
        """Reset reporting-only contact diagnostics for the current frame."""
        contact_state.raw_impulse = 0.0
        contact_state.compression_impulse = 0.0
        contact_state.release_impulse = 0.0
        contact_state.source_available_momentum = 0.0
        contact_state.source_available_share = 0.0
        contact_state.target_available_momentum = 0.0
        contact_state.target_available_share = 0.0
        contact_state.weighted_available_momentum = 0.0
        contact_state.source_vn = 0.0
        contact_state.target_vn = 0.0
        contact_state.rel_vn = 0.0
        contact_state.delta_px = 0.0
        contact_state.delta_py = 0.0
        contact_state.delta_pz = 0.0
        contact_state.source_vx_before = 0.0
        contact_state.source_vy_before = 0.0
        contact_state.source_vz_before = 0.0
        contact_state.source_vx_after = 0.0
        contact_state.source_vy_after = 0.0
        contact_state.source_vz_after = 0.0
        contact_state.source_ke_before = 0.0
        contact_state.source_ke_after = 0.0
        contact_state.source_ke_delta = 0.0
        contact_state.contact_ke_delta_estimate = 0.0

    def GeoClearContactSlot(self, contact_state):
        contact_state.ids = self.create_uvec4()
        contact_state.geom = self.create_vec4()
        contact_state.aux = self.create_vec4()
        self.GeoClearContactDiagnostics(contact_state)

    def GeoSetInternalMomentum(self, SourceID, internal_momentum):
        """Store source-owned internal momentum on the particle."""
        particle = self.particles[SourceID]
        particle.internal_momentum = max(0.0, internal_momentum)
        particle.Data.z = particle.internal_momentum

    def GeoInternalMomentum(self, SourceID):
        """Return source-owned internal momentum."""
        particle = self.particles[SourceID]
        contact_momentum = getattr(particle, "contact_internal_momentum", None)
        if contact_momentum is not None:
            return sum(max(0.0, momentum) for momentum in contact_momentum.values())
        return max(0.0, getattr(particle, "internal_momentum", particle.Data.z))

    def GeoSyncInternalMomentum(self, SourceID):
        """Update the source total from contact-owned ledgers."""
        self.GeoSetInternalMomentum(SourceID, self.GeoInternalMomentum(SourceID))

    def GeoContactInternalMomentum(self, SourceID, TargetID):
        source = self.particles[SourceID]
        ledgers = getattr(source, "contact_internal_momentum", None)
        if ledgers is None:
            source.contact_internal_momentum = {}
            ledgers = source.contact_internal_momentum
        return max(0.0, ledgers.get(TargetID, 0.0))

    def GeoSetContactInternalMomentum(self, SourceID, TargetID, internal_momentum):
        source = self.particles[SourceID]
        if not hasattr(source, "contact_internal_momentum"):
            source.contact_internal_momentum = {}
        internal_momentum = max(0.0, internal_momentum)
        if internal_momentum <= self.GEO_EPSILON:
            source.contact_internal_momentum.pop(TargetID, None)
        else:
            source.contact_internal_momentum[TargetID] = internal_momentum
        self.GeoSyncInternalMomentum(SourceID)

    def GeoContactInternalPhase(self, SourceID, TargetID):
        source = self.particles[SourceID]
        phases = getattr(source, "contact_internal_phase", None)
        if phases is None:
            source.contact_internal_phase = {}
            phases = source.contact_internal_phase
        return phases.get(TargetID, self.GEO_PHASE_COMPRESSION)

    def GeoSetContactInternalPhase(self, SourceID, TargetID, phase):
        source = self.particles[SourceID]
        if not hasattr(source, "contact_internal_phase"):
            source.contact_internal_phase = {}
        if phase == self.GEO_PHASE_COMPRESSION and self.GeoContactInternalMomentum(SourceID, TargetID) <= self.GEO_EPSILON:
            source.contact_internal_phase.pop(TargetID, None)
        else:
            source.contact_internal_phase[TargetID] = phase

    def GeoPruneInactiveContactLedgers(self, SourceID):
        """Keep contact memory tied to contacts active in the current frame."""
        source = self.particles[SourceID]
        active_targets = set(getattr(source, "collision_list", []))
        if hasattr(source, "contact_internal_momentum"):
            for TargetID in list(source.contact_internal_momentum.keys()):
                if TargetID not in active_targets:
                    source.contact_internal_momentum.pop(TargetID, None)
        if hasattr(source, "contact_internal_phase"):
            for TargetID in list(source.contact_internal_phase.keys()):
                if TargetID not in active_targets:
                    source.contact_internal_phase.pop(TargetID, None)
        self.GeoSyncInternalMomentum(SourceID)

    def GeoBeginContactFrame(self, SourceID):
        """Reset current-frame contact slots while preserving source ledgers."""
        source = self.particles[SourceID]
        source.collision_list = []
        source.contactCount = 0
        source.colFlg = 0
        for contact_state in self.GeoContactSlots(SourceID):
            self.GeoClearContactSlot(contact_state)

    def GeoAppendContactSlot(self, SourceID, TargetID):
        source = self.particles[SourceID]
        contact_slots = self.GeoContactSlots(SourceID)
        if source.contactCount >= len(contact_slots):
            return None
        contact_state = contact_slots[source.contactCount]
        contact_state.ids.x = TargetID
        contact_state.ids.y = self.GEO_CONTACT_PARTICLE
        contact_state.ids.z = self.GeoContactInternalPhase(SourceID, TargetID)
        contact_state.ids.w = self.GEO_CONTACT_ACTIVE_THIS_FRAME
        contact_state.aux.z = self.GeoContactInternalMomentum(SourceID, TargetID)
        source.contactCount += 1
        return contact_state

    def GeoContactState(self, SourceID, TargetID):
        return self.GeoAppendContactSlot(SourceID, TargetID)

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
            total_overlap_area += max(0.0, overlap_area)
            if relative_normal_velocity < -self.GEO_EPSILON:
                available_source_momentum += (
                    self.GeoReducedMass(SourceID, TargetID)
                    * -relative_normal_velocity
                )
        return total_overlap_area, available_source_momentum

    @staticmethod
    def GeoScaledImpulseParts(compression_impulse, release_impulse, planned_impulse):
        candidate_impulse = compression_impulse + release_impulse
        if candidate_impulse <= 1.0e-12:
            return 0.0, 0.0
        scale = max(0.0, min(1.0, planned_impulse / candidate_impulse))
        return compression_impulse * scale, release_impulse * scale

    def GeoDirectedContactCandidate(
        self,
        SourceID,
        TargetID,
        source_total_overlap_area,
        available_source_momentum,
        contact_internal_momentum,
        contact_phase_start,
    ):
        contact = self.GeoParticleGeometry(SourceID, TargetID)
        if contact is None or source_total_overlap_area <= self.GEO_EPSILON:
            return None

        normal_x, normal_y, normal_z, overlap_area, center_distance = contact
        source_velocity = self.GeoVelocity(SourceID)
        target_velocity = self.GeoVelocity(TargetID)
        relative_normal_velocity = (
            (target_velocity.x - source_velocity.x) * normal_x
            + (target_velocity.y - source_velocity.y) * normal_y
            + (target_velocity.z - source_velocity.z) * normal_z
        )
        target_total_overlap_area, target_available_momentum = self.GeoContactContext(TargetID)
        area_weight = max(0.0, overlap_area / source_total_overlap_area)
        target_area_weight = (
            max(0.0, overlap_area / target_total_overlap_area)
            if target_total_overlap_area > self.GEO_EPSILON
            else 0.0
        )
        raw_impulse = (
            self.GeoPairStiffness(SourceID, TargetID)
            * overlap_area
            * self.ShaderFlags.dt
        )
        source_available_share = available_source_momentum * area_weight
        target_available_share = target_available_momentum * target_area_weight
        weighted_available_momentum = min(source_available_share, target_available_share)
        compression_impulse = 0.0
        release_impulse = 0.0
        stored_internal_momentum = contact_internal_momentum
        contact_phase = contact_phase_start

        if (
            contact_phase_start != self.GEO_PHASE_RETURNING
            and relative_normal_velocity < -self.GEO_EPSILON
        ):
            compression_impulse = min(raw_impulse, weighted_available_momentum)
            stored_internal_momentum += compression_impulse
            contact_phase = (
                self.GEO_PHASE_RETURNING
                if compression_impulse < raw_impulse
                else self.GEO_PHASE_COMPRESSION
            )

        if contact_phase == self.GEO_PHASE_RETURNING:
            release_capacity = contact_internal_momentum + compression_impulse
            release_impulse = min(raw_impulse, release_capacity, stored_internal_momentum)
            stored_internal_momentum -= release_impulse
            if stored_internal_momentum <= self.GEO_EPSILON:
                stored_internal_momentum = 0.0

        return {
            "candidate_impulse": compression_impulse + release_impulse,
            "compression_impulse": compression_impulse,
            "release_impulse": release_impulse,
            "stored_internal_momentum": stored_internal_momentum,
            "phase": contact_phase,
            "raw_impulse": raw_impulse,
        }

    def GeoPlanContactImpulses(self):
        """Plan one frame-local impulse magnitude for each unordered pair."""
        directed_candidates = {}
        for SourceID, source in enumerate(self.particles):
            if not source.collision_list:
                continue
            total_overlap_area, available_source_momentum = self.GeoContactContext(SourceID)
            for TargetID in source.collision_list:
                candidate = self.GeoDirectedContactCandidate(
                    SourceID,
                    TargetID,
                    total_overlap_area,
                    available_source_momentum,
                    self.GeoContactInternalMomentum(SourceID, TargetID),
                    self.GeoContactInternalPhase(SourceID, TargetID),
                )
                if candidate is None:
                    continue
                directed_candidates[(SourceID, TargetID)] = candidate

        planned = {}
        handled_pairs = set()
        for SourceID, TargetID in directed_candidates:
            pair_key = tuple(sorted((SourceID, TargetID)))
            if pair_key in handled_pairs:
                continue
            handled_pairs.add(pair_key)
            source_candidate = directed_candidates.get((SourceID, TargetID))
            target_candidate = directed_candidates.get((TargetID, SourceID))
            if target_candidate is None:
                planned_impulse = source_candidate["candidate_impulse"]
            else:
                planned_impulse = min(
                    source_candidate["candidate_impulse"],
                    target_candidate["candidate_impulse"],
                )
            for DirectedSourceID, DirectedTargetID in (
                (SourceID, TargetID),
                (TargetID, SourceID),
            ):
                candidate = directed_candidates.get((DirectedSourceID, DirectedTargetID))
                if candidate is None:
                    continue
                compression_impulse, release_impulse = self.GeoScaledImpulseParts(
                    candidate["compression_impulse"],
                    candidate["release_impulse"],
                    planned_impulse,
                )
                planned[(DirectedSourceID, DirectedTargetID)] = {
                    "applied_impulse": compression_impulse + release_impulse,
                    "compression_impulse": compression_impulse,
                    "release_impulse": release_impulse,
                    "phase": candidate["phase"],
                }

        self.GeoPlannedContactImpulses = planned
        return True

    def GeoAddParticleContact(self, SourceID, TargetID):
        """Record that SourceID is in contact with TargetID this frame.

        Contact detection and overlap-area calculation happen in GeoBase before
        this function is called. This function appends the current-frame contact
        to the next indexed source-owned slot.
        """
        if not self.GeoValidParticleID(SourceID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_SOURCE_ID)
        if not self.GeoValidParticleID(TargetID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_TARGET_ID)

        particle = self.particles[SourceID]
        if not hasattr(particle, "collision_list"):
            return self.GeoSetError(self.constants.GEO_ERROR_CONTACT_LIST_MISSING)

        if TargetID in particle.collision_list:
            return True
        particle.collision_list.append(TargetID)
        contact_state = self.GeoContactState(SourceID, TargetID)
        if contact_state is None:
            return True
        particle.colFlg = 1
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
        self.GeoPruneInactiveContactLedgers(SourceID)
        if not source.collision_list:
            return True

        source_velocity = self.GeoVelocity(SourceID)
        source_mass = self.GeoMass(SourceID)
        source_vx_before = source.VelRad.x
        source_vy_before = source.VelRad.y
        source_vz_before = source.VelRad.z
        source_ke_before = 0.5 * source_mass * (
            source_vx_before * source_vx_before
            + source_vy_before * source_vy_before
            + source_vz_before * source_vz_before
        )
        contact_entries = []
        total_overlap_area, available_source_momentum = self.GeoContactContext(SourceID)

        for contact_index, TargetID in enumerate(source.collision_list):
            if not self.GeoValidParticleID(TargetID):
                return self.GeoSetError(self.constants.GEO_ERROR_INVALID_TARGET_ID)
            contact = self.GeoParticleGeometry(SourceID, TargetID)
            if contact is None:
                continue
            contact_slots = self.GeoContactSlots(SourceID)
            if contact_index >= len(contact_slots):
                continue
            contact_state = contact_slots[contact_index]

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
            target_normal_velocity = (
                target_velocity.x * normal_x
                + target_velocity.y * normal_y
                + target_velocity.z * normal_z
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
                    target_normal_velocity,
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
                source_normal_velocity,
                target_normal_velocity,
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
            contact_internal_momentum = self.GeoContactInternalMomentum(SourceID, TargetID)
            contact_phase_start = self.GeoContactInternalPhase(SourceID, TargetID)
            stored_internal_momentum = contact_internal_momentum
            contact_phase = contact_phase_start
            applied_impulse = 0.0
            compression_impulse = 0.0
            release_impulse = 0.0

            if (
                contact_phase_start != self.GEO_PHASE_RETURNING
                and relative_normal_velocity < -self.GEO_EPSILON
            ):
                compression_impulse = min(raw_impulse, weighted_available_momentum)
                applied_impulse += compression_impulse
                stored_internal_momentum += compression_impulse
                if compression_impulse < raw_impulse:
                    contact_phase = self.GEO_PHASE_RETURNING
                else:
                    contact_phase = self.GEO_PHASE_COMPRESSION

            if contact_phase == self.GEO_PHASE_RETURNING:
                release_capacity = contact_internal_momentum + compression_impulse
                release_impulse = min(raw_impulse, release_capacity, stored_internal_momentum)
                applied_impulse += release_impulse
                stored_internal_momentum -= release_impulse
                if stored_internal_momentum <= self.GEO_EPSILON:
                    stored_internal_momentum = 0.0

            planned_impulse = getattr(self, "GeoPlannedContactImpulses", {}).get(
                (SourceID, TargetID)
            )
            if planned_impulse is not None:
                compression_impulse = planned_impulse["compression_impulse"]
                release_impulse = planned_impulse["release_impulse"]
                applied_impulse = planned_impulse["applied_impulse"]
                contact_phase = planned_impulse["phase"]
                stored_internal_momentum = max(
                    0.0,
                    contact_internal_momentum + compression_impulse - release_impulse,
                )

            self.GeoSetContactInternalMomentum(SourceID, TargetID, stored_internal_momentum)
            if stored_internal_momentum <= self.GEO_EPSILON:
                contact_phase = self.GEO_PHASE_COMPRESSION
            self.GeoSetContactInternalPhase(SourceID, TargetID, contact_phase)
            contact_state.ids.z = contact_phase
            contact_state.aux.z = stored_internal_momentum
            contact_delta_px = -applied_impulse * normal_x
            contact_delta_py = -applied_impulse * normal_y
            contact_delta_pz = -applied_impulse * normal_z
            delta_momentum_x += contact_delta_px
            delta_momentum_y += contact_delta_py
            delta_momentum_z += contact_delta_pz

            contact_state.geom = self.create_vec4(normal_x, normal_y, normal_z, overlap_area)
            contact_state.aux.x = center_distance
            contact_state.aux.y = source.Data.x + self.particles[TargetID].Data.x - center_distance
            contact_state.aux.w = applied_impulse
            contact_state.raw_impulse = raw_impulse
            contact_state.compression_impulse = compression_impulse
            contact_state.release_impulse = release_impulse
            contact_state.source_available_momentum = available_source_momentum
            contact_state.source_available_share = source_available_share
            contact_state.target_available_momentum = target_available_momentum
            contact_state.target_available_share = target_available_share
            contact_state.weighted_available_momentum = weighted_available_momentum
            contact_state.source_vn = source_normal_velocity
            contact_state.target_vn = target_normal_velocity
            contact_state.rel_vn = relative_normal_velocity
            contact_state.delta_px = contact_delta_px
            contact_state.delta_py = contact_delta_py
            contact_state.delta_pz = contact_delta_pz
            contact_state.source_vx_before = source_vx_before
            contact_state.source_vy_before = source_vy_before
            contact_state.source_vz_before = source_vz_before
            contact_state.source_ke_before = source_ke_before
            contact_state.contact_ke_delta_estimate = (
                source_vx_before * contact_delta_px
                + source_vy_before * contact_delta_py
                + source_vz_before * contact_delta_pz
                + (
                    contact_delta_px * contact_delta_px
                    + contact_delta_py * contact_delta_py
                    + contact_delta_pz * contact_delta_pz
                )
                / (2.0 * source_mass)
            )

            if entry_index == 0:
                report_target = TargetID
                report_center_distance = center_distance
                report_normal_x = normal_x
                report_normal_y = normal_y
                report_rel_vn = relative_normal_velocity
                report_stiffness_q = stiffness_q
            report_closing_mom += applied_impulse

        source.VelRad.x += delta_momentum_x / source_mass
        source.VelRad.y += delta_momentum_y / source_mass
        source.VelRad.z += delta_momentum_z / source_mass
        self.GeoSyncInternalMomentum(SourceID)
        source.vx = source.VelRad.x
        source.vy = source.VelRad.y
        source.vz = source.VelRad.z
        source_ke_after = 0.5 * source_mass * (
            source.VelRad.x * source.VelRad.x
            + source.VelRad.y * source.VelRad.y
            + source.VelRad.z * source.VelRad.z
        )
        for _entry in contact_entries:
            contact_state = _entry[1]
            contact_state.source_vx_after = source.VelRad.x
            contact_state.source_vy_after = source.VelRad.y
            contact_state.source_vz_after = source.VelRad.z
            contact_state.source_ke_after = source_ke_after
            contact_state.source_ke_delta = source_ke_after - source_ke_before

        source.report_contacts = len(source.collision_list)
        source.report_target = report_target
        source.report_center_distance = report_center_distance
        source.report_normal_x = report_normal_x
        source.report_normal_y = report_normal_y
        source.report_stored_mom = self.GeoInternalMomentum(SourceID)
        source.report_alpha_zero = 0.0
        source.report_zero_area = 0.0
        source.report_compression_fraction = 0.0
        source.report_rel_vn = report_rel_vn
        source.report_closing_mom = report_closing_mom
        source.report_collision_stiffness_q = report_stiffness_q
        return True
