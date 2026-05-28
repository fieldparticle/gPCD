class GeoDynamics:
    """GLSL-shaped dynamics functions for the Geo path.

    This file is intentionally small again.  The reservoir/phase collision
    prototype has been backed out so the next model can be built as an
    instantaneous, purely geometric response.

    GeoBase still owns cfg loading, particle setup, contact scanning, reporting
    fields, and the frame loop.  GeoDynamics currently owns only:
        - GLSL-style error return helpers,
        - per-frame contact-list registration,
        - position double-buffered particle motion,
        - an empty collision-processing hook.
    """

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
        """Return pair stiffness with RUN_CONFIGURATION fallback."""
        source_q = self.particles[SourceID].Data.y or 0.0
        target_q = self.particles[TargetID].Data.y or 0.0
        default_q = float(self.run_configuration.get("collision_stiffness_q", 1.0))
        if source_q <= 0.0:
            source_q = default_q
        if target_q <= 0.0:
            target_q = default_q
        return max(0.0, 0.5 * (source_q + target_q))

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

    def GeoAddParticleContact(self, SourceID, TargetID):
        """Record that SourceID is in contact with TargetID this frame.

        Contact detection and overlap-area calculation happen in GeoBase before
        this function is called.  This function only records the current-frame
        contact list; it does not create persistent contact state or apply any
        dynamics.
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
        """Apply two-particle instantaneous geometric collision response.

        This first rule supports only one contact per source particle.  The
        response is rebuilt from current-frame geometry and velocity every
        frame:

            impulse = stiffness * overlap_area * dt

        The impulse is applied along the current contact normal and does not use
        persistent contact memory.
        """
        if not self.GeoValidParticleID(SourceID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_SOURCE_ID)
        source = self.particles[SourceID]
        if len(source.collision_list) != 1:
            return True

        TargetID = source.collision_list[0]
        if not self.GeoValidParticleID(TargetID):
            return self.GeoSetError(self.constants.GEO_ERROR_INVALID_TARGET_ID)

        contact = self.GeoParticleGeometry(SourceID, TargetID)
        if contact is None:
            return True

        normal_x, normal_y, normal_z, overlap_area, center_distance = contact
        source_velocity = self.GeoVelocity(SourceID)
        target_velocity = self.GeoVelocity(TargetID)
        relative_normal_velocity = (
            (target_velocity.x - source_velocity.x) * normal_x
            + (target_velocity.y - source_velocity.y) * normal_y
            + (target_velocity.z - source_velocity.z) * normal_z
        )
        stiffness_q = self.GeoPairStiffness(SourceID, TargetID)
        impulse = stiffness_q * overlap_area * self.ShaderFlags.dt

        source.VelRad.x -= (impulse / self.GeoMass(SourceID)) * normal_x
        source.VelRad.y -= (impulse / self.GeoMass(SourceID)) * normal_y
        source.VelRad.z -= (impulse / self.GeoMass(SourceID)) * normal_z
        source.vx = source.VelRad.x
        source.vy = source.VelRad.y
        source.vz = source.VelRad.z

        source.report_contacts = len(source.collision_list)
        source.report_target = TargetID
        source.report_center_distance = center_distance
        source.report_normal_x = normal_x
        source.report_normal_y = normal_y
        source.report_stored_mom = 0.0
        source.report_alpha_zero = 0.0
        source.report_zero_area = 0.0
        source.report_compression_fraction = 0.0
        source.report_rel_vn = relative_normal_velocity
        source.report_closing_mom = impulse
        return True
