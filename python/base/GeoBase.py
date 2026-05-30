from gbase.AttrDictFields import *
from gbase import libconf
from base.GeoDynamics import GeoDynamics
from base.InLineTest import InLineTest
import math
import re
from pathlib import Path


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


class Vec4Fields(AttrDictFields):
    def __setattr__(self, attr, value):
        if attr.startswith("_"):
            super().__setattr__(attr, value)
        else:
            self[attr] = value


class CollisionInFields(AttrDictFields):
    def __setattr__(self, attr, value):
        if attr.startswith("_"):
            super().__setattr__(attr, value)
        else:
            self[attr] = value


class GeoBase(GeoDynamics):
    
    def __init__(self, senario=None):
        ##JMB If senario is passed in then 
        #       assign it to self.senario, otherwise set self.senario to None
        if senario is not None:
            self.senario = senario
        else:
            self.senario = None
        self.study = senario is not None
        self.config = None
        self.run_configuration = None
        self.particle_data = None
        self.constants = AttrDictFields()
        self.error_names = {}
        self.collIn = self.create_collision_in()
        self.particles = []
        self.ShaderFlags = self.create_shader_flags()
        self.inline_test_flag = False
        self.config_error_return = None

    def load_cfg_file(self, cfg_file_name):
        self.load_constants()
        self.collIn.ErrorReturn = self.constants.GEO_ERROR_NONE
        with open(cfg_file_name, "r", encoding="utf-8") as cfg_file:
            self.config = libconf.load(cfg_file)

        self.config_error_return = None
        self.run_configuration = self.config.get("RUN_CONFIGURATION", {})
        self.particle_data = self.config.get("PARTICLE_DATA", {})
        self.particles = self.create_particle_array_from_cfg(self.particle_data)
        self.ShaderFlags = self.create_shader_flags_from_cfg(self.run_configuration)
        if "in_line_obj" in self.config.RUN_CONFIGURATION or self.study == True:
            self.inline_test_flag = True
        else:
            self.inline_test_flag = False
        # If there is a 
        return self.particles

    def load_constants(self, constants_file_name=None):
        if constants_file_name is None:
            constants_file_name = Path(__file__).resolve().parents[1] / "constants.glsl"
        constants_path = Path(constants_file_name)
        constants = AttrDictFields()
        constants_pattern = re.compile(r"const\s+uint\s+(\w+)\s*=\s*(\d+)\s*;")
        with constants_path.open("r", encoding="utf-8") as constants_file:
            for line in constants_file:
                match = constants_pattern.search(line)
                if match is None:
                    continue
                constants[match.group(1)] = int(match.group(2))
        self.constants = constants
        self.error_names = {
            value: name
            for name, value in constants.items()
            if name.startswith("GEO_ERROR_")
        }
        return self.constants

    def ErrorDescription(self):
        return self.error_names.get(self.collIn.ErrorReturn, "GEO_ERROR_UNKNOWN")

    def create_collision_in(self):
        coll_in = CollisionInFields()
        coll_in.ErrorReturn = 0
        coll_in.numParticles = 0
        coll_in.maxCells = 0
        coll_in.particleNumber = 0
        coll_in.ReadWriteConflict = 0
        coll_in.ExcessSlots = 0
        return coll_in

    def create_particle(self, **fields):
        particle = ParticleFields()
        particle.pnum = fields.get("pnum", 0)
        rx = fields.get("rx", 0.0)
        ry = fields.get("ry", 0.0)
        rz = fields.get("rz", 0.0)
        vx = fields.get("vx", 0.0)
        vy = fields.get("vy", 0.0)
        vz = fields.get("vz", 0.0)
        mass = fields.get("mass", fields.get("molar_mass", 1.0))
        radius = fields.get("radius", 0.0)
        particle.PosLocA = self.create_vec4(rx, ry, rz, 0.0)
        particle.PosLocB = self.create_vec4(rx, ry, rz, 1.0)
        particle.VelRad = self.create_vec4(vx, vy, vz, 0.0)
        particle.Data = self.create_vec4(radius, fields.get("collision_stiffness_q", 0.0), 0.0, fields.get("state_flg", 1.0))
        particle.parms = self.create_vec4(mass, 0.0, 0.0, 0.0)
        particle.contacts = [self.create_geo_contact_state() for _ in range(16)]
        particle.gcs = particle.contacts
        particle.contactCount = 0
        particle.colFlg = 0
        particle.rx = rx
        particle.ry = ry
        particle.rz = rz
        particle.vx = vx
        particle.vy = vy
        particle.vz = vz
        particle.mass = mass
        particle.radius = radius
        particle.state_flg = fields.get("state_flg", 1.0)
        particle.collision_list = fields.get("collision_list", [])
        particle.oa = fields.get("oa", 0.0)
        particle.max_penetration_depth = fields.get("max_penetration_depth", 0.0)
        particle.report_contacts = 0
        particle.report_phase = 0
        particle.report_target = 0
        particle.report_center_distance = 0.0
        particle.report_normal_x = 0.0
        particle.report_normal_y = 0.0
        particle.report_stored_mom = 0.0
        particle.report_alpha_zero = 0.0
        particle.report_zero_area = 0.0
        particle.report_compression_fraction = 0.0
        particle.report_rel_vn = 0.0
        particle.report_closing_mom = 0.0
        particle.report_collision_stiffness_q = 0.0
        return particle

    def create_vec4(self, x=0.0, y=0.0, z=0.0, w=0.0):
        vec4 = Vec4Fields()
        vec4.x = x
        vec4.y = y
        vec4.z = z
        vec4.w = w
        return vec4

    def create_uvec4(self, x=0, y=0, z=0, w=0):
        uvec4 = Vec4Fields()
        uvec4.x = int(x)
        uvec4.y = int(y)
        uvec4.z = int(z)
        uvec4.w = int(w)
        return uvec4

    def create_geo_contact_state(self):
        contact_state = ParticleFields()
        contact_state.ids = self.create_uvec4()
        contact_state.geom = self.create_vec4()
        contact_state.aux = self.create_vec4()
        return contact_state

    def create_particle_from_cfg(self, particle_name, particle_cfg):
        particle_number = int(str(particle_name).lstrip("p") or 0)
        location = particle_cfg.get("location", {})
        if "collision_stiffness_q" not in particle_cfg:
            self.config_error_return = self.constants.GEO_ERROR_MISSING_COLLISION_STIFFNESS_Q
            self.collIn.ErrorReturn = self.config_error_return
        collision_stiffness_q = particle_cfg.get("collision_stiffness_q", 0.0)
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
            collision_stiffness_q=collision_stiffness_q,
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
        
        self.item_cfg = shader_flags
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
        if not self.GeoBeginFrame():
            return self.particles

        self.GeoApplyBeforeContactScanHook()
        self.GeoResetFrameState()
        self.GeoApplyStartRunHook()
        self.GeoBuildFrameSnapshot()

        if not self.GeoBuildParticleContactLists():
            return self.particles

        if not self.GeoBuildWallContactLists():
            return self.particles

        if not self.GeoResolveContacts():
            return self.particles

        if not self.GeoMoveParticles():
            return self.particles

        self.GeoEndFrame()
        return self.particles

    def GeoBeginFrame(self):
        self.collIn.ErrorReturn = self.constants.GEO_ERROR_NONE
        if self.config_error_return is not None:
            self.collIn.ErrorReturn = self.config_error_return
            return False
        return True

    def GeoApplyBeforeContactScanHook(self):
        if self.senario:
            self.senario.BeforeContactScan(self.particles)

    def GeoResetFrameState(self):
        for particle_index, particle in enumerate(self.particles):
            self.GeoBeginContactFrame(particle_index)
            particle.oa = 0.0
            particle.max_penetration_depth = 0.0
            particle.report_contacts = 0
            particle.report_phase = 0
            particle.report_target = 0
            particle.report_center_distance = 0.0
            particle.report_normal_x = 0.0
            particle.report_normal_y = 0.0
            particle.report_stored_mom = 0.0
            particle.report_alpha_zero = 0.0
            particle.report_zero_area = 0.0
            particle.report_compression_fraction = 0.0
            particle.report_rel_vn = 0.0
            particle.report_closing_mom = 0.0
            particle.report_collision_stiffness_q = particle.Data.y

    def GeoApplyStartRunHook(self):
        if self.inline_test_flag == True and self.senario is not None:
            self.particles = self.senario.StartRun(self.particles)

    def GeoBuildFrameSnapshot(self):
        position_buffer = int(self.ShaderFlags.positionBuffer)
        self.PosLocFrame = [
            self.create_vec4(
                self.particle_position(particle, position_buffer).x,
                self.particle_position(particle, position_buffer).y,
                self.particle_position(particle, position_buffer).z,
                self.particle_position(particle, position_buffer).w,
            )
            for particle in self.particles
        ]
        self.VelRadFrame = [
            self.create_vec4(particle.VelRad.x, particle.VelRad.y, particle.VelRad.z, particle.VelRad.w)
            for particle in self.particles
        ]

    def GeoBuildParticleContactLists(self):
        position_buffer = int(self.ShaderFlags.positionBuffer)
        for source_id in range(len(self.particles)):
            for target_id in range(len(self.particles)):
                if source_id == target_id:
                    continue
                if self.isParticleContact(
                    self.ShaderFlags.frameNum,
                    source_id,
                    target_id,
                    position_buffer,
                ):
                    if not self.GeoAddParticleContact(source_id, target_id):
                        return False
                if self.collIn.ErrorReturn != self.constants.GEO_ERROR_NONE:
                    return False
        return True

    def GeoBuildWallContactLists(self):
        return True

    def GeoResolveContacts(self):
        for source_id in range(len(self.particles)):
            if not self.GeoProcessCollisions(source_id):
                return False
            if self.inline_test_flag == True and self.senario is not None:
                self.senario.AfterContactScan(
                    self.ShaderFlags.frameNum,
                    self.particles[source_id],
                    self.ShaderFlags.dt,
                    self.particles[source_id].report_collision_stiffness_q,
                )
        return True

    def GeoMoveParticles(self):
        position_buffer = int(self.ShaderFlags.positionBuffer)
        for source_id in range(len(self.particles)):
            if not self.GeoMoveParticle(
                source_id,
                position_buffer,
                self.ShaderFlags.dt,
            ):
                return False
        return True

    def GeoEndFrame(self):
        position_buffer = int(self.ShaderFlags.positionBuffer)
        self.ShaderFlags.positionBuffer = 1.0 if position_buffer == 0 else 0.0
        self.sync_particle_alias_positions(int(self.ShaderFlags.positionBuffer))
        self.PosLocFrame = []
        self.VelRadFrame = []

    def sync_particle_alias_positions(self, positionBuffer):
        for particle in self.particles:
            position = self.particle_position(particle, positionBuffer)
            particle.rx = position.x
            particle.ry = position.y
            particle.rz = position.z

    @staticmethod
    def particle_position(particle, positionBuffer):
        if int(positionBuffer) == 0:
            return particle.PosLocA
        return particle.PosLocB

    def isParticleContact(self, Frame, SourceID, TargetID, positionBuffer):
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

        overlap_area = self.particle_overlap_area(
            source_radius,
            target_radius,
            center_distance,
        )
        source.oa = max(source.oa, overlap_area)
        penetration_depth = source_radius + target_radius - center_distance
        source.max_penetration_depth = max(
            source.max_penetration_depth,
            penetration_depth,
        )
        if center_distance <= source_radius:
            self.collIn.ErrorReturn = self.constants.GEO_ERROR_TUNNELING
        return True

    @staticmethod
    def particle_overlap_area(source_radius, target_radius, center_distance):
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
