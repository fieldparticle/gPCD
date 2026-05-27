from gbase.AttrDictFields import *
from gbase import libconf
from base.GeoDynamics import GeoDynamics
import math


class ParticleFields(AttrDictFields):
    def __setattr__(self, attr, value):
        if attr.startswith("_"):
            super().__setattr__(attr, value)
        else:
            self[attr] = value


class ShaderFlagsFields(AttrDictFields):
    def __setattr__(self, attr, value):
        if attr.startswith("_"):
            super().__setattr__(attr, value)
        else:
            self[attr] = value


class GeoBase(GeoDynamics):
    def __init__(self):
        self.config = None
        self.run_configuration = None
        self.particle_data = None
        self.particles = []
        self.ShaderFlags = self.create_shader_flags()

    def load_cfg_file(self, cfg_file_name):
        with open(cfg_file_name, "r", encoding="utf-8") as cfg_file:
            self.config = libconf.load(cfg_file)

        self.run_configuration = self.config.get("RUN_CONFIGURATION", {})
        self.particle_data = self.config.get("PARTICLE_DATA", {})
        self.particles = self.create_particle_array_from_cfg(self.particle_data)
        self.ShaderFlags = self.create_shader_flags_from_cfg(self.run_configuration)
        return self.particles

    def create_particle(self, **fields):
        particle = ParticleFields()
        particle.pnum = fields.get("pnum", 0)
        particle.rx = fields.get("rx", 0.0)
        particle.ry = fields.get("ry", 0.0)
        particle.rz = fields.get("rz", 0.0)
        particle.vx = fields.get("vx", 0.0)
        particle.vy = fields.get("vy", 0.0)
        particle.vz = fields.get("vz", 0.0)
        particle.mass = fields.get("mass", fields.get("molar_mass", 1.0))
        particle.radius = fields.get("radius", 0.0)
        particle.state_flg = fields.get("state_flg", 1.0)
        particle.collision_list = fields.get("collision_list", [])
        return particle

    def create_particle_from_cfg(self, particle_name, particle_cfg):
        particle_number = int(str(particle_name).lstrip("p") or 0)
        location = particle_cfg.get("location", {})
        return self.create_particle(
            pnum=particle_number,
            rx=location.get("x1", 0.0),
            ry=location.get("y1", 0.0),
            rz=location.get("z1", 0.0),
            vx=particle_cfg.get("vx", 0.0),
            vy=particle_cfg.get("vy", 0.0),
            vz=particle_cfg.get("vz", 0.0),
            mass=particle_cfg.get("mass", 1.0),
            radius=particle_cfg.get("radius", 0.0),
            state_flg=particle_cfg.get("state_flg", 1.0),
        )

    def create_particle_array_from_cfg(self, particle_data):
        particles = []
        for particle_name in sorted(
            particle_data.keys(),
            key=lambda name: int(str(name).lstrip("p") or 0),
        ):
            particles.append(
                self.create_particle_from_cfg(
                    particle_name,
                    particle_data[particle_name],
                )
            )
        return particles

    def create_particle_array(self, count=0):
        self.particles = [
            self.create_particle(pnum=index)
            for index in range(count)
        ]
        return self.particles

    def create_shader_flags(self, **fields):
        shader_flags = ShaderFlagsFields()
        shader_flags.DrawInstance = fields.get("DrawInstance", 0.0)
        shader_flags.SideLength = fields.get("SideLength", 0.0)
        shader_flags.Ptot = fields.get("Ptot", 0.0)
        shader_flags.dt = fields.get("dt", 0.0)
        shader_flags.systemp = fields.get("systemp", 0.0)
        shader_flags.ColorMap = fields.get("ColorMap", 0.0)
        shader_flags.Boundary = fields.get("Boundary", 0.0)
        shader_flags.StopFlg = fields.get("StopFlg", 0.0)
        shader_flags.frameNum = fields.get("frameNum", 0.0)
        shader_flags.actualFrame = fields.get("actualFrame", 0.0)
        shader_flags.positionBuffer = fields.get("positionBuffer", 0.0)
        return shader_flags

    def create_shader_flags_from_cfg(self, run_configuration):
        return self.create_shader_flags(
            SideLength=run_configuration.get("side_len", 0.0),
            Ptot=len(self.particles),
            dt=run_configuration.get("dt", 0.0),
            Boundary=1.0 if run_configuration.get("walls_on", False) else 0.0,
            positionBuffer=run_configuration.get("positionBuffer", 0.0),
        )

    def CollisionRun(self):
        for source_id in range(len(self.particles)):
            for target_id in range(len(self.particles)):
                if source_id == target_id:
                    continue
                if self.isParticleContact(
                    self.ShaderFlags.frameNum,
                    source_id,
                    target_id,
                    self.ShaderFlags.positionBuffer,
                ):
                    self.GeoAddParticleContact(source_id, target_id)
            self.GeoProcessCollisions(source_id)
            self.GeoMoveParticle(
                source_id,
                self.ShaderFlags.positionBuffer,
                self.ShaderFlags.dt,
            )

    def isParticleContact(self, Frame, SourceID, TargetID, positionBuffer):
        source = self.particles[SourceID]
        target = self.particles[TargetID]
        dx = target.rx - source.rx
        dy = target.ry - source.ry
        dz = target.rz - source.rz
        center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        return center_distance <= source.radius + target.radius
