import math


class ForceContactDynamics:
    """Apply overlap-area central forces through a source-owned linear chain."""

    EPSILON = 1.0e-12
    CONTACT_PARTICLE = 1
    CONTACT_WALL = 2
    CONTACT_ACTIVE_THIS_FRAME = 1
    BOUNDARY_PARTICLE_EVALUATORS = {
        1: "EvaluateHorizontalWallSegment",
        2: "EvaluateVerticalWallSegment",
        3: "EvaluateCDNozzleWallSegment",
    }

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
            return False
        return self.AccumulateContactForce(SourceID, contact_state, totalForce)

    def ProcessWallCollision(self, SourceID, wall, totalForce):
        """Calculate and accumulate one wall-contact force."""
        contact_state = self.InitializeWallContactState(SourceID, wall)
        if contact_state is None:
            return True
        return self.AccumulateContactForce(SourceID, contact_state, totalForce)

    def BoundaryParticleWallFlag(self, SourceID, BoundaryID):
        """Infer the configured wall represented by a boundary marker."""
        boundary_position = self.GetParticlePosition(BoundaryID)
        boundary_particles = [
            particle_id
            for particle_id in range(len(self.particles))
            if self.IsBoundaryParticle(particle_id)
        ]
        if boundary_particles:
            boundary_y_values = [
                float(self.GetParticlePosition(particle_id).y)
                for particle_id in boundary_particles
            ]
            min_y = min(boundary_y_values)
            max_y = max(boundary_y_values)
        else:
            cfg = self.run_configuration
            min_y = float(cfg.get("WallYMIN", 0.0))
            max_y = float(cfg.get("WallYMAX", self.ShaderFlags.SideLength))
        mid_y = 0.5 * (min_y + max_y)
        if boundary_position.y < mid_y:
            return 3
        return 4

    def BoundaryParticleVerticalWallFlag(self, SourceID, BoundaryID):
        """Infer the left/right wall represented by a boundary marker."""
        boundary_position = self.GetParticlePosition(BoundaryID)
        boundary_particles = [
            particle_id
            for particle_id in range(len(self.particles))
            if self.IsBoundaryParticle(particle_id)
        ]
        if boundary_particles:
            boundary_x_values = [
                float(self.GetParticlePosition(particle_id).x)
                for particle_id in boundary_particles
            ]
            min_x = min(boundary_x_values)
            max_x = max(boundary_x_values)
        else:
            cfg = self.run_configuration
            min_x = float(cfg.get("WallXMIN", 0.0))
            max_x = float(cfg.get("WallXMAX", self.ShaderFlags.SideLength))
        mid_x = 0.5 * (min_x + max_x)
        if boundary_position.x < mid_x:
            return 1
        return 2

    def BoundaryParticleCDNozzleWallFlag(self, SourceID, BoundaryID):
        """Infer upper/lower CD nozzle wall identity from a boundary marker."""
        boundary_position = self.GetParticlePosition(BoundaryID)
        center_y = self.CDNozzleCenterY()
        if boundary_position.y < center_y:
            return 3
        return 4

    def CDNozzleCenterY(self):
        """Return the CD nozzle centerline y coordinate."""
        cfg = self.run_configuration
        default_center_y = 0.5 * (
            float(cfg.get("WallYMIN", 0.0))
            + float(cfg.get("WallYMAX", getattr(self.ShaderFlags, "SideLength", 1.0)))
        )
        return float(cfg.get("nozzle_center_y", default_center_y))

    def CDNozzleAxialPosition(self, x_position):
        """Return one-based axial position along the horizontal CD nozzle."""
        cfg = self.run_configuration
        nozzle_start_x = float(cfg.get("nozzle_start_x", cfg.get("WallXMIN", 1.0)))
        return float(x_position) - nozzle_start_x + 1.0

    def CDNozzleTotalLength(self):
        """Return the configured analytic CD nozzle length."""
        cfg = self.run_configuration
        return (
            float(cfg.get("nozzle_inlet_length", 5.0))
            + float(cfg.get("nozzle_converge_length", 20.0))
            + float(cfg.get("nozzle_throat_length", 5.0))
            + float(cfg.get("nozzle_diverge_length", 20.0))
            + float(cfg.get("nozzle_exit_length", 14.0))
        )

    def CDNozzleRadius(self, axial_position):
        """Return the analytic CD nozzle radius at a one-based axial position."""
        cfg = self.run_configuration
        x = float(axial_position)
        inlet_length = float(cfg.get("nozzle_inlet_length", 5.0))
        converge_length = float(cfg.get("nozzle_converge_length", 20.0))
        throat_length = float(cfg.get("nozzle_throat_length", 5.0))
        diverge_length = float(cfg.get("nozzle_diverge_length", 20.0))
        inlet_radius = float(cfg.get("nozzle_inlet_radius", 10.0))
        throat_radius = float(cfg.get("nozzle_throat_radius", 8.1))
        exit_radius = float(cfg.get("nozzle_exit_radius", 10.0))

        inlet_end = inlet_length
        converge_end = inlet_end + converge_length
        throat_end = converge_end + throat_length
        diverge_end = throat_end + diverge_length

        if 1.0 <= x < inlet_end:
            return inlet_radius
        if inlet_end <= x < converge_end:
            span = max(converge_length, self.EPSILON)
            throat_distance = converge_end - x
            t = throat_distance / span
            return throat_radius + (inlet_radius - throat_radius) * t * t
        if converge_end <= x < throat_end:
            return throat_radius
        if throat_end <= x < diverge_end:
            span = max(diverge_length, self.EPSILON)
            t = (x - throat_end) / span
            return throat_radius + (exit_radius - throat_radius) * t * t
        if x >= diverge_end:
            return exit_radius
        return inlet_radius

    def CDNozzleRadiusSlope(self, axial_position):
        """Return dr/dx for the analytic CD nozzle profile."""
        cfg = self.run_configuration
        x = float(axial_position)
        inlet_length = float(cfg.get("nozzle_inlet_length", 5.0))
        converge_length = float(cfg.get("nozzle_converge_length", 20.0))
        throat_length = float(cfg.get("nozzle_throat_length", 5.0))
        diverge_length = float(cfg.get("nozzle_diverge_length", 20.0))
        inlet_radius = float(cfg.get("nozzle_inlet_radius", 10.0))
        throat_radius = float(cfg.get("nozzle_throat_radius", 8.1))
        exit_radius = float(cfg.get("nozzle_exit_radius", 10.0))

        inlet_end = inlet_length
        converge_end = inlet_end + converge_length
        throat_end = converge_end + throat_length
        diverge_end = throat_end + diverge_length

        if inlet_end <= x < converge_end:
            span = max(converge_length, self.EPSILON)
            throat_distance = converge_end - x
            return (
                -2.0
                * (inlet_radius - throat_radius)
                * throat_distance
                / (span * span)
            )
        if throat_end <= x < diverge_end:
            span = max(diverge_length, self.EPSILON)
            throat_distance = x - throat_end
            return (
                2.0
                * (exit_radius - throat_radius)
                * throat_distance
                / (span * span)
            )
        return 0.0

    def EvaluateWallSegment(self, SourceID, BoundaryID):
        """Evaluate the self-described wall segment for a boundary marker."""
        boundary = self.particles[BoundaryID]
        evaluator_id = int(round(float(boundary.Data.z)))
        evaluator_name = self.BOUNDARY_PARTICLE_EVALUATORS.get(evaluator_id)
        if evaluator_name is None:
            return None
        return getattr(self, evaluator_name)(SourceID, BoundaryID)

    def EvaluateHorizontalWallSegment(self, SourceID, BoundaryID):
        """Evaluate a horizontal wall segment represented by a boundary marker.

        Boundary particles are occupancy markers.  For this first reservoir
        model, each marker represents a horizontal wall segment through the
        marker's cell center.  The returned tuple contains normal x/y/z,
        overlap area, ghost-center distance, and wall flag.
        """
        wall_flag = self.BoundaryParticleWallFlag(SourceID, BoundaryID)
        if wall_flag == 0:
            return None

        source = self.particles[SourceID]
        source_position = self.GetParticlePosition(SourceID)
        boundary_position = self.GetParticlePosition(BoundaryID)
        radius = float(source.Data.x)
        offset = self.WallContactOffsetDistance(radius)

        if wall_flag == 3:
            ghost = (
                source_position.x,
                boundary_position.y - radius + offset,
                source_position.z,
            )
            normal = (0.0, -1.0, 0.0)
        elif wall_flag == 4:
            ghost = (
                source_position.x,
                boundary_position.y + radius - offset,
                source_position.z,
            )
            normal = (0.0, 1.0, 0.0)
        else:
            return None

        dx = ghost[0] - source_position.x
        dy = ghost[1] - source_position.y
        dz = ghost[2] - source_position.z
        center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        if center_distance >= 2.0 * radius:
            return None
        overlap_area = self.particle_overlap_area(radius, radius, center_distance)
        return (*normal, overlap_area, center_distance, wall_flag)

    def EvaluateVerticalWallSegment(self, SourceID, BoundaryID):
        """Evaluate a vertical wall segment represented by a boundary marker.

        Boundary particles are occupancy markers.  Each marker represents a
        vertical wall segment through the marker's cell center.  The returned
        tuple contains normal x/y/z, overlap area, ghost-center distance, and
        wall flag.
        """
        wall_flag = self.BoundaryParticleVerticalWallFlag(SourceID, BoundaryID)
        if wall_flag == 0:
            return None

        source = self.particles[SourceID]
        source_position = self.GetParticlePosition(SourceID)
        boundary_position = self.GetParticlePosition(BoundaryID)
        radius = float(source.Data.x)
        offset = self.WallContactOffsetDistance(radius)

        if wall_flag == 1:
            ghost = (
                boundary_position.x - radius + offset,
                source_position.y,
                source_position.z,
            )
            normal = (-1.0, 0.0, 0.0)
        elif wall_flag == 2:
            ghost = (
                boundary_position.x + radius - offset,
                source_position.y,
                source_position.z,
            )
            normal = (1.0, 0.0, 0.0)
        else:
            return None

        dx = ghost[0] - source_position.x
        dy = ghost[1] - source_position.y
        dz = ghost[2] - source_position.z
        center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        if center_distance >= 2.0 * radius:
            return None
        overlap_area = self.particle_overlap_area(radius, radius, center_distance)
        return (*normal, overlap_area, center_distance, wall_flag)

    def EvaluateCDNozzleWallSegment(self, SourceID, BoundaryID):
        """Evaluate an analytic CD nozzle wall represented by a marker cell.

        Boundary particles only provide broad-phase locality.  The wall
        position and normal are calculated from the analytic nozzle profile at
        the source particle's current axial position.
        """
        wall_flag = self.BoundaryParticleCDNozzleWallFlag(SourceID, BoundaryID)
        if wall_flag == 0:
            return None

        source = self.particles[SourceID]
        source_position = self.GetParticlePosition(SourceID)
        radius = float(source.Data.x)
        axial = self.CDNozzleAxialPosition(source_position.x)
        if axial < 1.0 or axial > self.CDNozzleTotalLength():
            return None

        center_y = self.CDNozzleCenterY()
        nozzle_radius = self.CDNozzleRadius(axial)
        radius_slope = self.CDNozzleRadiusSlope(axial)
        offset = self.WallContactOffsetDistance(radius)

        if wall_flag == 3:
            wall_y = center_y - nozzle_radius
            normal_x = -radius_slope
            normal_y = -1.0
        elif wall_flag == 4:
            wall_y = center_y + nozzle_radius
            normal_x = -radius_slope
            normal_y = 1.0
        else:
            return None

        normal_mag = math.sqrt(normal_x * normal_x + normal_y * normal_y)
        if normal_mag <= self.EPSILON:
            return None
        normal = (
            normal_x / normal_mag,
            normal_y / normal_mag,
            0.0,
        )
        wall_point = (
            source_position.x,
            wall_y,
            source_position.z,
        )
        ghost = (
            wall_point[0] + normal[0] * (radius - offset),
            wall_point[1] + normal[1] * (radius - offset),
            wall_point[2],
        )

        dx = ghost[0] - source_position.x
        dy = ghost[1] - source_position.y
        dz = ghost[2] - source_position.z
        center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        if center_distance >= 2.0 * radius:
            return None
        overlap_area = self.particle_overlap_area(radius, radius, center_distance)
        return (*normal, overlap_area, center_distance, wall_flag)

    def ProcessBoundaryParticleWallCollision(self, SourceID, BoundaryID, totalForce):
        """Treat a boundary marker target as a source-owned wall collision."""
        contact_state = self.InitializeBoundaryParticleWallContactState(
            SourceID,
            BoundaryID,
        )
        if contact_state is None:
            return True
        return self.AccumulateContactForce(SourceID, contact_state, totalForce)

    def InitializeBoundaryParticleWallContactState(self, SourceID, BoundaryID):
        """Initialize one source-boundary-marker wall-segment contact."""
        segment = self.EvaluateWallSegment(SourceID, BoundaryID)
        if segment is None:
            return None
        normal_x, normal_y, normal_z, overlap_area, center_distance, wall_flag = segment
        radius = float(self.particles[SourceID].Data.x)
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

    def BoundaryParticleAppliesToSource(self, SourceID, BoundaryID):
        """Return True when a boundary marker is local to the source."""
        source_position = self.GetParticlePosition(SourceID)
        boundary_position = self.GetParticlePosition(BoundaryID)
        return (
            abs(source_position.x - boundary_position.x) <= 1.0
            and abs(source_position.z - boundary_position.z) <= 1.0
        )

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
        if not self.IsParticleActiveForDynamics(SourceID):
            return None
        if not self.IsParticleActiveForDynamics(TargetID):
            return None
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

    def ReservoirLifecycleEnabled(self):
        """Return True when Data.w is used as birth/live/dead state."""
        flow_type = str(
            getattr(self, "run_configuration", {}).get("flow_type", "")
        ).lower()
        return flow_type in ("pipe_reservoir_entry", "simple_reservoir")

    def IsParticleActiveForDynamics(self, ParticleID):
        """Return whether a particle participates in contacts and motion."""
        if not self.ReservoirLifecycleEnabled():
            return True
        return abs(float(self.particles[ParticleID].Data.w)) <= self.EPSILON

    def IsBoundaryParticle(self, ParticleID):
        """Return True when a particle is an occupancy-only boundary marker."""
        return float(getattr(self.particles[ParticleID], "ptype", 0.0)) > 0.5

    def IsMobileParticleActiveForDynamics(self, ParticleID):
        """Return True when a particle is a live mobile dynamics source."""
        if self.IsBoundaryParticle(ParticleID):
            return False
        return self.IsParticleActiveForDynamics(ParticleID)

    def BoundaryParticleWallsEnabled(self):
        """Return True when boundary markers provide wall broad phase."""
        return any(
            self.IsBoundaryParticle(particle_id)
            for particle_id in range(len(self.particles))
        )

    def WallFlagsForDynamics(self):
        """Return wall flags that are solid for the current flow model."""
        if self.ReservoirLifecycleEnabled():
            return (3, 4)
        return (1, 2, 3, 4)

    def StartingParticleKey(self, SourceID, TargetID):
        """Return the unordered key for a particle starting contact."""
        low_id = min(int(SourceID), int(TargetID))
        high_id = max(int(SourceID), int(TargetID))
        return ("particle", low_id, high_id)

    def StartingWallKey(self, SourceID, wall_flag):
        """Return the key for a source-owned wall starting contact."""
        return ("wall", int(SourceID), int(wall_flag))

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

        if bool(self.ShaderFlags.Boundary):
            for source_id, source in enumerate(self.particles):
                if not self.IsMobileParticleActiveForDynamics(source_id):
                    continue
                radius = float(source.Data.x)
                physical_limit = 2.0 * radius
                for wall_flag in self.WallFlagsForDynamics():
                    geometry = self.GetPhysicalWallGhostGeometry(source_id, wall_flag)
                    if geometry is None:
                        continue
                    center_distance = geometry[4]
                    if center_distance >= physical_limit - self.EPSILON:
                        continue
                    if center_distance <= self.EPSILON or physical_limit <= self.EPSILON:
                        continue

                    self.starting_contact_states[
                        self.StartingWallKey(source_id, wall_flag)
                    ] = {
                        "kind": "wall",
                        "status": "active",
                        "start_center_distance": center_distance,
                        "physical_separation_limit": physical_limit,
                        "effective_radius": 0.5 * center_distance,
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

    def GetPhysicalWallGhostGeometry(self, SourceID, wall_flag):
        """Return physical fixed-wall ghost geometry for the current snapshot."""
        source = self.particles[SourceID]
        position = self.GetParticlePosition(SourceID)
        radius = float(source.Data.x)
        offset = self.WallContactOffsetDistance(radius)
        cfg = self.run_configuration

        if wall_flag == 1:
            ghost = (
                float(cfg.get("WallXMIN", 0.0)) - radius + offset,
                position.y,
                position.z,
            )
            normal = (-1.0, 0.0, 0.0)
        elif wall_flag == 2:
            ghost = (
                float(cfg.get("WallXMAX", self.ShaderFlags.SideLength))
                + radius
                - offset,
                position.y,
                position.z,
            )
            normal = (1.0, 0.0, 0.0)
        elif wall_flag == 3:
            ghost = (
                position.x,
                float(cfg.get("WallYMIN", 0.0)) - radius + offset,
                position.z,
            )
            normal = (0.0, -1.0, 0.0)
        elif wall_flag == 4:
            ghost = (
                position.x,
                float(cfg.get("WallYMAX", self.ShaderFlags.SideLength))
                + radius
                - offset,
                position.z,
            )
            normal = (0.0, 1.0, 0.0)
        else:
            return None

        dx = ghost[0] - position.x
        dy = ghost[1] - position.y
        dz = ghost[2] - position.z
        center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        if center_distance >= 2.0 * radius:
            return None
        overlap_area = self.particle_overlap_area(radius, radius, center_distance)
        return (*normal, overlap_area, center_distance)

    def GetWallGhostGeometry(self, SourceID, wall_flag):
        """Return fixed-wall ghost geometry for the current position snapshot."""
        physical_geometry = self.GetPhysicalWallGhostGeometry(SourceID, wall_flag)
        if physical_geometry is None:
            self.starting_contact_states.pop(
                self.StartingWallKey(SourceID, wall_flag),
                None,
            )
            return None

        normal_x, normal_y, normal_z, _overlap_area, center_distance = physical_geometry
        radius = float(self.particles[SourceID].Data.x)
        physical_limit = 2.0 * radius
        key = self.StartingWallKey(SourceID, wall_flag)
        state = self.starting_contact_states.get(key)

        effective_radius = radius
        starting_contact = 0.0
        starting_resolved = 0.0
        if state is not None:
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
                starting_contact = 1.0
                starting_resolved = 1.0
                if center_distance >= physical_limit - self.EPSILON:
                    self.starting_contact_states.pop(key, None)
                return None

            effective_radius = float(state["effective_radius"])
            starting_contact = 1.0

        if center_distance >= 2.0 * effective_radius:
            return None
        overlap_area = self.particle_overlap_area(
            effective_radius,
            effective_radius,
            center_distance,
        )
        return (
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
            center_distance,
            effective_radius,
            physical_limit,
            starting_contact,
            starting_resolved,
        )

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
            not bool(self.ShaderFlags.Boundary)
            and (output_position.x < 1.0 or output_position.y < 1.0)
        ):
            return self.SetError(self.constants.ERROR_PARTICLE_OUT_OF_BOUNDS)
        return True

    def isParticleContact(self, Frame, SourceID, TargetID, positionBuffer):
        if not self.IsParticleActiveForDynamics(SourceID):
            return False
        if not self.IsParticleActiveForDynamics(TargetID):
            return False
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
        if not suppress_contact and center_distance <= effective_source_radius:
            self.collIn.ErrorReturn = self.constants.ERROR_TUNNELING
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
            processed_boundary_walls = set()
            for target_id in range(len(self.particles)):
                if source_id == target_id:
                    continue
                if self.IsBoundaryParticle(target_id):
                    if not self.BoundaryParticleAppliesToSource(source_id, target_id):
                        continue
                    segment = self.EvaluateWallSegment(source_id, target_id)
                    if segment is None:
                        continue
                    wall_flag = int(segment[-1])
                    if wall_flag in processed_boundary_walls:
                        continue
                    if not self.ProcessBoundaryParticleWallCollision(
                        source_id,
                        target_id,
                        total_forces[source_id],
                    ):
                        return False
                    processed_boundary_walls.add(wall_flag)
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
        return True

    def AddContactTargetID(self, SourceID, TargetID):
        """Add only the target id to the source contact list."""
        source = self.particles[SourceID]
        if TargetID not in source.collision_list:
            source.collision_list.append(TargetID)
        return True

    def BuildWallContactLists(self, total_forces):
        """Process each active stationary wall ghost exactly once."""
        if self.BoundaryParticleWallsEnabled():
            return True
        for source_id in range(len(self.particles)):
            if not self.IsMobileParticleActiveForDynamics(source_id):
                continue
            if bool(self.ShaderFlags.Boundary):
                for wall_flag in self.WallFlagsForDynamics():
                    if not self.ProcessWallCollision(
                        source_id,
                        wall_flag,
                        total_forces[source_id],
                    ):
                        return False
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

    def SetError(self, error_code):
        """Set the shared collision error state and return failure."""
        self.collIn.ErrorReturn = error_code
        return False
