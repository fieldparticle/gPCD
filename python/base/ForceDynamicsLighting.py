"""Lighting-specific Python dynamics entry point."""

from base.ForceDynamicsBase import ForceDynamics as BaseForceDynamics
from base.PhotonDynamicsMixin import PhotonDynamicsMixin


class ForceDynamicsLighting(PhotonDynamicsMixin, BaseForceDynamics):
    """ForceDynamics variant used by LightingBall and future FPML scenarios.

    The base particle fields and behavior remain available under their normal
    names.  Lighting-only photon transport state is appended as Python runtime
    attributes so the eventual Vulkan LightingParticleStruct can mirror it
    without changing the base FPM particle ABI.
    """

    dynamics_class_name = "ForceDynamicsLighting"

    def IsLightingDynamics(self):
        return True

    def AllowsPhotonParticles(self):
        return True

    def BeginContactFrame(self, SourceID):
        super().BeginContactFrame(SourceID)
        if self.IsPhotonParticle(SourceID):
            self.particles[SourceID].material_id = self.BasePhotonMaterialID(SourceID)

    def load_cfg_file(self, cfg_file_name):
        particles = super().load_cfg_file(cfg_file_name)
        self.photon_periodic_recycle_enabled = bool(
            self.run_configuration.get("photon_periodic_recycle_enabled", False)
        )
        self.InitializeLightingParticleTransport()
        return particles

    def InitializeLightingParticleTransport(self):
        """Append lighting transport state to every runtime particle."""
        initialized = 0
        for particle_id, particle in enumerate(self.particles):
            birth_frame = float(getattr(particle.Data, "w", 0.0))
            particle.initial_pos_birth = self.create_vec4(
                float(particle.PosLocA.x),
                float(particle.PosLocA.y),
                float(particle.PosLocA.z),
                birth_frame,
            )
            particle.initial_vel_energy = self.create_vec4(
                float(particle.VelRad.x),
                float(particle.VelRad.y),
                float(particle.VelRad.z),
                float(getattr(particle, "material_id", 0.0)),
            )
            particle.photon_transport = self.create_vec4(
                0.0,  # last lived frame count
                0.0,  # recycle/cycle count
                1.0 if self.IsPhotonParticle(particle_id) else 0.0,
                float(particle.parms.x) if self.IsPhotonParticle(particle_id) else 0.0,
            )
            if self.IsPhotonParticle(particle_id):
                initialized += 1
        return initialized

    def ResetPhotonToInitialSlot(self, SourceID, next_birth_frame, lived_frames):
        """Recycle a photon to its original emitter slot and pending birth."""
        particle = self.particles[SourceID]
        initial_pos = particle.initial_pos_birth
        initial_vel = particle.initial_vel_energy

        particle.PosLocA.x = initial_pos.x
        particle.PosLocA.y = initial_pos.y
        particle.PosLocA.z = initial_pos.z
        particle.PosLocB.x = initial_pos.x
        particle.PosLocB.y = initial_pos.y
        particle.PosLocB.z = initial_pos.z

        particle.VelRad.x = initial_vel.x
        particle.VelRad.y = initial_vel.y
        particle.VelRad.z = initial_vel.z
        particle.VelRad.w = self.VelocityAngle(initial_vel.x, initial_vel.y)

        particle.parms.x = self.InitialPhotonRelativeMass(SourceID)
        particle.Data.w = float(next_birth_frame)
        particle.state_flg = float(next_birth_frame)
        particle.colFlg = 0
        particle.contactCount = 0
        particle.material_id = self.OriginalPhotonMaterialID(SourceID)
        particle.photon_transport.x = float(lived_frames)
        particle.photon_transport.y = float(particle.photon_transport.y) + 1.0
        particle.photon_transport.z = 1.0
        return True

    def RecyclePhotonIfDead(self, SourceID, previous_birth_frame):
        """Convert base death-bound retirement into periodic photon reuse."""
        if not self.photon_periodic_recycle_enabled:
            return False
        if not self.IsPhotonParticle(SourceID):
            return False

        particle = self.particles[SourceID]
        if float(particle.Data.w) >= 0.0:
            return False

        current_frame = float(self.ShaderFlags.frameNum)
        lived_frames = max(1.0, current_frame - float(previous_birth_frame))
        next_birth_frame = current_frame + 1.0
        return self.ResetPhotonToInitialSlot(
            SourceID,
            next_birth_frame,
            lived_frames,
        )

    def CalcPosition(self, SourceID):
        previous_birth_frame = float(self.particles[SourceID].Data.w)
        if not super().CalcPosition(SourceID):
            return False
        self.RecyclePhotonIfDead(SourceID, previous_birth_frame)
        return True
