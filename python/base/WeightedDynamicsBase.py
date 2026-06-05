from gbase.AttrDictFields import *
from gbase import libconf
from base.WeightedDynamics import WeightedContactDynamics
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


class WeightedDynamics(WeightedContactDynamics):
    
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
        self.collIn.ErrorReturn = self.constants.ERROR_NONE
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
            if name.startswith("ERROR_")
        }
        return self.constants

    def ErrorDescription(self):
        return self.error_names.get(self.collIn.ErrorReturn, "ERROR_UNKNOWN")

    def create_collision_in(self):
        coll_in = CollisionInFields()
        coll_in.ErrorReturn = 0
        coll_in.numParticles = 0
        coll_in.maxCells = 0
        coll_in.particleNumber = 0
        coll_in.ReadWriteConflict = 0
        coll_in.ExcessSlots = 0
        return coll_in

    @staticmethod
    ##JMB Future common helper: move to ShadowCommon.py when shared geometry
    # and GLSL-coordinate utilities are split out of WeightedDynamicsBase.
    def VelocityAngle(vx, vy):
        """Return the GLSL VelRad.w velocity angle for an xy velocity."""
        return math.atan2(vy, vx) if vx != 0.0 or vy != 0.0 else 0.0

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
        velocity_angle = self.VelocityAngle(vx, vy)
        particle.PosLocA = self.create_vec4(rx, ry, rz, 0.0)
        particle.PosLocB = self.create_vec4(rx, ry, rz, 1.0)
        particle.VelRad = self.create_vec4(vx, vy, vz, velocity_angle)
        particle.Data = self.create_vec4(radius, fields.get("collision_stiffness_q", 0.0), 0.0, fields.get("state_flg", 1.0))
        particle.parms = self.create_vec4(mass, 0.0, 0.0, 0.0)
        particle.internal_momentum = particle.Data.z
        particle.internal_momentum_phase = self.PHASE_COMPRESSION
        particle.contact_internal_momentum = {}
        particle.contact_internal_phase = {}
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
        self.ClearContactDiagnostics(contact_state)
        return contact_state

    def create_particle_from_cfg(self, particle_name, particle_cfg):
        particle_number = int(str(particle_name).lstrip("p") or 0)
        location = particle_cfg.get("location", {})
        if "collision_stiffness_q" not in particle_cfg:
            self.config_error_return = self.constants.ERROR_MISSING_COLLISION_STIFFNESS_Q
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
        """Run one complete weighted-dynamics frame."""
        if not self.BeginFrame():
            return self.particles
        self.ApplyBeforeContactScanHook()
        self.ResetFrameState()
        self.ApplyStartRunHook()
        self.BuildFrameSnapshot()
        self.RecordFrameStartDiagnostics()

        if not self.DetectContacts():
            return self.particles
        if not self.BuildWallContactLists():
            return self.particles

        self.RecordAfterResolveDiagnostics()
        if not self.MoveParticles():
            return self.particles
        self.EndFrame()
        return self.particles

    def BeginFrame(self):
        """Start a shadow dynamics frame and validate configuration state.

        Each shadow frame begins with a clean runtime error value.  If cfg
        loading found a persistent configuration error, restore that error and
        return False so CollisionRun exits before contact detection, planning,
        resolution, or motion.  This does not reset particle state or contact
        ledgers; it only gates whether the frame is allowed to run.
        """
        self.collIn.ErrorReturn = self.constants.ERROR_NONE
        if self.config_error_return is not None:
            self.collIn.ErrorReturn = self.config_error_return
            return False
        return True

    def ApplyBeforeContactScanHook(self):
        """Run the optional scenario hook before shadow contact scanning.

        This hook is called after BeginFrame() and before frame reset,
        snapshot building, and contact-list construction.  When a scenario
        object is attached, its BeforeContactScan(particles) callback can make
        test-harness adjustments to the shadow particle list before contacts
        are detected for the frame.  If no scenario is attached, this stage is
        a no-op.
        """
        if self.senario:
            self.senario.BeforeContactScan(self.particles)

    def ResetFrameState(self):
        """Reset shadow per-frame contact and reporting state.

        This clears state that must be rebuilt from the current shadow frame:
        current-frame contact slots/list/count, overlap and penetration
        accumulators, and report fields consumed by UI/capture output.  It
        does not clear persistent shadow dynamics memory such as
        contact-owned internal momentum, contact phase, velocity references,
        or rebound references; those survive across frames until the shadow
        dynamics prunes or drains them.

        For each shadow particle this function:
        - calls BeginContactFrame(), which clears the current-frame contact
          list, contact count, and reusable contact slots;
        - resets overlap and maximum penetration measurements;
        - resets report fields so the current frame can repopulate them;
        - copies particle-owned collision stiffness from Data.y into the
          report field.
        """
        for particle_index, particle in enumerate(self.particles):
            self.BeginContactFrame(particle_index)
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

    def ApplyStartRunHook(self):
        """Run the optional inline-test StartRun hook for this frame.

        This hook executes after frame-local state has been reset and before
        the frame snapshot is built.  When inline-test mode is active and a
        scenario object is attached, senario.StartRun(particles) may adjust or
        replace the particle list used by the rest of the frame.  If inline
        testing is not active, or no scenario is attached, this stage is a
        no-op.
        """
        if self.inline_test_flag == True and self.senario is not None:
            self.particles = self.senario.StartRun(self.particles)
    
    def BuildFrameSnapshot(self):
        """Capture frame-start positions and velocities for dynamics logic.

        The snapshot freezes the state that contact geometry and relative
        velocity calculations should read for this frame.  Position data is
        copied from the currently active position buffer selected by
        ShaderFlags.positionBuffer.  Velocity data is copied from each
        particle's current VelRad value.

        Later stages may update particle velocities or move particles, but
        functions that read PosLocFrame or VelRadFrame continue to see this
        frame-start state.  This keeps contact detection, contact weighting,
        and impulse planning based on one consistent moment rather than on
        partially updated particle state.
        """
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
        ##JMB Huge model break. This would require 
        ## Frame-start VelRad snapshot: x/y/z are velocity components, and w
        ## is the velocity angle used by particle.glsl.
        ## Solution is to store in parms
        ## parms.x = mass
        ## parms.y = frame_start_vx
        ## parms.z = frame_start_vy
        ## parms.w = frame_start_vz
        self.VelRadFrame = [
            self.create_vec4(particle.VelRad.x, particle.VelRad.y, particle.VelRad.z, particle.VelRad.w)
            for particle in self.particles
        ]

    def ParticleKineticEnergy(self, particle_index, velocity=None):
        if velocity is None:
            velocity = self.particles[particle_index].VelRad
        mass = self.GetParticleMass(particle_index)
        return 0.5 * mass * (
            velocity.x * velocity.x
            + velocity.y * velocity.y
            + velocity.z * velocity.z
        )

    def RecordFrameStartDiagnostics(self):
        """Record per-particle kinetic energy at the frame-start snapshot.

        This uses VelRadFrame, not the mutable particle.VelRad, so the report
        captures kinetic energy before contact resolution changes velocities.
        The value is stored on each particle as report_frame_start_ke and is
        later written to the particle capture files.
        """
        for particle_index, particle in enumerate(self.particles):
            velocity = self.VelRadFrame[particle_index]
            particle.report_frame_start_ke = self.ParticleKineticEnergy(
                particle_index,
                velocity,
            )

    def RecordAfterResolveDiagnostics(self):
        for particle_index, particle in enumerate(self.particles):
            particle.report_after_resolve_ke = self.ParticleKineticEnergy(
                particle_index,
            )

    def BuildWallContactLists(self):
        return True

    def EndFrame(self):
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
    ##JMB Future common helper: move to ShadowCommon.py when particle buffer
    # access helpers are split out of WeightedDynamicsBase.
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
            self.collIn.ErrorReturn = self.constants.ERROR_TUNNELING
        return True

    @staticmethod
    ##JMB Future common helper: move to ShadowCommon.py when shared geometry
    # utilities are split out of WeightedDynamicsBase.
    def particle_overlap_area(source_radius, target_radius, center_distance):
        """Return the circular overlap area of two particles.

        The inputs are the two radii and the distance between particle centers.
        The function handles three geometric cases:

        - coincident centers or full containment: use the smaller circle area;
        - separated circles: return zero;
        - partial overlap: use the standard two-circle lens area formula.

        This is static because it is pure geometry.  It does not read particle
        objects, frame state, contact ledgers, or configuration data, and it
        does not mutate simulation state.  Keeping it static makes that
        independence explicit and keeps the calculation easy to port to GLSL.
        """
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

    def DetectContacts(self):
        """Run naive contact detection and weighted dynamics for every source."""
        return self.NaiveContactDetermination()

    def NaiveContactDetermination(self):
        """Fully process each source after scanning its possible targets."""
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
                    if not self.AddContactTargetID(source_id, target_id):
                        return False
                if self.collIn.ErrorReturn != self.constants.ERROR_NONE:
                    return False
            if not self.ContactDynamics(source_id):
                return False
        return True

    def AddContactTargetID(self, SourceID, TargetID):
        """Add only the target id to the source contact list."""
        source = self.particles[SourceID]
        if TargetID not in source.collision_list:
            source.collision_list.append(TargetID)
        return True

    def MoveParticles(self):
        """Move every particle using the weighted per-particle move function."""
        for SourceID in range(len(self.particles)):
            if not self.Move(SourceID):
                return False
        return True
