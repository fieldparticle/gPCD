from gbase.AttrDictFields import *


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


class GeoBase:
    def __init__(self):
        self.particles = []
        self.ShaderFlags = self.create_shader_flags()

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
        return particle

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

    def isParticleContact(self, Frame, SourceID, TargetID, positionBuffer):
        pass
