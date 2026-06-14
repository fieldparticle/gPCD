class ForceContactDynamics:
    """Apply overlap-area central forces through a source-owned linear chain."""

    EPSILON = 1.0e-12
    CONTACT_PARTICLE = 1
    CONTACT_ACTIVE_THIS_FRAME = 1
    def ClearContactDiagnostics(self, contact_state):
        """Reset reporting-only diagnostics on one reusable contact slot."""
        for field_name in (
            "raw_impulse",
            "force_magnitude",
            "contact_potential_energy",
            "compression_impulse",
            "release_impulse",
            "source_available_momentum",
            "source_available_share",
            "target_available_momentum",
            "target_available_share",
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
        """Reset current-frame source contact state."""
        source = self.particles[SourceID]
        source.collision_list = []
        source.contactCount = 0
        source.colFlg = 0
        source.internal_momentum = 0.0
        source.Data.z = 0.0
        for contact_state in self.GetContactSlots(SourceID):
            self.ClearContactSlot(contact_state)

    def ContactDynamics(self, SourceID):
        """Calculate every current overlap-area force for one source."""
        if not self.BeginSourceContactParms(SourceID):
            return False
        source = self.particles[SourceID]
        for TargetID in source.collision_list:
            contact_state = self.InitializeContactState(SourceID, TargetID)
            if contact_state is None:
                return False
            self.CalculateContactParms(SourceID, TargetID, contact_state)
        if not self.CalculateContactForces(SourceID):
            return False
        return self.CalculateSourceAcceleration(SourceID)

    def BeginSourceContactParms(self, SourceID):
        """Reset source-level geometry totals rebuilt from current contacts."""
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
        contact_state.aux.z = 0.0
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
        """Return the fixed contact-slot array owned by the source particle.

        Newer particle structures expose the array as contacts.  The gcs
        fallback preserves compatibility with the existing particle structure.
        """
        particle = self.particles[SourceID]
        if hasattr(particle, "contacts"):
            return particle.contacts
        return particle.gcs

    def CalculateContactParms(self, SourceID, TargetID, contact_state):
        """Record relative normal motion and overlap geometry for diagnostics."""
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
        contact_state.rel_vn = relative_normal_velocity
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

    def CalculateContactForces(self, SourceID):
        """Calculate central force and timestep impulse for every overlap."""
        source = self.particles[SourceID]
        contact_slots = self.GetContactSlots(SourceID)
        dt = max(0.0, float(self.ShaderFlags.dt))

        for slot_index in range(source.contactCount):
            contact_state = contact_slots[slot_index]
            TargetID = int(contact_state.ids.x)
            overlap_area = max(0.0, float(contact_state.geom.w))
            force_magnitude = self.GetPairStiffness(SourceID, TargetID) * overlap_area
            contact_state.force_magnitude = force_magnitude
            contact_state.raw_impulse = force_magnitude * dt
            contact_state.contact_potential_energy = self.GetContactPotentialEnergy(
                SourceID,
                TargetID,
                float(contact_state.aux.x),
            )
            contact_state.compression_impulse = 0.0
            contact_state.release_impulse = 0.0
        return True

    def GetPairStiffness(self, SourceID, TargetID):
        """Return the nonnegative mean particle-owned stiffness for a contact."""
        source_q = self.particles[SourceID].Data.y or 0.0
        target_q = self.particles[TargetID].Data.y or 0.0
        return max(0.0, 0.5 * (source_q + target_q))

    def GetContactPotentialEnergy(self, SourceID, TargetID, center_distance):
        """Return q times the overlap-area integral over center separation."""
        source_radius = float(self.particles[SourceID].Data.x)
        target_radius = float(self.particles[TargetID].Data.x)
        separation_limit = source_radius + target_radius
        center_distance = max(0.0, float(center_distance))
        if center_distance >= separation_limit:
            return 0.0

        interval_count = 32
        step = (separation_limit - center_distance) / interval_count
        area_sum = self.particle_overlap_area(
            source_radius,
            target_radius,
            center_distance,
        )
        for interval in range(1, interval_count):
            distance = center_distance + interval * step
            coefficient = 4.0 if interval % 2 else 2.0
            area_sum += coefficient * self.particle_overlap_area(
                source_radius,
                target_radius,
                distance,
            )
        area_sum += self.particle_overlap_area(
            source_radius,
            target_radius,
            separation_limit,
        )
        return self.GetPairStiffness(SourceID, TargetID) * step * area_sum / 3.0

    def TotalPotentialEnergy(self):
        """Return current whole-system pair potential energy."""
        total_potential_energy = 0.0
        for SourceID in range(len(self.particles)):
            source_position = self.GetParticlePosition(SourceID)
            for TargetID in range(SourceID + 1, len(self.particles)):
                target_position = self.GetParticlePosition(TargetID)
                dx = target_position.x - source_position.x
                dy = target_position.y - source_position.y
                dz = target_position.z - source_position.z
                center_distance = (dx * dx + dy * dy + dz * dz) ** 0.5
                total_potential_energy += self.GetContactPotentialEnergy(
                    SourceID,
                    TargetID,
                    center_distance,
                )
        return total_potential_energy

    def CalculateSourceAcceleration(self, SourceID):
        """Store the source acceleration from the current geometry snapshot."""
        source = self.particles[SourceID]
        contact_slots = self.GetContactSlots(SourceID)
        source_mass = self.GetParticleMass(SourceID)

        source_force_x = 0.0
        source_force_y = 0.0
        source_force_z = 0.0

        for slot_index in range(source.contactCount):
            contact_state = contact_slots[slot_index]
            normal_x = float(contact_state.geom.x)
            normal_y = float(contact_state.geom.y)
            normal_z = float(contact_state.geom.z)
            force_magnitude = max(0.0, float(contact_state.force_magnitude))
            applied_impulse = max(0.0, float(contact_state.raw_impulse))

            source_force_x -= force_magnitude * normal_x
            source_force_y -= force_magnitude * normal_y
            source_force_z -= force_magnitude * normal_z
            contact_delta_px = -applied_impulse * normal_x
            contact_delta_py = -applied_impulse * normal_y
            contact_delta_pz = -applied_impulse * normal_z

            contact_state.aux.w = applied_impulse
            contact_state.delta_px = contact_delta_px
            contact_state.delta_py = contact_delta_py
            contact_state.delta_pz = contact_delta_pz

        acceleration = (
            source.force_acceleration_current
            if getattr(self, "force_acceleration_pass", "current") == "current"
            else source.force_acceleration_next
        )
        acceleration.x = source_force_x / source_mass
        acceleration.y = source_force_y / source_mass
        acceleration.z = source_force_z / source_mass
        acceleration.w = 0.0
        return True

    def FinishSourceVelocity(self, SourceID):
        """Apply the velocity-Verlet average acceleration to one source."""
        if not self.isValidParticleID(SourceID):
            return self.SetError(self.constants.ERROR_INVALID_SOURCE_ID)
        dt = float(self.ShaderFlags.dt)
        if dt <= 0.0:
            return self.SetError(self.constants.ERROR_INVALID_DT)

        source = self.particles[SourceID]
        start_velocity = self.GetStartFrameVelocity(SourceID)
        current = source.force_acceleration_current
        next_acceleration = source.force_acceleration_next
        source.VelRad.x = start_velocity.x + 0.5 * (current.x + next_acceleration.x) * dt
        source.VelRad.y = start_velocity.y + 0.5 * (current.y + next_acceleration.y) * dt
        source.VelRad.z = start_velocity.z + 0.5 * (current.z + next_acceleration.z) * dt
        source.VelRad.w = self.VelocityAngle(source.VelRad.x, source.VelRad.y)
        source.vx = source.VelRad.x
        source.vy = source.VelRad.y
        source.vz = source.VelRad.z

        delta_momentum_x = self.GetParticleMass(SourceID) * (source.VelRad.x - start_velocity.x)
        delta_momentum_y = self.GetParticleMass(SourceID) * (source.VelRad.y - start_velocity.y)
        delta_momentum_z = self.GetParticleMass(SourceID) * (source.VelRad.z - start_velocity.z)
        for slot_index in range(source.contactCount):
            contact_state = self.GetContactSlots(SourceID)[slot_index]
            contact_state.source_vx_before = start_velocity.x
            contact_state.source_vy_before = start_velocity.y
            contact_state.source_vz_before = start_velocity.z
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
        """Predict one source position into the inactive position buffer."""
        position_buffer = int(self.ShaderFlags.positionBuffer)
        dt = self.ShaderFlags.dt
        if not self.isValidParticleID(SourceID):
            return self.SetError(self.constants.ERROR_INVALID_SOURCE_ID)
        if dt <= 0.0:
            return self.SetError(self.constants.ERROR_INVALID_DT)

        particle = self.particles[SourceID]
        position = self.GetParticlePosition(SourceID)
        velocity = self.GetStartFrameVelocity(SourceID)
        acceleration = particle.force_acceleration_current
        half_dt_squared = 0.5 * dt * dt
        if position_buffer == 0:
            particle.PosLocB.x = position.x + velocity.x * dt + acceleration.x * half_dt_squared
            particle.PosLocB.y = position.y + velocity.y * dt + acceleration.y * half_dt_squared
            particle.PosLocB.z = position.z + velocity.z * dt + acceleration.z * half_dt_squared
            particle.PosLocA.w = 1.0
            particle.PosLocB.w = 0.0
            output_position = particle.PosLocB
        else:
            particle.PosLocA.x = position.x + velocity.x * dt + acceleration.x * half_dt_squared
            particle.PosLocA.y = position.y + velocity.y * dt + acceleration.y * half_dt_squared
            particle.PosLocA.z = position.z + velocity.z * dt + acceleration.z * half_dt_squared
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
