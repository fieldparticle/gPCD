class ForceContactDynamics:
    """Apply overlap-area central forces through a source-owned linear chain."""

    EPSILON = 1.0e-12
    CONTACT_PARTICLE = 1
    CONTACT_WALL = 2
    CONTACT_ACTIVE_THIS_FRAME = 1

    def ProcessParticleCollision(self, TargetID, SourceID, totalForce):
        """Calculate and accumulate one particle-contact force."""
        contact_state = self.InitializeContactState(SourceID, TargetID)
        if contact_state is None:
            return False
        return self.AccumulateContactForce(SourceID, contact_state, totalForce)

    def ProcessWallCollision(self, SourceID, wall, totalForce):
        """Calculate and accumulate one wall-contact force."""
        contact_state = self.InitializeWallContactState(SourceID, wall)
        if contact_state is None:
            return True
        return self.AccumulateContactForce(SourceID, contact_state, totalForce)

    def InitializeWallContactState(self, SourceID, wall):
        """Initialize one current-frame source-wall contact."""
        geometry = self.GetWallGhostGeometry(SourceID, wall)
        if geometry is None:
            return None
        return self.AppendWallContactSlot(SourceID, wall, geometry)

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
        contact_state = self.AppendContactSlot(SourceID, TargetID)
        if contact_state is None:
            return None

        contact = self.GetParticleGeometry(SourceID, TargetID)
        if contact is None:
            return contact_state

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
        contact_state.aux.y = (
            effective_source_radius + effective_target_radius - center_distance
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
        and center distance.  Return None when no overlap exists.  Coincident
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
        force_magnitude = pair_stiffness * max(0.0, float(contact_state.geom.w))
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
            not bool(self.ShaderFlags.Boundary)
            and (output_position.x < 1.0 or output_position.y < 1.0)
        ):
            return self.SetError(self.constants.ERROR_PARTICLE_OUT_OF_BOUNDS)
        return True

    def SetError(self, error_code):
        """Set the shared collision error state and return failure."""
        self.collIn.ErrorReturn = error_code
        return False
