import math
import itertools

from gbase.FunctionWall import evaluate_wall_at_point
from gbase.FunctionWall import physical_penetration
from gbase.MaterialProperties import (
    PARTICLE_TYPE_BOUNDARY,
    PARTICLE_TYPE_PHOTON,
    PARTICLE_TYPE_REGULAR,
)
from gbase.pdata import PTYPE_BOUNDARY, PTYPE_PHOTON


class ForceContactDynamics:
    """Apply overlap-area central forces through a source-owned linear chain."""

    EPSILON = 1.0e-12
    CONTACT_PARTICLE = 1
    CONTACT_WALL = 2
    CONTACT_ACTIVE_THIS_FRAME = 1
    TARGET_PENETRATION_FRACTION = 0.5
    HARD_PENETRATION_FRACTION = 0.75

    @staticmethod
    def VelocityAngle(vx, vy):
        """Return the GLSL VelRad.w velocity angle for an xy velocity."""
        return math.atan2(vy, vx) if vx != 0.0 or vy != 0.0 else 0.0

    def GetParticleType(self, ParticleID):
        """Return the runtime particle behavior encoded in pdata.ptype."""
        ptype = int(round(float(getattr(self.particles[ParticleID], "ptype", 0.0))))
        if ptype == int(PTYPE_PHOTON):
            return PARTICLE_TYPE_PHOTON
        if ptype == int(PTYPE_BOUNDARY):
            return PARTICLE_TYPE_BOUNDARY
        return PARTICLE_TYPE_REGULAR

    def IsPhotonParticle(self, ParticleID):
        """Return true when a particle's runtime type marks it as a photon."""
        return self.GetParticleType(ParticleID) == PARTICLE_TYPE_PHOTON

    def ShouldSkipParticlePair(self, SourceID, TargetID):
        """Mirror photons.glsl pair filtering for Python direct scans."""
        source_photon = self.IsPhotonParticle(SourceID)
        target_photon = self.IsPhotonParticle(TargetID)
        return (source_photon and target_photon) or (
            not source_photon and target_photon
        )

    def ReflectFixedSpeed(self, velocity, normal):
        """Reflect a velocity across a normal while preserving speed."""
        vx, vy, vz = (float(velocity[0]), float(velocity[1]), float(velocity[2]))
        nx, ny, nz = (float(normal[0]), float(normal[1]), float(normal[2]))
        speed = math.sqrt(vx * vx + vy * vy + vz * vz)
        normal_length = math.sqrt(nx * nx + ny * ny + nz * nz)
        if speed <= 0.0 or normal_length <= 0.0:
            return vx, vy, vz

        ux, uy, uz = nx / normal_length, ny / normal_length, nz / normal_length
        dot = vx * ux + vy * uy + vz * uz
        rx = vx - 2.0 * dot * ux
        ry = vy - 2.0 * dot * uy
        rz = vz - 2.0 * dot * uz
        reflected_length = math.sqrt(rx * rx + ry * ry + rz * rz)
        if reflected_length <= 0.0:
            return vx, vy, vz
        scale = speed / reflected_length
        return rx * scale, ry * scale, rz * scale

    def RecordPhotonReflection(self, SourceID, normal):
        """Remember a fixed-speed reflected photon velocity for this source."""
        if not self.IsPhotonParticle(SourceID):
            return
        velocity = self.photon_reflected_velocity.get(SourceID)
        if velocity is None:
            start_velocity = self.GetStartFrameVelocity(SourceID)
            velocity = (
                float(start_velocity.x),
                float(start_velocity.y),
                float(start_velocity.z),
            )
        self.photon_reflected_velocity[SourceID] = self.ReflectFixedSpeed(
            velocity,
            normal,
        )

    def ApplyPhotonVelocityOverride(self, SourceID):
        """Apply the remembered reflected photon velocity after normal solving."""
        velocity = self.photon_reflected_velocity.get(SourceID)
        if velocity is None:
            return
        particle = self.particles[SourceID]
        particle.VelRad.x = velocity[0]
        particle.VelRad.y = velocity[1]
        particle.VelRad.z = velocity[2]
        particle.VelRad.w = self.VelocityAngle(velocity[0], velocity[1])

    def RecordPhotonParticleReflection(self, SourceID, TargetID, normal, hit_t):
        """Reflect one photon and remember where it ends this frame."""
        dt = float(self.ShaderFlags.dt)
        source_position = self.GetParticlePosition(SourceID)
        target_position = self.GetParticlePosition(TargetID)
        source_velocity = self.GetStartFrameVelocity(SourceID)
        target_velocity = self.GetStartFrameVelocity(TargetID)
        reflected_velocity = self.ReflectFixedSpeed(
            (
                float(source_velocity.x),
                float(source_velocity.y),
                float(source_velocity.z),
            ),
            normal,
        )
        hit_t = max(0.0, min(1.0, float(hit_t)))
        target_hit_x = float(target_position.x) + float(target_velocity.x) * dt * hit_t
        target_hit_y = float(target_position.y) + float(target_velocity.y) * dt * hit_t
        target_hit_z = float(target_position.z) + float(target_velocity.z) * dt * hit_t
        source_radius = float(self.particles[SourceID].Data.x)
        target_radius = float(self.particles[TargetID].Data.x)
        contact_radius = source_radius + target_radius
        normal_x, normal_y, normal_z = (
            float(normal[0]),
            float(normal[1]),
            float(normal[2]),
        )
        hit_x = target_hit_x - normal_x * contact_radius
        hit_y = target_hit_y - normal_y * contact_radius
        hit_z = target_hit_z - normal_z * contact_radius
        remaining_dt = dt * (1.0 - hit_t)
        exit_epsilon = max(self.EPSILON, source_radius * 0.01)
        self.photon_reflected_velocity[SourceID] = reflected_velocity
        self.photon_reflected_position[SourceID] = (
            hit_x + reflected_velocity[0] * remaining_dt - normal_x * exit_epsilon,
            hit_y + reflected_velocity[1] * remaining_dt - normal_y * exit_epsilon,
            hit_z + reflected_velocity[2] * remaining_dt - normal_z * exit_epsilon,
        )
        self.particles[SourceID].colFlg = 1
        self.particles[SourceID].material_id = getattr(
            self.particles[TargetID],
            "material_id",
            self.particles[SourceID].material_id,
        )

    def TryPhotonParticleReflection(self, SourceID, TargetID):
        """Handle photon-dust overlap or swept crossing without mechanical force."""
        if not self.IsPhotonParticle(SourceID) or self.IsPhotonParticle(TargetID):
            return False

        dt = float(self.ShaderFlags.dt)
        if dt <= 0.0:
            return False

        source_position = self.GetParticlePosition(SourceID)
        target_position = self.GetParticlePosition(TargetID)
        source_velocity = self.GetStartFrameVelocity(SourceID)
        target_velocity = self.GetStartFrameVelocity(TargetID)
        rel_vx = (float(source_velocity.x) - float(target_velocity.x)) * dt
        rel_vy = (float(source_velocity.y) - float(target_velocity.y)) * dt
        rel_vz = (float(source_velocity.z) - float(target_velocity.z)) * dt
        motion_length_sq = rel_vx * rel_vx + rel_vy * rel_vy + rel_vz * rel_vz
        if motion_length_sq <= self.EPSILON:
            return False

        start_dx = float(source_position.x) - float(target_position.x)
        start_dy = float(source_position.y) - float(target_position.y)
        start_dz = float(source_position.z) - float(target_position.z)
        source_radius = float(self.particles[SourceID].Data.x)
        target_radius = float(self.particles[TargetID].Data.x)
        contact_radius = source_radius + target_radius

        start_distance_sq = (
            start_dx * start_dx + start_dy * start_dy + start_dz * start_dz
        )
        if start_distance_sq < contact_radius * contact_radius:
            hit_t = 0.0
            center_distance = math.sqrt(max(start_distance_sq, 0.0))
            if center_distance <= self.EPSILON:
                normal = (1.0, 0.0, 0.0)
            else:
                normal = (
                    -start_dx / center_distance,
                    -start_dy / center_distance,
                    -start_dz / center_distance,
                )
        else:
            a = motion_length_sq
            b = 2.0 * (start_dx * rel_vx + start_dy * rel_vy + start_dz * rel_vz)
            c = start_distance_sq - contact_radius * contact_radius
            discriminant = b * b - 4.0 * a * c
            if discriminant < 0.0:
                return False
            sqrt_discriminant = math.sqrt(discriminant)
            first_t = (-b - sqrt_discriminant) / (2.0 * a)
            second_t = (-b + sqrt_discriminant) / (2.0 * a)
            if 0.0 <= first_t <= 1.0:
                hit_t = first_t
            elif 0.0 <= second_t <= 1.0:
                hit_t = second_t
            else:
                return False
            hit_dx = start_dx + rel_vx * hit_t
            hit_dy = start_dy + rel_vy * hit_t
            hit_dz = start_dz + rel_vz * hit_t
            center_distance = math.sqrt(
                max(hit_dx * hit_dx + hit_dy * hit_dy + hit_dz * hit_dz, 0.0)
            )
            if center_distance <= self.EPSILON:
                normal = (1.0, 0.0, 0.0)
            else:
                normal = (
                    -hit_dx / center_distance,
                    -hit_dy / center_distance,
                    -hit_dz / center_distance,
                )

        self.RecordPhotonParticleReflection(SourceID, TargetID, normal, hit_t)
        return True

    def ApplyPhotonPositionOverride(self, SourceID, output_position):
        """Move a reflected photon to its remembered end-of-frame position."""
        position = self.photon_reflected_position.get(SourceID)
        if position is None:
            return False
        output_position.x = position[0]
        output_position.y = position[1]
        output_position.z = position[2]
        return True

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

    def ProcessParticleCollision(
        self,
        TargetID,
        SourceID,
        totalForce,
        geometry=None,
    ):
        """Calculate and accumulate one particle-contact force."""
        contact_state = self.InitializeContactState(
            SourceID,
            TargetID,
            geometry,
        )
        if contact_state is None:
            return self.collIn.ErrorReturn == self.constants.ERROR_NONE
        return self.AccumulateContactForce(SourceID, contact_state, totalForce)

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
        if self.IsPhotonParticle(SourceID):
            return True

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
        penetration_reserve = self.GetHardPenetrationDepth(source_radius)
        if inward_displacement > penetration_reserve + self.EPSILON:
            return self.SetError(
                self.constants.ERROR_PENETRATION_STEP_TOO_LARGE,
                error_kind=error_kind,
                source_id=SourceID,
                target_id=target_id,
                wall_flag=wall_flag,
        )
        return True

    def GetTargetPenetrationFraction(self):
        return float(
            self.run_configuration.get(
                "target_penetration_fraction",
                self.run_configuration.get(
                    "max_penetration_fraction",
                    self.TARGET_PENETRATION_FRACTION,
                ),
            )
        )

    def GetHardPenetrationFraction(self):
        return float(
            self.run_configuration.get(
                "hard_penetration_fraction",
                self.HARD_PENETRATION_FRACTION,
            )
        )

    def GetTargetPenetrationDepth(self, source_radius):
        return self.GetTargetPenetrationFraction() * float(source_radius)

    def GetHardPenetrationDepth(self, source_radius):
        return self.GetHardPenetrationFraction() * float(source_radius)

    def GetContactTargetVelocity(self, contact_state):
        """Return the frame-start velocity of a contact target or wall ghost."""
        contact_type = int(contact_state.ids.y)
        if contact_type == self.CONTACT_WALL:
            return getattr(
                contact_state,
                "wall_target_velocity",
                self.create_vec4(),
            )
        return self.GetStartFrameVelocity(int(contact_state.ids.x))

    def GetContactTargetDepth(self, contact_state):
        """Return the preferred source-owned compression depth."""
        return self.GetTargetPenetrationDepth(contact_state.source_radius)

    def GetContactHardDepth(self, contact_state):
        """Return the source-owned fatal compression depth."""
        return self.GetHardPenetrationDepth(contact_state.source_radius)

    def GetContactRemainingDepth(self, contact_state):
        """Return how much additional penetration is available before hard depth."""
        hard_depth = self.GetContactHardDepth(contact_state)
        penetration_depth = max(0.0, float(contact_state.aux.y))
        return max(0.0, hard_depth - penetration_depth)

    def GetContactInwardSpeed(self, SourceID, contact_state, velocity=None):
        """Return positive speed that would increase contact penetration."""
        source_velocity = velocity if velocity is not None else self.particles[SourceID].VelRad
        target_velocity = self.GetContactTargetVelocity(contact_state)
        normal = (
            float(contact_state.geom.x),
            float(contact_state.geom.y),
            float(contact_state.geom.z),
        )
        relative_normal_velocity = (
            (float(target_velocity.x) - float(source_velocity.x)) * normal[0]
            + (float(target_velocity.y) - float(source_velocity.y)) * normal[1]
            + (float(target_velocity.z) - float(source_velocity.z)) * normal[2]
        )
        return max(0.0, -relative_normal_velocity)

    def CheckContactMaximumDepth(self, SourceID, contact_state):
        """Reject a contact whose current penetration exceeds hard depth."""
        penetration_depth = max(0.0, float(contact_state.aux.y))
        target_depth = self.GetContactTargetDepth(contact_state)
        hard_depth = self.GetContactHardDepth(contact_state)
        contact_state.maximum_depth = target_depth
        contact_state.hard_depth = hard_depth
        contact_state.remaining_depth = max(0.0, hard_depth - penetration_depth)
        contact_state.maximum_depth_reached = (
            1.0 if penetration_depth >= target_depth - self.EPSILON else 0.0
        )
        if penetration_depth <= hard_depth + self.EPSILON:
            return True

        contact_type = int(contact_state.ids.y)
        return self.SetError(
            self.constants.ERROR_MAX_DEPTH_CONSTRAINT,
            error_kind="particle-wall" if contact_type == self.CONTACT_WALL else "particle-particle",
            source_id=SourceID,
            target_id=int(contact_state.ids.x) if contact_type == self.CONTACT_PARTICLE else None,
            wall_flag=int(contact_state.ids.x) if contact_type == self.CONTACT_WALL else None,
        )

    def CheckContactPenetrationStepResolution(self, SourceID, contact_state, velocity=None):
        """Require the next source step to fit inside remaining contact depth."""
        if self.IsPhotonParticle(SourceID):
            return True

        penetration_depth = max(0.0, float(contact_state.aux.y))
        hard_depth = self.GetContactHardDepth(contact_state)
        if penetration_depth > hard_depth + self.EPSILON:
            contact_type = int(contact_state.ids.y)
            return self.SetError(
                self.constants.ERROR_MAX_DEPTH_CONSTRAINT,
                error_kind="particle-wall" if contact_type == self.CONTACT_WALL else "particle-particle",
                source_id=SourceID,
                target_id=int(contact_state.ids.x) if contact_type == self.CONTACT_PARTICLE else None,
                wall_flag=int(contact_state.ids.x) if contact_type == self.CONTACT_WALL else None,
            )

        inward_speed = self.GetContactInwardSpeed(SourceID, contact_state, velocity)
        inward_displacement = inward_speed * float(self.ShaderFlags.dt)
        remaining_depth = self.GetContactRemainingDepth(contact_state)
        if inward_displacement <= remaining_depth + self.EPSILON:
            return True

        contact_type = int(contact_state.ids.y)
        return self.SetError(
            self.constants.ERROR_PENETRATION_STEP_TOO_LARGE,
            error_kind="particle-wall" if contact_type == self.CONTACT_WALL else "particle-particle",
            source_id=SourceID,
            target_id=int(contact_state.ids.x) if contact_type == self.CONTACT_PARTICLE else None,
            wall_flag=int(contact_state.ids.x) if contact_type == self.CONTACT_WALL else None,
        )

    def CheckResolvedContactStep(self, SourceID):
        """Validate resolved velocity against all active contact reserves."""
        source = self.particles[SourceID]
        for contact_index in range(int(source.contactCount)):
            contact_state = self.GetContactSlots(SourceID)[contact_index]
            contact_type = int(contact_state.ids.y)
            if contact_type not in (self.CONTACT_PARTICLE, self.CONTACT_WALL):
                continue
            if not self.CheckContactPenetrationStepResolution(
                SourceID,
                contact_state,
                source.VelRad,
            ):
                return False
        return True

    def EvaluateFunctionWallSegment(self, SourceID, segment):
        """Evaluate one configured function wall against a mobile source."""
        source_position = self.GetParticlePosition(SourceID)
        source_point = (
            float(source_position.x),
            float(source_position.y),
        )
        evaluation = evaluate_wall_at_point(segment, source_point)
        if evaluation is None:
            return None

        wall_flag = int(evaluation["wall_flag"])
        if wall_flag <= 0:
            return None

        radius = float(self.particles[SourceID].Data.x)
        penetration_depth = physical_penetration(segment, source_point, radius)
        if penetration_depth is None or penetration_depth <= self.EPSILON:
            return None
        normal_x, normal_y = evaluation["normal"]
        normal = (normal_x, normal_y, 0.0)
        center_distance = max(0.0, 2.0 * radius - penetration_depth)
        overlap_area = self.particle_overlap_area(
            radius,
            radius,
            center_distance,
        )
        return (*normal, overlap_area, center_distance, wall_flag)

    def EvaluateFunctionWallContacts(self, SourceID):
        """Return the deepest current contact for each physical wall."""
        radius = float(self.particles[SourceID].Data.x)
        contacts = {}
        for segment in self.run_configuration.get("curve_wall_segments", ()):
            contact = self.EvaluateFunctionWallSegment(SourceID, segment)
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

    def EvaluateRectangleWallSegment(self, SourceID, wall_config):
        """Evaluate one configured 3D rectangle wall against a mobile source.

        rectangle_wall_segments store normals that point into the valid
        particle region. Contact slots store the opposite normal because the
        source force path applies -F * normal.
        """
        source_position = self.GetParticlePosition(SourceID)
        source_point = (
            float(source_position.x),
            float(source_position.y),
            float(source_position.z),
        )
        origin = self._vector3(wall_config.get("origin"), "origin")
        u_axis = self._axis_vector(wall_config.get("u_axis"))
        v_axis = self._axis_vector(wall_config.get("v_axis"))
        inward_normal = self._vector3(wall_config.get("normal"), "normal")
        normal_length = math.sqrt(
            inward_normal[0] * inward_normal[0]
            + inward_normal[1] * inward_normal[1]
            + inward_normal[2] * inward_normal[2]
        )
        if normal_length <= self.EPSILON:
            return None
        inward_normal = (
            inward_normal[0] / normal_length,
            inward_normal[1] / normal_length,
            inward_normal[2] / normal_length,
        )

        rel = (
            source_point[0] - origin[0],
            source_point[1] - origin[1],
            source_point[2] - origin[2],
        )
        u_coord = rel[0] * u_axis[0] + rel[1] * u_axis[1] + rel[2] * u_axis[2]
        v_coord = rel[0] * v_axis[0] + rel[1] * v_axis[1] + rel[2] * v_axis[2]
        u_length = float(wall_config.get("u_length", 0.0))
        v_length = float(wall_config.get("v_length", 0.0))
        if u_coord < -self.EPSILON or u_coord > u_length + self.EPSILON:
            return None
        if v_coord < -self.EPSILON or v_coord > v_length + self.EPSILON:
            return None

        signed_inward_distance = (
            rel[0] * inward_normal[0]
            + rel[1] * inward_normal[1]
            + rel[2] * inward_normal[2]
        )
        radius = float(self.particles[SourceID].Data.x)
        penetration_depth = radius - signed_inward_distance
        if penetration_depth <= self.EPSILON:
            return None

        center_distance = max(0.0, 2.0 * radius - penetration_depth)
        overlap_area = self.particle_overlap_area(radius, radius, center_distance)
        wall_flag = int(wall_config.get("wall_flag", 0))
        if wall_flag <= 0:
            return None
        outward_normal = (
            -inward_normal[0],
            -inward_normal[1],
            -inward_normal[2],
        )
        return (*outward_normal, overlap_area, center_distance, wall_flag)

    def EvaluateRectangleWallContacts(self, SourceID):
        """Return the deepest current rectangle-wall contact per wall flag."""
        radius = float(self.particles[SourceID].Data.x)
        contacts = {}
        segments = self.run_configuration.get("rectangle_wall_segments")
        if not segments:
            return contacts
        for _wall_name, wall_config in segments.items():
            contact = self.EvaluateRectangleWallSegment(SourceID, wall_config)
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

    def RectangleWallPhysicalPenetration(self, SourceID, wall_config):
        """Return physical penetration into one finite 3D rectangle wall."""
        contact = self.EvaluateRectangleWallSegment(SourceID, wall_config)
        if contact is None:
            return None
        radius = float(self.particles[SourceID].Data.x)
        return self.ParticlePenetrationDepth(radius, radius, float(contact[-2]))

    def EvaluateConfiguredWallContacts(self, SourceID):
        """Return current wall contacts for the active configured wall model."""
        if self.run_configuration.get("rectangle_wall_segments"):
            return self.EvaluateRectangleWallContacts(SourceID)
        return self.EvaluateFunctionWallContacts(SourceID)

    def LightingBallConfig(self):
        """Return configured lighting-ball center/radius, if present."""
        values = self.run_configuration.get("Lighting_ball")
        if values is None:
            return None
        if hasattr(values, "get"):
            center = (
                float(values.get("x")),
                float(values.get("y")),
                float(values.get("z")),
            )
            radius = float(values.get("radius"))
        else:
            if len(values) < 4:
                return None
            center = (
                float(values[0]),
                float(values[1]),
                float(values[2]),
            )
            radius = float(values[3])
        if radius <= 0.0:
            return None
        return (center, radius)

    def EvaluateLightingBallContact(self, SourceID):
        """Evaluate contact against the configured sphere equation."""
        lighting_ball = self.LightingBallConfig()
        if lighting_ball is None:
            return None

        center, ball_radius = lighting_ball
        source_position = self.GetParticlePosition(SourceID)
        dx = float(source_position.x) - center[0]
        dy = float(source_position.y) - center[1]
        dz = float(source_position.z) - center[2]
        center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        if center_distance <= self.EPSILON:
            return None

        source_radius = float(self.particles[SourceID].Data.x)
        signed_surface_distance = center_distance - ball_radius
        penetration_depth = source_radius - signed_surface_distance
        if penetration_depth <= self.EPSILON:
            return None

        normal = (
            dx / center_distance,
            dy / center_distance,
            dz / center_distance,
        )
        contact_center_distance = max(0.0, 2.0 * source_radius - penetration_depth)
        overlap_area = self.particle_overlap_area(
            source_radius,
            source_radius,
            contact_center_distance,
        )
        values = self.run_configuration.get("Lighting_ball")
        if hasattr(values, "get"):
            wall_flag = int(values.get("wall_flag", 1000))
        else:
            wall_flag = int(self.run_configuration.get("lighting_ball_wall_flag", 1000))
        return (*normal, overlap_area, contact_center_distance, wall_flag)

    def ProcessLightingBallCollision(self, SourceID, totalForce):
        """Reflect a source from the configured lighting-ball sphere."""
        contact = self.EvaluateLightingBallContact(SourceID)
        if contact is None:
            return True

        source = self.particles[SourceID]
        normal = contact[:3]
        source.colFlg = 1
        if self.IsPhotonParticle(SourceID):
            source.material_id = float(self.run_configuration.get(
                "lighting_ball_material_id",
                getattr(source, "material_id", 0.0),
            ))
            lighting_ball = self.run_configuration.get("Lighting_ball")
            if hasattr(lighting_ball, "get"):
                source.material_id = float(
                    lighting_ball.get("material_id", source.material_id)
                )
            self.DepositBoundaryLightForSurface(
                1,
                int(contact[-1]),
                source.material_id,
                self.particle_position_tuple(source),
            )
        source.report_contacts = max(int(getattr(source, "report_contacts", 0)), 1)
        source.report_target = int(contact[-1])
        source.report_normal_x = normal[0]
        source.report_normal_y = normal[1]
        source.report_normal_z = normal[2]

        start_velocity = self.GetStartFrameVelocity(SourceID)
        velocity = (
            float(start_velocity.x),
            float(start_velocity.y),
            float(start_velocity.z),
        )
        inward_speed = -(
            velocity[0] * normal[0]
            + velocity[1] * normal[1]
            + velocity[2] * normal[2]
        )
        if inward_speed <= self.EPSILON:
            return True

        if self.IsPhotonParticle(SourceID):
            self.photon_reflected_velocity[SourceID] = self.ReflectFixedSpeed(
                velocity,
                normal,
            )
        return True

    def GetPistonPosition(self, frame):
        """Return the piston x position for the specified simulation frame."""
        start_x = float(self.run_configuration["piston_x_start"])
        stop_x = float(self.run_configuration["piston_x_stop"])
        start_frame = int(self.run_configuration["piston_start_frame"])
        velocity_x = float(self.run_configuration["piston_velocity"][0])

        elapsed_frames = max(0, int(frame) - start_frame)
        position = start_x + elapsed_frames * float(self.ShaderFlags.dt) * velocity_x
        return min(position, stop_x)

    def PistonEnabled(self):
        """Return whether this scenario defines the analytic piston model."""
        if not bool(self.run_configuration.get("piston_enabled", False)):
            return False
        return all(
            key in self.run_configuration
            for key in (
                "piston_x_start",
                "piston_x_stop",
                "piston_velocity",
                "piston_start_frame",
            )
        )

    def GetPistonVelocity(self, frame):
        """Return zero while parked and the configured velocity while moving."""
        start_frame = int(self.run_configuration["piston_start_frame"])
        stop_x = float(self.run_configuration["piston_x_stop"])
        if int(frame) < start_frame or self.GetPistonPosition(frame) >= stop_x:
            return self.create_vec4()

        velocity = self.run_configuration["piston_velocity"]
        vx, vy, vz = (float(value) for value in velocity)
        return self.create_vec4(vx, vy, vz, self.VelocityAngle(vx, vy))

    def EvaluatePistonWall(self, SourceID):
        """Evaluate the analytic vertical piston plane for one mobile source."""
        source_position = self.GetParticlePosition(SourceID)
        radius = float(self.particles[SourceID].Data.x)

        piston_x = self.GetPistonPosition(self.ShaderFlags.frameNum)
        normal = (-1.0, 0.0, 0.0)
        penetration_depth = radius - (float(source_position.x) - piston_x)
        if penetration_depth <= self.EPSILON:
            return None
        center_distance = max(0.0, 2.0 * radius - penetration_depth)
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
        geometry = (
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
            center_distance,
            radius,
            radius,
        )
        contact_state = self.AppendWallContactSlot(SourceID, wall_flag, geometry)
        if contact_state is None:
            return False
        contact_state.wall_target_velocity = self.GetPistonVelocity(
            self.ShaderFlags.frameNum
        )
        contact_state.is_piston_contact = 1.0
        if not self.CheckContactMaximumDepth(SourceID, contact_state):
            return False
        if not self.CheckContactPenetrationStepResolution(SourceID, contact_state):
            return False
        if hasattr(self, "RecordContactParameters"):
            self.RecordContactParameters(SourceID, wall_flag, contact_state)
        return self.AccumulateContactForce(SourceID, contact_state, totalForce)

    def ProcessFunctionWallCollision(self, SourceID, contact, totalForce):
        """Apply one source-owned function-wall contact."""
        contact_state = self.InitializeFunctionWallContactState(SourceID, contact)
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

    def InitializeFunctionWallContactState(self, SourceID, contact):
        """Initialize one current-frame source-function-wall contact."""
        normal_x, normal_y, normal_z, overlap_area, center_distance, wall_flag = contact
        radius = float(self.particles[SourceID].Data.x)
        geometry = (
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
            center_distance,
            radius,
            radius,
        )
        contact_state = self.AppendWallContactSlot(SourceID, wall_flag, geometry)
        if contact_state is None:
            return None
        if not self.CheckContactMaximumDepth(SourceID, contact_state):
            return None
        if not self.CheckContactPenetrationStepResolution(SourceID, contact_state):
            return None
        return contact_state

    def BoundaryMarkerApplies(self, SourceID, BoundaryID):
        """Return True when a boundary sentinel is local to a source."""
        source_position = self.GetParticlePosition(SourceID)
        boundary_position = self.GetParticlePosition(BoundaryID)
        return (
            abs(source_position.x - boundary_position.x) <= 1.0
            and abs(source_position.y - boundary_position.y) <= 1.0
            and abs(source_position.z - boundary_position.z) <= 1.0
        )

    def BoundaryParticleNormal(self, BoundaryID):
        """Return a boundary-particle normal stored in VelRad.xyz, if present."""
        boundary = self.particles[BoundaryID]
        nx = float(boundary.VelRad.x)
        ny = float(boundary.VelRad.y)
        nz = float(boundary.VelRad.z)
        normal_length = math.sqrt(nx * nx + ny * ny + nz * nz)
        if normal_length <= self.EPSILON:
            return None
        return nx / normal_length, ny / normal_length, nz / normal_length

    def EvaluateBoundaryParticleContact(self, SourceID, BoundaryID):
        """Evaluate a direct boundary-particle contact from marker normal data."""
        if not self.BoundaryMarkerApplies(SourceID, BoundaryID):
            return None

        normal = self.BoundaryParticleNormal(BoundaryID)
        if normal is None:
            return None

        source_position = self.GetParticlePosition(SourceID)
        boundary_position = self.GetParticlePosition(BoundaryID)
        source_radius = float(self.particles[SourceID].Data.x)
        signed_distance = (
            (float(source_position.x) - float(boundary_position.x)) * normal[0]
            + (float(source_position.y) - float(boundary_position.y)) * normal[1]
            + (float(source_position.z) - float(boundary_position.z)) * normal[2]
        )
        offset_x = float(source_position.x) - float(boundary_position.x)
        offset_y = float(source_position.y) - float(boundary_position.y)
        offset_z = float(source_position.z) - float(boundary_position.z)
        tangent_x = offset_x - signed_distance * normal[0]
        tangent_y = offset_y - signed_distance * normal[1]
        tangent_z = offset_z - signed_distance * normal[2]
        tangent_distance = math.sqrt(
            tangent_x * tangent_x
            + tangent_y * tangent_y
            + tangent_z * tangent_z
        )
        marker_half_extent = float(
            self.run_configuration.get("boundary_marker_contact_half_extent", 0.75)
        )
        if tangent_distance > marker_half_extent:
            return None

        penetration_depth = source_radius - signed_distance
        if penetration_depth <= self.EPSILON:
            return None

        center_distance = max(0.0, 2.0 * source_radius - penetration_depth)
        overlap_area = self.particle_overlap_area(
            source_radius,
            source_radius,
            center_distance,
        )
        wall_flag = int(round(float(self.particles[BoundaryID].pnum)))
        if wall_flag <= 0:
            return None
        return (*normal, overlap_area, center_distance, wall_flag)

    def ProcessBoundaryParticleCollision(self, SourceID, BoundaryID, totalForce):
        """Apply one source-owned direct boundary-particle contact."""
        contact = self.EvaluateBoundaryParticleContact(SourceID, BoundaryID)
        if contact is None:
            return True
        normal = contact[:3]
        start_velocity = self.GetStartFrameVelocity(SourceID)
        velocity = (
            float(start_velocity.x),
            float(start_velocity.y),
            float(start_velocity.z),
        )
        inward_speed = -(
            velocity[0] * normal[0]
            + velocity[1] * normal[1]
            + velocity[2] * normal[2]
        )
        if inward_speed <= self.EPSILON:
            return True

        source = self.particles[SourceID]
        self.photon_reflected_velocity[SourceID] = self.ReflectFixedSpeed(
            velocity,
            normal,
        )
        source.colFlg = 1
        if self.IsPhotonParticle(SourceID):
            source.material_id = float(
                getattr(
                    self.particles[BoundaryID],
                    "material_id",
                    source.material_id,
                )
            )
            self.DepositBoundaryLightForMaterial(BoundaryID, source.material_id)
        source.report_contacts = max(int(getattr(source, "report_contacts", 0)), 1)
        source.report_target = BoundaryID
        source.report_normal_x = normal[0]
        source.report_normal_y = normal[1]
        source.report_normal_z = normal[2]
        return True

    def InitializeContactState(self, SourceID, TargetID, geometry=None):
        """Initialize one current-frame source-target contact."""
        source = self.particles[SourceID]
        contact_state = self.GetContactState(SourceID, TargetID, geometry)
        if contact_state is None:
            return None
        source.colFlg = 1
        return contact_state

    def GetContactState(self, SourceID, TargetID, geometry=None):
        """Create and populate one current-frame source-owned contact slot.

        The slot first receives its target ID and current collision state.
        Current geometry is then calculated and stored in the slot. Returning
        a slot with no geometry is allowed when no current overlap is found;
        returning None means no contact slot was available.
        """
        contact = geometry
        if contact is None:
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
            source_radius,
            target_radius,
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
            source_radius,
            target_radius,
            center_distance,
        )
        contact_state.aux.z = 0.0
        contact_state.source_radius = source_radius
        contact_state.target_radius = target_radius
        contact_state.separation_limit = source_radius + target_radius
        return contact_state

    def GetParticleGeometry(self, SourceID, TargetID):
        """Calculate current-frame geometry for one source-target pair.

        Positions come from the frame-start snapshot.  When the physical radii
        overlap, return the source-to-target unit normal, circular overlap area,
        center distance, and physical radii.  In depth mode, penetration is
        the physical radius sum minus center distance.  Return None when no
        overlap exists.  Coincident centers use +x as a deterministic fallback
        normal.
        """
        source_position = self.GetParticlePosition(SourceID)
        target_position = self.GetParticlePosition(TargetID)
        dx = target_position.x - source_position.x
        dy = target_position.y - source_position.y
        dz = target_position.z - source_position.z
        center_distance = (dx * dx + dy * dy + dz * dz) ** 0.5

        source_radius = float(self.particles[SourceID].Data.x)
        target_radius = float(self.particles[TargetID].Data.x)
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
        )

    @staticmethod
    def ParticlePenetrationDepth(source_radius, target_radius, center_distance):
        """Return physical overlap depth from physical radii and distance."""
        return float(source_radius) + float(target_radius) - float(center_distance)

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

            source_radius = float(contact_state.source_radius)
            target_depth = self.GetTargetPenetrationDepth(source_radius)
            hard_depth = self.GetHardPenetrationDepth(source_radius)
            penetration_depth = max(0.0, float(contact_state.aux.y))
            contact_state.maximum_depth = target_depth
            contact_state.hard_depth = hard_depth
            contact_state.remaining_depth = max(
                0.0,
                hard_depth - penetration_depth,
            )
            contact_state.maximum_depth_reached = (
                1.0
                if penetration_depth >= target_depth - self.EPSILON
                else 0.0
            )
            if penetration_depth < target_depth - self.EPSILON:
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

    def GetCurrentParticlePosition(self, ParticleID):
        """Return position from the currently selected runtime buffer."""
        return self.particle_position(
            self.particles[ParticleID],
            int(self.ShaderFlags.positionBuffer),
        )

    def GetParticleVelocity(self, ParticleID):
        """Return the current runtime particle velocity."""
        return self.particles[ParticleID].VelRad

    def FunctionWallPhysicalPenetration(self, SourceID, segment):
        """Return signed physical penetration into one outward-facing wall."""
        source_position = self.GetParticlePosition(SourceID)
        source_point = (float(source_position.x), float(source_position.y))
        radius = float(self.particles[SourceID].Data.x)
        return physical_penetration(segment, source_point, radius)

    def IsBoundaryParticle(self, ParticleID):
        """Return True when a particle is an occupancy-only boundary marker."""
        return self.GetParticleType(ParticleID) == PARTICLE_TYPE_BOUNDARY

    def IsNullParticle(self, ParticleID):
        """Return True only for the reserved ABI particle at index zero."""
        particle = self.particles[ParticleID]
        return (
            int(ParticleID) == 0
            and int(getattr(particle, "pnum", -1)) == 0
            and float(getattr(particle, "ptype", 0.0)) < -0.5
        )

    def IsParticleDead(self, ParticleID):
        """Return True when Data.w marks a particle as retired/dead."""
        return float(self.particles[ParticleID].Data.w) < 0.0

    def IsParticlePendingBirth(self, ParticleID):
        """Return True while a positive Data.w release frame is in the future."""
        state_flag = float(self.particles[ParticleID].Data.w)
        if state_flag <= 0.0:
            return False
        return float(self.ShaderFlags.frameNum) < state_flag

    def IsParticleBorn(self, ParticleID):
        """Return True when a particle is not dead and has reached its release frame."""
        return (
            not self.IsParticleDead(ParticleID)
            and not self.IsParticlePendingBirth(ParticleID)
        )

    def IsParticleActiveForLifecycle(self, ParticleID):
        """Return True when lifecycle state allows a particle to be visible/usable."""
        return not self.IsNullParticle(ParticleID) and self.IsParticleBorn(ParticleID)

    def IsMobileParticleActiveForDynamics(self, ParticleID):
        """Return True when a particle is a mobile dynamics source."""
        return (
            self.IsParticleActiveForLifecycle(ParticleID)
            and not self.IsBoundaryParticle(ParticleID)
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

    def ParticleContactTargetIDs(self, SourceID):
        """Return active particle target IDs derived from contact slots."""
        source = self.particles[SourceID]
        return [
            int(contact_state.ids.x)
            for contact_state in self.GetContactSlots(SourceID)[
                : int(source.contactCount)
            ]
            if int(contact_state.ids.y) == self.CONTACT_PARTICLE
            and int(contact_state.ids.w) == self.CONTACT_ACTIVE_THIS_FRAME
        ]

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
        base_stiffness = self.GetContactStiffness(
            SourceID,
            TargetID,
            contact_type,
        )
        penetration_depth = max(0.0, float(contact_state.aux.y))
        pair_stiffness = self.GetEffectiveContactStiffness(
            base_stiffness,
            penetration_depth,
            float(getattr(contact_state, "source_radius", 0.0)),
        )
        if self.contact_force_measure == "depth":
            contact_measure = penetration_depth
        else:
            contact_measure = float(contact_state.geom.w)
        force_magnitude = pair_stiffness * max(0.0, contact_measure)
        contact_state.base_stiffness_q = base_stiffness
        contact_state.effective_stiffness_q = pair_stiffness
        contact_state.force_magnitude = force_magnitude
        totalForce.x -= force_magnitude * float(contact_state.geom.x)
        totalForce.y -= force_magnitude * float(contact_state.geom.y)
        totalForce.z -= force_magnitude * float(contact_state.geom.z)
        return True

    def GetCompressionStiffnessGain(self):
        """Return the dimensionless near-hard-depth stiffness gain."""
        return max(
            0.0,
            float(self.run_configuration.get("compression_stiffness_gain", 0.0)),
        )

    def GetCompressionStiffnessPower(self):
        """Return the exponent used by the depth-dependent stiffness curve."""
        return max(
            0.0,
            float(self.run_configuration.get("compression_stiffness_power", 2.0)),
        )

    def GetEffectiveContactStiffness(
        self,
        base_stiffness,
        penetration_depth,
        source_radius,
    ):
        """Return reversible depth-dependent stiffness for one contact."""
        base_stiffness = max(0.0, float(base_stiffness))
        gain = self.GetCompressionStiffnessGain()
        if gain <= 0.0:
            return base_stiffness

        hard_depth = self.GetHardPenetrationDepth(source_radius)
        if hard_depth <= self.EPSILON:
            return base_stiffness

        compression_fraction = max(
            0.0,
            min(1.0, float(penetration_depth) / hard_depth),
        )
        power = self.GetCompressionStiffnessPower()
        return base_stiffness * (1.0 + gain * (compression_fraction ** power))

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
            source_radius,
            target_radius,
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
            source_radius,
            target_radius,
            center_distance,
        )
        contact_state.aux.z = 0.0
        contact_state.source_radius = source_radius
        contact_state.target_radius = target_radius
        contact_state.separation_limit = source_radius + target_radius
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
            if not self.ApplyPhotonPositionOverride(SourceID, particle.PosLocB):
                particle.PosLocB.x = position.x + velocity.x * dt
                particle.PosLocB.y = position.y + velocity.y * dt
                particle.PosLocB.z = position.z + velocity.z * dt
            particle.PosLocA.w = 1.0
            particle.PosLocB.w = 0.0
            output_position = particle.PosLocB
        else:
            if not self.ApplyPhotonPositionOverride(SourceID, particle.PosLocA):
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

    def GetPhysicalParticleContact(self, SourceID, TargetID):
        """Return validated physical geometry for one overlapping pair."""
        source = self.particles[SourceID]
        geometry = self.GetParticleGeometry(SourceID, TargetID)
        if geometry is None:
            return None
        (
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
            center_distance,
            source_radius,
            target_radius,
        ) = geometry

        physical_proximity = center_distance - target_radius
        if physical_proximity < -self.EPSILON and not self.IsPhotonParticle(SourceID):
            self.SetError(
                self.constants.ERROR_PARTICLE_TUNNELING,
                error_kind="particle-particle",
                source_id=SourceID,
                target_id=TargetID,
            )
            return None

        if not self.CheckPenetrationStepResolution(
            SourceID,
            (normal_x, normal_y, normal_z),
            source_radius,
            self.GetStartFrameVelocity(TargetID),
            "particle-particle",
            target_id=TargetID,
        ):
            return None
        source.oa = max(source.oa, overlap_area)
        penetration_depth = self.ParticlePenetrationDepth(
            source_radius,
            target_radius,
            center_distance,
        )
        source.max_penetration_depth = max(
            source.max_penetration_depth,
            penetration_depth,
        )
        return geometry

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
