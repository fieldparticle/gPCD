from gbase.AttrDictFields import *
from gbase import libconf
from base.VerAForceDynamics import ForceContactDynamics
from base.InLineTest import InLineTest
from gbase import BinaryFileUtilities
import math
import re
from pathlib import Path
from gbase.libconf import AttrDict

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


class ForceDynamics(ForceContactDynamics):
    
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
        self.pair_phase_totals = {}
        self.pair_phase_frame_diagnostics = []
        self.pair_phase_energy_reference = None
        self.wall_contact_offset = 0.0

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
            "wall_ghost_mass",
        ):
            setattr(contact_state, field_name, 0.0)

    def ClearContactSlot(self, contact_state):
        """Reset one reusable current-frame contact slot."""
        contact_state.ids = self.create_uvec4()
        contact_state.geom = self.create_vec4()
        contact_state.aux = self.create_vec4()
        self.ClearContactDiagnostics(contact_state)

    def BeginContactFrame(self, SourceID):
        """Reset Python current-frame contact and reporting state."""
        source = self.particles[SourceID]
        source.collision_list = []
        source.contactCount = 0
        source.colFlg = 0
        source.internal_momentum = 0.0
        source.Data.z = 0.0
        source.total_overlap_area = 0.0
        for contact_state in self.GetContactSlots(SourceID):
            self.ClearContactSlot(contact_state)

    def GetContactSlots(self, SourceID):
        """Return contact slots while preserving legacy Python structures."""
        particle = self.particles[SourceID]
        if hasattr(particle, "contacts"):
            return particle.contacts
        return particle.gcs

    def InitializeContactState(self, SourceID, TargetID):
        """Initialize a physical contact, then attach Python diagnostics."""
        contact_state = super().InitializeContactState(SourceID, TargetID)
        if contact_state is None:
            return None
        source = self.particles[SourceID]
        source.report_contacts = len(source.collision_list)
        source.report_target = TargetID
        self.RecordContactParameters(SourceID, TargetID, contact_state)
        return contact_state

    def RecordContactParameters(self, SourceID, TargetID, contact_state):
        """Record relative motion and overlap totals without affecting dynamics."""
        source = self.particles[SourceID]
        overlap_area = max(0.0, float(contact_state.geom.w))
        normal_x = float(contact_state.geom.x)
        normal_y = float(contact_state.geom.y)
        normal_z = float(contact_state.geom.z)
        source_velocity = self.GetStartFrameVelocity(SourceID)
        target_velocity = (
            self.create_vec4()
            if int(contact_state.ids.y) == self.constants.CONTACT_WALL
            else self.GetStartFrameVelocity(TargetID)
        )
        contact_state.rel_vn = (
            (target_velocity.x - source_velocity.x) * normal_x
            + (target_velocity.y - source_velocity.y) * normal_y
            + (target_velocity.z - source_velocity.z) * normal_z
        )
        source.total_overlap_area += overlap_area

    def InitializeWallContactState(self, SourceID, wall):
        """Initialize a physical wall contact, then attach Python diagnostics."""
        contact_state = super().InitializeWallContactState(SourceID, wall)
        if contact_state is not None:
            self.RecordContactParameters(SourceID, wall, contact_state)
        return contact_state

    def AccumulateContactForce(self, SourceID, contact_state, totalForce):
        """Accumulate one physical force, then attach Python diagnostics."""
        if not super().AccumulateContactForce(SourceID, contact_state, totalForce):
            return False
        source = self.particles[SourceID]
        dt = max(0.0, float(self.ShaderFlags.dt))
        target_id = int(contact_state.ids.x)
        contact_type = int(contact_state.ids.y)
        stiffness = self.GetContactStiffness(SourceID, target_id, contact_type)
        source_radius = float(source.Data.x)
        target_radius = (
            source_radius
            if contact_type == self.constants.CONTACT_WALL
            else float(self.particles[target_id].Data.x)
        )
        contact_state.raw_impulse = contact_state.force_magnitude * dt
        contact_state.contact_potential_energy = self.GetOverlapPotentialEnergy(
            source_radius,
            target_radius,
            stiffness,
            float(contact_state.aux.x),
        )
        return True

    def CalcVelocity(self, SourceID, totalForce):
        """Calculate source velocity, then attach impulse diagnostics."""
        start_velocity = self.GetStartFrameVelocity(SourceID)
        if not super().CalcVelocity(SourceID, totalForce):
            return False
        source = self.particles[SourceID]
        source.vx = source.VelRad.x
        source.vy = source.VelRad.y
        source.vz = source.VelRad.z
        mass = self.GetParticleMass(SourceID)
        delta_momentum_x = mass * (source.VelRad.x - start_velocity.x)
        delta_momentum_y = mass * (source.VelRad.y - start_velocity.y)
        delta_momentum_z = mass * (source.VelRad.z - start_velocity.z)
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
            applied_impulse = max(0.0, float(contact_state.raw_impulse))
            contact_state.aux.w = applied_impulse
            contact_state.delta_px = -applied_impulse * float(contact_state.geom.x)
            contact_state.delta_py = -applied_impulse * float(contact_state.geom.y)
            contact_state.delta_pz = -applied_impulse * float(contact_state.geom.z)
        return True

    def load_cfg_file(self, cfg_file_name):
        self.load_constants()
        self.collIn.ErrorReturn = self.constants.ERROR_NONE
        with open(cfg_file_name, "r", encoding="utf-8") as cfg_file:
            self.config = libconf.load(cfg_file)

        self.config_error_return = None
        self.run_configuration = self.config.get("RUN_CONFIGURATION", {})
        if self.config.pdata_from_file == True:
            self.particle_data = self.getParticleData(self.config)
        else:
            self.particle_data = self.config.get("PARTICLE_DATA", {})

        self.particles = self.create_particle_array_from_cfg(self.particle_data)
        self.ShaderFlags = self.create_shader_flags_from_cfg(self.run_configuration)
        self.wall_contact_offset = max(
            0.0,
            float(self.run_configuration.get("wall_contact_offset", 0.0)),
        )
        self.pair_phase_totals = {}
        self.pair_phase_frame_diagnostics = []
        self.pair_phase_energy_reference = None
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
    # and GLSL-coordinate utilities are split out of ForceDynamicsBase.
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
            collision_stiffness_q = 4.0
        else:
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

    def getParticleData(self,config):
        file_name = f"{config.data_dir}/{config.STUDY_NAME}.bin"
        results = BinaryFileUtilities.read_all_particle_data(file_name)
        particle_data = AttrDict()
        particles = AttrDict()
        for pp in results:
            if pp.pnum == 0:
                continue  # Skip null particle

            dict_location = {
                "use": 0,
                "x1": pp.rx,
                "y1": pp.ry,
                "z1": pp.rz,
                "x2": pp.rx,
                "y2": pp.ry,
                "z2": pp.rz,
                "vx": pp.vx,
                "vy": pp.vy,
                "vz": pp.vz
            }
            particle = AttrDict()
            particle["location"] = AttrDict(dict_location)
            particle["vx"] = pp.vx
            particle["vy"] = pp.vy
            particle["vz"] = pp.vz
            particle["mass"] = pp.molar_mass
            particle["radius"] = pp.radius
            particle["ptype"] = pp.ptype
            particle["state_flg"] = int(pp.state_flg)
            particle["edge"] = (100, 170, 255)
            particle["fill"] = (160, 210, 255)
            particle_data[pp.pnum] = particle
            pnumtxt = f"p{int(pp.pnum)}"
            particles[pnumtxt] =  particle

            print(f"Read particle: {pp.pnum} at ({pp.rx}, {pp.ry}, {pp.rz}) with velocity ({pp.vx}, {pp.vy}, {pp.vz})")

        return particles

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
        """Run one source-owned semi-implicit ForceDynamics frame."""
        if not self.BeginFrame():
            return self.particles
        self.ApplyBeforeContactScanHook()
        self.ResetFrameState()
        self.ApplyStartRunHook()
        self.BuildFrameSnapshot()
        self.RecordFrameStartDiagnostics()
        self.InitializePairPhaseEnergyReference()

        total_forces = [self.create_vec4() for _ in self.particles]
        if not self.DetectContacts(total_forces):
            return self.particles
        if not self.BuildWallContactLists(total_forces):
            return self.particles
        frame_start_pairs = self.CapturePairGeometryDiagnostics()
        if not self.CalculateVelocities(total_forces):
            return self.particles
        if not self.CalculatePositions():
            return self.particles
        self.BuildEndPositionSnapshot()
        frame_end_pairs = self.CapturePairGeometryDiagnostics()
        self.RecordAfterResolveDiagnostics()
        self.RecordPairPhaseDiagnostics(frame_start_pairs, frame_end_pairs)
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

    def BuildEndPositionSnapshot(self):
        """Expose end positions for diagnostics after dynamics is complete."""
        end_buffer = 1 - int(self.ShaderFlags.positionBuffer)
        self.PosLocFrame = [
            self.create_vec4(position.x, position.y, position.z, position.w)
            for position in (
                self.particle_position(particle, end_buffer)
                for particle in self.particles
            )
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

    def GetContactPotentialEnergy(self, SourceID, TargetID, center_distance):
        """Return diagnostic pair potential energy from current geometry."""
        source_radius = float(self.particles[SourceID].Data.x)
        target_radius = float(self.particles[TargetID].Data.x)
        return self.GetOverlapPotentialEnergy(
            source_radius,
            target_radius,
            self.GetPairStiffness(SourceID, TargetID),
            center_distance,
        )

    def GetOverlapPotentialEnergy(
        self,
        source_radius,
        target_radius,
        stiffness,
        center_distance,
    ):
        """Return diagnostic stiffness times the overlap-area integral."""
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
        return stiffness * step * area_sum / 3.0

    def TotalPotentialEnergy(self):
        """Return diagnostic whole-system particle and wall potential energy."""
        total_potential_energy = 0.0
        for source_id in range(len(self.particles)):
            source_position = self.GetParticlePosition(source_id)
            for target_id in range(source_id + 1, len(self.particles)):
                target_position = self.GetParticlePosition(target_id)
                dx = target_position.x - source_position.x
                dy = target_position.y - source_position.y
                dz = target_position.z - source_position.z
                center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
                total_potential_energy += self.GetContactPotentialEnergy(
                    source_id,
                    target_id,
                    center_distance,
                )
        return total_potential_energy + self.TotalWallPotentialEnergy()

    def CapturePairGeometryDiagnostics(self):
        """Capture unordered-pair geometry from the current position snapshot."""
        pairs = {}
        for source_id in range(len(self.particles)):
            source_position = self.GetParticlePosition(source_id)
            for target_id in range(source_id + 1, len(self.particles)):
                target_position = self.GetParticlePosition(target_id)
                dx = target_position.x - source_position.x
                dy = target_position.y - source_position.y
                dz = target_position.z - source_position.z
                center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
                if center_distance > 1.0e-12:
                    normal = (dx / center_distance, dy / center_distance, dz / center_distance)
                else:
                    normal = (1.0, 0.0, 0.0)
                source_radius = float(self.particles[source_id].Data.x)
                target_radius = float(self.particles[target_id].Data.x)
                overlap_area = self.particle_overlap_area(
                    source_radius,
                    target_radius,
                    center_distance,
                )
                pairs[(source_id, target_id)] = {
                    "center_distance": center_distance,
                    "normal": normal,
                    "overlap_area": overlap_area,
                    "potential_energy": self.GetContactPotentialEnergy(
                        source_id,
                        target_id,
                        center_distance,
                    ),
                }
        return pairs

    def CurrentDiagnosticTotalEnergy(self):
        kinetic_energy = sum(
            self.ParticleKineticEnergy(particle_index)
            for particle_index in range(len(self.particles))
        )
        return kinetic_energy + self.TotalPotentialEnergy()

    def InitializePairPhaseEnergyReference(self):
        if self.pair_phase_energy_reference is None:
            self.pair_phase_energy_reference = self.CurrentDiagnosticTotalEnergy()

    def RecordPairPhaseDiagnostics(self, frame_start_pairs, frame_end_pairs):
        """Accumulate diagnostics-only compression/rebound symmetry measures."""
        dt = float(self.ShaderFlags.dt)
        energy_drift = self.CurrentDiagnosticTotalEnergy() - self.pair_phase_energy_reference
        self.pair_phase_frame_diagnostics = []
        for pair, start in frame_start_pairs.items():
            end = frame_end_pairs[pair]
            if start["overlap_area"] <= 0.0 and end["overlap_area"] <= 0.0:
                continue

            distance_change = end["center_distance"] - start["center_distance"]
            if distance_change < -self.EPSILON:
                phase = "compression"
            elif distance_change > self.EPSILON:
                phase = "rebound"
            else:
                phase = "stationary"

            area_time = 0.5 * (start["overlap_area"] + end["overlap_area"]) * dt
            pair_stiffness = self.GetPairStiffness(*pair)
            start_force = tuple(
                pair_stiffness * start["overlap_area"] * component
                for component in start["normal"]
            )
            end_force = tuple(
                pair_stiffness * end["overlap_area"] * component
                for component in end["normal"]
            )
            relative_displacement = tuple(
                end["normal"][axis] * end["center_distance"]
                - start["normal"][axis] * start["center_distance"]
                for axis in range(3)
            )
            force_work = sum(
                0.5 * (start_force[axis] + end_force[axis])
                * relative_displacement[axis]
                for axis in range(3)
            )

            totals = self.pair_phase_totals.setdefault(
                pair,
                {
                    "compression_steps": 0,
                    "rebound_steps": 0,
                    "stationary_steps": 0,
                    "compression_area_time": 0.0,
                    "rebound_area_time": 0.0,
                    "stationary_area_time": 0.0,
                    "compression_work": 0.0,
                    "rebound_work": 0.0,
                    "stationary_work": 0.0,
                    "compression_min_energy_drift": 0.0,
                    "compression_max_energy_drift": 0.0,
                    "rebound_min_energy_drift": 0.0,
                    "rebound_max_energy_drift": 0.0,
                },
            )
            totals[f"{phase}_steps"] += 1
            totals[f"{phase}_area_time"] += area_time
            totals[f"{phase}_work"] += force_work
            if phase != "stationary":
                totals[f"{phase}_min_energy_drift"] = min(
                    totals[f"{phase}_min_energy_drift"],
                    energy_drift,
                )
                totals[f"{phase}_max_energy_drift"] = max(
                    totals[f"{phase}_max_energy_drift"],
                    energy_drift,
                )

            self.pair_phase_frame_diagnostics.append(
                {
                    "frame": int(self.ShaderFlags.frameNum),
                    "source_index": pair[0],
                    "target_index": pair[1],
                    "phase": phase,
                    "start_overlap_area": start["overlap_area"],
                    "end_overlap_area": end["overlap_area"],
                    "area_time": area_time,
                    "force_work": force_work,
                    "energy_drift": energy_drift,
                    **totals,
                    "step_count_difference": (
                        totals["compression_steps"] - totals["rebound_steps"]
                    ),
                    "area_time_difference": (
                        totals["compression_area_time"] - totals["rebound_area_time"]
                    ),
                    "work_residual": (
                        totals["compression_work"] + totals["rebound_work"]
                    ),
                }
            )

    def BuildWallContactLists(self, total_forces):
        """Process each active stationary wall ghost exactly once."""
        for source_id in range(len(self.particles)):
            if bool(self.ShaderFlags.Boundary):
                for wall_flag in (1, 2, 3, 4):
                    if not self.ProcessWallCollision(
                        source_id,
                        wall_flag,
                        total_forces[source_id],
                    ):
                        return False
        return True

    def WallContactOffsetDistance(self, radius):
        """Return configured wall offset as a bounded fraction of radius."""
        return min(float(radius), float(radius) * self.wall_contact_offset)

    def GetWallGhostGeometry(self, SourceID, wall_flag):
        """Return fixed-wall ghost geometry for the current position snapshot."""
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

    def AppendWallContactSlot(self, SourceID, wall_flag, geometry):
        """Append one source-owned stationary wall-ghost contact slot."""
        source = self.particles[SourceID]
        slots = self.GetContactSlots(SourceID)
        if source.contactCount >= len(slots):
            return None
        contact_state = slots[source.contactCount]
        normal_x, normal_y, normal_z, overlap_area, center_distance = geometry
        contact_state.ids.x = int(wall_flag)
        contact_state.ids.y = self.constants.CONTACT_WALL
        contact_state.ids.z = int(wall_flag)
        contact_state.ids.w = self.constants.CONTACT_ACTIVE_THIS_FRAME
        contact_state.geom = self.create_vec4(
            normal_x,
            normal_y,
            normal_z,
            overlap_area,
        )
        contact_state.aux.x = center_distance
        contact_state.aux.y = 2.0 * float(source.Data.x) - center_distance
        contact_state.aux.z = 0.0
        contact_state.wall_ghost_mass = self.GetParticleMass(SourceID)
        source.contactCount += 1
        source.colFlg = 1
        source.report_contacts = source.contactCount
        return contact_state

    def TotalWallPotentialEnergy(self):
        """Return current conservative potential energy stored against walls."""
        if not bool(self.ShaderFlags.Boundary):
            return 0.0
        total = 0.0
        for source_id, source in enumerate(self.particles):
            radius = float(source.Data.x)
            stiffness = max(0.0, float(source.Data.y or 0.0))
            for wall_flag in (1, 2, 3, 4):
                geometry = self.GetWallGhostGeometry(source_id, wall_flag)
                if geometry is None:
                    continue
                total += self.GetOverlapPotentialEnergy(
                    radius,
                    radius,
                    stiffness,
                    geometry[4],
                )
        return total

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
    # access helpers are split out of ForceDynamicsBase.
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
    # utilities are split out of ForceDynamicsBase.
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

    def DetectContacts(self, total_forces):
        """Run naive contact detection and overlap-area forces for every source."""
        return self.NaiveContactDetermination(total_forces)

    def NaiveContactDetermination(self, total_forces):
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

    def CalculateVelocities(self, total_forces):
        """Calculate each source velocity after all source contacts are known."""
        for SourceID in range(len(self.particles)):
            if not self.CalcVelocity(SourceID, total_forces[SourceID]):
                return False
        return True

    def CalculatePositions(self):
        """Move every source using its newly calculated velocity."""
        for SourceID in range(len(self.particles)):
            if not self.CalcPosition(SourceID):
                return False
        return True
