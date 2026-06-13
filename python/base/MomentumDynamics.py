class MomentumContactDynamics:
    """Process independent contact momentum through a source-owned chain.

    Each source particle completes contact initialization, parameter
    calculation, impulse planning, momentum application, and ledger updates
    before processing moves to the next source particle. Functions read the
    same frame-start state, vector-sum contact contributions locally, and write
    only the source particle.
    """

    EPSILON = 1.0e-12
    CONTACT_PARTICLE = 1
    CONTACT_ACTIVE_THIS_FRAME = 1
    PHASE_COMPRESSION = 1
    PHASE_RETURNING = 2

    def ClearContactDiagnostics(self, contact_state):
        """Reset reporting-only diagnostics on one reusable contact slot."""
        for field_name in (
            "raw_impulse",
            "compression_impulse",
            "release_impulse",
            "source_available_momentum",
            "source_available_share",
            "target_available_momentum",
            "target_available_share",
            "weighted_available_momentum",
            "source_vn",
            "target_vn",
            "rel_vn",
            "delta_px",
            "delta_py",
            "delta_pz",
            "source_vx_before",
            "source_vy_before",
            "source_vz_before",
            "source_vx_after",
            "source_vy_after",
            "source_vz_after",
            "source_ke_before",
            "source_ke_after",
            "source_ke_delta",
            "contact_ke_delta_estimate",
            "source_net_delta_px",
            "source_net_delta_py",
            "source_net_delta_pz",
            "source_net_ke_delta_estimate",
            "source_contact_ke_delta_sum",
            "source_ke_cross_term",
            "source_ke_residual",
        ):
            setattr(contact_state, field_name, 0.0)

    def ClearContactSlot(self, contact_state):
        """Reset one reusable current-frame contact slot."""
        contact_state.ids = self.create_uvec4()
        contact_state.geom = self.create_vec4()
        contact_state.aux = self.create_vec4()
        self.ClearContactDiagnostics(contact_state)

    def BeginContactFrame(self, SourceID):
        """Reset current-frame source contact state while preserving ledgers."""
        source = self.particles[SourceID]
        source.collision_list = []
        source.contactCount = 0
        source.colFlg = 0
        for contact_state in self.GetContactSlots(SourceID):
            self.ClearContactSlot(contact_state)

    def ContactDynamics(self, SourceID):
        """Run the complete contact-response chain for one source particle.

        The source contact list must already contain the current-frame target
        IDs.  This function initializes each source-owned contact slot,
        accumulates contact parameters, then performs the source-level stages
        that require the complete contact set.  Return False immediately when
        a required stage fails.
        """
        if not self.BeginSourceContactParms(SourceID):
            return False
        source = self.particles[SourceID]
        for TargetID in source.collision_list:
            contact_state = self.InitializeContactState(SourceID, TargetID)
            if contact_state is None:
                return False
            if not self.CalculateContactParms(SourceID, TargetID, contact_state):
                return False
            if not self.CalculateContactImpulse(SourceID, TargetID, contact_state):
                return False
        if not self.ApplySourceMomentumDelta(SourceID):
            return False
        return self.UpdateContactLedgers(SourceID)

    def BeginSourceContactParms(self, SourceID):
        """Reset accumulators that will be rebuilt from this source's contacts.

        total_overlap_area remains available for diagnostics. Contact momentum
        is not pooled or redistributed at the source level in this model.
        """
        source = self.particles[SourceID]
        source.total_overlap_area = 0.0
        return True

    def InitializeContactState(self, SourceID, TargetID):
        """Initialize reporting and contact state for one source-target contact.

        GetContactState creates and fills the next source-owned contact slot.
        On success, this function marks the source as colliding and updates the
        source reporting fields for the current target.
        """
        source = self.particles[SourceID]
        contact_state = self.GetContactState(SourceID, TargetID)
        if contact_state is None:
            return None
        source.colFlg = 1
        source.report_contacts = len(source.collision_list)
        source.report_target = TargetID
        return contact_state

    def GetContactState(self, SourceID, TargetID):
        """Create and populate one current-frame source-owned contact slot.

        The slot first receives its target ID and persistent collision state.
        Current geometry is then calculated and stored in the slot.  Returning
        a slot with no geometry is allowed when no current overlap is found;
        returning None means no contact slot was available.
        """
        contact_state = self.AppendContactSlot(SourceID, TargetID)
        if contact_state is None:
            return None

        contact = self.GetParticleGeometry(SourceID, TargetID)
        if contact is None:
            return contact_state

        normal_x, normal_y, normal_z, overlap_area, center_distance = contact
        source = self.particles[SourceID]
        target = self.particles[TargetID]
        contact_state.geom = self.create_vec4(
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
        )
        contact_state.aux.x = center_distance
        contact_state.aux.y = source.Data.x + target.Data.x - center_distance
        contact_state.aux.z = self.GetCollisionInternalMomentum(SourceID, TargetID)
        return contact_state

    def GetParticleGeometry(self, SourceID, TargetID):
        """Calculate current-frame geometry for one source-target pair.

        Positions come from the frame-start snapshot.  When the particle radii
        overlap, return the source-to-target unit normal, circular overlap area,
        and center distance.  Return None when no overlap exists.  Coincident
        centers use +x as a deterministic fallback normal.
        """
        source_position = self.GetParticlePosition(SourceID)
        target_position = self.GetParticlePosition(TargetID)
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

    def AppendContactSlot(self, SourceID, TargetID):
        """Allocate and initialize the next source-owned contact slot.

        The slot records the target ID, contact type, persistent collision
        phase, active-this-frame flag, and previously stored internal momentum.
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
        contact_state.ids.z = self.GetCollisionPhase(SourceID, TargetID)
        contact_state.ids.w = self.CONTACT_ACTIVE_THIS_FRAME
        contact_state.aux.z = self.GetCollisionInternalMomentum(SourceID, TargetID)
        source.contactCount += 1
        return contact_state

    def GetContactSlots(self, SourceID):
        """Return the fixed contact-slot array owned by the source particle.

        Newer particle structures expose the array as contacts.  The gcs
        fallback preserves compatibility with the existing particle structure.
        """
        particle = self.particles[SourceID]
        if hasattr(particle, "contacts"):
            return particle.contacts
        return particle.gcs

    def GetCollisionInternalMomentum(self, SourceID, TargetID):
        """Return stored internal momentum for one source-owned contact ledger.

        Create the source ledger dictionary when it does not yet exist.  A
        missing target entry represents zero stored momentum.
        """
        source = self.particles[SourceID]
        ledgers = getattr(source, "contact_internal_momentum", None)
        if ledgers is None:
            source.contact_internal_momentum = {}
            ledgers = source.contact_internal_momentum
        return max(0.0, ledgers.get(TargetID, 0.0))

    def GetCollisionPhase(self, SourceID, TargetID):
        """Return the persistent source-owned phase for one contact.

        Create the phase dictionary when needed.  Contacts without history
        begin in the compression phase.
        """
        source = self.particles[SourceID]
        phases = getattr(source, "contact_internal_phase", None)
        if phases is None:
            source.contact_internal_phase = {}
            phases = source.contact_internal_phase
        return phases.get(TargetID, self.PHASE_COMPRESSION)

    def CalculateContactParms(self, SourceID, TargetID, contact_state):
        """Calculate one contact's relative motion and source contribution.

        Use frame-start source and target velocities projected onto the stored
        contact normal.  Convert closing speed to closing momentum using
        reduced mass and store the per-contact result. Each contact retains its
        own available momentum; it is not weighted against sibling contacts.
        """
        source = self.particles[SourceID]
        overlap_area = max(0.0, float(contact_state.geom.w))
        normal_x = float(contact_state.geom.x)
        normal_y = float(contact_state.geom.y)
        normal_z = float(contact_state.geom.z)

        source_velocity = self.GetStartFrameVelocity(SourceID)
        target_velocity = self.GetStartFrameVelocity(TargetID)
        relative_normal_velocity = (
            (target_velocity.x - source_velocity.x) * normal_x
            + (target_velocity.y - source_velocity.y) * normal_y
            + (target_velocity.z - source_velocity.z) * normal_z
        )
        closing_speed = max(0.0, -relative_normal_velocity)
        closing_momentum = (
            self.GetReducedMass(SourceID, TargetID)
            * closing_speed
        )

        contact_state.rel_vn = relative_normal_velocity
        contact_state.source_available_momentum = closing_momentum
        contact_state.source_available_share = closing_momentum
        contact_state.weighted_available_momentum = closing_momentum
        source.total_overlap_area += overlap_area
        return True

    def GetStartFrameVelocity(self, ParticleID):
        """Return a particle's immutable frame-start velocity.

        Prefer VelRadFrame so contact calculations cannot observe velocity
        writes made earlier in the frame.  Fall back to the particle velocity
        when a frame snapshot is unavailable.
        """
        if hasattr(self, "VelRadFrame") and self.VelRadFrame:
            return self.VelRadFrame[ParticleID]
        return self.particles[ParticleID].VelRad

    def GetReducedMass(self, SourceID, TargetID):
        """Return the Newtonian reduced mass for one source-target contact.

        Particle masses come from parms.x.  The epsilon floor prevents a zero
        denominator and keeps this calculation compatible with shader logic.
        """
        source_mass = max(self.particles[SourceID].parms.x, 1.0e-12)
        target_mass = max(self.particles[TargetID].parms.x, 1.0e-12)
        return (source_mass * target_mass) / (source_mass + target_mass)

    def CalculateContactImpulse(self, SourceID, TargetID, contact_state):
        """Plan one independent source-owned contact impulse.

        Raw impulse is stiffness times this contact's overlap area times dt.
        Compression is bounded by this contact's reduced-mass closing momentum;
        rebound is bounded by this contact's stored internal momentum. No
        source-level overlap weighting or momentum redistribution is applied.
        """
        dt = max(0.0, float(self.ShaderFlags.dt))
        overlap_area = max(0.0, float(contact_state.geom.w))
        raw_impulse = (
            self.GetPairStiffness(SourceID, TargetID)
            * overlap_area
            * dt
        )
        available_momentum = max(
            0.0,
            float(contact_state.source_available_momentum),
        )
        stored_internal_momentum = self.GetCollisionInternalMomentum(
            SourceID,
            TargetID,
        )

        compression_impulse = 0.0
        release_impulse = 0.0
        if contact_state.rel_vn < -self.EPSILON:
            compression_impulse = min(raw_impulse, available_momentum)
        else:
            release_impulse = min(raw_impulse, stored_internal_momentum)

        contact_state.raw_impulse = raw_impulse
        contact_state.compression_impulse = compression_impulse
        contact_state.release_impulse = release_impulse
        return True

    def GetPairStiffness(self, SourceID, TargetID):
        """Return the nonnegative mean particle-owned stiffness for a contact."""
        source_q = self.particles[SourceID].Data.y or 0.0
        target_q = self.particles[TargetID].Data.y or 0.0
        return max(0.0, 0.5 * (source_q + target_q))

    def UpdateContactLedgers(self, SourceID):
        """Commit planned impulses to persistent source-owned contact ledgers.

        Compression adds internal momentum and release removes it.  The contact
        phase is updated from the resulting stored momentum and release state,
        current slot diagnostics are synchronized, and the source total
        internal momentum is rebuilt after all contact ledgers are committed.
        """
        source = self.particles[SourceID]
        contact_slots = self.GetContactSlots(SourceID)

        for slot_index in range(source.contactCount):
            contact_state = contact_slots[slot_index]
            TargetID = int(contact_state.ids.x)
            stored_internal_momentum = max(
                0.0,
                self.GetCollisionInternalMomentum(SourceID, TargetID)
                + max(0.0, float(contact_state.compression_impulse))
                - max(0.0, float(contact_state.release_impulse)),
            )

            if stored_internal_momentum <= self.EPSILON:
                stored_internal_momentum = 0.0
                collision_phase = self.PHASE_COMPRESSION
            elif contact_state.release_impulse > self.EPSILON:
                collision_phase = self.PHASE_RETURNING
            else:
                collision_phase = self.PHASE_COMPRESSION

            self.SetCollisionInternalMomentum(
                SourceID,
                TargetID,
                stored_internal_momentum,
            )
            self.SetCollisionPhase(SourceID, TargetID, collision_phase)
            contact_state.ids.z = collision_phase
            contact_state.aux.z = stored_internal_momentum

        self.SyncInternalMomentum(SourceID)
        return True

    def SetCollisionInternalMomentum(self, SourceID, TargetID, internal_momentum):
        """Store or remove one source-owned contact internal-momentum entry.

        Values at or below EPSILON are removed so an empty contact ledger does
        not retain meaningless zero entries.
        """
        source = self.particles[SourceID]
        if not hasattr(source, "contact_internal_momentum"):
            source.contact_internal_momentum = {}

        internal_momentum = max(0.0, float(internal_momentum))
        if internal_momentum <= self.EPSILON:
            source.contact_internal_momentum.pop(TargetID, None)
        else:
            source.contact_internal_momentum[TargetID] = internal_momentum
        return True

    def SetCollisionPhase(self, SourceID, TargetID, phase):
        """Store or remove one source-owned persistent collision phase.

        A drained compression contact is the default state and therefore needs
        no dictionary entry.  Other phases remain stored by target ID.
        """
        source = self.particles[SourceID]
        if not hasattr(source, "contact_internal_phase"):
            source.contact_internal_phase = {}

        if (
            phase == self.PHASE_COMPRESSION
            and self.GetCollisionInternalMomentum(SourceID, TargetID) <= self.EPSILON
        ):
            source.contact_internal_phase.pop(TargetID, None)
        else:
            source.contact_internal_phase[TargetID] = phase
        return True

    def SyncInternalMomentum(self, SourceID):
        """Rebuild and store the source total from its contact ledgers."""
        self.SetInternalMomentum(SourceID, self.GetInternalMomentum(SourceID))
        return True

    def GetInternalMomentum(self, SourceID):
        """Return the sum of all source-owned contact internal momentum.

        Use the particle total only as a compatibility fallback when no contact
        ledger dictionary exists.
        """
        source = self.particles[SourceID]
        ledgers = getattr(source, "contact_internal_momentum", None)
        if ledgers is not None:
            return sum(max(0.0, momentum) for momentum in ledgers.values())
        return max(0.0, getattr(source, "internal_momentum", source.Data.z))

    def SetInternalMomentum(self, SourceID, internal_momentum):
        """Store the source total internal momentum in runtime and data fields."""
        source = self.particles[SourceID]
        source.internal_momentum = max(0.0, float(internal_momentum))
        source.Data.z = source.internal_momentum
        return True

    def ApplySourceMomentumDelta(self, SourceID):
        """Apply the vector sum of planned contact impulses to source momentum.

        Each scalar planned impulse is directed opposite the source-to-target
        contact normal.  Per-contact momentum deltas are accumulated before one
        source velocity write is made.  The function also records before/after
        velocity and source-net momentum diagnostics in each active slot.
        """
        source = self.particles[SourceID]
        contact_slots = self.GetContactSlots(SourceID)
        source_mass = self.GetParticleMass(SourceID)
        source_vx_before = source.VelRad.x
        source_vy_before = source.VelRad.y
        source_vz_before = source.VelRad.z

        delta_momentum_x = 0.0
        delta_momentum_y = 0.0
        delta_momentum_z = 0.0

        for slot_index in range(source.contactCount):
            contact_state = contact_slots[slot_index]
            normal_x = float(contact_state.geom.x)
            normal_y = float(contact_state.geom.y)
            normal_z = float(contact_state.geom.z)
            applied_impulse = (
                max(0.0, float(contact_state.compression_impulse))
                + max(0.0, float(contact_state.release_impulse))
            )

            contact_delta_px = -applied_impulse * normal_x
            contact_delta_py = -applied_impulse * normal_y
            contact_delta_pz = -applied_impulse * normal_z
            delta_momentum_x += contact_delta_px
            delta_momentum_y += contact_delta_py
            delta_momentum_z += contact_delta_pz

            contact_state.aux.w = applied_impulse
            contact_state.delta_px = contact_delta_px
            contact_state.delta_py = contact_delta_py
            contact_state.delta_pz = contact_delta_pz
            contact_state.source_vx_before = source_vx_before
            contact_state.source_vy_before = source_vy_before
            contact_state.source_vz_before = source_vz_before

        source.VelRad.x += delta_momentum_x / source_mass
        source.VelRad.y += delta_momentum_y / source_mass
        source.VelRad.z += delta_momentum_z / source_mass
        source.VelRad.w = self.VelocityAngle(source.VelRad.x, source.VelRad.y)
        source.vx = source.VelRad.x
        source.vy = source.VelRad.y
        source.vz = source.VelRad.z

        for slot_index in range(source.contactCount):
            contact_state = contact_slots[slot_index]
            contact_state.source_vx_after = source.VelRad.x
            contact_state.source_vy_after = source.VelRad.y
            contact_state.source_vz_after = source.VelRad.z
            contact_state.source_net_delta_px = delta_momentum_x
            contact_state.source_net_delta_py = delta_momentum_y
            contact_state.source_net_delta_pz = delta_momentum_z
        return True

    def GetParticleMass(self, ParticleID):
        """Return particle mass from parms.x with an EPSILON lower bound."""
        return max(self.particles[ParticleID].parms.x, self.EPSILON)

    def Move(self, SourceID):
        """Move one source particle into the inactive position buffer.

        Validate the source ID and frame dt, integrate position using the
        source's newly updated velocity, mark which position buffer is active,
        and report an error if the output position crosses the lower bounds.
        The frame-chain owner performs the final buffer swap.
        """
        position_buffer = int(self.ShaderFlags.positionBuffer)
        dt = self.ShaderFlags.dt
        if not self.isValidParticleID(SourceID):
            return self.SetError(self.constants.ERROR_INVALID_SOURCE_ID)
        if dt <= 0.0:
            return self.SetError(self.constants.ERROR_INVALID_DT)

        particle = self.particles[SourceID]
        velocity = particle.VelRad
        if position_buffer == 0:
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
            return self.SetError(self.constants.ERROR_PARTICLE_OUT_OF_BOUNDS)
        return True

    def isValidParticleID(self, ParticleID):
        """Return True when ParticleID addresses an existing particle."""
        return 0 <= ParticleID < len(self.particles)

    def SetError(self, error_code):
        """Set the shared collision error state and return failure."""
        self.collIn.ErrorReturn = error_code
        return False
