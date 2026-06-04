class ShadowDynamics:
    """GLSL-shaped dynamics functions for the shadow path."""

    GEO_EPSILON = 1.0e-12
    GEO_CONTACT_INACTIVE = 0
    GEO_CONTACT_PARTICLE = 1
    GEO_PHASE_INACTIVE = 0
    GEO_PHASE_COMPRESSION = 1
    GEO_PHASE_RETURNING = 2
    GEO_CONTACT_ACTIVE_THIS_FRAME = 1
    GEO_PZERO_VELOCITY_FRACTION = 0.02

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
        """Return the two-particle reduced mass for a contact pair.

        Reduced mass converts relative normal velocity into contact normal
        momentum:

            p_n = mu * v_n

        where:

            mu = (m_source * m_target) / (m_source + m_target)

        The mass values come from the GLSL-shaped particle parms.x field via
        GeoMass().
        """
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
        contact_state.source_net_delta_px = 0.0
        contact_state.source_net_delta_py = 0.0
        contact_state.source_net_delta_pz = 0.0
        contact_state.source_net_ke_delta_estimate = 0.0
        contact_state.source_contact_ke_delta_sum = 0.0
        contact_state.source_ke_cross_term = 0.0
        contact_state.source_ke_residual = 0.0

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

    def GeoContactVelocityReference(self, SourceID, TargetID):
        source = self.particles[SourceID]
        references = getattr(source, "contact_velocity_reference", None)
        if references is None:
            source.contact_velocity_reference = {}
            references = source.contact_velocity_reference
        return max(0.0, references.get(TargetID, 0.0))

    def GeoSetContactVelocityReference(self, SourceID, TargetID, velocity_reference):
        source = self.particles[SourceID]
        if not hasattr(source, "contact_velocity_reference"):
            source.contact_velocity_reference = {}
        velocity_reference = max(0.0, velocity_reference)
        if velocity_reference <= self.GEO_EPSILON:
            source.contact_velocity_reference.pop(TargetID, None)
        else:
            source.contact_velocity_reference[TargetID] = velocity_reference

    def GeoContactReboundReference(self, SourceID, TargetID):
        source = self.particles[SourceID]
        references = getattr(source, "contact_rebound_reference", None)
        if references is None:
            source.contact_rebound_reference = {}
            references = source.contact_rebound_reference
        return max(0.0, references.get(TargetID, 0.0))

    def GeoSetContactReboundReference(self, SourceID, TargetID, rebound_reference):
        source = self.particles[SourceID]
        if not hasattr(source, "contact_rebound_reference"):
            source.contact_rebound_reference = {}
        rebound_reference = max(0.0, rebound_reference)
        if rebound_reference <= self.GEO_EPSILON:
            source.contact_rebound_reference.pop(TargetID, None)
        else:
            source.contact_rebound_reference[TargetID] = rebound_reference

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
        if hasattr(source, "contact_velocity_reference"):
            for TargetID in list(source.contact_velocity_reference.keys()):
                if TargetID not in active_targets:
                    source.contact_velocity_reference.pop(TargetID, None)
        if hasattr(source, "contact_rebound_reference"):
            for TargetID in list(source.contact_rebound_reference.keys()):
                if TargetID not in active_targets:
                    source.contact_rebound_reference.pop(TargetID, None)
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
        """Return frame-snapshot contact geometry for a source-target pair.

        Positions are read through GeoCurrentLocation(), so this geometry is
        based on the frame-start snapshot when one exists.  If the two particle
        radii do not overlap, return None.

        When a contact exists, return:

        (normal_x, normal_y, normal_z, overlap_area, center_distance)

        The normal points from the source center toward the target center.
        overlap_area is the circular overlap area used by the current
        geometric impulse rule.  If the centers coincide, the normal defaults
        to +x so the response has a deterministic direction.
        """
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

    def GeoStartFrameVelocity(self, ParticleID):
        """Read the particle velocity from the frame-start snapshot."""
        if hasattr(self, "VelRadFrame") and self.VelRadFrame:
            return self.VelRadFrame[ParticleID]
        return self.particles[ParticleID].VelRad

    def GeoContactContext(self, SourceID):
        """Return source-level contact context for the current frame.

        The context is computed from the frame snapshot, not from partially
        updated particle state.  It consumes the already-built source
        collision_list and accumulates:

        - total_overlap_area: the sum of positive overlap areas for all current
          contacts touching this source;
        - available_source_momentum: the sum of reduced-mass closing normal
          momentum for contacts whose relative normal velocity is closing.

        Later planning uses total_overlap_area to compute contact weights and
        available_source_momentum to limit how much source compression capacity
        can be distributed across the source's active contacts.
        """
        source_velocity = self.GeoStartFrameVelocity(SourceID)
        total_overlap_area = 0.0
        available_source_momentum = 0.0
        for TargetID in self.particles[SourceID].collision_list:
            # Get the current frame contact geometry. 
            #  If the geometry is invalid, skip this contact.
            # geoetry is normal_x, normal_y, normal_z, overlap_area,
            # _center_distance
            contact = self.GeoParticleGeometry(SourceID, TargetID)
            if contact is None:
                continue
            normal_x, normal_y, normal_z, overlap_area, _center_distance = contact
            # Get the starting frame velocity snapshot for the target.  
            target_velocity = self.GeoStartFrameVelocity(TargetID)
            # Calcuate the relative normal velocity from the frame-start snapshot.
            relative_normal_velocity = (
                (target_velocity.x - source_velocity.x) * normal_x
                + (target_velocity.y - source_velocity.y) * normal_y
                + (target_velocity.z - source_velocity.z) * normal_z
            )
            # Sum the positive overlap area for all contacts.  
            # This is used to compute contact weights for distributing the source's 
            # available momentum across
            total_overlap_area += max(0.0, overlap_area)
            # For contacts that are closing (negative relative normal velocity), 
            # sum the available source momentum.
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


    def GeoVelocityProgressImpulse(
        self,
        SourceID,
        TargetID,
        relative_normal_velocity,
        contact_internal_momentum,
        contact_phase_start,
        raw_impulse,
        weighted_available_momentum,
    ):
        """Convert relative normal velocity progress into contact impulses.

        This function owns the compression/rebound decision for one directed
        source-target contact.  It reads the contact's persistent velocity
        reference and phase, then returns the scalar compression impulse,
        rebound release impulse, updated internal momentum, and updated phase.

        Compression uses the current closing normal velocity relative to the
        stored velocity reference.  Rebound uses the stored internal momentum
        and rebound reference to release momentum back into velocity.  No
        particle velocity is written here; the returned impulses are still part
        of planning and are applied later by contact resolution.
        """
        reduced_mass = self.GeoReducedMass(SourceID, TargetID)
        closing_speed = max(0.0, -relative_normal_velocity)
        separating_speed = max(0.0, relative_normal_velocity)
        velocity_reference = self.GeoContactVelocityReference(SourceID, TargetID)

        if velocity_reference <= self.GEO_EPSILON and closing_speed > self.GEO_EPSILON:
            velocity_reference = closing_speed
            self.GeoSetContactVelocityReference(SourceID, TargetID, velocity_reference)

        if velocity_reference <= self.GEO_EPSILON or reduced_mass <= self.GEO_EPSILON:
            return 0.0, 0.0, contact_internal_momentum, self.GEO_PHASE_COMPRESSION

        velocity_tolerance = velocity_reference * 0.01
        contact_phase = contact_phase_start
        if (
            contact_phase == self.GEO_PHASE_COMPRESSION
            and closing_speed <= velocity_tolerance
            and contact_internal_momentum > self.GEO_EPSILON
        ):
            contact_phase = self.GEO_PHASE_RETURNING
            self.GeoSetContactReboundReference(
                SourceID,
                TargetID,
                contact_internal_momentum,
            )

        if contact_phase == self.GEO_PHASE_RETURNING:
            compression_impulse = 0.0
            release_seed = raw_impulse if raw_impulse > self.GEO_EPSILON else contact_internal_momentum
            released_momentum = max(
                0.0,
                self.GeoContactReboundReference(SourceID, TargetID)
                - contact_internal_momentum,
            )
            rebound_reference = self.GeoContactReboundReference(SourceID, TargetID)
            if rebound_reference <= self.GEO_EPSILON:
                rebound_reference = contact_internal_momentum
                self.GeoSetContactReboundReference(SourceID, TargetID, rebound_reference)
            release_progress = min(
                1.0,
                (released_momentum + release_seed) / rebound_reference,
            )
            target_separating_speed = velocity_reference * release_progress
            current_normal_momentum = reduced_mass * separating_speed
            target_normal_momentum = reduced_mass * target_separating_speed
            release_impulse = max(0.0, target_normal_momentum - current_normal_momentum)
            release_impulse = min(contact_internal_momentum, release_impulse)
            if release_impulse <= self.GEO_EPSILON and raw_impulse <= self.GEO_EPSILON:
                release_impulse = contact_internal_momentum
            stored_internal_momentum = max(
                0.0,
                contact_internal_momentum - release_impulse,
            )
            if stored_internal_momentum <= self.GEO_EPSILON:
                contact_phase = self.GEO_PHASE_COMPRESSION
            return (
                compression_impulse,
                release_impulse,
                stored_internal_momentum,
                contact_phase,
            )

        seed_impulse = 0.0
        if closing_speed > self.GEO_EPSILON:
            seed_impulse = min(raw_impulse, weighted_available_momentum)
        speed_for_progress = max(0.0, closing_speed - seed_impulse / reduced_mass)
        velocity_progress = 1.0 - (
            min(speed_for_progress, velocity_reference)
            / velocity_reference
        )
        velocity_progress = max(0.0, min(1.0, velocity_progress))
        target_closing_speed = velocity_reference * (1.0 - velocity_progress)
        current_normal_momentum = reduced_mass * closing_speed
        target_normal_momentum = reduced_mass * target_closing_speed
        compression_impulse = max(
            0.0,
            current_normal_momentum - target_normal_momentum,
        )
        release_impulse = 0.0

        stored_internal_momentum = max(
            0.0,
            contact_internal_momentum + compression_impulse - release_impulse,
        )
        if stored_internal_momentum <= self.GEO_EPSILON:
            contact_phase = self.GEO_PHASE_COMPRESSION
            self.GeoSetContactReboundReference(SourceID, TargetID, 0.0)

        return (
            compression_impulse,
            release_impulse,
            stored_internal_momentum,
            contact_phase,
        )

    def GeoReboundProfileImpulse(
        self,
        SourceID,
        TargetID,
        contact_internal_momentum,
        raw_impulse,
    ):
        """Return stored momentum through the parabolic rebound profile."""
        if contact_internal_momentum <= self.GEO_EPSILON:
            return 0.0
        rebound_reference = self.GeoContactReboundReference(SourceID, TargetID)
        if rebound_reference <= self.GEO_EPSILON:
            rebound_reference = contact_internal_momentum
            self.GeoSetContactReboundReference(SourceID, TargetID, rebound_reference)
        release_seed = raw_impulse if raw_impulse > self.GEO_EPSILON else contact_internal_momentum
        released_momentum = max(0.0, rebound_reference - contact_internal_momentum)
        release_progress = min(
            1.0,
            (released_momentum + release_seed) / rebound_reference,
        )
        remaining_target = rebound_reference * (1.0 - release_progress) ** 2.0
        release_impulse = max(0.0, contact_internal_momentum - remaining_target)
        if release_impulse > self.GEO_EPSILON:
            return min(contact_internal_momentum, release_impulse)
        if raw_impulse <= self.GEO_EPSILON:
            return contact_internal_momentum
        return min(contact_internal_momentum, raw_impulse)

    def GeoCalculatePairContact(
        self,
        SourceID,
        TargetID,
        source_total_overlap_area,
        available_source_momentum,
        contact_internal_momentum,
        contact_phase_start,
    ):
        """Build one directed source-to-target impulse candidate.

        A directed candidate is the proposed response for one source particle
        writing only itself because it is in contact with one target particle.
        The reverse direction, TargetID -> SourceID, is built separately when
        the target is processed as a source.

        This function:
        - recomputes the current frame contact geometry for this active
          source-target pair;
        - computes relative normal velocity from the frame-start velocity
          snapshot;
        - computes source and target area weights from each particle's current
          contact context;
        - computes the raw overlap/stiffness impulse;
        - limits compression by the weighted source/target available momentum;
        - asks GeoVelocityProgressImpulse() for compression, release, updated
          stored internal momentum, and contact phase.

        The returned dictionary is still a candidate.  It is not applied
        directly.  GeoBuildPairCompatiblePlan() later reconciles this directed
        candidate with the opposite directed candidate so both source-owned
        writes use compatible scalar impulses.
        """
        contact = self.GeoParticleGeometry(SourceID, TargetID)
        if contact is None or source_total_overlap_area <= self.GEO_EPSILON:
            return None
        # Calulate relative velocity for this pair
        normal_x, normal_y, normal_z, overlap_area, center_distance = contact
        source_velocity = self.GeoStartFrameVelocity(SourceID)
        target_velocity = self.GeoStartFrameVelocity(TargetID)
        relative_normal_velocity = (
            (target_velocity.x - source_velocity.x) * normal_x
            + (target_velocity.y - source_velocity.y) * normal_y
            + (target_velocity.z - source_velocity.z) * normal_z
        )

        # Get the target's contact context for area weighting and momentum limiting.
        target_total_overlap_area, target_available_momentum = self.GeoContactContext(TargetID)
        # The area weight is the fraction of the source's total overlap area 
        # that this contact represents.
        area_weight = max(0.0, overlap_area / source_total_overlap_area)
        # The target area weight is the fraction of the target's total overlap area
        target_area_weight = (
            max(0.0, overlap_area / target_total_overlap_area)
            if target_total_overlap_area > self.GEO_EPSILON
            else 0.0
        )
        # The raw impulse is the GLSL-shaped stiffness-area 
        # impulse without any velocity or momentum limiting applied.  
        # It is used as a seed for the velocity-progress-based 
        # compression and release impulses, and it is also 
        # reported for diagnostics.
        raw_impulse = (
            self.GeoPairStiffness(SourceID, TargetID)
            * overlap_area
            * self.ShaderFlags.dt
        )
        # The source share is this source contact's fraction of the source's
        # available closing momentum.  The target share is a pair-compatibility
        # cap: this directed source candidate should not claim more closing
        # momentum than the opposite side of the same physical contact can
        # compatibly supply.  This bounds the directed contact candidate, but
        # it is not the same thing as solving source-level multi-contact
        # storage allocation.
        source_available_share = available_source_momentum * area_weight
        target_available_share = target_available_momentum * target_area_weight
        ##JMB This may not be nessesary if the velocity-progress-based impulse 
        # is doing the limiting, but it is a sanity check to prevent 
        # extreme impulses from bad geometry or stiffness values.
        weighted_available_momentum = min(source_available_share, target_available_share)
        # We ask GeoVelocityProgressImpulse() to propose compression and 
        # release impulses based on the contact phase and velocity progress, 
        # and we also pass the weighted available momentum for it to 
        # limit against if needed.
        (
            compression_impulse,
            release_impulse,
            stored_internal_momentum,
            contact_phase,
        ) = self.GeoVelocityProgressImpulse(
            SourceID,
            TargetID,
            relative_normal_velocity,
            contact_internal_momentum,
            contact_phase_start,
            raw_impulse,
            weighted_available_momentum,
        )
        compression_impulse = min(compression_impulse, weighted_available_momentum)
        # Update this directed contact's stored internal momentum ledger.
        # Compression adds momentum into storage; rebound release removes
        # momentum from storage.  The clamp prevents numerical noise or an
        # over-large release from making the contact ledger negative.
        stored_internal_momentum = max(
            0.0,
            contact_internal_momentum + compression_impulse - release_impulse,
        )

        return {
            "candidate_impulse": compression_impulse + release_impulse,
            "compression_impulse": compression_impulse,
            "release_impulse": release_impulse,
            "stored_internal_momentum": stored_internal_momentum,
            "phase": contact_phase,
            "raw_impulse": raw_impulse,
            "normal_x": normal_x,
            "normal_y": normal_y,
            "normal_z": normal_z,
        }

    def GeoBuildPairCompatiblePlan(self, directed_candidates):
        """Build pair-compatible directed impulses from directed candidates."""
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

        return planned

    def GeoPlanContactImpulses(self):
        """Build the frame's planned directed contact impulses.

        A directed candidate is one proposed contact response from 
        one source particle to one target particle.    
        
        This stage reads the current-frame collision lists and persistent
        source-target contact history, but it does not write particle
        velocities.  For each source particle, it computes source-level
        contact context such as total overlap area and available source
        momentum.  Then each active target is converted into a directed contact
        candidate through GeoCalculatePairContact().

        Directed candidates are keyed as (SourceID, TargetID).  After all
        candidates are collected, GeoBuildPairCompatiblePlan() turns them into
        pair-compatible planned impulses and stores the result in
        GeoPlannedContactImpulses.  GeoApplyParticleResponse() later consumes
        that plan to perform the source-owned velocity write and update contact
        ledgers/report fields.
        """
        directed_candidates = {}
        for SourceID, source in enumerate(self.particles):
            if not source.collision_list:
                continue
            # Get total overlap are and associated available source momentum 
            # for this source particle's contact list.
            total_overlap_area, available_source_momentum = self.GeoContactContext(SourceID)
            # Run thorugh the collision list and build a directed candidate for each target.
            for TargetID in source.collision_list:
                # The candidate construction may fail if the contact 
                # geometry is invalid or if the contact state cannot 
                # be initialized, so we check for None and skip 
                # those candidates.
                candidate = self.GeoCalculatePairContact(
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

        self.GeoPlannedContactImpulses = self.GeoBuildPairCompatiblePlan(
            directed_candidates
        )
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
        # The target is added to the source's collision list, but the contact state 
        # is only initialized when the source particle processes its collision list.  
        # This allows the source to maintain contact state across frames even when 
        # the target is not currently in contact, and it allows the source to 
        # avoid initializing contact state for targets that are no longer in contact.
        particle.collision_list.append(TargetID)
        # We are carrying contact history, but not in the slot index. 
        # We carry it by source/target identity:
        #   source.contact_internal_momentum[TargetID]
        #   source.contact_internal_phase[TargetID]
        ##JMB What effect does this have on the claim of instantaniusness 
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
        """Apply planned contact response for one source particle.

        This is the source-owned collision resolution stage.  It consumes the
        current-frame collision_list and the frame plan produced by
        GeoPlanContactImpulses(), then writes only the source particle's
        velocity and source-owned contact ledgers.

        The function works in four broad steps:

        1. Validate the source, prune inactive contact ledgers, and collect
           current contact entries from the source collision_list.
        2. For each active contact, read frame-start source/target velocities,
           geometry, normal velocity diagnostics, and the planned impulse for
           (SourceID, TargetID).
        3. Update the source-target contact ledger and convert the scalar
           applied impulse into a vector momentum delta along the contact
           normal.
        4. Sum all contact momentum deltas into one source net delta, update
           source.VelRad, synchronize report fields, and record diagnostics.

        The actual velocity write is:

            source.VelRad.xyz += source_net_delta_momentum / source_mass

        The frame-start velocity snapshot is used for contact-relative velocity
        calculations, while the live source VelRad is updated only after all of
        this source's contact deltas have been accumulated.

        Current limitation: multi-contact storage/allocation is still contact
        candidate based.  For sources such as particle 1 in ThreeParticle, the
        next rule should compute source-level internal-momentum change once and
        distribute it across active contacts before this resolution stage
        applies the resulting vector sum.
        """
        if not self.GeoValidParticleID(SourceID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_SOURCE_ID)
        source = self.particles[SourceID]
        self.GeoPruneInactiveContactLedgers(SourceID)
        if not source.collision_list:
            return True

        source_velocity = self.GeoStartFrameVelocity(SourceID)
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
            target_velocity = self.GeoStartFrameVelocity(TargetID)
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
        source_contact_ke_delta_sum = 0.0
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
            ##JMB The raw impulse is the GLSL-shaped stiffness-area impulse 
            ## without any velocity or momentum limiting applied.
            ## May need to weight this by the area weight to prevent 
            # extreme impulses from bad geometry or stiffness values, 
            # but it is also useful to report it as a diagnostic for 
            # tuning and debugging.
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
                contact_phase = (
                    self.GEO_PHASE_RETURNING
                    if compression_impulse < raw_impulse
                    else self.GEO_PHASE_COMPRESSION
                )

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
            source_contact_ke_delta_sum += contact_state.contact_ke_delta_estimate

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
        source.VelRad.w = self.GeoVelocityAngle(source.VelRad.x, source.VelRad.y)
        self.GeoSyncInternalMomentum(SourceID)
        source.vx = source.VelRad.x
        source.vy = source.VelRad.y
        source.vz = source.VelRad.z
        source_ke_after = 0.5 * source_mass * (
            source.VelRad.x * source.VelRad.x
            + source.VelRad.y * source.VelRad.y
            + source.VelRad.z * source.VelRad.z
        )
        source_net_ke_delta_estimate = (
            source_vx_before * delta_momentum_x
            + source_vy_before * delta_momentum_y
            + source_vz_before * delta_momentum_z
            + (
                delta_momentum_x * delta_momentum_x
                + delta_momentum_y * delta_momentum_y
                + delta_momentum_z * delta_momentum_z
            )
            / (2.0 * source_mass)
        )
        source_ke_delta = source_ke_after - source_ke_before
        source_ke_cross_term = (
            source_net_ke_delta_estimate - source_contact_ke_delta_sum
        )
        for _entry in contact_entries:
            contact_state = _entry[1]
            contact_state.source_vx_after = source.VelRad.x
            contact_state.source_vy_after = source.VelRad.y
            contact_state.source_vz_after = source.VelRad.z
            contact_state.source_ke_after = source_ke_after
            contact_state.source_ke_delta = source_ke_delta
            contact_state.source_net_delta_px = delta_momentum_x
            contact_state.source_net_delta_py = delta_momentum_y
            contact_state.source_net_delta_pz = delta_momentum_z
            contact_state.source_net_ke_delta_estimate = source_net_ke_delta_estimate
            contact_state.source_contact_ke_delta_sum = source_contact_ke_delta_sum
            contact_state.source_ke_cross_term = source_ke_cross_term
            contact_state.source_ke_residual = (
                source_ke_delta - source_net_ke_delta_estimate
            )

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
