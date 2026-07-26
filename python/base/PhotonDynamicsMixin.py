"""Photon-only behavior for ForceDynamicsLighting."""

import math

from gbase.MaterialProperties import (
    PARTICLE_TYPE_BOUNDARY,
    PARTICLE_TYPE_PHOTON,
    PARTICLE_TYPE_REGULAR,
    parse_particle_type,
)
from gbase.pdata import PTYPE_BOUNDARY, PTYPE_PHOTON


class PhotonDynamicsMixin:
    """FPML photon behavior layered on top of base particle dynamics."""

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
        """Photons ignore photons; non-photons ignore photon targets."""
        source_photon = self.IsPhotonParticle(SourceID)
        target_photon = self.IsPhotonParticle(TargetID)
        return (source_photon and target_photon) or (
            not source_photon and target_photon
        )

    def BasePhotonMaterialID(self, SourceID):
        """Return the configured photon material id used between contacts."""
        materials = ()
        if getattr(self, "run_configuration", None) is not None:
            materials = self.run_configuration.get("material_properties", ())
        for material in materials or ():
            if hasattr(material, "get"):
                particle_type = parse_particle_type(material.get("particle_type", 0))
                material_id = material.get("material_id", 0)
            else:
                particle_type = parse_particle_type(
                    getattr(material, "particle_type", 0)
                )
                material_id = getattr(material, "material_id", 0)
            if particle_type == PARTICLE_TYPE_PHOTON:
                return float(material_id)
        return float(getattr(self.particles[SourceID], "material_id", 0.0))

    def PhotonVelocityMagnitude(self, SourceID):
        """Return the current photon speed used in strength calculations."""
        velocity = self.GetStartFrameVelocity(SourceID)
        return math.sqrt(
            float(velocity.x) * float(velocity.x)
            + float(velocity.y) * float(velocity.y)
            + float(velocity.z) * float(velocity.z)
        )

    def PhotonRelativeMass(self, SourceID):
        """Return the photon relative mass stored in the existing mass slot."""
        return max(0.0, float(self.particles[SourceID].parms.x))

    def InitialPhotonRelativeMass(self, SourceID):
        """Return the emitter-slot photon mass saved for periodic recycle."""
        transport = getattr(self.particles[SourceID], "photon_transport", None)
        if transport is None:
            return self.PhotonRelativeMass(SourceID)
        return max(0.0, float(getattr(transport, "w", 0.0)))

    def PhotonStrength(self, SourceID):
        """Return photon strength as relative_mass * speed."""
        if not self.IsPhotonParticle(SourceID):
            return 0.0
        return self.PhotonRelativeMass(SourceID) * self.PhotonVelocityMagnitude(SourceID)

    def PhotonNormalAlignment(self, SourceID, surface_normal):
        """Return max(0, -dot(normalized photon velocity, normalized normal))."""
        velocity = self.GetStartFrameVelocity(SourceID)
        vx = float(velocity.x)
        vy = float(velocity.y)
        vz = float(velocity.z)
        speed = math.sqrt(vx * vx + vy * vy + vz * vz)
        if speed <= self.EPSILON:
            return 0.0

        nx, ny, nz = [float(value) for value in surface_normal[:3]]
        normal_length = math.sqrt(nx * nx + ny * ny + nz * nz)
        if normal_length <= self.EPSILON:
            return 0.0

        dot = (
            (vx / speed) * (nx / normal_length)
            + (vy / speed) * (ny / normal_length)
            + (vz / speed) * (nz / normal_length)
        )
        return max(0.0, -dot)

    def MaterialPhotonCoupling(self, material_id):
        """Return the configured photon coupling for a surface material."""
        material_id = int(round(float(material_id)))
        materials = ()
        if getattr(self, "run_configuration", None) is not None:
            materials = self.run_configuration.get("material_properties", ())
        for material in materials or ():
            if int(material.get("material_id", -1)) == material_id:
                return max(0.0, min(1.0, float(material.get("photon_coupling", 1.0))))
        return 1.0

    def MaterialPhotonMinRelativeMass(self, material_id):
        """Return the configured photon death threshold for a material."""
        material_id = int(round(float(material_id)))
        materials = ()
        if getattr(self, "run_configuration", None) is not None:
            materials = self.run_configuration.get("material_properties", ())
        for material in materials or ():
            if int(material.get("material_id", -1)) == material_id:
                return max(0.0, float(material.get("photon_min_relative_mass", 0.001)))
        return 0.001

    def PhotonMinRelativeMass(self, SourceID):
        """Return the photon death threshold for the source photon material."""
        return self.MaterialPhotonMinRelativeMass(self.BasePhotonMaterialID(SourceID))

    def PhotonDepositFraction(self, SourceID, surface_normal, surface_material_id):
        """Return clamp(normal_alignment * photon_coupling, 0, 1)."""
        normal_alignment = self.PhotonNormalAlignment(SourceID, surface_normal)
        photon_coupling = self.MaterialPhotonCoupling(surface_material_id)
        return max(0.0, min(1.0, normal_alignment * photon_coupling))

    def PhotonPayloadRGB(self, SourceID):
        """Return the current photon payload color."""
        material_id = int(round(float(getattr(self.particles[SourceID], "material_id", 0.0))))
        if hasattr(self, "MaterialColorRGB"):
            return self.MaterialColorRGB(material_id)
        return 1.0, 1.0, 1.0

    def PhotonDepositRGB(self, SourceID, deposit_fraction, payload_rgb=None):
        """Return photon_payload_rgb * deposit_fraction * relative_mass."""
        scale = max(0.0, min(1.0, float(deposit_fraction))) * self.PhotonRelativeMass(
            SourceID
        )
        payload = self.PhotonPayloadRGB(SourceID) if payload_rgb is None else payload_rgb
        return tuple(float(payload[index]) * scale for index in range(3))

    def ReducePhotonMassByDepositFraction(self, SourceID, deposit_fraction):
        """Reduce photon mass while preserving velocity magnitude."""
        fraction = max(0.0, min(1.0, float(deposit_fraction)))
        particle = self.particles[SourceID]
        particle.parms.x = max(0.0, float(particle.parms.x) * (1.0 - fraction))
        return float(particle.parms.x)

    def RetirePhotonIfBelowMinMass(self, SourceID, previous_birth_frame=None):
        """Retire photons whose remaining mass is at or below threshold."""
        if not self.IsPhotonParticle(SourceID):
            return False
        if self.PhotonRelativeMass(SourceID) > self.PhotonMinRelativeMass(SourceID):
            return False

        particle = self.particles[SourceID]
        if previous_birth_frame is None:
            previous_birth_frame = float(getattr(particle.Data, "w", 0.0))
        particle.Data.w = -1.0
        particle.state_flg = -1.0
        transport = getattr(particle, "photon_transport", None)
        if transport is not None:
            transport.z = 0.0
        if hasattr(self, "RecyclePhotonIfDead"):
            self.RecyclePhotonIfDead(SourceID, previous_birth_frame)
        return True

    def TransferPhotonStrengthToSurface(
        self,
        SourceID,
        surface_normal,
        surface_material_id,
        payload_rgb=None,
    ):
        """Compute deposited RGB and reduce photon mass for one surface hit."""
        previous_birth_frame = float(getattr(self.particles[SourceID].Data, "w", 0.0))
        deposit_fraction = self.PhotonDepositFraction(
            SourceID,
            surface_normal,
            surface_material_id,
        )
        deposit_rgb = self.PhotonDepositRGB(
            SourceID,
            deposit_fraction,
            payload_rgb=payload_rgb,
        )
        remaining_mass = self.ReducePhotonMassByDepositFraction(
            SourceID,
            deposit_fraction,
        )
        self.RetirePhotonIfBelowMinMass(SourceID, previous_birth_frame)
        return deposit_fraction, deposit_rgb, remaining_mass

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
