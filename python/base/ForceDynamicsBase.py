from gbase.AttrDictFields import *
#from gbase import libconf
from gbase import libconf
from base.ForceDynamics import ForceContactDynamics
from base.InLineTest import InLineTest
from gbase import BinaryFileUtilities
from gbase.BoundaryLighting import (
    BOUNDARY_LIGHT_MODEL_LIGHTING_BALL,
    BOUNDARY_LIGHT_MODEL_NONE,
    BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL,
    BOUNDARY_LIGHT_SURFACE_SPHERE,
    parse_boundary_light_model,
    parse_boundary_light_rgb,
)
from gbase.utilities import get_cell_dimensions, get_run_configuration
import math
import re
from pathlib import Path
from gbase.libconf import AttrDict
from gbase.FunctionWall import parse_keyed_curve_wall_segments, wall_marker_records
from gbase.MaterialProperties import PARTICLE_TYPE_PHOTON, parse_particle_type
from gbase.pdata import PTYPE_BOUNDARY, PTYPE_NULL
AXIS_VECTOR = {
    "X": (1.0, 0.0, 0.0),
    "Y": (0.0, 1.0, 0.0),
    "Z": (0.0, 0.0, 1.0),
}

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
    
    def __init__(self, scenario=None):
        self.scenario = scenario
        self.study = scenario is not None
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
        self.initial_geometry_validated = False
        self.piston_contact_count = 0
        self.piston_frame_impulse = 0.0
        self.piston_frame_momentum = self.create_vec4()
        self.piston_total_impulse = 0.0
        self.piston_total_momentum = self.create_vec4()
        self.photon_reflected_velocity = {}
        self.photon_reflected_position = {}
        self.boundary_lighting_enabled = False
        self.boundary_lighting_model = BOUNDARY_LIGHT_MODEL_NONE
        self.boundary_light_initial_rgb = (0.0, 0.0, 0.0)
        self.boundary_space_patch_angle = 0.20
        self.boundary_space_patch_radius = 0.50
        self.boundary_space_patch_falloff = "quadratic"
        self.boundary_light_source_metadata = {}

    def ClearContactDiagnostics(self, contact_state):
        """Reset reporting-only diagnostics on one reusable contact slot."""
        for field_name in (
            "raw_impulse",
            "force_magnitude",
            "contact_potential_energy",
            "compression_impulse",
            "release_impulse",
            "internal_momentum_px",
            "internal_momentum_py",
            "internal_momentum_pz",
            "internal_momentum_mag",
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
            "source_net_delta_px",
            "source_net_delta_py",
            "source_net_delta_pz",
            "source_radius",
            "target_radius",
            "separation_limit",
            "maximum_depth",
            "remaining_depth",
            "maximum_depth_reached",
            "is_piston_contact",
        ):
            setattr(contact_state, field_name, 0.0)
        contact_state.wall_target_velocity = self.create_vec4()

    def ClearContactSlot(self, contact_state):
        """Reset one reusable current-frame contact slot."""
        contact_state.ids = self.create_uvec4()
        contact_state.geom = self.create_vec4()
        contact_state.aux = self.create_vec4()
        self.ClearContactDiagnostics(contact_state)

    def BeginContactFrame(self, SourceID):
        """Reset Python current-frame contact and reporting state."""
        source = self.particles[SourceID]
        source.contactCount = 0
        source.colFlg = 0
        if self.IsPhotonParticle(SourceID):
            source.material_id = self.BasePhotonMaterialID(SourceID)
        if (
            hasattr(self, "IsMobileParticleActiveForDynamics")
            and self.IsMobileParticleActiveForDynamics(SourceID)
        ):
            self.SyncInternalMomentumMagnitude(source)
        source.total_overlap_area = 0.0
        for contact_state in self.GetContactSlots(SourceID):
            self.ClearContactSlot(contact_state)

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

    def GetContactSlots(self, SourceID):
        """Return contact slots while preserving legacy Python structures."""
        particle = self.particles[SourceID]
        if hasattr(particle, "contacts"):
            return particle.contacts
        return particle.gcs

    def InitializeContactState(self, SourceID, TargetID, geometry=None):
        """Initialize a physical contact, then attach Python diagnostics."""
        contact_state = super().InitializeContactState(
            SourceID,
            TargetID,
            geometry,
        )
        if contact_state is None:
            return None
        source = self.particles[SourceID]
        source.report_contacts = source.contactCount
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
        source.report_normal_x = normal_x
        source.report_normal_y = normal_y
        source.report_normal_z = normal_z
        source_velocity = self.GetStartFrameVelocity(SourceID)
        target_velocity = (
            getattr(contact_state, "wall_target_velocity", self.create_vec4())
            if int(contact_state.ids.y) == self.constants.CONTACT_WALL
            else self.GetStartFrameVelocity(TargetID)
        )
        contact_state.rel_vn = (
            (target_velocity.x - source_velocity.x) * normal_x
            + (target_velocity.y - source_velocity.y) * normal_y
            + (target_velocity.z - source_velocity.z) * normal_z
        )
        source.total_overlap_area += overlap_area

    def AccumulateContactForce(self, SourceID, contact_state, totalForce):
        """Accumulate one physical force, then attach Python diagnostics."""
        if not super().AccumulateContactForce(SourceID, contact_state, totalForce):
            return False
        source = self.particles[SourceID]
        dt = max(0.0, float(self.ShaderFlags.dt))
        target_id = int(contact_state.ids.x)
        contact_type = int(contact_state.ids.y)
        stiffness = getattr(
            contact_state,
            "effective_stiffness_q",
            self.GetContactStiffness(SourceID, target_id, contact_type),
        )
        source_radius = float(getattr(contact_state, "source_radius", source.Data.x))
        target_radius = float(
            getattr(
                contact_state,
                "target_radius",
                source_radius
                if contact_type == self.constants.CONTACT_WALL
                else self.particles[target_id].Data.x,
            )
        )
        contact_state.raw_impulse = contact_state.force_magnitude * dt
        if float(getattr(contact_state, "is_piston_contact", 0.0)) != 0.0:
            impulse = contact_state.raw_impulse
            transfer_x = -impulse * float(contact_state.geom.x)
            transfer_y = -impulse * float(contact_state.geom.y)
            transfer_z = -impulse * float(contact_state.geom.z)
            self.piston_contact_count += 1
            self.piston_frame_impulse += impulse
            self.piston_frame_momentum.x += transfer_x
            self.piston_frame_momentum.y += transfer_y
            self.piston_frame_momentum.z += transfer_z
            self.piston_total_impulse += impulse
            self.piston_total_momentum.x += transfer_x
            self.piston_total_momentum.y += transfer_y
            self.piston_total_momentum.z += transfer_z
        self.RecordRecoverableInternalMomentum(SourceID, contact_state)
        contact_state.contact_potential_energy = self.GetOverlapPotentialEnergy(
            source_radius,
            target_radius,
            stiffness,
            float(contact_state.aux.x),
        )
        return True

    def SyncInternalMomentumMagnitude(self, particle):
        """Mirror source-owned internal momentum vector magnitude for reports."""
        px = float(getattr(particle.parms, "y", 0.0))
        py = float(getattr(particle.parms, "z", 0.0))
        pz = float(getattr(particle.parms, "w", 0.0))
        magnitude = math.sqrt(px * px + py * py + pz * pz)
        particle.internal_momentum = magnitude
        particle.Data.z = magnitude
        particle.report_stored_mom = magnitude
        return magnitude

    def ClearRecoverableInternalMomentum(self, particle):
        """Clear diagnostic recoverable internal momentum for an inactive contact."""
        particle.parms.y = 0.0
        particle.parms.z = 0.0
        particle.parms.w = 0.0
        particle.internal_momentum = 0.0
        particle.Data.z = 0.0
        particle.report_stored_mom = 0.0

    def ClearInactiveRecoverableInternalMomentum(self):
        """Clear recoverable internal momentum when a source has no contacts."""
        for particle_index, particle in enumerate(self.particles):
            if not self.IsMobileParticleActiveForDynamics(particle_index):
                continue
            if int(getattr(particle, "contactCount", 0)) == 0:
                self.ClearRecoverableInternalMomentum(particle)

    def RecordRecoverableInternalMomentum(self, SourceID, contact_state):
        """Diagnostic-only source-owned compression/rebound momentum storage."""
        source = self.particles[SourceID]
        normal_x = float(contact_state.geom.x)
        normal_y = float(contact_state.geom.y)
        normal_z = float(contact_state.geom.z)
        impulse = max(0.0, float(contact_state.raw_impulse))
        rel_vn = float(getattr(contact_state, "rel_vn", 0.0))

        stored_x = float(source.parms.y)
        stored_y = float(source.parms.z)
        stored_z = float(source.parms.w)
        compression_impulse = 0.0
        release_impulse = 0.0

        if rel_vn < -self.EPSILON:
            compression_impulse = impulse
            stored_x += compression_impulse * normal_x
            stored_y += compression_impulse * normal_y
            stored_z += compression_impulse * normal_z
        elif rel_vn > self.EPSILON:
            stored_along_normal = (
                stored_x * normal_x
                + stored_y * normal_y
                + stored_z * normal_z
            )
            release_impulse = min(max(0.0, stored_along_normal), impulse)
            stored_x -= release_impulse * normal_x
            stored_y -= release_impulse * normal_y
            stored_z -= release_impulse * normal_z

        source.parms.y = stored_x
        source.parms.z = stored_y
        source.parms.w = stored_z
        internal_mag = self.SyncInternalMomentumMagnitude(source)

        contact_state.compression_impulse = compression_impulse
        contact_state.release_impulse = release_impulse
        contact_state.internal_momentum_px = stored_x
        contact_state.internal_momentum_py = stored_y
        contact_state.internal_momentum_pz = stored_z
        contact_state.internal_momentum_mag = internal_mag
        contact_state.aux.z = internal_mag
        return True

    def CalcVelocity(self, SourceID, totalForce):
        """Calculate source velocity, then attach impulse diagnostics."""
        start_velocity = self.GetStartFrameVelocity(SourceID)
        if not super().CalcVelocity(SourceID, totalForce):
            return False
        if not self.ApplySourceMaximumDepth(SourceID):
            return False
        self.ApplyPhotonVelocityOverride(SourceID)
        if not self.CheckResolvedContactStep(SourceID):
            return False
        source = self.particles[SourceID]
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

    def load_include(self):
        #include_items = libconf.load(self.config.include_file)
        with open(self.config.include_file, "r", encoding="utf-8") as cfg_file:
            include_config = libconf.load(cfg_file)
        for key, value in include_config.items():
            if key in self.config:
                raise ValueError(
                    f"include_file {self.config.include_file!r} tries to override "
                    f"existing cfg item {key!r}"
                )
            self.config[key] = value
        
    def load_cfg_file(self, cfg_file_name):
        self.load_constants()
        self.collIn.ErrorReturn = self.constants.ERROR_NONE
        with open(cfg_file_name, "r", encoding="utf-8") as cfg_file:
            self.config = libconf.load(cfg_file)

        if 'include_file' in self.config:
                self.load_include()


        self.config_error_return = None
        self.initial_geometry_validated = False
        self.run_configuration = get_run_configuration(self.config)
        raw_segments = self.run_configuration.get("curve_wall_segments")
        rectangle_segments = self.run_configuration.get("rectangle_wall_segments")
        if (
            isinstance(rectangle_segments, AttrDict)
            and isinstance(raw_segments, AttrDict)
            and not raw_segments
        ):
            self.run_configuration["curve_wall_segments"] = ()
            self.config["curve_wall_segments"] = ()
        elif isinstance(raw_segments, AttrDict):
            curve_segments, curve_errors = parse_keyed_curve_wall_segments(raw_segments)
            if curve_errors:
                raise ValueError(
                    "Runtime wall configuration error(s):\n  - "
                    + "\n  - ".join(curve_errors)
                )
            self.run_configuration["curve_wall_segments"] = curve_segments
            self.config["curve_wall_segments"] = curve_segments
        elif isinstance(rectangle_segments, AttrDict):
            self.run_configuration["curve_wall_segments"] = ()
            self.config["curve_wall_segments"] = ()
        else:
            raise ValueError(
                "Runtime wall configuration error(s):\n  - "
                "curve_wall_segments or rectangle_wall_segments must be a key-value object"
            )
        if self.config.pdata_from_file == True:
            self.particle_data = self.getParticleData(self.config)
        else:
            self.particle_data = self.config.get("PARTICLE_DATA", {})

        self.particles = self.create_particle_array_from_cfg(self.particle_data)
        self.configure_boundary_lighting_from_cfg()
        if self.config.pdata_from_file == False:
            self.add_function_boundary_markers_from_cfg()
            self.add_rectangle_boundary_markers_from_cfg()
        if self.boundary_lighting_enabled:
            self.infer_boundary_light_sources_from_particles()
        self.InitializeBoundarySpaceLighting()
        self.ShaderFlags = self.create_shader_flags_from_cfg(self.run_configuration)
        self.wall_contact_offset = max(
            0.0,
            float(self.run_configuration.get("wall_contact_offset", 0.0)),
        )
        self.contact_force_measure = str(
            self.run_configuration.get("contact_force_measure", "area")
        ).strip().lower()
        if self.contact_force_measure not in {"area", "depth"}:
            self.contact_force_measure = "area"
        self.pair_phase_totals = {}
        self.pair_phase_frame_diagnostics = []
        self.pair_phase_energy_reference = None
        if "in_line_obj" in self.run_configuration or self.study == True:
            self.inline_test_flag = True
        else:
            self.inline_test_flag = False
        # If there is a 
        return self.particles

    def add_function_boundary_markers_from_cfg(self):
        """Build runtime wall markers when mobile particles come from cfg data."""
        segments = self.run_configuration.get("curve_wall_segments", ())
        if not segments:
            return 0

        mobile_particles = [
            particle
            for particle in self.particles
            if int(round(float(getattr(particle, "ptype", 0.0)))) != int(PTYPE_BOUNDARY)
            and int(getattr(particle, "pnum", 0)) != 0
        ]
        if not mobile_particles:
            return 0

        plane_z = float(mobile_particles[0].PosLocA.z)
        radius = float(self.run_configuration.get("radius", 0.0))
        marker_count = 0
        for marker_x, marker_y, marker_z, material_id in wall_marker_records(
            segments,
            plane_z,
        ):
            self.particles.append(
                self.create_particle(
                    pnum=len(self.particles),
                    rx=marker_x,
                    ry=marker_y,
                    rz=marker_z,
                    radius=radius,
                    mass=1.0,
                    ptype=PTYPE_BOUNDARY,
                    material_id=material_id,
                    collision_stiffness_q=0.0,
                    state_flg=0.0,
                )
            )
            marker_count += 1
        return marker_count

    def configure_boundary_lighting_from_cfg(self):
        boundary_lighting_enabled = self.run_configuration.get(
            "boundary_lighting_enabled",
            False,
        )
        if not isinstance(boundary_lighting_enabled, bool):
            raise ValueError("boundary_lighting_enabled must be a boolean")
        self.boundary_lighting_enabled = boundary_lighting_enabled
        if self.boundary_lighting_enabled:
            self.boundary_lighting_model = parse_boundary_light_model(
                self.run_configuration.get("boundary_lighting_model", "LightingBall")
            )
            if self.boundary_lighting_model != BOUNDARY_LIGHT_MODEL_LIGHTING_BALL:
                raise ValueError(
                    "boundary_lighting_model must be LightingBall when "
                    "boundary_lighting_enabled is true"
                )
        else:
            self.boundary_lighting_model = BOUNDARY_LIGHT_MODEL_NONE
        self.boundary_light_initial_rgb = parse_boundary_light_rgb(
            self.run_configuration.get("boundary_light_initial_rgb", (0.0, 0.0, 0.0))
        )
        self.boundary_light_source_metadata = {}
        self.boundary_space_patch_angle = float(
            self.run_configuration.get("boundary_space_patch_angle", 0.20)
        )
        if (
            not math.isfinite(self.boundary_space_patch_angle)
            or self.boundary_space_patch_angle <= 0.0
        ):
            raise ValueError("boundary_space_patch_angle must be positive and finite")
        self.boundary_space_patch_radius = float(
            self.run_configuration.get("boundary_space_patch_radius", 0.50)
        )
        if (
            not math.isfinite(self.boundary_space_patch_radius)
            or self.boundary_space_patch_radius <= 0.0
        ):
            raise ValueError("boundary_space_patch_radius must be positive and finite")
        self.boundary_space_patch_falloff = str(
            self.run_configuration.get("boundary_space_patch_falloff", "quadratic")
        ).strip().lower()
        if self.boundary_space_patch_falloff not in ("linear", "quadratic"):
            raise ValueError("boundary_space_patch_falloff must be linear or quadratic")

    def register_boundary_light_source(
        self,
        particle_id,
        surface_type,
        surface_id,
        material_id,
        normal,
        area=1.0,
    ):
        self.boundary_light_source_metadata[int(particle_id)] = {
            "surface_type": int(surface_type),
            "surface_id": int(surface_id),
            "material_id": int(material_id),
            "normal": tuple(float(value) for value in normal),
            "area": float(area),
        }

    def particle_position_tuple(self, particle):
        return (
            float(particle.PosLocA.x),
            float(particle.PosLocA.y),
            float(particle.PosLocA.z),
        )

    def infer_boundary_light_sources_from_particles(self):
        if not self.boundary_lighting_enabled:
            return 0

        lighting_ball = self.run_configuration.get("Lighting_ball")
        sphere_center = None
        sphere_radius = None
        sphere_material_id = None
        sphere_wall_flag = 1000
        if lighting_ball is not None and hasattr(lighting_ball, "get"):
            sphere_center = (
                float(lighting_ball.get("x")),
                float(lighting_ball.get("y")),
                float(lighting_ball.get("z")),
            )
            sphere_radius = float(lighting_ball.get("radius"))
            sphere_material_id = int(lighting_ball.get("material_id", 0))
            sphere_wall_flag = int(lighting_ball.get("wall_flag", 1000))

        inferred_count = 0
        for particle_id, particle in enumerate(self.particles):
            if not self.IsBoundaryParticle(particle_id):
                continue
            position = self.particle_position_tuple(particle)
            material_id = int(round(float(getattr(particle, "material_id", 0.0))))
            if (
                sphere_center is not None
                and material_id == sphere_material_id
                and sphere_radius is not None
            ):
                normal = (
                    position[0] - sphere_center[0],
                    position[1] - sphere_center[1],
                    position[2] - sphere_center[2],
                )
                normal_length = math.sqrt(
                    normal[0] * normal[0]
                    + normal[1] * normal[1]
                    + normal[2] * normal[2]
                )
                if normal_length > 1.0e-12:
                    self.register_boundary_light_source(
                        particle_id,
                        BOUNDARY_LIGHT_SURFACE_SPHERE,
                        sphere_wall_flag,
                        material_id,
                        (
                            normal[0] / normal_length,
                            normal[1] / normal_length,
                            normal[2] / normal_length,
                        ),
                    )
                    inferred_count += 1
                    continue

            rectangle_segments = self.run_configuration.get("rectangle_wall_segments")
            if isinstance(rectangle_segments, AttrDict):
                for _wall_name, wall_config in rectangle_segments.items():
                    if material_id != int(wall_config.get("material_id", 0)):
                        continue
                    if not self.rectangle_wall_contains_point(wall_config, position):
                        continue
                    normal = self._vector3(wall_config.get("normal"), "normal")
                    self.register_boundary_light_source(
                        particle_id,
                        BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL,
                        int(wall_config.get("wall_flag", 0)),
                        material_id,
                        normal,
                    )
                    inferred_count += 1
                    break
        return inferred_count

    def rectangle_wall_contains_point(self, wall_config, position):
        origin = self._vector3(wall_config.get("origin"), "origin")
        u_axis = self._axis_vector(wall_config.get("u_axis"))
        v_axis = self._axis_vector(wall_config.get("v_axis"))
        normal = self._vector3(wall_config.get("normal"), "normal")
        u_length = float(wall_config.get("u_length", 0.0))
        v_length = float(wall_config.get("v_length", 0.0))
        rel = (
            float(position[0]) - origin[0],
            float(position[1]) - origin[1],
            float(position[2]) - origin[2],
        )
        plane_distance = (
            rel[0] * normal[0]
            + rel[1] * normal[1]
            + rel[2] * normal[2]
        )
        if abs(plane_distance) > 1.0e-6:
            return False
        u_value = rel[0] * u_axis[0] + rel[1] * u_axis[1] + rel[2] * u_axis[2]
        v_value = rel[0] * v_axis[0] + rel[1] * v_axis[1] + rel[2] * v_axis[2]
        return (
            -1.0e-6 <= u_value <= u_length + 1.0e-6
            and -1.0e-6 <= v_value <= v_length + 1.0e-6
        )

    def InitializeBoundarySpaceLighting(self):
        for particle in self.particles:
            particle.boundary_space_light_valid = 0
            particle.boundary_space_light_r = float(self.boundary_light_initial_rgb[0])
            particle.boundary_space_light_g = float(self.boundary_light_initial_rgb[1])
            particle.boundary_space_light_b = float(self.boundary_light_initial_rgb[2])
        return len(self.boundary_light_source_metadata)

    def MaterialColorRGB(self, material_id):
        material_id = int(round(float(material_id)))
        for material in self.run_configuration.get("material_properties", ()) or ():
            if int(material.get("material_id", 0)) == material_id:
                color = material.get("color", (1.0, 1.0, 1.0, 1.0))
                return tuple(
                    max(0.0, min(1.0, float(color[index])))
                    for index in range(3)
                )
        return 1.0, 1.0, 1.0

    def DepositBoundaryLight(self, target_id, rgb):
        if not self.boundary_lighting_enabled:
            return False
        target_id = int(target_id)
        if target_id < 0 or target_id >= len(self.particles):
            return False
        if not self.IsBoundaryParticle(target_id):
            return False
        particle = self.particles[target_id]
        particle.boundary_space_light_valid = 1
        particle.boundary_space_light_r = max(0.0, min(1.0, float(rgb[0])))
        particle.boundary_space_light_g = max(0.0, min(1.0, float(rgb[1])))
        particle.boundary_space_light_b = max(0.0, min(1.0, float(rgb[2])))
        return True

    def DepositBoundaryLightForMaterial(self, target_id, material_id):
        return self.DepositBoundaryLight(target_id, self.MaterialColorRGB(material_id))

    def DepositBoundaryLightForSurface(
        self,
        surface_type,
        surface_id,
        material_id,
        position,
    ):
        if not self.boundary_lighting_enabled:
            return False
        surface_type = int(surface_type)
        surface_id = int(surface_id)
        position = tuple(float(value) for value in position)
        nearest_particle_id = None
        nearest_distance2 = None
        for particle_id, metadata in self.boundary_light_source_metadata.items():
            if (
                int(metadata["surface_type"]) == surface_type
                and int(metadata["surface_id"]) == surface_id
            ):
                point = self.particle_position_tuple(self.particles[particle_id])
                dx = point[0] - position[0]
                dy = point[1] - position[1]
                dz = point[2] - position[2]
                distance2 = dx * dx + dy * dy + dz * dz
                if nearest_distance2 is None or distance2 < nearest_distance2:
                    nearest_distance2 = distance2
                    nearest_particle_id = int(particle_id)
        if nearest_particle_id is None:
            return False
        return self.DepositBoundaryLightForMaterial(
            nearest_particle_id,
            material_id,
        )

    def BoundaryLightFilteredRGB(self, particle_id):
        particle_id = int(particle_id)
        if (
            not self.boundary_lighting_enabled
            or particle_id < 0
            or particle_id >= len(self.particles)
        ):
            return None
        metadata = self.boundary_light_source_metadata.get(particle_id)
        if metadata is None:
            return None
        particle = self.particles[particle_id]
        if int(getattr(particle, "boundary_space_light_valid", 0)) == 1:
            return (
                float(particle.boundary_space_light_r),
                float(particle.boundary_space_light_g),
                float(particle.boundary_space_light_b),
            )

        source_position = self.particle_position_tuple(particle)
        source_normal = metadata["normal"]
        total_weight = 0.0
        total_rgb = [0.0, 0.0, 0.0]
        for other_id, other_metadata in self.boundary_light_source_metadata.items():
            if (
                int(other_metadata["surface_type"]) != int(metadata["surface_type"])
                or int(other_metadata["surface_id"]) != int(metadata["surface_id"])
            ):
                continue
            other = self.particles[other_id]
            if int(getattr(other, "boundary_space_light_valid", 0)) != 1:
                continue
            weight = self.BoundarySpaceLightWeight(
                metadata,
                source_position,
                source_normal,
                other_metadata,
                self.particle_position_tuple(other),
            )
            if weight <= 0.0:
                continue
            total_weight += weight
            total_rgb[0] += float(other.boundary_space_light_r) * weight
            total_rgb[1] += float(other.boundary_space_light_g) * weight
            total_rgb[2] += float(other.boundary_space_light_b) * weight
        if total_weight <= 0.0:
            return None
        return tuple(value / total_weight for value in total_rgb)

    def BoundarySpaceLightWeight(
        self,
        metadata,
        position,
        normal,
        other_metadata,
        other_position,
    ):
        if int(metadata["surface_type"]) == BOUNDARY_LIGHT_SURFACE_SPHERE:
            dot_value = (
                float(normal[0]) * float(other_metadata["normal"][0])
                + float(normal[1]) * float(other_metadata["normal"][1])
                + float(normal[2]) * float(other_metadata["normal"][2])
            )
            value = 1.0 - (
                math.acos(max(-1.0, min(1.0, dot_value)))
                / self.boundary_space_patch_angle
            )
        else:
            dx = float(position[0]) - float(other_position[0])
            dy = float(position[1]) - float(other_position[1])
            dz = float(position[2]) - float(other_position[2])
            distance = math.sqrt(dx * dx + dy * dy + dz * dz)
            value = 1.0 - distance / self.boundary_space_patch_radius
        if value <= 0.0:
            return 0.0
        if self.boundary_space_patch_falloff == "quadratic":
            return value * value
        return value

    def _axis_vector(self, axis_name):
        axis_key = str(axis_name).strip().upper()
        if axis_key not in AXIS_VECTOR:
            raise ValueError(
                "rectangle_wall_segments axis values must be one of X, Y, or Z"
            )
        return AXIS_VECTOR[axis_key]

    @staticmethod
    def _vector3(raw_value, field_name):
        if raw_value is None or len(raw_value) != 3:
            raise ValueError(f"rectangle_wall_segments.{field_name} must have 3 values")
        return tuple(float(value) for value in raw_value)

    def _sample_rectangle_wall_points(self, wall_name, wall_config):
        origin = self._vector3(wall_config.get("origin"), f"{wall_name}.origin")
        normal = self._vector3(wall_config.get("normal"), f"{wall_name}.normal")
        if math.sqrt(sum(component * component for component in normal)) <= 1.0e-12:
            raise ValueError(f"rectangle_wall_segments.{wall_name}.normal must not be zero")

        u_axis = self._axis_vector(wall_config.get("u_axis"))
        v_axis = self._axis_vector(wall_config.get("v_axis"))
        if u_axis == v_axis:
            raise ValueError(
                f"rectangle_wall_segments.{wall_name}.u_axis and v_axis must differ"
            )

        u_length = float(wall_config.get("u_length", 0.0))
        v_length = float(wall_config.get("v_length", 0.0))
        if u_length < 0.0 or v_length < 0.0:
            raise ValueError(
                f"rectangle_wall_segments.{wall_name}.u_length/v_length must be nonnegative"
            )

        u_steps = max(1, int(math.floor(u_length)) + 1)
        v_steps = max(1, int(math.floor(v_length)) + 1)
        for u_index in range(u_steps):
            for v_index in range(v_steps):
                yield (
                    origin[0] + u_axis[0] * u_index + v_axis[0] * v_index,
                    origin[1] + u_axis[1] * u_index + v_axis[1] * v_index,
                    origin[2] + u_axis[2] * u_index + v_axis[2] * v_index,
                )

    def add_rectangle_boundary_markers_from_cfg(self):
        """Build runtime boundary markers from 3D rectangle wall patches."""
        segments = self.run_configuration.get("rectangle_wall_segments")
        if not isinstance(segments, AttrDict):
            return 0

        marker_cells = {
            (
                int(round(float(particle.PosLocA.x))),
                int(round(float(particle.PosLocA.y))),
                int(round(float(particle.PosLocA.z))),
            )
            for particle in self.particles
            if int(round(float(getattr(particle, "ptype", 0.0)))) == int(PTYPE_BOUNDARY)
        }
        radius = float(self.run_configuration.get("radius", 0.0))
        marker_count = 0
        for wall_name, wall_config in segments.items():
            if not isinstance(wall_config, AttrDict):
                raise ValueError(
                    f"rectangle_wall_segments.{wall_name} must be a key-value object"
                )
            material_id = int(wall_config.get("material_id", 0))
            for point in self._sample_rectangle_wall_points(wall_name, wall_config):
                marker_cell = tuple(int(round(value)) for value in point)
                if marker_cell in marker_cells:
                    continue
                marker_cells.add(marker_cell)
                particle_id = len(self.particles)
                self.particles.append(
                    self.create_particle(
                        pnum=particle_id,
                        rx=point[0],
                        ry=point[1],
                        rz=point[2],
                        radius=radius,
                        mass=1.0,
                        ptype=PTYPE_BOUNDARY,
                        material_id=material_id,
                        collision_stiffness_q=0.0,
                        state_flg=0.0,
                    )
                )
                self.register_boundary_light_source(
                    particle_id,
                    BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL,
                    int(wall_config.get("wall_flag", 0)),
                    material_id,
                    self._vector3(wall_config.get("normal"), f"{wall_name}.normal"),
                )
                marker_count += 1
        return marker_count

    def ConfiguredWallMaterialID(self, wall_flag):
        """Return the configured material id for a wall flag."""
        wall_flag = int(wall_flag)
        rectangle_segments = self.run_configuration.get("rectangle_wall_segments")
        if isinstance(rectangle_segments, AttrDict):
            for _wall_name, wall_config in rectangle_segments.items():
                if int(wall_config.get("wall_flag", 0)) == wall_flag:
                    return float(wall_config.get("material_id", 0))

        for segment in self.run_configuration.get("curve_wall_segments", ()):
            if len(segment) >= 11 and int(round(float(segment[9]))) == wall_flag:
                return float(segment[10])
        return 0.0

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
        self.constants.ERROR_INITIAL_PARTICLE_OVERLAP = 11
        self.constants.ERROR_INITIAL_WALL_OVERLAP = 12
        self.error_names = {
            value: name
            for name, value in constants.items()
            if name.startswith("ERROR_")
        }
        self.error_names[self.constants.ERROR_INITIAL_PARTICLE_OVERLAP] = (
            "ERROR_INITIAL_PARTICLE_OVERLAP"
        )
        self.error_names[self.constants.ERROR_INITIAL_WALL_OVERLAP] = (
            "ERROR_INITIAL_WALL_OVERLAP"
        )
        return self.constants

    def ErrorDescription(self):
        description = self.error_names.get(
            self.collIn.ErrorReturn,
            "ERROR_UNKNOWN",
        )
        if self.collIn.ErrorReturn not in {
            self.constants.ERROR_PARTICLE_TUNNELING,
            self.constants.ERROR_WALL_TUNNELING,
            self.constants.ERROR_MAX_DEPTH_CONSTRAINT,
            self.constants.ERROR_PENETRATION_STEP_TOO_LARGE,
            self.constants.ERROR_INITIAL_PARTICLE_OVERLAP,
            self.constants.ERROR_INITIAL_WALL_OVERLAP,
        }:
            return description

        error_kind = str(getattr(self.collIn, "ErrorKind", "unknown"))
        source_id = int(getattr(self.collIn, "ErrorSourceID", -1))
        if self.collIn.ErrorReturn == self.constants.ERROR_PARTICLE_TUNNELING:
            target_id = int(getattr(self.collIn, "ErrorTargetID", -1))
            return (
                f"{description} particle-particle "
                f"source={source_id} target={target_id}"
            )
        if self.collIn.ErrorReturn == self.constants.ERROR_INITIAL_PARTICLE_OVERLAP:
            target_id = int(getattr(self.collIn, "ErrorTargetID", -1))
            return (
                f"{description} particle-particle "
                f"source={source_id} target={target_id}"
            )
        if self.collIn.ErrorReturn == self.constants.ERROR_INITIAL_WALL_OVERLAP:
            wall_flag = int(getattr(self.collIn, "ErrorWallFlag", 0))
            return (
                f"{description} particle-wall "
                f"source={source_id} wall={wall_flag}"
            )
        if self.collIn.ErrorReturn == self.constants.ERROR_WALL_TUNNELING:
            wall_flag = int(getattr(self.collIn, "ErrorWallFlag", 0))
            return (
                f"{description} particle-wall "
                f"source={source_id} wall={wall_flag}"
            )
        if self.collIn.ErrorReturn == self.constants.ERROR_MAX_DEPTH_CONSTRAINT:
            target_id = int(getattr(self.collIn, "ErrorTargetID", -1))
            wall_flag = int(getattr(self.collIn, "ErrorWallFlag", 0))
            if target_id >= 0 and wall_flag > 0:
                contact_text = f"mixed first_target={target_id} first_wall={wall_flag}"
            elif target_id >= 0:
                contact_text = f"particle first_target={target_id}"
            elif wall_flag > 0:
                contact_text = f"wall first_wall={wall_flag}"
            else:
                contact_text = "unknown"
            return f"{description} source contact set source={source_id} {contact_text}"
        if self.collIn.ErrorReturn == self.constants.ERROR_PENETRATION_STEP_TOO_LARGE:
            target_id = int(getattr(self.collIn, "ErrorTargetID", -1))
            wall_flag = int(getattr(self.collIn, "ErrorWallFlag", 0))
            if error_kind == "particle-wall":
                return (
                    f"{description} particle-wall "
                    f"source={source_id} wall={wall_flag}"
                )
            return (
                f"{description} particle-particle "
                f"source={source_id} target={target_id}"
            )
        return f"{description} kind={error_kind} source={source_id}"

    def create_collision_in(self):
        coll_in = CollisionInFields()
        coll_in.ErrorReturn = 0
        coll_in.numParticles = 0
        coll_in.maxCells = 0
        coll_in.particleNumber = 0
        coll_in.ReadWriteConflict = 0
        coll_in.ExcessSlots = 0
        coll_in.ErrorKind = "none"
        coll_in.ErrorSourceID = -1
        coll_in.ErrorTargetID = -1
        coll_in.ErrorWallFlag = 0
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
        ptype = fields.get("ptype", 0.0)
        material_id = fields.get("material_id", 0.0)
        velocity_angle = self.VelocityAngle(vx, vy)
        particle.PosLocA = self.create_vec4(rx, ry, rz, 0.0)
        particle.PosLocB = self.create_vec4(rx, ry, rz, 1.0)
        particle.VelRad = self.create_vec4(vx, vy, vz, velocity_angle)
        particle.Data = self.create_vec4(
            radius,
            fields.get("collision_stiffness_q", 0.0),
            0.0,
            fields.get("state_flg", 1.0),
        )
        particle.parms = self.create_vec4(mass, 0.0, 0.0, 0.0)
        particle.internal_momentum = 0.0
        particle.contacts = (
            [self.create_geo_contact_state() for _ in range(16)]
            if float(ptype) <= 0.5
            else []
        )
        particle.gcs = particle.contacts
        particle.contactCount = 0
        particle.colFlg = 0
        particle.mass = mass
        particle.radius = radius
        particle.ptype = ptype
        particle.material_id = material_id
        particle.state_flg = fields.get("state_flg", 1.0)
        particle.oa = fields.get("oa", 0.0)
        particle.max_penetration_depth = fields.get("max_penetration_depth", 0.0)
        particle.report_contacts = 0
        particle.report_phase = 0
        particle.report_target = 0
        particle.report_center_distance = 0.0
        particle.report_normal_x = 0.0
        particle.report_normal_y = 0.0
        particle.report_normal_z = 0.0
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
        state_flg = particle_cfg.get(
            "releaseFrame",
            particle_cfg.get("state_flg", 0.0),
        )
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
            ptype=particle_cfg.get("ptype", 0.0),
            material_id=particle_cfg.get("material_id", 0.0),
            collision_stiffness_q=collision_stiffness_q,
            state_flg=state_flg,
        )

    def getParticleData(self,config):
        cfg_data_name = config["output_file_prefix"]
        file_name = f"{config.data_dir}/{cfg_data_name}.bin"
        
        results = BinaryFileUtilities.read_all_particle_data(file_name)
        particle_data = AttrDict()
        particles = AttrDict()
        for pp in results:
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
            particle["ptype"] = PTYPE_NULL if pp.pnum == 0 else pp.ptype
            particle["material_id"] = pp.material_id
            particle["collision_stiffness_q"] = pp.collision_stiffness_q
            particle["state_flg"] = int(pp.state_flg)
            particle["edge"] = (100, 170, 255)
            particle["fill"] = (160, 210, 255)
            particle_data[pp.pnum] = particle
            pnumtxt = f"p{int(pp.pnum)}"
            particles[pnumtxt] =  particle

            #print(f"Read particle: {pp.pnum} at ({pp.rx}, {pp.ry}, {pp.rz}) with velocity ({pp.vx}, {pp.vy}, {pp.vz})")

        return particles

    def create_particle_array_from_cfg(self, particle_data):
        particles = []

        if not any(
            int(str(particle_name).lstrip("p") or 0) == 0
            for particle_name in particle_data.keys()
        ):
            particles.append(
                self.create_particle(
                    pnum=0,
                    ptype=PTYPE_NULL,
                    state_flg=1.0,
                )
            )

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
        if not particles or int(particles[0].pnum) != 0:
            raise ValueError("Python particle array must begin with null particle p0")
        particles[0].ptype = PTYPE_NULL
        for particle_index, particle in enumerate(particles):
            if int(particle.pnum) != particle_index:
                raise ValueError(
                    "Python particle ABI index mismatch: "
                    f"particles[{particle_index}].pnum={particle.pnum}"
                )
        return particles

    def create_particle_array(self, count=0):
        self.particles = [
            self.create_particle(
                pnum=index,
                ptype=PTYPE_NULL if index == 0 else 0.0,
            )
            for index in range(count)
        ]
        return self.particles

    def create_shader_flags(self, **fields):
        shader_flags = ShaderFlagsFields()
        
        self.item_cfg = shader_flags
        shader_flags.DrawInstance = fields.get("DrawInstance", 0.0)
        shader_flags.CellAryW = fields.get("CellAryW", 0.0)
        shader_flags.CellAryH = fields.get("CellAryH", 0.0)
        shader_flags.CellAryL = fields.get("CellAryL", 0.0)
        shader_flags.Ptot = fields.get("Ptot", 0.0)
        shader_flags.dt = fields.get("dt", 0.0)
        shader_flags.systemp = fields.get("systemp", 0.0)
        shader_flags.ColorMap = fields.get("ColorMap", 0.0)
        shader_flags.StopFlg = fields.get("StopFlg", 0.0)
        shader_flags.frameNum = fields.get("frameNum", 0.0)
        shader_flags.actualFrame = fields.get("actualFrame", 0.0)
        shader_flags.positionBuffer = fields.get("positionBuffer", 0.0)
        shader_flags.boundaryLightingEnabled = fields.get(
            "boundaryLightingEnabled",
            0.0,
        )
        shader_flags.boundaryLightingModel = fields.get("boundaryLightingModel", 0.0)
        shader_flags.boundaryLightSampleCount = fields.get(
            "boundaryLightSampleCount",
            0.0,
        )
        shader_flags.boundaryLightFilterAlpha = fields.get(
            "boundaryLightFilterAlpha",
            0.0,
        )
        return shader_flags

    def create_shader_flags_from_cfg(self, run_configuration):
        width, height, depth = get_cell_dimensions(run_configuration)
        return self.create_shader_flags(
            CellAryW=width,
            CellAryH=height,
            CellAryL=depth,
            Ptot=len(self.particles),
            dt=run_configuration.get("dt", 0.0),
            positionBuffer=run_configuration.get("positionBuffer", 0.0),
            boundaryLightingEnabled=1.0 if self.boundary_lighting_enabled else 0.0,
            boundaryLightingModel=float(self.boundary_lighting_model),
            boundaryLightSampleCount=float(len(self.boundary_light_source_metadata)),
            boundaryLightFilterAlpha=0.0,
        )

    def ValidateInitialGeometry(self):
        """Reject physical particle or wall overlap before first dynamics."""
        if self.initial_geometry_validated:
            return True

        mobile_ids = [
            particle_id
            for particle_id in range(len(self.particles))
            if self.IsMobileParticleActiveForDynamics(particle_id)
        ]
        for source_offset, source_id in enumerate(mobile_ids):
            source_position = self.GetParticlePosition(source_id)
            source_radius = float(self.particles[source_id].Data.x)
            for target_id in mobile_ids[source_offset + 1 :]:
                target_position = self.GetParticlePosition(target_id)
                target_radius = float(self.particles[target_id].Data.x)
                dx = float(target_position.x) - float(source_position.x)
                dy = float(target_position.y) - float(source_position.y)
                dz = float(target_position.z) - float(source_position.z)
                center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
                penetration = source_radius + target_radius - center_distance
                if penetration > self.EPSILON:
                    return self.SetError(
                        self.constants.ERROR_INITIAL_PARTICLE_OVERLAP,
                        error_kind="initial-particle-overlap",
                        source_id=source_id,
                        target_id=target_id,
                    )

        rectangle_segments = self.run_configuration.get("rectangle_wall_segments")
        if rectangle_segments:
            for source_id in mobile_ids:
                for _wall_name, wall_config in rectangle_segments.items():
                    penetration = self.RectangleWallPhysicalPenetration(
                        source_id,
                        wall_config,
                    )
                    if penetration is None or penetration <= self.EPSILON:
                        continue
                    return self.SetError(
                        self.constants.ERROR_INITIAL_WALL_OVERLAP,
                        error_kind="initial-wall-overlap",
                        source_id=source_id,
                        wall_flag=int(wall_config.get("wall_flag", 0)),
                    )
        else:
            segments = self.run_configuration.get("curve_wall_segments", ())
            for source_id in mobile_ids:
                for segment in segments:
                    penetration = self.FunctionWallPhysicalPenetration(
                        source_id,
                        segment,
                    )
                    if penetration is None or penetration <= self.EPSILON:
                        continue
                    return self.SetError(
                        self.constants.ERROR_INITIAL_WALL_OVERLAP,
                        error_kind="initial-wall-overlap",
                        source_id=source_id,
                        wall_flag=int(round(float(segment[9]))),
                    )

        if self.PistonEnabled():
            piston_x = self.GetPistonPosition(self.ShaderFlags.frameNum)
            for source_id in mobile_ids:
                source_position = self.GetParticlePosition(source_id)
                radius = float(self.particles[source_id].Data.x)
                penetration = radius - (float(source_position.x) - piston_x)
                if penetration > self.EPSILON:
                    return self.SetError(
                        self.constants.ERROR_INITIAL_WALL_OVERLAP,
                        error_kind="initial-wall-overlap",
                        source_id=source_id,
                        wall_flag=1,
                    )

        self.initial_geometry_validated = True
        return True

    def DetectContacts(self, total_forces):
        """Run direct Python contact detection for every active source."""
        return self.NaiveContactDetermination(total_forces)

    def NaiveContactDetermination(self, total_forces):
        """Scan Python particles and process each source-owned contact."""
        self.photon_reflected_velocity = {}
        self.photon_reflected_position = {}
        for source_id in range(len(self.particles)):
            if not self.IsMobileParticleActiveForDynamics(source_id):
                continue
            source_is_photon = self.IsPhotonParticle(source_id)
            if not self.ProcessPistonCollision(
                source_id,
                total_forces[source_id],
            ):
                return False
            has_local_boundary_marker = False
            has_local_lighting_ball_marker = False
            for target_id in range(len(self.particles)):
                if source_id == target_id:
                    continue
                if self.IsBoundaryParticle(target_id):
                    if self.BoundaryParticleNormal(target_id) is not None:
                        has_local_lighting_ball_marker = (
                            has_local_lighting_ball_marker
                            or self.BoundaryMarkerApplies(source_id, target_id)
                        )
                        continue
                    has_local_boundary_marker = (
                        has_local_boundary_marker
                        or self.BoundaryMarkerApplies(
                            source_id,
                            target_id,
                        )
                    )
                    continue
                if source_is_photon:
                    continue
                if not self.IsMobileParticleActiveForDynamics(target_id):
                    continue
                if self.ShouldSkipParticlePair(source_id, target_id):
                    continue
                if self.TryPhotonParticleReflection(source_id, target_id):
                    continue
                geometry = self.GetPhysicalParticleContact(source_id, target_id)
                if geometry is not None:
                    self.RecordPhotonReflection(source_id, geometry[:3])
                    if self.IsPhotonParticle(source_id):
                        self.particles[source_id].colFlg = 1
                        self.particles[source_id].material_id = getattr(
                            self.particles[target_id],
                            "material_id",
                            self.particles[source_id].material_id,
                        )
                        continue
                    if not self.ProcessParticleCollision(
                        target_id,
                        source_id,
                        total_forces[source_id],
                        geometry,
                    ):
                        return False
                if self.collIn.ErrorReturn != self.constants.ERROR_NONE:
                    return False
            if has_local_lighting_ball_marker:
                if not self.ProcessLightingBallCollision(
                    source_id,
                    total_forces[source_id],
                ):
                    return False
                if self.collIn.ErrorReturn != self.constants.ERROR_NONE:
                    return False
            if not has_local_boundary_marker:
                continue
            boundary_contacts = self.EvaluateConfiguredWallContacts(source_id)
            for wall_flag in sorted(boundary_contacts):
                _penetration_depth, contact = boundary_contacts[wall_flag]
                self.RecordPhotonReflection(source_id, contact[:3])
                if self.IsPhotonParticle(source_id):
                    self.particles[source_id].colFlg = 1
                    self.particles[source_id].material_id = self.ConfiguredWallMaterialID(wall_flag)
                    self.DepositBoundaryLightForSurface(
                        2,
                        wall_flag,
                        self.particles[source_id].material_id,
                        self.particle_position_tuple(self.particles[source_id]),
                    )
                    continue
                if not self.ProcessFunctionWallCollision(
                    source_id,
                    contact,
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

    def CollisionRun(self):
        """Run one source-owned semi-implicit ForceDynamics frame."""
        diagnostics_enabled = bool(
            self.run_configuration.get("dynamics_diagnostics", False)
        )
        if not self.BeginFrame():
            return self.particles
        self.ApplyBeforeContactScanHook()
        self.ResetFrameState()
        self.ApplyStartRunHook()
        self.BuildFrameSnapshot()
        if not self.ValidateInitialGeometry():
            return self.particles
        if diagnostics_enabled:
            self.RecordFrameStartDiagnostics()
            self.InitializePairPhaseEnergyReference()

        total_forces = [self.create_vec4() for _ in self.particles]
        if not self.DetectContacts(total_forces):
            return self.particles
        self.ClearInactiveRecoverableInternalMomentum()
        frame_start_pairs = (
            self.CapturePairGeometryDiagnostics()
            if diagnostics_enabled
            else None
        )
        if not self.CalculateVelocities(total_forces):
            return self.particles
        if not self.CalculatePositions():
            return self.particles
        if diagnostics_enabled:
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
        self.piston_contact_count = 0
        self.piston_frame_impulse = 0.0
        self.piston_frame_momentum = self.create_vec4()
        self.collIn.ErrorReturn = self.constants.ERROR_NONE
        self.collIn.ErrorKind = "none"
        self.collIn.ErrorSourceID = -1
        self.collIn.ErrorTargetID = -1
        self.collIn.ErrorWallFlag = 0
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
        if self.scenario:
            self.scenario.BeforeContactScan(self.particles)

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
            particle.report_normal_z = 0.0
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
        scenario object is attached, scenario.StartRun(particles) may adjust or
        replace the particle list used by the rest of the frame.  If inline
        testing is not active, or no scenario is attached, this stage is a
        no-op.
        """
        if self.inline_test_flag == True and self.scenario is not None:
            self.particles = self.scenario.StartRun(self.particles)
    
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
        ## Frame-start velocity lives in VelRadFrame. Runtime parms keeps
        ## parms.x = mass and parms.yzw = recoverable internal momentum.
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
            if not self.IsMobileParticleActiveForDynamics(particle_index):
                particle.report_frame_start_ke = 0.0
                continue
            velocity = self.VelRadFrame[particle_index]
            particle.report_frame_start_ke = self.ParticleKineticEnergy(
                particle_index,
                velocity,
            )

    def RecordAfterResolveDiagnostics(self):
        for particle_index, particle in enumerate(self.particles):
            if not self.IsMobileParticleActiveForDynamics(particle_index):
                particle.report_after_resolve_ke = 0.0
                continue
            particle.report_after_resolve_ke = self.ParticleKineticEnergy(
                particle_index,
            )

    def GetContactPotentialEnergy(self, SourceID, TargetID, center_distance):
        """Return diagnostic pair potential energy from current geometry."""
        source_radius = float(self.particles[SourceID].Data.x)
        target_radius = float(self.particles[TargetID].Data.x)
        if center_distance >= source_radius + target_radius:
            return 0.0
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
            if not self.IsMobileParticleActiveForDynamics(source_id):
                continue
            source_position = self.GetParticlePosition(source_id)
            for target_id in range(source_id + 1, len(self.particles)):
                if not self.IsMobileParticleActiveForDynamics(target_id):
                    continue
                if self.ShouldSkipParticlePair(source_id, target_id):
                    continue
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
            if not self.IsMobileParticleActiveForDynamics(source_id):
                continue
            source_position = self.GetParticlePosition(source_id)
            for target_id in range(source_id + 1, len(self.particles)):
                if not self.IsMobileParticleActiveForDynamics(target_id):
                    continue
                if self.ShouldSkipParticlePair(source_id, target_id):
                    continue
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
                if center_distance >= source_radius + target_radius:
                    overlap_area = 0.0
                else:
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
            if self.IsMobileParticleActiveForDynamics(particle_index)
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
            end = frame_end_pairs.get(pair)
            if end is None:
                continue
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

    def TotalWallPotentialEnergy(self):
        """Return potential energy stored against function walls."""
        total = 0.0
        for source_id, source in enumerate(self.particles):
            if not self.IsMobileParticleActiveForDynamics(source_id):
                continue
            stiffness = max(0.0, float(source.Data.y or 0.0))
            contacts = self.EvaluateConfiguredWallContacts(source_id)
            for _penetration_depth, geometry in contacts.values():
                radius = float(source.Data.x)
                total += self.GetOverlapPotentialEnergy(
                    radius,
                    radius,
                    stiffness,
                    float(geometry[-2]),
                )
        return total

    def EndFrame(self):
        position_buffer = int(self.ShaderFlags.positionBuffer)
        self.ShaderFlags.positionBuffer = 1.0 if position_buffer == 0 else 0.0
        self.PosLocFrame = []
        self.VelRadFrame = []
