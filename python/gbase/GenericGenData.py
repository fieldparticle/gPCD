import os
import re
from collections import Counter

from gbase.BoundarySpaceLighting import (
    BOUNDARY_SPACE_SURFACE_RECTANGLE_WALL,
    BOUNDARY_SPACE_SURFACE_SPHERE,
    RETIRED_BOUNDARY_LIGHTING_CONFIG_KEYS,
)
from gbase.FunctionWall import bounds as wall_bounds
from gbase.FunctionWall import evaluate_wall_at_point
from gbase.FunctionWall import parse_keyed_curve_wall_segments
from gbase.FunctionWall import sample_points
from gbase.FunctionWall import segment_values
from gbase.MaterialProperties import (
    COLOR_MODE_COLLISION,
    COLOR_MODE_INTERNAL_MOMENTUM,
    COLOR_MODE_LUMENS,
    COLOR_MODE_NAMES,
    COLOR_MODE_SOLID,
    COLOR_MODE_VELOCITY_ANGLE,
    DEFAULT_MATERIAL_PROPERTIES,
    PARTICLE_TYPE_BOUNDARY,
    PARTICLE_TYPE_PHOTON,
    PARTICLE_TYPE_REFLECTION_PHOTON,
    PHOTON_SURFACE_BEHAVIOR_NONE,
    PHOTON_SURFACE_BEHAVIOR_REFLECT,
    PHOTON_LIFE_TIME_PERIODIC,
    PHOTON_LIFE_TIME_PERISH,
    CONTACT_ILLUMINATION_MAX,
    CONTACT_ILLUMINATION_FIRST,
    parse_debug_visible,
    parse_contact_illumination,
    parse_color_map,
    parse_material_color,
    parse_material_point_size,
    parse_momentum_span,
    parse_capture_angles,
    parse_particle_type,
    parse_photon_surface_behavior,
    parse_photon_life_time,
    parse_spectral_rgb,
    write_color_mode_defines,
    write_material_properties,
)
from gbase.SceneModel import apply_scene_model
from gbase.pdata import (
    PTYPE_BOUNDARY,
    PTYPE_MOBILE,
    PTYPE_NULL,
    PTYPE_PHOTON,
    PTYPE_REFLECTION_PHOTON,
    pdata,
)
import math


AXIS_VECTOR = {
    "X": (1.0, 0.0, 0.0),
    "Y": (0.0, 1.0, 0.0),
    "Z": (0.0, 0.0, 1.0),
}


def _rectangle_axis_vector(axis_name, errors, context):
    axis_key = str(axis_name).strip().upper()
    if axis_key not in AXIS_VECTOR:
        errors.append(f"{context} must be X, Y, or Z")
        return None
    return AXIS_VECTOR[axis_key]


def _rectangle_vector3(raw_value, errors, context):
    if raw_value is None:
        errors.append(f"{context} is required")
        return None
    if len(raw_value) != 3:
        errors.append(f"{context} must contain exactly 3 values")
        return None
    try:
        values = tuple(float(value) for value in raw_value)
    except (TypeError, ValueError):
        errors.append(f"{context} values must be numeric")
        return None
    if not all(math.isfinite(value) for value in values):
        errors.append(f"{context} values must be finite")
        return None
    return values


def parse_keyed_rectangle_wall_segments(raw_segments):
    """Parse keyed 3D rectangle wall config into numeric internal records."""
    if not raw_segments:
        return (), []

    errors = []
    parsed_segments = []
    try:
        items = raw_segments.items()
    except AttributeError:
        return (), ["rectangle_wall_segments must be a key-value object"]

    for segment_name, segment_config in items:
        context = f"rectangle_wall_segments.{segment_name}"
        try:
            origin = _rectangle_vector3(
                segment_config.get("origin"),
                errors,
                f"{context}.origin",
            )
            u_axis = _rectangle_axis_vector(
                segment_config.get("u_axis"),
                errors,
                f"{context}.u_axis",
            )
            v_axis = _rectangle_axis_vector(
                segment_config.get("v_axis"),
                errors,
                f"{context}.v_axis",
            )
            u_length = float(segment_config.get("u_length"))
            v_length = float(segment_config.get("v_length"))
            inward_normal = _rectangle_vector3(
                segment_config.get("normal"),
                errors,
                f"{context}.normal",
            )
            wall_flag = int(segment_config.get("wall_flag"))
            material_id = int(segment_config.get("material_id", 0))
        except (AttributeError, TypeError, ValueError):
            errors.append(f"{context} is invalid")
            continue

        if origin is None or u_axis is None or v_axis is None or inward_normal is None:
            continue
        if u_axis == v_axis:
            errors.append(f"{context}.u_axis and v_axis must differ")
        if not math.isfinite(u_length) or u_length < 0.0:
            errors.append(f"{context}.u_length must be a finite nonnegative number")
        if not math.isfinite(v_length) or v_length < 0.0:
            errors.append(f"{context}.v_length must be a finite nonnegative number")
        normal_length = math.sqrt(sum(component * component for component in inward_normal))
        if normal_length <= 1.0e-12:
            errors.append(f"{context}.normal must not be zero")
        if wall_flag <= 0:
            errors.append(f"{context}.wall_flag must be a positive integer")
        if material_id < 0:
            errors.append(f"{context}.material_id must be a non-negative integer")

        parsed_segments.append(
            {
                "name": str(segment_name),
                "origin": origin,
                "u_axis": u_axis,
                "v_axis": v_axis,
                "u_length": u_length,
                "v_length": v_length,
                "normal": inward_normal,
                "wall_flag": wall_flag,
                "material_id": material_id,
            }
        )

    if errors:
        return (), errors
    return tuple(parsed_segments), []


class GenericGenData:
    """Generate particle data from declarative particle and wall configuration."""

    BOUNDARY_PARTICLE_PTYPE = PTYPE_BOUNDARY
    COLOR_MODE_COLLISION = COLOR_MODE_COLLISION
    COLOR_MODE_VELOCITY_ANGLE = COLOR_MODE_VELOCITY_ANGLE
    COLOR_MODE_SOLID = COLOR_MODE_SOLID
    COLOR_MODE_LUMENS = COLOR_MODE_LUMENS
    COLOR_MODE_INTERNAL_MOMENTUM = COLOR_MODE_INTERNAL_MOMENTUM
    COLOR_MODE_NAMES = COLOR_MODE_NAMES
    COLOR_MODE_VALUES = set(COLOR_MODE_NAMES.values())
    DEFAULT_MATERIAL_PROPERTIES = DEFAULT_MATERIAL_PROPERTIES

    def __init__(self):
        self.parent = None
        self.bobj = None
        self.cfg = None
        self.log = None
        self.itemcfg = None
        self.p_list = []
        self.bin_file = None
        self.count = 0
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0
        self.boundary_space_lighting_enabled = False
        self.boundary_space_proxy_metadata = {}
        self.material_properties = [dict(item) for item in self.DEFAULT_MATERIAL_PROPERTIES]
        self.material_properties_by_id = {
            int(item["material_id"]): dict(item)
            for item in self.material_properties
        }
        self.lighting_surface_triangle_inventory = ()

    def create(self, parent, itemcfg):
        self.parent = parent
        self.bobj = parent.bobj
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.itemcfg = itemcfg
        apply_scene_model(self.itemcfg)

    def openSelectionsFile(self):
        """This generator does not use a selections file."""

    def clear_selections(self):
        """This generator does not use selection records."""

    def clear_files(self):
        """Output replacement occurs only after configuration verification."""

    def do_all_files_dbg(self):
        return self.runner()

    def parse_color_mode(self, raw_value, errors, context):
        if isinstance(raw_value, str):
            color_mode = self.COLOR_MODE_NAMES.get(raw_value.strip().upper())
            if color_mode is None:
                errors.append(f"{context}.color_mode is unknown: {raw_value}")
                return None
            return color_mode
        try:
            color_mode = int(raw_value)
        except (TypeError, ValueError):
            errors.append(f"{context}.color_mode must be an integer or known name")
            return None
        if color_mode not in self.COLOR_MODE_VALUES:
            errors.append(f"{context}.color_mode is not a known color mode")
            return None
        return color_mode

    def validate_material_properties(self, errors):
        initial_error_count = len(errors)
        raw_materials = self.itemcfg.get("material_properties")
        if raw_materials is None:
            materials = [dict(item) for item in self.DEFAULT_MATERIAL_PROPERTIES]
            self.set_material_properties(materials)
            return materials

        materials = []
        material_ids = set()
        try:
            material_count = len(raw_materials)
        except TypeError:
            errors.append("material_properties must be a list or tuple")
            return []

        for index, raw_material in enumerate(raw_materials):
            context = f"material_properties[{index}]"
            try:
                material_id = int(raw_material.material_id)
            except (AttributeError, TypeError, ValueError):
                errors.append(f"{context}.material_id is required and must be an integer")
                continue

            if material_id < 0:
                errors.append(f"{context}.material_id must not be negative")
            if material_id in material_ids:
                errors.append(f"{context}.material_id duplicates {material_id}")
            material_ids.add(material_id)

            name = str(raw_material.get("name", f"material_{material_id}"))
            try:
                particle_type = parse_particle_type(
                    raw_material.get("particle_type", "regular")
                )
            except (TypeError, ValueError):
                errors.append(f"{context}.particle_type is unknown")
                particle_type = None

            try:
                relative_mass = float(raw_material.get("relative_mass", 1.0))
            except (TypeError, ValueError):
                errors.append(f"{context}.relative_mass must be numeric")
                relative_mass = None
            if relative_mass is not None:
                if not math.isfinite(relative_mass):
                    errors.append(f"{context}.relative_mass must be finite")
                elif relative_mass <= 0.0:
                    errors.append(f"{context}.relative_mass must be positive")

            try:
                thermal_velocity = float(raw_material.get("thermal_velocity", 0.0))
            except (TypeError, ValueError):
                errors.append(f"{context}.thermal_velocity must be numeric")
                thermal_velocity = None
            if thermal_velocity is not None:
                if not math.isfinite(thermal_velocity):
                    errors.append(f"{context}.thermal_velocity must be finite")
                elif thermal_velocity < 0.0:
                    errors.append(f"{context}.thermal_velocity must not be negative")

            try:
                cell_density = float(raw_material.get("cell_density", 0.0))
            except (TypeError, ValueError):
                errors.append(f"{context}.cell_density must be numeric")
                cell_density = None
            if cell_density is not None:
                if not math.isfinite(cell_density):
                    errors.append(f"{context}.cell_density must be finite")
                elif not 0.0 <= cell_density <= 1.0:
                    errors.append(f"{context}.cell_density must be between 0 and 1")
                elif material_id == 0 and cell_density > 0.0:
                    errors.append(
                        f"{context}.cell_density must be 0 for stream-generated material 0"
                    )

            color_mode = self.parse_color_mode(
                raw_material.get(
                    "color_mode",
                    self.COLOR_MODE_VELOCITY_ANGLE,
                ),
                errors,
                context,
            )
            color_map = None
            if raw_material.get("color_map") is not None:
                try:
                    color_map = parse_color_map(raw_material.get("color_map"))
                except (TypeError, ValueError) as exc:
                    errors.append(f"{context}.color_map is invalid: {exc}")
            point_size = None
            if raw_material.get("point_size") is not None:
                try:
                    point_size = parse_material_point_size(raw_material.get("point_size"))
                except (TypeError, ValueError) as exc:
                    errors.append(f"{context}.point_size is invalid: {exc}")
            start_mom = None
            end_mom = None
            try:
                start_mom, end_mom = parse_momentum_span(
                    raw_material.get("start_mom", 0.0),
                    raw_material.get("end_mom", 1.0),
                )
            except (TypeError, ValueError) as exc:
                errors.append(f"{context}.momentum span is invalid: {exc}")
            capture_angles = ()
            try:
                capture_angles = parse_capture_angles(raw_material)
            except (TypeError, ValueError) as exc:
                errors.append(f"{context}.capture_angle is invalid: {exc}")
            color = None
            if color_mode is not None:
                try:
                    color = parse_material_color(
                        raw_material.get("color"),
                        color_mode,
                    )
                except (TypeError, ValueError) as exc:
                    errors.append(f"{context}.color is invalid: {exc}")
            collision_color = None
            try:
                collision_color = parse_material_color(
                    raw_material.get("collision_color", (1.0, 0.0, 0.0, 1.0)),
                    self.COLOR_MODE_SOLID,
                )
            except (TypeError, ValueError) as exc:
                errors.append(f"{context}.collision_color is invalid: {exc}")
            non_collision_color = None
            try:
                non_collision_color = parse_material_color(
                    raw_material.get("non_collision_color", (0.0, 1.0, 0.0, 1.0)),
                    self.COLOR_MODE_SOLID,
                )
            except (TypeError, ValueError) as exc:
                errors.append(f"{context}.non_collision_color is invalid: {exc}")

            try:
                debug_visible = parse_debug_visible(
                    raw_material.get("debug_visible", False)
                )
            except (TypeError, ValueError) as exc:
                errors.append(f"{context}.debug_visible is invalid: {exc}")
                debug_visible = None
            debug_color = None
            try:
                debug_color = parse_material_color(
                    raw_material.get("debug_color"),
                    self.COLOR_MODE_SOLID,
                )
            except (TypeError, ValueError) as exc:
                errors.append(f"{context}.debug_color is invalid: {exc}")

            spectral_response = None
            try:
                spectral_response = parse_spectral_rgb(
                    raw_material.get("spectral_response"),
                    "spectral_response",
                )
            except (TypeError, ValueError) as exc:
                errors.append(f"{context}.spectral_response is invalid: {exc}")

            spectral_emission = None
            try:
                spectral_emission = parse_spectral_rgb(
                    raw_material.get("spectral_emission"),
                    "spectral_emission",
                )
            except (TypeError, ValueError) as exc:
                errors.append(f"{context}.spectral_emission is invalid: {exc}")

            try:
                photon_coupling = float(raw_material.get("photon_coupling", 1.0))
            except (TypeError, ValueError):
                errors.append(f"{context}.photon_coupling must be numeric")
                photon_coupling = None
            if photon_coupling is not None:
                if not math.isfinite(photon_coupling):
                    errors.append(f"{context}.photon_coupling must be finite")
                elif photon_coupling < 0.0 or photon_coupling > 1.0:
                    errors.append(
                        f"{context}.photon_coupling must be between 0.0 and 1.0"
                    )

            try:
                photon_min_relative_mass = float(
                    raw_material.get("photon_min_relative_mass", 0.001)
                )
            except (TypeError, ValueError):
                errors.append(f"{context}.photon_min_relative_mass must be numeric")
                photon_min_relative_mass = None
            if photon_min_relative_mass is not None:
                if not math.isfinite(photon_min_relative_mass):
                    errors.append(f"{context}.photon_min_relative_mass must be finite")
                elif photon_min_relative_mass < 0.0:
                    errors.append(
                        f"{context}.photon_min_relative_mass must not be negative"
                    )

            try:
                photon_surface_behavior = parse_photon_surface_behavior(
                    raw_material.get(
                        "photon_surface_behavior",
                        PHOTON_SURFACE_BEHAVIOR_NONE,
                    )
                )
            except (TypeError, ValueError):
                errors.append(f"{context}.photon_surface_behavior is unknown")
                photon_surface_behavior = None
            if photon_surface_behavior is not None and (
                photon_surface_behavior < PHOTON_SURFACE_BEHAVIOR_NONE
                or photon_surface_behavior > PHOTON_SURFACE_BEHAVIOR_REFLECT
            ):
                errors.append(f"{context}.photon_surface_behavior is outside the valid range")

            try:
                photon_life_time = parse_photon_life_time(
                    raw_material.get(
                        "photon_life_time",
                        PHOTON_LIFE_TIME_PERIODIC,
                    )
                )
            except (TypeError, ValueError):
                errors.append(f"{context}.photon_life_time is unknown")
                photon_life_time = None
            if photon_life_time is not None and (
                photon_life_time < PHOTON_LIFE_TIME_PERIODIC
                or photon_life_time > PHOTON_LIFE_TIME_PERISH
            ):
                errors.append(f"{context}.photon_life_time is outside the valid range")

            try:
                contact_illumination = parse_contact_illumination(
                    raw_material.get(
                        "contact_illumination",
                        CONTACT_ILLUMINATION_MAX,
                    )
                )
            except (TypeError, ValueError):
                errors.append(f"{context}.contact_illumination is unknown")
                contact_illumination = None
            if contact_illumination is not None and (
                contact_illumination < CONTACT_ILLUMINATION_MAX
                or contact_illumination > CONTACT_ILLUMINATION_FIRST
            ):
                errors.append(f"{context}.contact_illumination is outside the valid range")

            if (
                material_id >= 0
                and relative_mass is not None
                and thermal_velocity is not None
                and cell_density is not None
                and color_mode is not None
                and color is not None
                and collision_color is not None
                and non_collision_color is not None
                and start_mom is not None
                and end_mom is not None
                and particle_type is not None
                and debug_visible is not None
                and debug_color is not None
                and spectral_response is not None
                and spectral_emission is not None
                and photon_coupling is not None
                and photon_min_relative_mass is not None
                and photon_surface_behavior is not None
                and photon_life_time is not None
                and contact_illumination is not None
            ):
                materials.append(
                    {
                        "material_id": material_id,
                        "name": name,
                        "particle_type": particle_type,
                        "relative_mass": relative_mass,
                        "thermal_velocity": thermal_velocity,
                        "color_mode": color_mode,
                        "color": color,
                        "start_mom": start_mom,
                        "end_mom": end_mom,
                        "capture_angles": capture_angles,
                        "collision_color": collision_color,
                        "non_collision_color": non_collision_color,
                        "debug_visible": debug_visible,
                        "debug_color": debug_color,
                        "spectral_response": spectral_response,
                        "spectral_emission": spectral_emission,
                        "photon_coupling": photon_coupling,
                        "photon_min_relative_mass": photon_min_relative_mass,
                        "photon_surface_behavior": photon_surface_behavior,
                        "photon_life_time": photon_life_time,
                        "contact_illumination": contact_illumination,
                        "cell_density": cell_density,
                    }
                )
                if color_map is not None:
                    materials[-1]["color_map"] = color_map
                if point_size is not None:
                    materials[-1]["point_size"] = point_size

        if material_count == 0:
            errors.append("material_properties must not be empty")
        if 0 not in material_ids:
            errors.append("material_properties must define material_id 0")

        if len(errors) == initial_error_count:
            self.set_material_properties(materials)
        return materials

    def set_material_properties(self, materials):
        self.material_properties = sorted(
            (dict(material) for material in materials),
            key=lambda material: int(material["material_id"]),
        )
        self.material_properties_by_id = {
            int(material["material_id"]): dict(material)
            for material in self.material_properties
        }

    def validate_simulation_configuration(self):
        errors = []

        def required_values(name, count):
            values = self.itemcfg.get(name)
            if values is None:
                errors.append(f"{name} is required")
                return ()
            if len(values) != count:
                errors.append(f"{name} must contain exactly {count} values")
                return ()
            try:
                result = tuple(float(value) for value in values)
            except (TypeError, ValueError):
                errors.append(f"{name} values must be numeric")
                return ()
            if not all(math.isfinite(value) for value in result):
                errors.append(f"{name} values must be finite")
                return ()
            return result

        dimensions = []
        for name in (
            "cell_array_width",
            "cell_array_height",
            "cell_array_depth",
        ):
            value = self.itemcfg.get(name)
            if not isinstance(value, int) or value <= 0:
                errors.append(f"{name} must be a positive integer")
            else:
                dimensions.append(value)

        particle_data = self.itemcfg.get("PARTICLE_DATA")

        def particle_data_float(name, default):
            source = particle_data if particle_data and hasattr(particle_data, "get") else self.itemcfg
            value = source.get(name, self.itemcfg.get(name, default))
            try:
                result = float(value)
            except (TypeError, ValueError):
                errors.append(f"{name} must be numeric")
                return default
            if not math.isfinite(result):
                errors.append(f"{name} must be finite")
                return default
            return result

        try:
            target_penetration_fraction = float(
                particle_data.get(
                    "target_penetration_fraction",
                    self.itemcfg.get(
                        "target_penetration_fraction",
                        self.itemcfg.get("max_penetration_fraction", 0.5),
                    ),
                )
                if particle_data and hasattr(particle_data, "get")
                else self.itemcfg.get(
                    "target_penetration_fraction",
                    self.itemcfg.get("max_penetration_fraction", 0.5),
                )
            )
        except (TypeError, ValueError):
            errors.append("target_penetration_fraction must be numeric")
            target_penetration_fraction = None

        try:
            hard_penetration_fraction = float(
                particle_data.get(
                    "hard_penetration_fraction",
                    self.itemcfg.get("hard_penetration_fraction", 0.75),
                )
                if particle_data and hasattr(particle_data, "get")
                else self.itemcfg.get("hard_penetration_fraction", 0.75)
            )
        except (TypeError, ValueError):
            errors.append("hard_penetration_fraction must be numeric")
            hard_penetration_fraction = None
        min_compression_frames = particle_data_float("min_compression_frames", 3.0)
        compression_stiffness_gain = particle_data_float(
            "compression_stiffness_gain",
            0.0,
        )
        compression_stiffness_power = particle_data_float(
            "compression_stiffness_power",
            2.0,
        )

        if target_penetration_fraction is not None:
            if not math.isfinite(target_penetration_fraction):
                errors.append("target_penetration_fraction must be finite")
            elif not 0.0 < target_penetration_fraction < 1.0:
                errors.append("target_penetration_fraction must be between 0 and 1")

        if hard_penetration_fraction is not None:
            if not math.isfinite(hard_penetration_fraction):
                errors.append("hard_penetration_fraction must be finite")
            elif not 0.0 < hard_penetration_fraction < 1.0:
                errors.append("hard_penetration_fraction must be between 0 and 1")
        for field_name, field_value in (
            ("min_compression_frames", min_compression_frames),
            ("compression_stiffness_gain", compression_stiffness_gain),
            ("compression_stiffness_power", compression_stiffness_power),
        ):
            if field_value < 0.0:
                errors.append(f"{field_name} must not be negative")

        if (
            target_penetration_fraction is not None
            and hard_penetration_fraction is not None
            and math.isfinite(target_penetration_fraction)
            and math.isfinite(hard_penetration_fraction)
            and hard_penetration_fraction <= target_penetration_fraction
        ):
            errors.append(
                "hard_penetration_fraction must be greater than "
                "target_penetration_fraction"
            )

        death_bounds = required_values("death_bounds", 6)
        if death_bounds:
            for axis, minimum, maximum in (
                ("x", death_bounds[0], death_bounds[1]),
                ("y", death_bounds[2], death_bounds[3]),
                ("z", death_bounds[4], death_bounds[5]),
            ):
                if minimum >= maximum:
                    errors.append(
                        f"death_bounds {axis}_min must be less than {axis}_max"
                    )

        raw_segments = self.itemcfg.get("curve_wall_segments")
        rectangle_raw_segments = self.itemcfg.get("rectangle_wall_segments")
        rectangle_wall_segments, rectangle_errors = parse_keyed_rectangle_wall_segments(
            rectangle_raw_segments
        )
        errors.extend(rectangle_errors)
        if rectangle_wall_segments:
            curve_segments = ()
        else:
            curve_segments, curve_errors = parse_keyed_curve_wall_segments(raw_segments)
            errors.extend(curve_errors)

        particles = []
        if not particle_data:
            errors.append("PARTICLE_DATA is required and must not be empty")
        else:
            try:
                default_particle_material_id = int(particle_data.get("material_id", 0))
            except (TypeError, ValueError):
                errors.append("PARTICLE_DATA.material_id must be an integer")
                default_particle_material_id = 0
            particle_names = sorted(
                (
                    str(key)
                    for key in particle_data.keys()
                    if re.fullmatch(r"p\d+", str(key))
                ),
                key=lambda name: int(name[1:]),
            )
            if not particle_names:
                errors.append("PARTICLE_DATA must define at least one p# particle")
            for name in particle_names:
                particle = particle_data.get(name)
                if particle is None:
                    errors.append(f"PARTICLE_DATA.{name} is required")
                    continue
                try:
                    material_id = int(
                        particle.get("material_id", default_particle_material_id)
                    )
                    raw_mass = particle.get("mass")
                    mass = None if raw_mass is None else float(raw_mass)
                    values = {
                        "name": name,
                        "x": float(particle.location.x1),
                        "y": float(particle.location.y1),
                        "z": float(particle.location.z1),
                        "vx": float(particle.vx),
                        "vy": float(particle.vy),
                        "vz": float(particle.get("vz", 0.0)),
                        "mass": mass,
                        "radius": float(particle.radius),
                        "material_id": material_id,
                        "collision_stiffness_q": float(
                            particle.get(
                                "collision_stiffness_q",
                                particle_data.get(
                                    "collision_stiffness_q",
                                    self.itemcfg.get("collision_stiffness_q", 0.0),
                                ),
                            )
                        ),
                    }
                except (AttributeError, TypeError, ValueError) as error:
                    errors.append(f"PARTICLE_DATA.{name} is invalid: {error}")
                    continue
                numeric_values = (
                    value
                    for key, value in values.items()
                    if key != "name" and value is not None
                )
                if not all(math.isfinite(value) for value in numeric_values):
                    errors.append(f"PARTICLE_DATA.{name} values must be finite")
                if values["radius"] <= 0.0:
                    errors.append(f"PARTICLE_DATA.{name}.radius must be positive")
                if values["mass"] is not None and values["mass"] <= 0.0:
                    errors.append(f"PARTICLE_DATA.{name}.mass must be positive")
                if values["collision_stiffness_q"] < 0.0:
                    errors.append(
                        f"PARTICLE_DATA.{name}.collision_stiffness_q must not be negative"
                    )
                particles.append(values)

        if len(dimensions) == 3:
            width, height, depth = dimensions
            if death_bounds and (
                death_bounds[0] < 0.0
                or death_bounds[1] > width
                or death_bounds[2] < 0.0
                or death_bounds[3] > height
                or death_bounds[4] < 0.0
                or death_bounds[5] > depth
            ):
                errors.append("death_bounds must fit inside the cell array")
            for index, segment in enumerate(curve_segments):
                x_min, x_max, y_min, y_max = wall_bounds(segment)
                if x_min < 0.0 or x_max > width:
                    errors.append(
                        f"curve_wall_segments[{index}] x extent is outside the cell array"
                    )
                if y_min < 0.0 or y_max > height:
                    errors.append(
                        f"curve_wall_segments[{index}] y extent is outside the cell array"
                    )
            for segment in rectangle_wall_segments:
                origin = segment["origin"]
                u_axis = segment["u_axis"]
                v_axis = segment["v_axis"]
                corners = (
                    origin,
                    (
                        origin[0] + u_axis[0] * segment["u_length"],
                        origin[1] + u_axis[1] * segment["u_length"],
                        origin[2] + u_axis[2] * segment["u_length"],
                    ),
                    (
                        origin[0] + v_axis[0] * segment["v_length"],
                        origin[1] + v_axis[1] * segment["v_length"],
                        origin[2] + v_axis[2] * segment["v_length"],
                    ),
                    (
                        origin[0]
                        + u_axis[0] * segment["u_length"]
                        + v_axis[0] * segment["v_length"],
                        origin[1]
                        + u_axis[1] * segment["u_length"]
                        + v_axis[1] * segment["v_length"],
                        origin[2]
                        + u_axis[2] * segment["u_length"]
                        + v_axis[2] * segment["v_length"],
                    ),
                )
                if any(
                    point[0] < 0.0
                    or point[0] > width
                    or point[1] < 0.0
                    or point[1] > height
                    or point[2] < 0.0
                    or point[2] > depth
                    for point in corners
                ):
                    errors.append(
                        f"rectangle_wall_segments.{segment['name']} extent is outside the cell array"
                    )
            for index, particle in enumerate(particles, start=1):
                if not (
                    0.0 <= particle["x"] <= width
                    and 0.0 <= particle["y"] <= height
                    and 0.0 <= particle["z"] <= depth
                ):
                    errors.append(
                        f"PARTICLE_DATA.p{index} position is outside the cell array"
                    )

        self.validate_material_properties(errors)
        for retired_key in RETIRED_BOUNDARY_LIGHTING_CONFIG_KEYS:
            if retired_key in self.itemcfg:
                errors.append(
                    f"{retired_key} is retired; use boundary_space_lighting_enabled"
                )
        try:
            boundary_space_lighting_enabled = self.itemcfg.get(
                "boundary_space_lighting_enabled",
                False,
            )
            if not isinstance(boundary_space_lighting_enabled, bool):
                errors.append("boundary_space_lighting_enabled must be a boolean")
        except (TypeError, ValueError):
            boundary_space_lighting_enabled = False
            errors.append("boundary_space_lighting_enabled must be a boolean")

        try:
            photon_periodic_recycle_enabled = self.itemcfg.get(
                "photon_periodic_recycle_enabled",
                False,
            )
            if not isinstance(photon_periodic_recycle_enabled, bool):
                errors.append("photon_periodic_recycle_enabled must be a boolean")
        except (TypeError, ValueError):
            errors.append("photon_periodic_recycle_enabled must be a boolean")

        if boundary_space_lighting_enabled:
            if self.itemcfg.get("Lighting_ball") is None:
                errors.append(
                    "Lighting_ball is required when boundary_space_lighting_enabled is true"
                )

        known_material_ids = set(self.material_properties_by_id)
        for segment in rectangle_wall_segments:
            material_id = int(segment.get("material_id", 0))
            if material_id not in known_material_ids:
                errors.append(
                    f"rectangle_wall_segments.{segment['name']}.material_id is not defined"
                )
        for index, particle in enumerate(particles, start=1):
            material_id = particle.get("material_id", 0)
            if material_id not in known_material_ids:
                errors.append(
                    f"PARTICLE_DATA.p{index}.material_id is not defined"
                )
            elif particle["mass"] is None:
                particle["mass"] = float(
                    self.material_properties_by_id[material_id]["relative_mass"]
                )

        if errors:
            raise ValueError(
                "GenericGenData configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )

        self.cell_array_width, self.cell_array_height, self.cell_array_depth = dimensions
        self.death_bounds = death_bounds
        self.curve_wall_segments = curve_segments
        self.rectangle_wall_segments = rectangle_wall_segments
        self.explicit_particles = particles
        self.number_configured_particles = len(particles)
        self.particle_plane_z = particles[0]["z"]
        self.radius = float(self.itemcfg.radius)
        self.wall_contact_offset = float(self.itemcfg.wall_contact_offset)
        self.dt = float(self.itemcfg.dt)
        self.cell_occupancy_list_size = int(self.itemcfg.cell_occupancy_list_size)
        self.boundary_space_lighting_enabled = bool(boundary_space_lighting_enabled)
        self.target_penetration_fraction = target_penetration_fraction
        self.hard_penetration_fraction = hard_penetration_fraction
        self.min_compression_frames = min_compression_frames
        self.compression_stiffness_gain = compression_stiffness_gain
        self.compression_stiffness_power = compression_stiffness_power
        return True

    def report_collision_feasibility(self):
        """Print a kinematic collision timing estimate for configured particles."""
        if len(self.explicit_particles) < 2:
            report_text = "Collision Feasibility: fewer than two mobile particles"
            print(report_text)
            self.write_validation_log(report_text)
            return []

        dt = float(self.dt)
        target_penetration_fraction = self.target_penetration_fraction
        hard_penetration_fraction = self.hard_penetration_fraction
        min_compression_frames = self.min_compression_frames
        compression_stiffness_gain = max(0.0, self.compression_stiffness_gain)
        compression_stiffness_power = max(0.0, self.compression_stiffness_power)
        reports = []

        lines = [
            "Collision Feasibility:",
            f"  minimum compression frames: {min_compression_frames:.3f}",
        ]
        for source_index, source in enumerate(self.explicit_particles):
            for target in self.explicit_particles[source_index + 1 :]:
                dx = target["x"] - source["x"]
                dy = target["y"] - source["y"]
                dz = target["z"] - source["z"]
                center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
                if center_distance <= 1.0e-12:
                    normal_x, normal_y, normal_z = 1.0, 0.0, 0.0
                else:
                    normal_x = dx / center_distance
                    normal_y = dy / center_distance
                    normal_z = dz / center_distance

                relative_velocity_x = source["vx"] - target["vx"]
                relative_velocity_y = source["vy"] - target["vy"]
                relative_velocity_z = source["vz"] - target["vz"]
                relative_normal_speed = (
                    relative_velocity_x * normal_x
                    + relative_velocity_y * normal_y
                    + relative_velocity_z * normal_z
                )

                contact_distance = source["radius"] + target["radius"]
                initial_gap = center_distance - contact_distance
                per_frame_closing_distance = max(0.0, relative_normal_speed) * dt
                target_penetration_depth = (
                    target_penetration_fraction * source["radius"]
                )
                hard_penetration_depth = (
                    hard_penetration_fraction * source["radius"]
                )
                if target_penetration_depth > 0.0:
                    target_depth_step_fraction = (
                        per_frame_closing_distance / target_penetration_depth
                    )
                else:
                    target_depth_step_fraction = math.inf
                if hard_penetration_depth > 0.0:
                    hard_depth_step_fraction = (
                        per_frame_closing_distance / hard_penetration_depth
                    )
                else:
                    hard_depth_step_fraction = math.inf

                if initial_gap <= 0.0:
                    frames_to_first_contact = 0.0
                elif per_frame_closing_distance > 0.0:
                    frames_to_first_contact = initial_gap / per_frame_closing_distance
                else:
                    frames_to_first_contact = math.inf

                if per_frame_closing_distance > 0.0:
                    frames_to_target_depth = (
                        target_penetration_depth / per_frame_closing_distance
                    )
                    frames_to_hard_depth = (
                        hard_penetration_depth / per_frame_closing_distance
                    )
                else:
                    frames_to_target_depth = math.inf
                    frames_to_hard_depth = math.inf
                time_to_first_contact = frames_to_first_contact * dt
                time_to_target_depth = frames_to_target_depth * dt
                time_to_hard_depth = frames_to_hard_depth * dt

                stiffness_at_contact = min(
                    source["collision_stiffness_q"],
                    target["collision_stiffness_q"],
                )
                if (
                    compression_stiffness_gain > 0.0
                    and hard_penetration_depth > 0.0
                ):
                    target_compression_fraction = max(
                        0.0,
                        min(1.0, target_penetration_depth / hard_penetration_depth),
                    )
                    hard_compression_fraction = 1.0
                    effective_stiffness_at_target = stiffness_at_contact * (
                        1.0
                        + compression_stiffness_gain
                        * (target_compression_fraction ** compression_stiffness_power)
                    )
                    effective_stiffness_at_hard = stiffness_at_contact * (
                        1.0
                        + compression_stiffness_gain
                        * (hard_compression_fraction ** compression_stiffness_power)
                    )
                else:
                    effective_stiffness_at_target = stiffness_at_contact
                    effective_stiffness_at_hard = stiffness_at_contact
                force_at_target_depth = (
                    effective_stiffness_at_target * target_penetration_depth
                )
                source_dv_per_frame_at_max = (
                    force_at_target_depth / source["mass"]
                ) * dt
                target_dv_per_frame_at_max = (
                    force_at_target_depth / target["mass"]
                ) * dt
                relative_dv_per_frame_at_max = (
                    source_dv_per_frame_at_max + target_dv_per_frame_at_max
                )
                response_mass_factor = (1.0 / source["mass"]) + (
                    1.0 / target["mass"]
                )
                if (
                    relative_normal_speed > 0.0
                    and frames_to_target_depth > 0.0
                    and math.isfinite(frames_to_target_depth)
                    and target_penetration_depth > 0.0
                    and dt > 0.0
                    and response_mass_factor > 0.0
                ):
                    required_stiffness_for_max_depth = relative_normal_speed / (
                        frames_to_target_depth
                        * target_penetration_depth
                        * dt
                        * response_mass_factor
                    )
                else:
                    required_stiffness_for_max_depth = 0.0
                if relative_normal_speed <= 0.0:
                    frames_to_cancel_relative_speed = 0.0
                elif relative_dv_per_frame_at_max > 0.0:
                    frames_to_cancel_relative_speed = (
                        relative_normal_speed / relative_dv_per_frame_at_max
                    )
                else:
                    frames_to_cancel_relative_speed = math.inf
                time_to_cancel_relative_speed = (
                    frames_to_cancel_relative_speed * dt
                )

                if relative_normal_speed <= 0.0:
                    status = "OPENING"
                elif frames_to_hard_depth < 1.0:
                    status = "ERROR"
                elif frames_to_target_depth < min_compression_frames:
                    status = "WARNING"
                elif frames_to_cancel_relative_speed > frames_to_target_depth:
                    status = "WARNING_STIFFNESS"
                else:
                    status = "OK"

                lines.extend(
                    [
                        f"  source pair: {source['name']} -> {target['name']}",
                        f"  initial gap: {initial_gap:.6f}",
                        "  relative normal speed: "
                        f"{max(0.0, relative_normal_speed):.6f}",
                        "  per-frame closing distance: "
                        f"{per_frame_closing_distance:.6f}",
                        "  frames to first contact: "
                        f"{frames_to_first_contact:.3f}",
                        "  time to first contact: "
                        f"{time_to_first_contact:.6f}",
                        "  target penetration depth: "
                        f"{target_penetration_depth:.6f}",
                        "  hard penetration depth: "
                        f"{hard_penetration_depth:.6f}",
                        "  target-depth step fraction: "
                        f"{target_depth_step_fraction:.6f}",
                        "  hard-depth step fraction: "
                        f"{hard_depth_step_fraction:.6f}",
                        "  frames from contact to target depth: "
                        f"{frames_to_target_depth:.3f}",
                        "  time from contact to target depth: "
                        f"{time_to_target_depth:.6f}",
                        "  frames from contact to hard depth: "
                        f"{frames_to_hard_depth:.3f}",
                        "  time from contact to hard depth: "
                        f"{time_to_hard_depth:.6f}",
                        "  stiffness at contact: "
                        f"{stiffness_at_contact:.6f}",
                        "  compression stiffness gain: "
                        f"{compression_stiffness_gain:.6f}",
                        "  compression stiffness power: "
                        f"{compression_stiffness_power:.6f}",
                        "  effective stiffness at target depth: "
                        f"{effective_stiffness_at_target:.6f}",
                        "  effective stiffness at hard depth: "
                        f"{effective_stiffness_at_hard:.6f}",
                        "  force at target depth: "
                        f"{force_at_target_depth:.6f}",
                        "  source dv/frame at max: "
                        f"{source_dv_per_frame_at_max:.6f}",
                        "  target dv/frame at max: "
                        f"{target_dv_per_frame_at_max:.6f}",
                        "  relative dv/frame at max: "
                        f"{relative_dv_per_frame_at_max:.6f}",
                        "  frames to cancel relative speed: "
                        f"{frames_to_cancel_relative_speed:.3f}",
                        "  time to cancel relative speed: "
                        f"{time_to_cancel_relative_speed:.6f}",
                        "  required stiffness for max-depth response: "
                        f"{required_stiffness_for_max_depth:.6f}",
                        f"  status: {status}",
                    ]
                )

                reports.append(
                    {
                        "source": source["name"],
                        "target": target["name"],
                        "initial_gap": initial_gap,
                        "relative_normal_speed": relative_normal_speed,
                        "per_frame_closing_distance": per_frame_closing_distance,
                        "frames_to_first_contact": frames_to_first_contact,
                        "time_to_first_contact": time_to_first_contact,
                        "target_penetration_depth": target_penetration_depth,
                        "hard_penetration_depth": hard_penetration_depth,
                        "target_depth_step_fraction": target_depth_step_fraction,
                        "hard_depth_step_fraction": hard_depth_step_fraction,
                        "frames_to_target_depth": frames_to_target_depth,
                        "time_to_target_depth": time_to_target_depth,
                        "frames_to_hard_depth": frames_to_hard_depth,
                        "time_to_hard_depth": time_to_hard_depth,
                        "stiffness_at_contact": stiffness_at_contact,
                        "compression_stiffness_gain": compression_stiffness_gain,
                        "compression_stiffness_power": compression_stiffness_power,
                        "effective_stiffness_at_target": effective_stiffness_at_target,
                        "effective_stiffness_at_hard": effective_stiffness_at_hard,
                        "force_at_target_depth": force_at_target_depth,
                        "source_dv_per_frame_at_max": source_dv_per_frame_at_max,
                        "target_dv_per_frame_at_max": target_dv_per_frame_at_max,
                        "relative_dv_per_frame_at_max": relative_dv_per_frame_at_max,
                        "frames_to_cancel_relative_speed": frames_to_cancel_relative_speed,
                        "time_to_cancel_relative_speed": time_to_cancel_relative_speed,
                        "required_stiffness_for_max_depth": required_stiffness_for_max_depth,
                        "status": status,
                    }
                )

        report_text = "\n".join(lines)
        print(report_text)
        self.write_validation_log(report_text)
        return reports

    def initialize_generation(self):
        self.p_list = []
        self.bin_file = None
        self.count = 0
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0
        self.boundary_space_proxy_metadata = {}
        self.lighting_surface_triangle_inventory = ()
        self.configure_output_paths(delete_stale=True)

    def configure_output_paths(self, delete_stale=False):
        output_prefix = str(
            self.itemcfg.get("output_file_prefix", self.itemcfg.STUDY_NAME)
        )
        output_directory = str(self.itemcfg.data_dir)
        os.makedirs(output_directory, exist_ok=True)
        self.test_bin_name = os.path.join(output_directory, f"{output_prefix}.bin")
        self.test_file_name = os.path.join(output_directory, f"{output_prefix}.tst")
        self.report_file = os.path.join(output_directory, f"{output_prefix}.rpt")
        self.validation_log_name = os.path.join(output_directory, f"{output_prefix}.log")
        if delete_stale:
            self.delete_stale_generated_outputs()
        with open(self.validation_log_name, "w", encoding="ascii", newline="\n") as output:
            output.write(
                "Function-wall particle validation log\n"
                f"  output prefix: {output_prefix}\n"
            )
        configured_obj_file = self.itemcfg.get("obj_file_name")
        if configured_obj_file:
            self.obj_file_name = os.path.normpath(str(configured_obj_file))
        else:
            self.obj_file_name = os.path.join(
                output_directory,
                f"{output_prefix}.obj",
            )
        self.surface_sphere_obj_name = os.path.join(
            output_directory,
            f"{output_prefix}_sphere.obj",
        )
        self.surface_wall_obj_name = os.path.join(
            output_directory,
            f"{output_prefix}_wall.obj",
        )
        self.surface_combined_obj_name = os.path.join(
            output_directory,
            f"{output_prefix}_surfaces.obj",
        )
        self.surface_object_obj_names = {}
        for surface_object in self.itemcfg.get("lighting_surface_objects", ()):
            object_name = str(surface_object.get("name", "surface"))
            object_slug = re.sub(r"[^A-Za-z0-9_]+", "_", object_name).strip("_")
            if not object_slug:
                object_slug = "surface"
            surface_id = int(surface_object.get("surface_id", 0))
            self.surface_object_obj_names[object_name] = os.path.join(
                output_directory,
                f"{output_prefix}_{object_slug}_{surface_id}.obj",
            )

    def delete_stale_generated_outputs(self):
        removed_paths = []
        for path in (self.test_bin_name, self.test_file_name):
            if not os.path.exists(path):
                continue
            os.remove(path)
            removed_paths.append(path)
        if removed_paths:
            print("Deleted stale generated output(s):")
            for path in removed_paths:
                print(f"  {path}")

    def write_validation_log(self, text):
        with open(self.validation_log_name, "a", encoding="ascii", newline="\n") as output:
            output.write(text.rstrip())
            output.write("\n")

    def write_color_mode_defines(self, output):
        write_color_mode_defines(output)

    def write_material_properties(self, output):
        write_material_properties(output, {"material_properties": self.material_properties})

    def write_reflecting_wall_light_map(self, output):
        light_map = self.itemcfg.get("reflecting_wall_light_map")
        if light_map is None:
            return

        output.write("reflecting_wall_light_map = {\n")
        output.write(
            "    enabled = "
            f"{'true' if light_map.get('enabled', False) else 'false'};\n"
        )
        output.write(
            "    surface_id = "
            f"{int(light_map.get('surface_id', 0))};\n"
        )
        output.write(
            "    width = "
            f"{int(light_map.get('width', 1))};\n"
        )
        output.write(
            "    height = "
            f"{int(light_map.get('height', 1))};\n"
        )
        if "splat_capacity" in light_map:
            output.write(
                "    splat_capacity = "
                f"{int(light_map.get('splat_capacity', 1))};\n"
            )
        if "splat_radius" in light_map:
            output.write(
                "    splat_radius = "
                f"{float(light_map.get('splat_radius', 10.0))};\n"
            )
        if "splat_alpha" in light_map:
            output.write(
                "    splat_alpha = "
                f"{float(light_map.get('splat_alpha', 0.06))};\n"
            )
        if "glass_tint" in light_map:
            tint = light_map.get("glass_tint", [0.08, 0.12, 0.14, 0.35])
            output.write(
                "    glass_tint = "
                f"[{float(tint[0])}, {float(tint[1])}, "
                f"{float(tint[2])}, {float(tint[3])}];\n"
            )
        if "reflection_gain" in light_map:
            output.write(
                "    reflection_gain = "
                f"{float(light_map.get('reflection_gain', 1.5))};\n"
            )
        if "fresnel_strength" in light_map:
            output.write(
                "    fresnel_strength = "
                f"{float(light_map.get('fresnel_strength', 0.25))};\n"
            )
        output.write("};\n")

    def add_null_particle(self):
        particle = pdata()
        particle.pnum = 0
        particle.ptype = PTYPE_NULL
        particle.material_id = 0.0
        self.p_list.append(particle)
        return particle

    def register_boundary_space_proxy(
        self,
        particle_id,
        surface_type,
        surface_id,
        material_id,
        normal,
    ):
        self.boundary_space_proxy_metadata[int(particle_id)] = {
            "surface_type": int(surface_type),
            "surface_id": int(surface_id),
            "material_id": int(material_id),
            "normal": tuple(float(value) for value in normal),
        }

    def boundary_space_first_particle_id(self):
        if not self.boundary_space_proxy_metadata:
            return 0
        return min(int(particle_id) for particle_id in self.boundary_space_proxy_metadata)

    def boundary_space_last_particle_id(self):
        if not self.boundary_space_proxy_metadata:
            return 0
        return max(int(particle_id) for particle_id in self.boundary_space_proxy_metadata)

    def boundary_space_proxy_count(self):
        return len(self.boundary_space_proxy_metadata)

    def boundary_space_proxy_ids_are_contiguous(self):
        proxy_count = self.boundary_space_proxy_count()
        if proxy_count <= 0:
            return True
        return (
            self.boundary_space_last_particle_id()
            - self.boundary_space_first_particle_id()
            + 1
            == proxy_count
        )

    def validate_boundary_space_proxy_packing(self):
        if not self.boundary_space_lighting_enabled:
            return
        if not self.boundary_space_proxy_ids_are_contiguous():
            raise ValueError(
                "boundary-space proxy particle ids must be contiguous for Vulkan "
                "subtraction indexing"
            )

    def add_mobile_particle(
        self,
        position,
        velocity,
        radius=None,
        mass=None,
        material_id=0,
        collision_stiffness_q=None,
        ptype=None,
    ):
        material_id = int(material_id)
        if material_id not in self.material_properties_by_id:
            raise ValueError(f"material_id {material_id} is not defined")
        if mass is None:
            mass = float(self.material_properties_by_id[material_id]["relative_mass"])
        if ptype is None:
            material_particle_type = int(
                self.material_properties_by_id[material_id].get("particle_type", 0)
            )
            ptype = self.pdata_ptype_for_particle_type(material_particle_type)
        particle = pdata()
        self.number_particles += 1
        self.number_active_particles += 1
        particle.pnum = self.number_particles
        particle.ptype = float(ptype)
        particle.material_id = float(material_id)
        particle.rx, particle.ry, particle.rz = position
        particle.vx, particle.vy, particle.vz = velocity
        particle.radius = self.radius if radius is None else radius
        particle.molar_mass = float(mass)
        particle.state_flg = 0.0
        particle.collision_stiffness_q = (
            float(self.itemcfg.get("collision_stiffness_q", 0.0))
            if collision_stiffness_q is None
            else collision_stiffness_q
        )
        self.p_list.append(particle)
        return particle

    @staticmethod
    def pdata_ptype_for_particle_type(particle_type):
        particle_type = int(particle_type)
        if particle_type == PARTICLE_TYPE_PHOTON:
            return PTYPE_PHOTON
        if particle_type == PARTICLE_TYPE_REFLECTION_PHOTON:
            return PTYPE_REFLECTION_PHOTON
        if particle_type == PARTICLE_TYPE_BOUNDARY:
            return PTYPE_BOUNDARY
        return PTYPE_MOBILE

    def add_explicit_mobile_particles(self):
        """Create the mobile particles declared by PARTICLE_DATA."""
        for configured in self.explicit_particles:
            self.add_mobile_particle(
                (configured["x"], configured["y"], configured["z"]),
                (configured["vx"], configured["vy"], configured["vz"]),
                radius=configured["radius"],
                mass=configured["mass"],
                material_id=configured.get("material_id", 0),
                collision_stiffness_q=configured["collision_stiffness_q"],
            )

        if self.number_active_particles != self.number_configured_particles:
            raise RuntimeError(
                "generated mobile-particle count does not match PARTICLE_DATA"
            )
        return self.number_active_particles

    def add_boundary_particle(self, position, material_id=0):
        material_id = int(material_id)
        if material_id not in self.material_properties_by_id:
            raise ValueError(f"boundary material_id {material_id} is not defined")
        particle = pdata()
        self.number_particles += 1
        self.number_boundary_particles += 1
        particle.pnum = self.number_particles
        particle.ptype = self.BOUNDARY_PARTICLE_PTYPE
        particle.material_id = float(material_id)
        particle.rx, particle.ry, particle.rz = position
        particle.vx = 0.0
        particle.vy = 0.0
        particle.vz = 0.0
        particle.radius = self.radius
        particle.molar_mass = float(
            self.material_properties_by_id[material_id]["relative_mass"]
        )
        particle.state_flg = 0.0
        particle.collision_stiffness_q = 0.0
        self.p_list.append(particle)
        return particle

    def curve_marker_points(self, segment, maximum_spacing=1.0):
        """Return sampled points used only for boundary-sentinel placement."""
        return sample_points(segment, maximum_spacing)

    def add_function_wall_markers(self):
        """Create deduplicated boundary-sentinel markers along wall segments."""
        marker_cells = set()
        segment_marker_counts = []

        for segment in self.curve_wall_segments:
            wall_flag = int(round(segment[9]))
            material_id = int(round(segment_values(segment)[10]))
            points = self.curve_marker_points(segment)
            added_for_segment = 0
            for marker_x, marker_y in points:
                evaluation = evaluate_wall_at_point(segment, (marker_x, marker_y))
                if evaluation is None:
                    continue
                normal_x, normal_y = evaluation["normal"]
                cell_x = round(marker_x)
                cell_y = round(marker_y)
                cell_z = int(math.floor(self.particle_plane_z))
                marker_cell_key = (
                    cell_x,
                    cell_y,
                    cell_z,
                    wall_flag,
                )
                if marker_cell_key in marker_cells:
                    continue
                marker_cells.add(marker_cell_key)
                particle = self.add_boundary_particle(
                    (float(cell_x), float(cell_y), float(cell_z)),
                    material_id=material_id,
                )
                self.register_boundary_space_proxy(
                    particle.pnum,
                    BOUNDARY_SPACE_SURFACE_RECTANGLE_WALL,
                    wall_flag,
                    material_id,
                    (normal_x, normal_y, 0.0),
                )
                added_for_segment += 1
            segment_marker_counts.append(added_for_segment)

        report_text = (
            "Function wall-marker report:\n"
            f"  curve segments: {len(self.curve_wall_segments)}\n"
            f"  unique boundary markers: {self.number_boundary_particles}\n"
            f"  boundary ptype: {self.BOUNDARY_PARTICLE_PTYPE:g}\n"
            f"  markers added per segment: {segment_marker_counts}\n"
            "  occupancy rule: boundary markers are cell-locality sentinels\n"
            "  marker position: integer cell center\n"
            "  maximum sampled function interval: 1 cell"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.number_boundary_particles

    def rectangle_marker_points(self, segment):
        """Return sampled integer-cell points for one rectangle wall patch."""
        origin = segment["origin"]
        u_axis = segment["u_axis"]
        v_axis = segment["v_axis"]
        u_steps = max(1, int(math.floor(segment["u_length"])) + 1)
        v_steps = max(1, int(math.floor(segment["v_length"])) + 1)
        points = []
        for u_index in range(u_steps):
            for v_index in range(v_steps):
                points.append(
                    (
                        origin[0] + u_axis[0] * u_index + v_axis[0] * v_index,
                        origin[1] + u_axis[1] * u_index + v_axis[1] * v_index,
                        origin[2] + u_axis[2] * u_index + v_axis[2] * v_index,
                    )
                )
        return points

    def add_rectangle_wall_markers(self):
        """Create deduplicated boundary-sentinel markers on rectangle walls."""
        marker_cells = set()
        segment_marker_counts = []

        for segment in self.rectangle_wall_segments:
            wall_flag = int(segment["wall_flag"])
            material_id = int(segment.get("material_id", 0))
            added_for_segment = 0
            for marker_x, marker_y, marker_z in self.rectangle_marker_points(segment):
                cell_x = round(marker_x)
                cell_y = round(marker_y)
                cell_z = round(marker_z)
                marker_cell_key = (
                    cell_x,
                    cell_y,
                    cell_z,
                    wall_flag,
                )
                if marker_cell_key in marker_cells:
                    continue
                marker_cells.add(marker_cell_key)
                self.add_boundary_particle(
                    (float(cell_x), float(cell_y), float(cell_z)),
                    material_id=material_id,
                )
                added_for_segment += 1
            segment_marker_counts.append(added_for_segment)

        report_text = (
            "Rectangle wall-marker report:\n"
            f"  rectangle segments: {len(self.rectangle_wall_segments)}\n"
            f"  unique boundary markers: {self.number_boundary_particles}\n"
            f"  boundary ptype: {self.BOUNDARY_PARTICLE_PTYPE:g}\n"
            f"  markers added per segment: {segment_marker_counts}\n"
            "  occupancy rule: boundary markers are cell-locality sentinels\n"
            "  marker position: integer cell center\n"
            "  maximum sampled rectangle interval: 1 cell"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.number_boundary_particles

    def add_configured_wall_markers(self):
        """Create boundary markers for the active wall model."""
        if self.rectangle_wall_segments:
            return self.add_rectangle_wall_markers()
        return self.add_function_wall_markers()

    def report_boundary_space_lighting(self):
        report_text = (
            "Boundary-space lighting report:\n"
            f"  enabled: {self.boundary_space_lighting_enabled}\n"
            f"  proxies: {self.boundary_space_proxy_count()}\n"
            f"  first particle id: {self.boundary_space_first_particle_id()}\n"
            f"  last particle id: {self.boundary_space_last_particle_id()}\n"
            f"  contiguous ids: {self.boundary_space_proxy_ids_are_contiguous()}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.boundary_space_proxy_count()

    def report_scene_model_toggles(self):
        disabled_objects = tuple(
            self.itemcfg.get("_scene_model_disabled_objects", ())
        )
        if not disabled_objects:
            return 0
        report_lines = ["Scene model toggle report:"]
        for object_name in disabled_objects:
            report_lines.extend(
                (
                    f"  object: {object_name}",
                    "    status: disabled",
                    "    derived geometry: none",
                )
            )
        report_text = "\n".join(report_lines)
        print(report_text)
        self.write_validation_log(report_text)
        return len(disabled_objects)

    def write_boundary_space_lighting(self, output):
        self.validate_boundary_space_proxy_packing()
        output.write(
            "boundary_space_lighting_enabled = "
            f"{'true' if self.boundary_space_lighting_enabled else 'false'};\n"
        )
        if not self.boundary_space_lighting_enabled:
            return
        output.write(
            f"boundary_space_proxy_count = {self.boundary_space_proxy_count()};\n"
        )
        output.write(
            "boundary_space_first_particle_id = "
            f"{self.boundary_space_first_particle_id()};\n"
        )

    def write_function_wall_obj(self):
        """Write triangle ribbons sampled from function-wall paths."""
        half_thickness = 0.25
        vertices = []
        vertex_colors = []
        wall_faces = []
        piston_faces = []

        for segment in self.curve_wall_segments:
            boundary_visual_material_id = int(round(segment_values(segment)[11]))
            boundary_visual_color = self._material_color_by_id(
                boundary_visual_material_id
            ) or (1.0, 1.0, 1.0, 1.0)
            points = self.curve_marker_points(segment)
            segment_vertices = []

            for point_index, (point_x, point_y) in enumerate(points):
                if len(points) == 1:
                    tangent_x, tangent_y = 1.0, 0.0
                elif point_index == 0:
                    next_x, next_y = points[point_index + 1]
                    tangent_x = next_x - point_x
                    tangent_y = next_y - point_y
                else:
                    previous_x, previous_y = points[point_index - 1]
                    tangent_x = point_x - previous_x
                    tangent_y = point_y - previous_y
                tangent_length = math.hypot(tangent_x, tangent_y)
                if tangent_length <= 1.0e-12:
                    raise RuntimeError(
                        "cannot generate OBJ ribbon from a zero-length wall sample"
                    )

                normal_x = -tangent_y / tangent_length
                normal_y = tangent_x / tangent_length
                first_index = len(vertices) + 1
                vertices.append(
                    (
                        point_x + half_thickness * normal_x,
                        point_y + half_thickness * normal_y,
                        self.particle_plane_z,
                    )
                )
                vertex_colors.append(boundary_visual_color)
                vertices.append(
                    (
                        point_x - half_thickness * normal_x,
                        point_y - half_thickness * normal_y,
                        self.particle_plane_z,
                    )
                )
                vertex_colors.append(boundary_visual_color)
                segment_vertices.append((first_index, first_index + 1))

            for index in range(len(segment_vertices) - 1):
                outer_a, inner_a = segment_vertices[index]
                outer_b, inner_b = segment_vertices[index + 1]
                wall_faces.append(
                    ((outer_a, outer_b, inner_b), boundary_visual_material_id)
                )
                wall_faces.append(
                    ((outer_a, inner_b, inner_a), boundary_visual_material_id)
                )

        piston_faces.extend(self._append_piston_visual_obj(vertices))

        os.makedirs(os.path.dirname(self.obj_file_name), exist_ok=True)
        mtl_file_name = os.path.splitext(self.obj_file_name)[0] + ".mtl"
        mtl_base_name = os.path.basename(mtl_file_name)
        material_ids = sorted({material_id for _face, material_id in wall_faces})
        with open(mtl_file_name, "w", encoding="ascii", newline="\n") as output:
            output.write("# Generated from function-wall boundary_visual_material_id.\n")
            for material_id in material_ids:
                color = self._material_color_by_id(material_id) or (1.0, 1.0, 1.0, 1.0)
                output.write(
                    f"newmtl {self._material_name_for_obj('boundary', material_id)}\n"
                )
                output.write(
                    f"Kd {color[0]:.9f} {color[1]:.9f} {color[2]:.9f}\n"
                )
                output.write(f"d {color[3]:.9f}\n")
        with open(self.obj_file_name, "w", encoding="ascii", newline="\n") as output:
            output.write("# Generated from function-wall curve_wall_segments.\n")
            output.write("# Dynamics use boundary particles; this mesh is visual only.\n")
            output.write(f"mtllib {mtl_base_name}\n")
            for vertex_index, (vertex_x, vertex_y, vertex_z) in enumerate(vertices):
                color = (
                    vertex_colors[vertex_index]
                    if vertex_index < len(vertex_colors)
                    else (1.0, 1.0, 1.0, 1.0)
                )
                output.write(
                    f"v {vertex_x:.9f} {vertex_y:.9f} {vertex_z:.9f} "
                    f"{color[0]:.9f} {color[1]:.9f} {color[2]:.9f}\n"
                )
            for _ in vertices:
                output.write("vt 0.0 0.0\n")
            output.write("vn 0.0 0.0 1.0\n")
            output.write("vn 0.0 0.0 -1.0\n")
            output.write("o GeneratedFunctionWalls\n")
            current_material_id = None
            for (first, second, third), material_id in wall_faces:
                if material_id != current_material_id:
                    output.write(
                        f"usemtl {self._material_name_for_obj('boundary', material_id)}\n"
                    )
                    current_material_id = material_id
                output.write(
                    f"f {first}/{first}/1 {second}/{second}/1 {third}/{third}/1\n"
                )
                output.write(
                    f"f {third}/{third}/2 {second}/{second}/2 {first}/{first}/2\n"
                )
            if piston_faces:
                output.write("o PistonVisual\n")
                for first, second, third in piston_faces:
                    output.write(
                        f"f {first}/{first}/1 {second}/{second}/1 {third}/{third}/1\n"
                    )
                    output.write(
                        f"f {third}/{third}/2 {second}/{second}/2 {first}/{first}/2\n"
                    )

        report_text = (
            "Function wall OBJ report:\n"
            f"  file: {self.obj_file_name}\n"
            f"  vertices: {len(vertices)}\n"
            f"  wall triangles: {2 * len(wall_faces)}\n"
            f"  piston visual triangles: {2 * len(piston_faces)}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.obj_file_name

    def _append_piston_visual_obj(self, vertices):
        piston_visual = self.itemcfg.get("piston_visual")
        if (
            not piston_visual
            or not piston_visual.get("enabled", False)
            or not piston_visual.get("write_to_obj", False)
        ):
            return []

        x = float(getattr(self, "piston_x_start", piston_visual.get("x", 0.0)))
        y_min = float(
            piston_visual.get(
                "y_min",
                getattr(self, "packing_bounds", (0.0, 0.0, 0.0, 0.0))[2],
            )
        )
        y_max = float(
            piston_visual.get(
                "y_max",
                getattr(self, "packing_bounds", (0.0, 0.0, 0.0, 0.0))[3],
            )
        )
        x_thickness = float(piston_visual.get("x_thickness", 1.0))
        z = float(piston_visual.get("z", getattr(self, "particle_plane_z", 0.5)))
        if y_min >= y_max:
            raise ValueError("piston_visual.y_min must be less than y_max")
        if x_thickness <= 0.0:
            raise ValueError("piston_visual.x_thickness must be positive")

        x_min = x - 0.5 * x_thickness
        x_max = x + 0.5 * x_thickness
        first_index = len(vertices) + 1
        vertices.extend(
            (
                (x_min, y_min, z),
                (x_max, y_min, z),
                (x_max, y_max, z),
                (x_min, y_max, z),
            )
        )
        return [
            (first_index, first_index + 1, first_index + 2),
            (first_index, first_index + 2, first_index + 3),
        ]

    def generate_model_obj(self):
        """Generate only the editable/visual model OBJ for the current config."""
        self.validate_simulation_configuration()
        self.configure_output_paths(delete_stale=False)
        return self.write_function_wall_obj()

    def _lighting_ball_values(self):
        lighting_ball = self.itemcfg.get("Lighting_ball")
        if lighting_ball is None:
            return None
        if not hasattr(lighting_ball, "get"):
            if len(lighting_ball) < 4:
                raise ValueError("Lighting_ball must contain x, y, z, and radius")
            return {
                "name": "lighting_sphere",
                "center": (
                    float(lighting_ball[0]),
                    float(lighting_ball[1]),
                    float(lighting_ball[2]),
                ),
                "radius": float(lighting_ball[3]),
                "material_id": int(lighting_ball[4]) if len(lighting_ball) >= 5 else 0,
                "surface_id": int(self.itemcfg.get("lighting_ball_wall_flag", 1000)),
            }
        return {
            "name": "lighting_sphere",
            "center": (
                float(lighting_ball.get("x")),
                float(lighting_ball.get("y")),
                float(lighting_ball.get("z")),
            ),
            "radius": float(lighting_ball.get("radius")),
            "material_id": int(lighting_ball.get("material_id", 0)),
            "surface_id": int(lighting_ball.get("wall_flag", 1000)),
        }

    def _surface_obj_add_vertex(self, obj_data, position, normal, texcoord):
        obj_data["vertices"].append(position)
        obj_data["normals"].append(normal)
        obj_data["texcoords"].append(texcoord)
        return len(obj_data["vertices"])

    def _lighting_surface_object_by_type_and_id(self, surface_type, surface_id):
        requested_type = str(surface_type).upper()
        requested_id = int(surface_id)
        for surface_object in self.itemcfg.get("lighting_surface_objects", ()):
            if (
                str(surface_object.get("surface_type", "")).upper() == requested_type
                and int(surface_object.get("surface_id", -1)) == requested_id
            ):
                return surface_object
        return None

    def _build_lighting_sphere_obj_data(self):
        lighting_ball = self._lighting_ball_values()
        if lighting_ball is None:
            return None
        center = lighting_ball["center"]
        radius = lighting_ball["radius"]
        if radius <= 0.0:
            raise ValueError("Lighting_ball.radius must be greater than zero")

        surface_object = self._lighting_surface_object_by_type_and_id(
            "SPHERE",
            lighting_ball["surface_id"],
        )
        segments = int(
            surface_object.get("sphere_lon_segments", 64)
            if surface_object is not None
            else self.itemcfg.get("boundary_light_sphere_segments", 64)
        )
        rings = int(
            surface_object.get("sphere_lat_segments", 32)
            if surface_object is not None
            else self.itemcfg.get("boundary_light_sphere_rings", 32)
        )
        if segments < 3:
            raise ValueError("sphere_lon_segments must be at least 3")
        if rings < 2:
            raise ValueError("sphere_lat_segments must be at least 2")

        obj_data = {
            "objects": [
                {
                    "name": "lighting_sphere",
                    "surface_type": "SPHERE",
                    "material_id": lighting_ball["material_id"],
                    "surface_id": lighting_ball["surface_id"],
                    "obj_file": (
                        surface_object.get("obj_file")
                        if surface_object is not None
                        else None
                    ),
                    "mesh_file": (
                        surface_object.get("mesh_file")
                        if surface_object is not None
                        else None
                    ),
                    "obj_regions": (
                        surface_object.get("obj_regions", ())
                        if surface_object is not None
                        else ()
                    ),
                    "sphere_lat_segments": rings,
                    "sphere_lon_segments": segments,
                    "faces": [],
                }
            ],
            "vertices": [],
            "normals": [],
            "texcoords": [],
        }
        vertex_ids = []
        for ring_index in range(rings + 1):
            theta = math.pi * ring_index / rings
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)
            row = []
            for segment_index in range(segments):
                phi = 2.0 * math.pi * segment_index / segments
                normal = (
                    sin_theta * math.cos(phi),
                    sin_theta * math.sin(phi),
                    cos_theta,
                )
                position = (
                    center[0] + radius * normal[0],
                    center[1] + radius * normal[1],
                    center[2] + radius * normal[2],
                )
                vertex_id = self._surface_obj_add_vertex(
                    obj_data,
                    position,
                    normal,
                    (
                        segment_index / segments,
                        ring_index / rings,
                    ),
                )
                row.append(vertex_id)
            vertex_ids.append(row)

        faces = obj_data["objects"][0]["faces"]
        for ring_index in range(rings):
            for segment_index in range(segments):
                next_segment = (segment_index + 1) % segments
                v00 = vertex_ids[ring_index][segment_index]
                v10 = vertex_ids[ring_index][next_segment]
                v01 = vertex_ids[ring_index + 1][segment_index]
                v11 = vertex_ids[ring_index + 1][next_segment]
                if ring_index == 0:
                    faces.append((v00, v11, v01))
                elif ring_index + 1 == rings:
                    faces.append((v00, v10, v01))
                else:
                    faces.append((v00, v10, v11))
                    faces.append((v00, v11, v01))
        return obj_data

    def _build_lighting_wall_obj_data(self):
        rectangle_wall_segments = getattr(self, "rectangle_wall_segments", ())
        if not rectangle_wall_segments:
            return None

        obj_data = {
            "objects": [],
            "vertices": [],
            "normals": [],
            "texcoords": [],
        }
        for segment in rectangle_wall_segments:
            lighting_surface = self._lighting_surface_object_by_type_and_id(
                "RECTANGLE_WALL",
                int(segment["wall_flag"]),
            )
            surface_object = {
                "name": str(segment["name"]),
                "surface_type": "RECTANGLE_WALL",
                "material_id": int(segment.get("material_id", 0)),
                "surface_id": int(segment["wall_flag"]),
                "obj_file": (
                    lighting_surface.get("obj_file")
                    if lighting_surface is not None
                    else None
                ),
                "mesh_file": (
                    lighting_surface.get("mesh_file")
                    if lighting_surface is not None
                    else None
                ),
                "faces": [],
            }
            obj_data["objects"].append(surface_object)
            origin = segment["origin"]
            u_axis = segment["u_axis"]
            v_axis = segment["v_axis"]
            normal = segment["normal"]
            u_length = float(segment["u_length"])
            v_length = float(segment["v_length"])
            u_step_count = int(
                lighting_surface.get(
                    "rectangle_u_segments",
                    max(1, math.ceil(u_length)),
                )
                if lighting_surface is not None
                else max(1, math.ceil(u_length))
            )
            v_step_count = int(
                lighting_surface.get(
                    "rectangle_v_segments",
                    max(1, math.ceil(v_length)),
                )
                if lighting_surface is not None
                else max(1, math.ceil(v_length))
            )
            if u_step_count <= 0:
                raise ValueError("rectangle_u_segments must be positive")
            if v_step_count <= 0:
                raise ValueError("rectangle_v_segments must be positive")

            def point(local_u, local_v):
                return (
                    origin[0] + u_axis[0] * local_u + v_axis[0] * local_v,
                    origin[1] + u_axis[1] * local_u + v_axis[1] * local_v,
                    origin[2] + u_axis[2] * local_u + v_axis[2] * local_v,
                )

            def emit(local_u, local_v):
                return self._surface_obj_add_vertex(
                    obj_data,
                    point(local_u, local_v),
                    normal,
                    (
                        0.0 if u_length <= 0.0 else local_u / u_length,
                        0.0 if v_length <= 0.0 else local_v / v_length,
                    ),
                )

            for u_index in range(u_step_count):
                u0 = u_length * u_index / u_step_count
                u1 = u_length * (u_index + 1) / u_step_count
                for v_index in range(v_step_count):
                    v0 = v_length * v_index / v_step_count
                    v1 = v_length * (v_index + 1) / v_step_count
                    p00 = emit(u0, v0)
                    p10 = emit(u1, v0)
                    p11 = emit(u1, v1)
                    p00b = emit(u0, v0)
                    p11b = emit(u1, v1)
                    p01 = emit(u0, v1)
                    surface_object["faces"].append((p00, p10, p11))
                    surface_object["faces"].append((p00b, p11b, p01))
        return obj_data

    def _merge_obj_data(self, obj_data_items):
        merged = {
            "objects": [],
            "vertices": [],
            "normals": [],
            "texcoords": [],
        }
        vertex_offset = 0
        for obj_data in obj_data_items:
            if obj_data is None:
                continue
            merged["vertices"].extend(obj_data["vertices"])
            merged["normals"].extend(obj_data["normals"])
            merged["texcoords"].extend(obj_data["texcoords"])
            for surface_object in obj_data["objects"]:
                merged["objects"].append(
                    {
                        "name": surface_object["name"],
                        "surface_type": surface_object.get("surface_type"),
                        "material_id": surface_object["material_id"],
                        "surface_id": surface_object["surface_id"],
                        "obj_file": surface_object.get("obj_file"),
                        "mesh_file": surface_object.get("mesh_file"),
                        "faces": tuple(
                            tuple(vertex_id + vertex_offset for vertex_id in face)
                            for face in surface_object["faces"]
                        ),
                    }
                )
            vertex_offset += len(obj_data["vertices"])
        return merged

    def _single_surface_obj_data(self, obj_data, object_name):
        for surface_object in obj_data["objects"]:
            if surface_object["name"] != object_name:
                continue

            referenced_vertices = []
            seen_vertices = set()
            for face in surface_object["faces"]:
                for vertex_id in face:
                    if vertex_id in seen_vertices:
                        continue
                    seen_vertices.add(vertex_id)
                    referenced_vertices.append(vertex_id)

            vertex_map = {
                old_vertex_id: new_vertex_id
                for new_vertex_id, old_vertex_id in enumerate(referenced_vertices, start=1)
            }
            return {
                "objects": [
                    {
                        "name": surface_object["name"],
                        "surface_type": surface_object.get("surface_type"),
                        "material_id": surface_object["material_id"],
                        "surface_id": surface_object["surface_id"],
                        "obj_file": surface_object.get("obj_file"),
                        "mesh_file": surface_object.get("mesh_file"),
                        "faces": tuple(
                            tuple(vertex_map[vertex_id] for vertex_id in face)
                            for face in surface_object["faces"]
                        ),
                    }
                ],
                "vertices": [
                    obj_data["vertices"][vertex_id - 1]
                    for vertex_id in referenced_vertices
                ],
                "normals": [
                    obj_data["normals"][vertex_id - 1]
                    for vertex_id in referenced_vertices
                ],
                "texcoords": [
                    obj_data["texcoords"][vertex_id - 1]
                    for vertex_id in referenced_vertices
                ],
            }

        return None

    def _write_surface_obj(self, path, obj_data, description):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="ascii", newline="\n") as output:
            output.write(f"# {description}\n")
            output.write("# Generated surface geometry only; no particles.\n")
            output.write("# Dynamics contact remains analytic/configured.\n")
            for vertex_x, vertex_y, vertex_z in obj_data["vertices"]:
                output.write(f"v {vertex_x:.9f} {vertex_y:.9f} {vertex_z:.9f}\n")
            for tex_u, tex_v in obj_data["texcoords"]:
                output.write(f"vt {tex_u:.9f} {tex_v:.9f}\n")
            for normal_x, normal_y, normal_z in obj_data["normals"]:
                output.write(f"vn {normal_x:.9f} {normal_y:.9f} {normal_z:.9f}\n")
            for surface_object in obj_data["objects"]:
                output.write(f"o {surface_object['name']}\n")
                output.write(f"# surface_id: {surface_object['surface_id']}\n")
                output.write(f"# material_id: {surface_object['material_id']}\n")
                for first, second, third in surface_object["faces"]:
                    output.write(
                        f"f {first}/{first}/{first} "
                        f"{second}/{second}/{second} "
                        f"{third}/{third}/{third}\n"
                    )
        return path

    def _material_name_for_obj(self, prefix, material_id):
        safe_prefix = "".join(
            value if value.isalnum() or value == "_" else "_"
            for value in str(prefix)
        )
        return f"{safe_prefix}_material_{int(material_id)}"

    def _write_decaled_sphere_diag_obj(self, obj_path, obj_data):
        surface_object = obj_data["objects"][0]
        sphere_decal_map = surface_object.get("sphere_decal_map")
        if not sphere_decal_map:
            return None

        rings = int(surface_object.get("sphere_lat_segments", 0))
        segments = int(surface_object.get("sphere_lon_segments", 0))
        if rings < 2 or segments < 3:
            return None

        object_name = str(surface_object.get("name", "lighting_sphere"))
        diag_dir = os.path.dirname(obj_path)
        diag_obj_path = os.path.join(diag_dir, f"{object_name}diag.obj")
        marker_obj_path = os.path.join(diag_dir, f"{object_name}diag_markers.obj")
        marker_mtl_name = f"{object_name}diag_markers.mtl"
        marker_mtl_path = os.path.join(diag_dir, marker_mtl_name)
        default_material_id = int(surface_object.get("material_id", 0))
        default_color = (
            self._material_color_by_id(default_material_id)
            or (0.8, 0.8, 0.8, 1.0)
        )
        decal_cells = {
            (int(cell["ring"]), int(cell["segment"])): cell
            for cell in sphere_decal_map.get("cells", ())
        }

        def vertex_cell(vertex_id):
            local_vertex_id = int(vertex_id) - 1
            if local_vertex_id < 0:
                return None
            ring = local_vertex_id // segments
            segment = local_vertex_id % segments
            if ring < 0 or ring > rings:
                return None
            return ring, segment

        def vertex_color(vertex_id):
            cell_key = vertex_cell(vertex_id)
            if cell_key in decal_cells:
                return tuple(float(value) for value in decal_cells[cell_key]["albedo"][:4])
            return default_color

        def sphere_normal(point):
            lighting_ball = self._lighting_ball_values()
            if lighting_ball is None:
                return (0.0, 0.0, 1.0)
            center = lighting_ball["center"]
            direction = tuple(
                float(point[axis]) - float(center[axis])
                for axis in range(3)
            )
            direction_length = math.sqrt(sum(value * value for value in direction))
            if direction_length <= 1.0e-9:
                return (0.0, 0.0, 1.0)
            return tuple(value / direction_length for value in direction)

        with open(diag_obj_path, "w", encoding="ascii", newline="\n") as output:
            output.write("# Generated decaled LightingBall sphere diagnostic.\n")
            output.write("# Vertex colors mark projected sphere_decal_map cells.\n")
            for vertex_index, (vertex_x, vertex_y, vertex_z) in enumerate(
                obj_data["vertices"],
                start=1,
            ):
                red, green, blue, _alpha = vertex_color(vertex_index)
                output.write(
                    f"v {vertex_x:.9f} {vertex_y:.9f} {vertex_z:.9f} "
                    f"{red:.9f} {green:.9f} {blue:.9f}\n"
                )
            for tex_u, tex_v in obj_data["texcoords"]:
                output.write(f"vt {tex_u:.9f} {tex_v:.9f}\n")
            for normal_x, normal_y, normal_z in obj_data["normals"]:
                output.write(f"vn {normal_x:.9f} {normal_y:.9f} {normal_z:.9f}\n")
            output.write(f"o {object_name}_decal_diag\n")
            for first, second, third in surface_object["faces"]:
                output.write(
                    f"f {first}/{first}/{first} "
                    f"{second}/{second}/{second} "
                    f"{third}/{third}/{third}\n"
                )
        marker_vertices = []
        marker_faces = []
        marker_size = float(
            surface_object.get(
                "sphere_decal_diag_marker_size",
                self.itemcfg.get("sphere_decal_diag_marker_size", 0.075),
            )
        )
        for cell in decal_cells.values():
            ring = int(cell["ring"])
            segment = int(cell["segment"])
            vertex_id = ring * segments + segment + 1
            if vertex_id <= 0 or vertex_id > len(obj_data["vertices"]):
                continue
            point = tuple(float(value) for value in obj_data["vertices"][vertex_id - 1])
            normal = sphere_normal(point)
            up = (0.0, 0.0, 1.0)
            if abs(sum(normal[axis] * up[axis] for axis in range(3))) > 0.95:
                up = (0.0, 1.0, 0.0)
            tangent_u = (
                up[1] * normal[2] - up[2] * normal[1],
                up[2] * normal[0] - up[0] * normal[2],
                up[0] * normal[1] - up[1] * normal[0],
            )
            tangent_u_length = math.sqrt(sum(value * value for value in tangent_u))
            if tangent_u_length <= 1.0e-9:
                continue
            tangent_u = tuple(value / tangent_u_length for value in tangent_u)
            tangent_v = (
                normal[1] * tangent_u[2] - normal[2] * tangent_u[1],
                normal[2] * tangent_u[0] - normal[0] * tangent_u[2],
                normal[0] * tangent_u[1] - normal[1] * tangent_u[0],
            )
            base_index = len(marker_vertices) + 1
            lifted_point = tuple(point[axis] + normal[axis] * marker_size for axis in range(3))
            marker_vertices.extend(
                (
                    tuple(lifted_point[axis] + tangent_u[axis] * marker_size for axis in range(3)),
                    tuple(
                        lifted_point[axis]
                        - tangent_u[axis] * marker_size * 0.5
                        + tangent_v[axis] * marker_size * 0.866
                        for axis in range(3)
                    ),
                    tuple(
                        lifted_point[axis]
                        - tangent_u[axis] * marker_size * 0.5
                        - tangent_v[axis] * marker_size * 0.866
                        for axis in range(3)
                    ),
                )
            )
            marker_faces.append((base_index, base_index + 1, base_index + 2))

        with open(marker_mtl_path, "w", encoding="ascii", newline="\n") as output:
            output.write("# Generated decal diagnostic marker material.\n")
            output.write("newmtl decal_marker_blue\n")
            output.write("Kd 0.000000000 0.000000000 1.000000000\n")
            output.write("d 1.000000000\n")

        with open(marker_obj_path, "w", encoding="ascii", newline="\n") as output:
            output.write("# Generated visible decal vertex markers.\n")
            output.write(f"mtllib {marker_mtl_name}\n")
            output.write(f"o {object_name}_decal_vertex_markers\n")
            output.write("usemtl decal_marker_blue\n")
            for vertex_x, vertex_y, vertex_z in marker_vertices:
                output.write(f"v {vertex_x:.9f} {vertex_y:.9f} {vertex_z:.9f}\n")
            for first, second, third in marker_faces:
                output.write(f"f {first} {second} {third}\n")
        return diag_obj_path

    def _normalized_obj_path(self, raw_path):
        path = str(raw_path)
        path = (
            path.replace("\b", "\\b")
            .replace("\f", "\\f")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
            .replace("\v", "\\v")
        )
        return os.path.normpath(path)

    def _mesh_file_path_for_obj(self, obj_path):
        root, _extension = os.path.splitext(obj_path)
        return f"{root}.mesh.cfg"

    def _mesh_file_path_for_surface(self, surface_object, obj_path):
        configured_mesh_file = surface_object.get("mesh_file")
        if configured_mesh_file:
            return self._normalized_obj_path(configured_mesh_file)
        return self._mesh_file_path_for_obj(obj_path)

    def _read_mtl_colors(self, obj_path, mtllibs):
        colors = {}
        for mtllib in mtllibs:
            mtl_path = os.path.join(os.path.dirname(obj_path), mtllib)
            if not os.path.exists(mtl_path):
                continue
            current_material = None
            with open(mtl_path, "r", encoding="ascii") as source:
                for raw_line in source:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if parts[0] == "newmtl" and len(parts) >= 2:
                        current_material = " ".join(parts[1:])
                    elif parts[0] == "Kd" and current_material and len(parts) >= 4:
                        colors[current_material] = (
                            float(parts[1]),
                            float(parts[2]),
                            float(parts[3]),
                            1.0,
                        )
        return colors

    def _write_surface_mesh_cfg(self, path, obj_path, obj_data, description):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="ascii", newline="\n") as output:
            output.write(f"# {description}\n")
            output.write("# Generated metadata for Vulkan lighting surface import.\n")
            output.write('format = "gpcd_lighting_surface_mesh_v1";\n')
            output.write(f'obj_file = "{obj_path.replace("\\", "/")}";\n')
            output.write(f"vertex_count = {len(obj_data['vertices'])};\n")
            output.write("objects = (\n")
            for object_index, surface_object in enumerate(obj_data["objects"]):
                separator = "," if object_index + 1 < len(obj_data["objects"]) else ""
                faces = tuple(surface_object["faces"])
                referenced_vertices = {
                    int(vertex_id)
                    for face in faces
                    for vertex_id in face
                }
                surface_type = str(surface_object.get("surface_type", "SPHERE")).upper()
                output.write("  {\n")
                output.write(f'    name = "{surface_object["name"]}";\n')
                output.write(f'    surface_type = "{surface_type}";\n')
                output.write(f"    surface_id = {int(surface_object['surface_id'])};\n")
                output.write(f"    material_id = {int(surface_object['material_id'])};\n")
                output.write("    vertex_offset = 0;\n")
                output.write(f"    vertex_count = {len(referenced_vertices)};\n")
                output.write("    index_offset = 0;\n")
                output.write(f"    index_count = {len(faces) * 3};\n")
                output.write(f"    triangle_count = {len(faces)};\n")
                if "sphere_lat_segments" in surface_object:
                    output.write(
                        f"    sphere_lat_segments = {int(surface_object['sphere_lat_segments'])};\n"
                    )
                if "sphere_lon_segments" in surface_object:
                    output.write(
                        f"    sphere_lon_segments = {int(surface_object['sphere_lon_segments'])};\n"
                    )
                sphere_surface_map = surface_object.get("sphere_surface_map")
                if sphere_surface_map:
                    material_ids = tuple(sphere_surface_map["material_ids"])
                    albedos = tuple(sphere_surface_map["albedos"])
                    if len(material_ids) != len(albedos):
                        raise ValueError(
                            f"{surface_object['name']} sphere_surface_map material/albedo length mismatch"
                        )
                    output.write("    sphere_surface_map = {\n")
                    output.write(
                        f"      lat_segments = {int(sphere_surface_map['lat_segments'])};\n"
                    )
                    output.write(
                        f"      lon_segments = {int(sphere_surface_map['lon_segments'])};\n"
                    )
                    output.write(f"      cell_count = {len(material_ids)};\n")
                    output.write("      material_ids = (\n")
                    for cell_index, material_id in enumerate(material_ids):
                        separator = "," if cell_index + 1 < len(material_ids) else ""
                        output.write(f"        {int(material_id)}{separator}\n")
                    output.write("      );\n")
                    output.write("      albedos = (\n")
                    for cell_index, albedo in enumerate(albedos):
                        separator = "," if cell_index + 1 < len(albedos) else ""
                        red, green, blue, alpha = (
                            float(value) for value in albedo[:4]
                        )
                        output.write(
                            "        "
                            f"[{red:.9f}, {green:.9f}, {blue:.9f}, {alpha:.9f}]"
                            f"{separator}\n"
                        )
                    output.write("      );\n")
                    output.write("    };\n")
                sphere_decal_map = surface_object.get("sphere_decal_map")
                if sphere_decal_map:
                    cells = tuple(sphere_decal_map["cells"])
                    output.write("    sphere_decal_map = {\n")
                    output.write(
                        f"      lat_segments = {int(sphere_decal_map['lat_segments'])};\n"
                    )
                    output.write(
                        f"      lon_segments = {int(sphere_decal_map['lon_segments'])};\n"
                    )
                    output.write(f"      cell_count = {len(cells)};\n")
                    output.write("      cells = (\n")
                    for cell_index, cell in enumerate(cells):
                        separator = "," if cell_index + 1 < len(cells) else ""
                        red, green, blue, alpha = (
                            float(value) for value in cell["albedo"][:4]
                        )
                        output.write("        {\n")
                        output.write(f"          ring = {int(cell['ring'])};\n")
                        output.write(f"          segment = {int(cell['segment'])};\n")
                        output.write(f"          material_id = {int(cell['material_id'])};\n")
                        output.write(
                            "          "
                            f"albedo = [{red:.9f}, {green:.9f}, {blue:.9f}, {alpha:.9f}];\n"
                        )
                        output.write(f"        }}{separator}\n")
                    output.write("      );\n")
                    output.write("    };\n")
                if "rectangle_u_segments" in surface_object:
                    output.write(
                        f"    rectangle_u_segments = {int(surface_object['rectangle_u_segments'])};\n"
                    )
                if "rectangle_v_segments" in surface_object:
                    output.write(
                        f"    rectangle_v_segments = {int(surface_object['rectangle_v_segments'])};\n"
                    )
                output.write("    indices = (\n")
                for face_index, face in enumerate(faces):
                    face_separator = "," if face_index + 1 < len(faces) else ""
                    first, second, third = (int(value) - 1 for value in face)
                    output.write(
                        f"      [{first}, {second}, {third}]{face_separator}\n"
                    )
                output.write("    );\n")
                face_colors = tuple(surface_object.get("face_colors", ()))
                if face_colors:
                    if len(face_colors) != len(faces):
                        raise ValueError(
                            f"{surface_object['name']} face_colors length must match faces"
                        )
                    output.write("    triangle_colors = (\n")
                    for face_index, color in enumerate(face_colors):
                        color_separator = "," if face_index + 1 < len(face_colors) else ""
                        red, green, blue, alpha = (
                            float(value) for value in color[:4]
                        )
                        output.write(
                            "      "
                            f"[{red:.9f}, {green:.9f}, {blue:.9f}, {alpha:.9f}]"
                            f"{color_separator}\n"
                        )
                    output.write("    );\n")
                face_material_ids = tuple(surface_object.get("face_material_ids", ()))
                if face_material_ids:
                    if len(face_material_ids) != len(faces):
                        raise ValueError(
                            f"{surface_object['name']} face_material_ids length must match faces"
                        )
                    output.write("    triangle_material_ids = (\n")
                    for face_index, material_id in enumerate(face_material_ids):
                        material_separator = (
                            "," if face_index + 1 < len(face_material_ids) else ""
                        )
                        output.write(
                            f"      {int(material_id)}{material_separator}\n"
                        )
                    output.write("    );\n")
                output.write(f"  }}{separator}\n")
            output.write(");\n")
        return path

    def _build_sphere_surface_map(self, surface_object, obj_data):
        if str(surface_object.get("surface_type", "")).upper() != "SPHERE":
            return None
        if "sphere_lat_segments" not in surface_object or "sphere_lon_segments" not in surface_object:
            return None

        lighting_ball = self._lighting_ball_values()
        if lighting_ball is None:
            return None

        rings = int(surface_object["sphere_lat_segments"])
        segments = int(surface_object["sphere_lon_segments"])
        if rings < 2 or segments < 3:
            return None

        cell_count = (rings + 1) * segments
        default_material_id = int(surface_object.get("material_id", 0))
        material_ids = [0 for _ in range(cell_count)]
        albedos = [(0.0, 0.0, 0.0, 0.0) for _ in range(cell_count)]
        faces = tuple(surface_object.get("faces", ()))
        face_colors = tuple(surface_object.get("face_colors", ()))
        face_material_ids = tuple(surface_object.get("face_material_ids", ()))
        vertices = tuple(obj_data.get("vertices", ()))
        center = tuple(float(value) for value in lighting_ball["center"])

        for face_index, face in enumerate(faces):
            material_id = (
                int(face_material_ids[face_index])
                if face_index < len(face_material_ids)
                else default_material_id
            )
            color = (
                tuple(float(value) for value in face_colors[face_index][:4])
                if face_index < len(face_colors)
                else None
            )
            if material_id == default_material_id and color is None:
                continue

            points = []
            for vertex_id in face:
                vertex = vertices[int(vertex_id) - 1]
                points.append(tuple(float(value) for value in vertex[:3]))
            centroid = tuple(sum(point[axis] for point in points) / len(points) for axis in range(3))
            direction = tuple(centroid[axis] - center[axis] for axis in range(3))
            direction_length = math.sqrt(sum(value * value for value in direction))
            if direction_length <= 1.0e-9:
                continue

            nx, ny, nz = (value / direction_length for value in direction)
            theta = math.acos(max(-1.0, min(1.0, nz)))
            phi = math.atan2(ny, nx)
            if phi < 0.0:
                phi += 2.0 * math.pi
            ring = int(round(theta / math.pi * rings))
            segment = int(round(phi / (2.0 * math.pi) * segments)) % segments
            ring = max(0, min(rings, ring))
            cell_index = ring * segments + segment
            material_ids[cell_index] = material_id
            if color is not None:
                albedos[cell_index] = color

        if not any(material_ids) and not any(albedo[3] > 0.0 for albedo in albedos):
            return None

        return {
            "lat_segments": rings,
            "lon_segments": segments,
            "material_ids": material_ids,
            "albedos": albedos,
        }

    def _material_color_by_id(self, material_id):
        requested_id = int(material_id)
        for material in self.itemcfg.get("material_properties", ()):
            if not hasattr(material, "get"):
                continue
            if int(material.get("material_id", -1)) != requested_id:
                continue
            color = material.get("color")
            if color is None:
                return None
            values = tuple(float(value) for value in color)
            if len(values) >= 4:
                return values[:4]
            if len(values) >= 3:
                return (values[0], values[1], values[2], 1.0)
        return None

    def _infer_sphere_segments_from_faces(self, surface_object, vertex_count):
        faces = tuple(surface_object.get("faces", ()))
        face_count = len(faces)
        if vertex_count <= 0 or face_count <= 0 or face_count % 2 != 0:
            return None
        half_face_count = face_count // 2
        segment_delta = vertex_count - half_face_count
        if segment_delta <= 0 or segment_delta % 2 != 0:
            return None
        segments = segment_delta // 2
        if segments < 3 or vertex_count % segments != 0:
            return None
        rings = vertex_count // segments - 1
        if rings < 2 or face_count != 2 * segments * (rings - 1):
            return None
        return rings, segments

    def _build_sphere_decal_map(self, surface_object, obj_data):
        if str(surface_object.get("surface_type", "")).upper() != "SPHERE":
            return None
        if "sphere_lat_segments" not in surface_object or "sphere_lon_segments" not in surface_object:
            return None

        lighting_ball = self._lighting_ball_values()
        if lighting_ball is None:
            return None

        rings = int(surface_object["sphere_lat_segments"])
        segments = int(surface_object["sphere_lon_segments"])
        if rings < 2 or segments < 3:
            return None

        radius = float(lighting_ball["radius"])
        if radius <= 0.0:
            return None
        default_material_id = int(surface_object.get("material_id", 0))
        faces = tuple(
            surface_object.get("decal_faces")
            or surface_object.get("faces", ())
        )
        face_colors = tuple(
            surface_object.get("decal_face_colors")
            or surface_object.get("face_colors", ())
        )
        face_material_ids = tuple(
            surface_object.get("decal_face_material_ids")
            or surface_object.get("face_material_ids", ())
        )
        vertices = tuple(obj_data.get("vertices", ()))
        center = tuple(float(value) for value in lighting_ball["center"])
        source_triangles = []

        for face_index, face in enumerate(faces):
            material_id = (
                int(face_material_ids[face_index])
                if face_index < len(face_material_ids)
                else default_material_id
            )
            if material_id == default_material_id:
                continue

            color = self._material_color_by_id(material_id)
            if color is None and face_index < len(face_colors):
                color = tuple(float(value) for value in face_colors[face_index][:4])
            if color is None:
                color = (0.0, 0.0, 0.0, 0.0)
            points = [
                tuple(float(value) for value in vertices[int(vertex_id) - 1][:3])
                for vertex_id in face
            ]
            edge_a = tuple(points[1][axis] - points[0][axis] for axis in range(3))
            edge_b = tuple(points[2][axis] - points[0][axis] for axis in range(3))
            face_normal = (
                edge_a[1] * edge_b[2] - edge_a[2] * edge_b[1],
                edge_a[2] * edge_b[0] - edge_a[0] * edge_b[2],
                edge_a[0] * edge_b[1] - edge_a[1] * edge_b[0],
            )
            face_normal_length = math.sqrt(
                sum(value * value for value in face_normal)
            )
            if face_normal_length <= 1.0e-9:
                continue
            centroid = tuple(
                sum(point[axis] for point in points) / len(points)
                for axis in range(3)
            )
            direction = tuple(centroid[axis] - center[axis] for axis in range(3))
            direction_length = math.sqrt(sum(value * value for value in direction))
            if direction_length <= 1.0e-9:
                continue

            nx, ny, nz = (value / direction_length for value in direction)
            unit_face_normal = tuple(value / face_normal_length for value in face_normal)
            if abs(
                sum(unit_face_normal[axis] * (nx, ny, nz)[axis] for axis in range(3))
            ) < 0.35:
                continue

            source_triangles.append(
                {
                    "points": points,
                    "direction": (nx, ny, nz),
                    "material_id": material_id,
                    "albedo": color,
                }
            )

        if not source_triangles:
            return None

        def direction_to_sphere_cell(direction):
            nx, ny, nz = direction
            theta = math.acos(max(-1.0, min(1.0, nz)))
            phi = math.atan2(ny, nx)
            if phi < 0.0:
                phi += 2.0 * math.pi
            ring = int(round(theta / math.pi * rings))
            segment = int(round(phi / (2.0 * math.pi) * segments)) % segments
            return max(0, min(rings, ring)), segment

        max_ray_distance = float(
            surface_object.get(
                "sphere_decal_ray_distance",
                self.itemcfg.get("sphere_decal_ray_distance", radius * 0.35),
            )
        )
        ray_epsilon = max(radius * 1.0e-5, 1.0e-5)

        triangle_buckets = {}
        for triangle in source_triangles:
            bucket_key = direction_to_sphere_cell(triangle["direction"])
            triangle_buckets.setdefault(bucket_key, []).append(triangle)

        default_bucket_radius = max(
            1,
            int(math.ceil(math.asin(min(0.999, max_ray_distance / radius)) / math.pi * rings)) + 2,
        )
        bucket_search_radius = int(
            surface_object.get(
                "sphere_decal_bucket_search_radius",
                self.itemcfg.get(
                    "sphere_decal_bucket_search_radius",
                    default_bucket_radius,
                ),
            )
        )
        if bucket_search_radius < 0:
            bucket_search_radius = 0

        def candidate_triangles(direction):
            center_ring, center_segment = direction_to_sphere_cell(direction)
            candidates = []
            seen_triangle_ids = set()
            for ring_offset in range(-bucket_search_radius, bucket_search_radius + 1):
                ring = center_ring + ring_offset
                if ring < 0 or ring > rings:
                    continue
                for segment_offset in range(
                    -bucket_search_radius,
                    bucket_search_radius + 1,
                ):
                    segment = (center_segment + segment_offset) % segments
                    for triangle in triangle_buckets.get((ring, segment), ()):
                        triangle_id = id(triangle)
                        if triangle_id in seen_triangle_ids:
                            continue
                        seen_triangle_ids.add(triangle_id)
                        candidates.append(triangle)
            return candidates

        def ray_triangle_distance(origin, direction, points):
            edge_a = tuple(points[1][axis] - points[0][axis] for axis in range(3))
            edge_b = tuple(points[2][axis] - points[0][axis] for axis in range(3))
            h = (
                direction[1] * edge_b[2] - direction[2] * edge_b[1],
                direction[2] * edge_b[0] - direction[0] * edge_b[2],
                direction[0] * edge_b[1] - direction[1] * edge_b[0],
            )
            determinant = sum(edge_a[axis] * h[axis] for axis in range(3))
            if abs(determinant) <= 1.0e-9:
                return None
            inverse_determinant = 1.0 / determinant
            s = tuple(origin[axis] - points[0][axis] for axis in range(3))
            u_value = inverse_determinant * sum(s[axis] * h[axis] for axis in range(3))
            if u_value < -1.0e-7 or u_value > 1.0 + 1.0e-7:
                return None
            q = (
                s[1] * edge_a[2] - s[2] * edge_a[1],
                s[2] * edge_a[0] - s[0] * edge_a[2],
                s[0] * edge_a[1] - s[1] * edge_a[0],
            )
            v_value = inverse_determinant * sum(
                direction[axis] * q[axis] for axis in range(3)
            )
            if v_value < -1.0e-7 or u_value + v_value > 1.0 + 1.0e-7:
                return None
            distance = inverse_determinant * sum(edge_b[axis] * q[axis] for axis in range(3))
            if distance <= ray_epsilon or distance > max_ray_distance:
                return None
            return distance

        def vertex_cell(vertex_id):
            local_vertex_id = int(vertex_id) - 1
            if local_vertex_id < 0:
                return None
            ring = local_vertex_id // segments
            segment = local_vertex_id % segments
            if ring < 0 or ring > rings or segment < 0 or segment >= segments:
                return None
            return ring, segment

        def face_rect_cell(face):
            face_cells = [vertex_cell(vertex_id) for vertex_id in face]
            face_cells = [cell for cell in face_cells if cell is not None]
            if not face_cells:
                return None
            face_rings = [ring for ring, _segment in face_cells]
            ring = min(face_rings)
            if ring >= rings:
                ring = rings - 1

            face_segments = [_segment for _ring, _segment in face_cells]
            unique_segments = sorted(set(face_segments))
            if 0 in unique_segments and segments - 1 in unique_segments:
                segment = segments - 1
            else:
                segment = min(unique_segments)
            return ring, segment

        def face_rect_indices(face_index):
            if face_index < segments:
                return (face_index,)
            interior_face_count = max(0, rings - 2) * segments * 2
            interior_start = segments
            interior_end = interior_start + interior_face_count
            if face_index < interior_end:
                local_index = face_index - interior_start
                rect_start = interior_start + (local_index // 2) * 2
                return (rect_start, rect_start + 1)
            return (face_index,)

        cells = {}
        diag_faces = []
        diag_face_keys = set()
        for face_index, sphere_face in enumerate(surface_object.get("faces", ())):
            face_points = [
                tuple(float(value) for value in vertices[int(vertex_id) - 1][:3])
                for vertex_id in sphere_face
            ]
            sphere_point = tuple(
                sum(point[axis] for point in face_points) / len(face_points)
                for axis in range(3)
            )
            direction = tuple(sphere_point[axis] - center[axis] for axis in range(3))
            direction_length = math.sqrt(sum(value * value for value in direction))
            if direction_length <= 1.0e-9:
                continue
            normal = tuple(value / direction_length for value in direction)
            origin = tuple(
                sphere_point[axis] + normal[axis] * ray_epsilon
                for axis in range(3)
            )
            closest_distance = None
            closest_triangle = None
            for triangle in candidate_triangles(normal):
                distance = ray_triangle_distance(
                    origin,
                    normal,
                    triangle["points"],
                )
                if distance is None:
                    continue
                if closest_distance is None or distance < closest_distance:
                    closest_distance = distance
                    closest_triangle = triangle
            if closest_triangle is None:
                continue
            for diag_face_index in face_rect_indices(face_index):
                if diag_face_index in diag_face_keys:
                    continue
                diag_face_keys.add(diag_face_index)
                diag_faces.append(
                    {
                        "face_index": diag_face_index,
                        "material_id": closest_triangle["material_id"],
                        "albedo": closest_triangle["albedo"],
                    }
                )
            cell_key = face_rect_cell(sphere_face)
            if cell_key is None:
                continue
            ring, segment = cell_key
            cells[cell_key] = {
                "ring": ring,
                "segment": segment,
                "material_id": closest_triangle["material_id"],
                "albedo": closest_triangle["albedo"],
            }

        if not cells:
            return None

        return {
            "lat_segments": rings,
            "lon_segments": segments,
            "cells": [cells[key] for key in sorted(cells)],
            "diag_faces": diag_faces,
        }

    def _parse_obj_face_vertex(self, raw_value, vertex_count):
        token = raw_value.split("/")[0]
        if not token:
            raise ValueError(f"OBJ face token {raw_value!r} has no vertex index")
        vertex_id = int(token)
        if vertex_id < 0:
            vertex_id = vertex_count + vertex_id + 1
        if vertex_id <= 0 or vertex_id > vertex_count:
            raise ValueError(f"OBJ face vertex index {vertex_id} is out of range")
        return vertex_id

    def _read_surface_obj(self, path, template_surface_object):
        vertices = []
        texcoords = []
        normals = []
        faces = []
        face_colors = []
        face_material_ids = []
        decal_faces = []
        decal_face_colors = []
        decal_face_material_ids = []
        mtllibs = []
        current_obj_name = None
        current_material = None
        material_colors = {}
        default_material_id = int(template_surface_object["material_id"])
        region_material_ids = {
            str(region.get("obj_name")): int(region.get("material_id"))
            for region in template_surface_object.get("obj_regions", ())
            if hasattr(region, "get")
        }
        with open(path, "r", encoding="ascii") as source:
            for line_number, raw_line in enumerate(source, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if parts[0] == "mtllib" and len(parts) >= 2:
                    mtllibs.append(" ".join(parts[1:]))
                    material_colors = self._read_mtl_colors(path, mtllibs)
                elif parts[0] == "o" and len(parts) >= 2:
                    current_obj_name = " ".join(parts[1:])
                elif parts[0] == "usemtl" and len(parts) >= 2:
                    current_material = " ".join(parts[1:])
                elif parts[0] == "v":
                    if len(parts) < 4:
                        raise ValueError(f"{path}:{line_number} vertex requires xyz")
                    vertices.append(tuple(float(value) for value in parts[1:4]))
                elif parts[0] == "vt":
                    if len(parts) < 3:
                        raise ValueError(f"{path}:{line_number} texcoord requires uv")
                    texcoords.append(tuple(float(value) for value in parts[1:3]))
                elif parts[0] == "vn":
                    if len(parts) < 4:
                        raise ValueError(f"{path}:{line_number} normal requires xyz")
                    normals.append(tuple(float(value) for value in parts[1:4]))
                elif parts[0] == "f":
                    if len(parts) < 4:
                        raise ValueError(f"{path}:{line_number} face requires 3 vertices")
                    face_vertices = [
                        self._parse_obj_face_vertex(value, len(vertices))
                        for value in parts[1:]
                    ]
                    first = face_vertices[0]
                    color = material_colors.get(current_material)
                    face_material_id = region_material_ids.get(
                        current_obj_name,
                        default_material_id,
                    )
                    for index in range(1, len(face_vertices) - 1):
                        triangle = (first, face_vertices[index], face_vertices[index + 1])
                        if face_material_id == default_material_id:
                            faces.append(triangle)
                            if color is not None:
                                face_colors.append(color)
                            face_material_ids.append(face_material_id)
                        else:
                            decal_faces.append(triangle)
                            if color is not None:
                                decal_face_colors.append(color)
                            decal_face_material_ids.append(face_material_id)

        if not vertices:
            raise ValueError(f"{path} contains no OBJ vertices")
        if not faces:
            raise ValueError(f"{path} contains no OBJ faces")

        surface_object = dict(template_surface_object)
        surface_object["faces"] = faces
        if face_colors and len(face_colors) == len(faces):
            surface_object["face_colors"] = face_colors
        if face_material_ids and len(face_material_ids) == len(faces):
            surface_object["face_material_ids"] = face_material_ids
        if decal_faces:
            surface_object["decal_faces"] = decal_faces
        if decal_face_colors and len(decal_face_colors) == len(decal_faces):
            surface_object["decal_face_colors"] = decal_face_colors
        if decal_face_material_ids and len(decal_face_material_ids) == len(decal_faces):
            surface_object["decal_face_material_ids"] = decal_face_material_ids
        if str(surface_object.get("surface_type", "")).upper() == "SPHERE":
            sphere_vertex_ids = {
                int(vertex_id)
                for face in faces
                for vertex_id in face
            }
            inferred_segments = self._infer_sphere_segments_from_faces(
                surface_object,
                len(sphere_vertex_ids),
            )
            if inferred_segments is not None:
                inferred_rings, inferred_lon_segments = inferred_segments
                surface_object["sphere_lat_segments"] = inferred_rings
                surface_object["sphere_lon_segments"] = inferred_lon_segments
        if bool(self.itemcfg.get("enable_sphere_surface_map", False)):
            sphere_surface_map = self._build_sphere_surface_map(
                surface_object,
                {
                    "vertices": vertices,
                    "objects": [surface_object],
                },
            )
            if sphere_surface_map is not None:
                surface_object["sphere_surface_map"] = sphere_surface_map
        sphere_decal_map = self._build_sphere_decal_map(
            surface_object,
            {
                "vertices": vertices,
                "objects": [surface_object],
            },
        )
        if sphere_decal_map is not None:
            surface_object["sphere_decal_map"] = sphere_decal_map
        return {
            "objects": [surface_object],
            "vertices": vertices,
            "normals": normals,
            "texcoords": texcoords,
        }

    def generate_lighting_sphere_obj(self):
        """Write only the lighting sphere OBJ from scene_model."""
        if self.itemcfg.get("scene_model") is None:
            print("No scene_model configured; no sphere OBJ generated.")
            return ()

        sphere_obj = self._build_lighting_sphere_obj_data()
        if sphere_obj is None or not sphere_obj["objects"]:
            print("No lighting sphere configured; no sphere OBJ generated.")
            return ()

        surface_object = sphere_obj["objects"][0]
        obj_file = surface_object.get("obj_file")
        if obj_file:
            obj_path = self._normalized_obj_path(obj_file)
        else:
            output_prefix = str(
                self.itemcfg.get("output_file_prefix", self.itemcfg.STUDY_NAME)
            )
            obj_path = os.path.join(
                str(self.itemcfg.data_dir),
                f"{output_prefix}_sphere.obj",
            )

        written_path = self._write_surface_obj(
            obj_path,
            sphere_obj,
            "Generated LightingBall sphere surface",
        )
        mesh_path = self._mesh_file_path_for_surface(surface_object, written_path)
        written_mesh_path = self._write_surface_mesh_cfg(
            mesh_path,
            written_path,
            sphere_obj,
            "Generated LightingBall sphere mesh metadata",
        )
        report_text = (
            "Lighting sphere OBJ report:\n"
            f"  file: {written_path}\n"
            f"  mesh file: {written_mesh_path}\n"
            f"  vertices: {len(sphere_obj['vertices'])}\n"
            f"  triangles: {len(surface_object['faces'])}"
        )
        print(report_text)
        return (written_path, written_mesh_path)

    def refresh_lighting_sphere_mesh(self):
        """Refresh only sphere mesh metadata from the current OBJ file."""
        if self.itemcfg.get("scene_model") is None:
            print("No scene_model configured; no sphere mesh refreshed.")
            return ()

        sphere_obj = self._build_lighting_sphere_obj_data()
        if sphere_obj is None or not sphere_obj["objects"]:
            print("No lighting sphere configured; no sphere mesh refreshed.")
            return ()

        surface_object = sphere_obj["objects"][0]
        obj_file = surface_object.get("obj_file")
        if not obj_file:
            print("lighting_sphere has no obj_file; no sphere mesh refreshed.")
            return ()

        obj_path = self._normalized_obj_path(obj_file)
        if not os.path.exists(obj_path):
            raise FileNotFoundError(f"lighting_sphere obj_file does not exist: {obj_path}")

        edited_obj = self._read_surface_obj(obj_path, surface_object)
        mesh_path = self._mesh_file_path_for_surface(surface_object, obj_path)
        written_mesh_path = self._write_surface_mesh_cfg(
            mesh_path,
            obj_path,
            edited_obj,
            "Refreshed LightingBall sphere mesh metadata",
        )
        diag_obj_path = self._write_decaled_sphere_diag_obj(obj_path, edited_obj)
        face_count = len(edited_obj["objects"][0]["faces"])
        decal_source_face_count = len(
            edited_obj["objects"][0].get("decal_faces", ())
        )
        decal_cell_count = len(
            edited_obj["objects"][0]
            .get("sphere_decal_map", {})
            .get("cells", ())
        )
        report_text = (
            "Lighting sphere mesh refresh report:\n"
            f"  obj file: {obj_path}\n"
            f"  mesh file: {written_mesh_path}\n"
            f"  vertices: {len(edited_obj['vertices'])}\n"
            f"  triangles: {face_count}\n"
            f"  decal source triangles: {decal_source_face_count}\n"
            f"  decal cells: {decal_cell_count}"
        )
        if diag_obj_path is not None:
            report_text += f"\n  decal diag obj: {diag_obj_path}"
        print(report_text)
        return (written_mesh_path,)

    def write_lighting_surface_objs(self):
        """Write render-surface OBJ files for LightingBall inspection."""
        if self.itemcfg.get("scene_model") is None:
            return ()

        sphere_obj = self._build_lighting_sphere_obj_data()
        wall_obj = self._build_lighting_wall_obj_data()
        written_paths = []
        if sphere_obj is not None:
            written_paths.append(
                self._write_surface_obj(
                    self.surface_sphere_obj_name,
                    sphere_obj,
                    "Generated LightingBall sphere surface",
                )
            )
            for surface_object in sphere_obj["objects"]:
                object_path = self.surface_object_obj_names.get(surface_object["name"])
                object_obj = self._single_surface_obj_data(
                    sphere_obj,
                    surface_object["name"],
                )
                if object_path is not None and object_obj is not None:
                    written_paths.append(
                        self._write_surface_obj(
                            object_path,
                            object_obj,
                            f"Generated LightingBall surface {surface_object['name']}",
                        )
                    )
        if wall_obj is not None:
            written_paths.append(
                self._write_surface_obj(
                    self.surface_wall_obj_name,
                    wall_obj,
                    "Generated LightingBall rectangle wall surface",
                )
            )
            for surface_object in wall_obj["objects"]:
                object_path = self.surface_object_obj_names.get(surface_object["name"])
                object_obj = self._single_surface_obj_data(
                    wall_obj,
                    surface_object["name"],
                )
                if object_path is not None and object_obj is not None:
                    written_paths.append(
                        self._write_surface_obj(
                            object_path,
                            object_obj,
                            f"Generated LightingBall surface {surface_object['name']}",
                        )
                    )
        combined_obj = self._merge_obj_data((sphere_obj, wall_obj))
        if combined_obj["vertices"]:
            written_paths.append(
                self._write_surface_obj(
                    self.surface_combined_obj_name,
                    combined_obj,
                    "Generated LightingBall combined lighting surfaces",
                )
            )

        surface_type_by_name = {
            str(surface_object.get("name")): str(
                surface_object.get("surface_type", "UNKNOWN")
            ).upper()
            for surface_object in self.itemcfg.get("lighting_surface_objects", ())
        }
        self.lighting_surface_triangle_inventory = tuple(
            {
                "name": str(surface_object["name"]),
                "surface_type": surface_type_by_name.get(
                    str(surface_object["name"]),
                    "UNKNOWN",
                ),
                "surface_id": int(surface_object["surface_id"]),
                "material_id": int(surface_object["material_id"]),
                "vertex_count": len(
                    {
                        int(vertex_id)
                        for face in surface_object["faces"]
                        for vertex_id in face
                    }
                ),
                "triangle_count": len(surface_object["faces"]),
            }
            for surface_object in combined_obj["objects"]
        )

        if written_paths:
            report_text = (
                "Lighting surface OBJ report:\n"
                + "\n".join(f"  file: {path}" for path in written_paths)
            )
            print(report_text)
            self.write_validation_log(report_text)
        return tuple(written_paths)

    def lighting_surface_obj_file_for_export(self, surface_object):
        configured_obj_file = surface_object.get("obj_file")
        if configured_obj_file:
            return self._normalized_obj_path(configured_obj_file).replace("\\", "/")
        object_path = self.surface_object_obj_names.get(str(surface_object["name"]))
        if object_path is not None:
            return object_path.replace("\\", "/")
        surface_type = str(surface_object["surface_type"]).upper()
        if surface_type == "SPHERE":
            return self.surface_sphere_obj_name.replace("\\", "/")
        if surface_type == "RECTANGLE_WALL":
            return self.surface_wall_obj_name.replace("\\", "/")
        return self.surface_combined_obj_name.replace("\\", "/")

    def lighting_surface_mesh_file_for_export(self, surface_object):
        configured_mesh_file = surface_object.get("mesh_file")
        if configured_mesh_file:
            return self._normalized_obj_path(configured_mesh_file).replace("\\", "/")
        obj_file = self.lighting_surface_obj_file_for_export(surface_object)
        return self._mesh_file_path_for_obj(obj_file).replace("\\", "/")

    def report_generated_bounds(self):
        """Report generated mobile-particle center and perimeter bounds."""
        mobile_particles = [
            particle
            for particle in self.p_list
            if int(round(float(particle.ptype))) not in (int(PTYPE_NULL), int(PTYPE_BOUNDARY))
            and int(round(float(particle.pnum))) != 0
        ]
        if not mobile_particles:
            report_text = "Generic particle generated bounds: no mobile particles"
            print(report_text)
            self.write_validation_log(report_text)
            return None

        center_bounds = (
            min(particle.rx for particle in mobile_particles),
            max(particle.rx for particle in mobile_particles),
            min(particle.ry for particle in mobile_particles),
            max(particle.ry for particle in mobile_particles),
            min(particle.rz for particle in mobile_particles),
            max(particle.rz for particle in mobile_particles),
        )
        perimeter_bounds = (
            min(particle.rx - particle.radius for particle in mobile_particles),
            max(particle.rx + particle.radius for particle in mobile_particles),
            min(particle.ry - particle.radius for particle in mobile_particles),
            max(particle.ry + particle.radius for particle in mobile_particles),
            min(particle.rz - particle.radius for particle in mobile_particles),
            max(particle.rz + particle.radius for particle in mobile_particles),
        )
        report_text = (
            "Generic particle generated bounds:\n"
            f"  center x: [{center_bounds[0]:g}, {center_bounds[1]:g}]\n"
            f"  center y: [{center_bounds[2]:g}, {center_bounds[3]:g}]\n"
            f"  center z: [{center_bounds[4]:g}, {center_bounds[5]:g}]\n"
            f"  perimeter x: [{perimeter_bounds[0]:g}, "
            f"{perimeter_bounds[1]:g}]\n"
            f"  perimeter y: [{perimeter_bounds[2]:g}, "
            f"{perimeter_bounds[3]:g}]\n"
            f"  perimeter z: [{perimeter_bounds[4]:g}, "
            f"{perimeter_bounds[5]:g}]"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return center_bounds, perimeter_bounds

    def particle_type_name(self, ptype):
        ptype_value = int(round(float(ptype)))
        if ptype_value == int(PTYPE_NULL):
            return "null"
        if ptype_value == int(PTYPE_MOBILE):
            return "mobile"
        if ptype_value == int(PTYPE_PHOTON):
            return "photon"
        if ptype_value == int(PTYPE_REFLECTION_PHOTON):
            return "reflection_photon"
        if ptype_value == int(PTYPE_BOUNDARY):
            return "boundary"
        return f"ptype_{ptype_value}"

    def material_name(self, material_id):
        material = self.material_properties_by_id.get(int(material_id))
        if material is None:
            return f"material_{int(material_id)}"
        return str(material.get("name", f"material_{int(material_id)}"))

    def report_generation_inventory(self):
        """Print a final itemized inventory of generated particles and surfaces."""
        particle_counts_by_name_type = Counter()
        for particle in self.p_list:
            particle_type = self.particle_type_name(particle.ptype)
            material_id = int(round(float(particle.material_id)))
            particle_counts_by_name_type[
                (self.material_name(material_id), particle_type)
            ] += 1
        total_particles = sum(particle_counts_by_name_type.values())

        lines = [
            "Generated inventory:",
            "  particles:",
        ]
        if particle_counts_by_name_type:
            lines.append("    name, type, number particles")
            for name, particle_type in sorted(particle_counts_by_name_type):
                lines.append(
                    f"    {name}, {particle_type}, "
                    f"{particle_counts_by_name_type[(name, particle_type)]}"
                )
        else:
            lines.append("    none")

        lines.append("  objects:")
        if self.lighting_surface_triangle_inventory:
            lines.append("    name, type, number triangles")
            for surface in self.lighting_surface_triangle_inventory:
                lines.append(
                    f"    {surface['name']}, {surface['surface_type']}, "
                    f"{surface['triangle_count']}"
                )
        else:
            lines.append("    none")

        total_triangles = sum(
            int(surface["triangle_count"])
            for surface in self.lighting_surface_triangle_inventory
        )
        lines.append(f"  total, triangles, {total_triangles}")
        lines.append(f"  total, particles, {total_particles}")

        report_text = "\n".join(lines)
        print(report_text)
        self.write_validation_log(report_text)
        return report_text

    @staticmethod
    def next_power_of_two(value):
        value = int(math.ceil(float(value)))
        if value <= 1:
            return 1
        return 1 << (value - 1).bit_length()

    def cell_location_from_indices(self, cell_x, cell_y, cell_z):
        return (
            cell_x
            + self.cell_array_width
            * (cell_y + self.cell_array_height * cell_z)
        )

    def particle_cell_indices(self, particle):
        return (
            int(math.floor(float(particle.rx))),
            int(math.floor(float(particle.ry))),
            int(math.floor(float(particle.rz))),
        )

    def particle_corner_cell_indices(self, particle):
        radius = float(particle.radius)
        x_values = {
            int(math.floor(float(particle.rx) - radius)),
            int(math.floor(float(particle.rx) + radius)),
        }
        y_values = {
            int(math.floor(float(particle.ry) - radius)),
            int(math.floor(float(particle.ry) + radius)),
        }
        z_values = {
            int(math.floor(float(particle.rz) - radius)),
            int(math.floor(float(particle.rz) + radius)),
        }
        cells = set()
        for cell_x in x_values:
            for cell_y in y_values:
                for cell_z in z_values:
                    cells.add((cell_x, cell_y, cell_z))
        return cells

    def is_valid_cell_index(self, cell_x, cell_y, cell_z):
        return (
            0 <= cell_x < self.cell_array_width
            and 0 <= cell_y < self.cell_array_height
            and 0 <= cell_z < self.cell_array_depth
        )

    def report_cell_occupancy_capacity(self):
        """Report initial occupancy against configured Vulkan cell-list capacity."""
        center_occupancy = {}
        corner_occupancy = {}
        out_of_bounds = []

        for particle in self.p_list:
            if int(round(float(particle.pnum))) == 0:
                continue

            center_cell = self.particle_cell_indices(particle)
            if self.is_valid_cell_index(*center_cell):
                center_loc = self.cell_location_from_indices(*center_cell)
                center_occupancy.setdefault(center_loc, []).append(particle.pnum)
            else:
                out_of_bounds.append((particle.pnum, center_cell))

            for corner_cell in self.particle_corner_cell_indices(particle):
                if not self.is_valid_cell_index(*corner_cell):
                    out_of_bounds.append((particle.pnum, corner_cell))
                    continue
                corner_loc = self.cell_location_from_indices(*corner_cell)
                corner_occupancy.setdefault(corner_loc, set()).add(particle.pnum)

        def max_entry(occupancy):
            if not occupancy:
                return 0, None
            location, particles = max(
                occupancy.items(),
                key=lambda item: len(item[1]),
            )
            return len(particles), location

        max_center_count, max_center_location = max_entry(center_occupancy)
        max_corner_count, max_corner_location = max_entry(corner_occupancy)
        headroom_factor = float(
            self.itemcfg.get("cell_occupancy_runtime_headroom_factor", 1.25)
        )
        recommended_size = self.next_power_of_two(
            max_corner_count * max(1.0, headroom_factor)
        )
        configured_size = int(self.cell_occupancy_list_size)
        runtime_headroom = configured_size - max_corner_count

        if configured_size < max_corner_count:
            status = "ERROR"
        elif configured_size < recommended_size:
            status = "WARNING_HEADROOM"
        else:
            status = "OK"

        report_text = (
            "Cell occupancy capacity report:\n"
            f"  configured cell_occupancy_list_size: {configured_size}\n"
            f"  initial max particles per center cell: {max_center_count}"
            f" at loc {max_center_location}\n"
            f"  initial max particles per occupied corner cell: {max_corner_count}"
            f" at loc {max_corner_location}\n"
            f"  initial max center occupancy: {max_center_count}"
            f" at loc {max_center_location}\n"
            f"  initial max corner occupancy: {max_corner_count}"
            f" at loc {max_corner_location}\n"
            f"  runtime headroom factor: {headroom_factor:g}\n"
            f"  runtime headroom slots: {runtime_headroom}\n"
            f"  recommended cell_occupancy_list_size: {recommended_size}\n"
            f"  out-of-bounds cell references: {len(out_of_bounds)}\n"
            f"  status: {status}"
        )
        print(report_text)
        self.write_validation_log(report_text)

        if out_of_bounds:
            sample = ", ".join(
                f"p{int(pnum)}->{cell}" for pnum, cell in out_of_bounds[:8]
            )
            raise RuntimeError(
                "generated particle occupancy references cells outside the "
                f"cell array: {sample}"
            )
        if configured_size < max_corner_count:
            raise RuntimeError(
                "cell_occupancy_list_size is too small for the generated "
                f"initial state: configured {configured_size}, initial "
                f"corner occupancy {max_corner_count}"
            )
        return {
            "configured_size": configured_size,
            "max_center_count": max_center_count,
            "max_center_location": max_center_location,
            "max_corner_count": max_corner_count,
            "max_corner_location": max_corner_location,
            "recommended_size": recommended_size,
            "status": status,
        }

    def create_bin_file(self):
        os.makedirs(str(self.itemcfg.data_dir), exist_ok=True)
        self.bin_file = open(self.test_bin_name, "wb")
        self.count = 0

    def write_bin_file(self):
        if self.bin_file is None:
            raise RuntimeError("binary output file is not open")
        for particle in self.p_list:
            self.bin_file.write(particle)
            self.count += 1

    def close_bin_file(self):
        if self.bin_file is None:
            return
        self.bin_file.flush()
        self.bin_file.close()
        self.bin_file = None

    def write_particle_bin(self):
        self.create_bin_file()
        try:
            self.write_bin_file()
        finally:
            self.close_bin_file()
        return self.test_bin_name

    def write_test_file(self):
        """Write Vulkan metadata for the function-wall particle simulation."""
        particle_data_bin_file = self.test_bin_name.replace(os.sep, "/")
        report_file = self.report_file.replace(os.sep, "/")
        view_center = self.itemcfg.get(
            "view_center",
            (
                0.5 * self.cell_array_width,
                0.5 * self.cell_array_height,
                0.5 * self.cell_array_depth,
            ),
        )
        view = self.itemcfg.get("view", (0.0, 0.0, 0.0))
        if len(view) != 3:
            raise ValueError("view must contain exactly 3 values")
        view = tuple(float(value) for value in view)
        if not all(math.isfinite(value) for value in view):
            raise ValueError("view values must be finite")
        zoom = float(self.itemcfg.get("zoom", 1.0))
        if not math.isfinite(zoom) or zoom <= 0.0:
            raise ValueError("zoom must be a positive finite number")
        view_pan = self.itemcfg.get("view_pan", (0.0, 0.0))
        if len(view_pan) != 2:
            raise ValueError("view_pan must contain exactly 2 values")
        view_pan = tuple(float(value) for value in view_pan)
        if not all(math.isfinite(value) for value in view_pan):
            raise ValueError("view_pan values must be finite")
        (
            death_x_min,
            death_x_max,
            death_y_min,
            death_y_max,
            death_z_min,
            death_z_max,
        ) = self.death_bounds

        try:
            output = open(self.test_file_name, "w", encoding="ascii")
        except OSError as error:
            raise OSError(
                f"Could not create test file {self.test_file_name}: {error}"
            ) from error

        with output:
            output.write("index = 0;\n")
            python_dynamics_class = self.itemcfg.get("python_dynamics_class")
            if not python_dynamics_class:
                python_dynamics_class = (
                    "ForceDynamicsLighting"
                    if self.itemcfg.get("photon_periodic_recycle_enabled", False)
                    or self.itemcfg.get("boundary_space_lighting_enabled", False)
                    else "ForceDynamics"
                )
            output.write(
                "python_dynamics_class = "
                f'"{python_dynamics_class}";\n'
            )
            output.write(f"CellAryW = {self.cell_array_width};\n")
            output.write(f"CellAryH = {self.cell_array_height};\n")
            output.write(f"CellAryL = {self.cell_array_depth};\n")
            output.write(
                "view_center = ["
                f"{float(view_center[0]):.9f}, "
                f"{float(view_center[1]):.9f}, "
                f"{float(view_center[2]):.9f}];\n"
            )
            output.write(
                "view = ["
                f"{view[0]:.9f}, "
                f"{view[1]:.9f}, "
                f"{view[2]:.9f}];\n"
            )
            output.write(f"zoom = {zoom:.9f};\n")
            output.write(
                "view_pan = ["
                f"{view_pan[0]:.9f}, "
                f"{view_pan[1]:.9f}];\n"
            )
            clear_color = self.itemcfg.get("clear_color")
            if clear_color is not None:
                try:
                    clear_red = float(clear_color.get("red", 0.0))
                    clear_green = float(clear_color.get("green", 0.0))
                    clear_blue = float(clear_color.get("blue", 0.0))
                    clear_alpha = float(clear_color.get("alpha", 1.0))
                except (AttributeError, TypeError, ValueError) as exc:
                    raise ValueError("clear_color must contain numeric red, green, blue, and alpha values") from exc
                if not all(
                    math.isfinite(value)
                    for value in (clear_red, clear_green, clear_blue, clear_alpha)
                ):
                    raise ValueError("clear_color values must be finite")
                output.write(
                    "clear_color = {"
                    f"red = {clear_red:.9f}; "
                    f"green = {clear_green:.9f}; "
                    f"blue = {clear_blue:.9f}; "
                    f"alpha = {clear_alpha:.9f};"
                    "};\n"
                )
            gl_point_size = float(self.itemcfg.get("gl_point_size", 3.0))
            if not math.isfinite(gl_point_size) or gl_point_size <= 0.0:
                raise ValueError("gl_point_size must be a positive finite number")
            output.write(f"gl_point_size = {gl_point_size:.9f};\n")
            align_with_eye = self.itemcfg.get("align_with_eye", False)
            if not isinstance(align_with_eye, bool):
                raise ValueError("align_with_eye must be a boolean")
            output.write(
                f"align_with_eye = {'true' if align_with_eye else 'false'};\n"
            )
            if align_with_eye:
                lighting_eye_position = self.itemcfg.get("lighting_eye_position")
                lighting_eye_direction = self.itemcfg.get("lighting_eye_direction")
                if lighting_eye_position is None:
                    raise ValueError(
                        "lighting_eye_position is required when align_with_eye is true"
                    )
                if lighting_eye_direction is None:
                    raise ValueError(
                        "lighting_eye_direction is required when align_with_eye is true"
                    )
                if len(lighting_eye_position) != 3:
                    raise ValueError("lighting_eye_position must contain three values")
                if len(lighting_eye_direction) != 3:
                    raise ValueError("lighting_eye_direction must contain three values")
                lighting_eye_fov = float(
                    self.itemcfg.get("lighting_eye_fov_degrees", 90.0)
                )
                eye_view_distance = float(
                    self.itemcfg.get("eye_view_distance", 0.0)
                )
                if eye_view_distance <= 0.0:
                    raise ValueError(
                        "eye_view_distance must be greater than zero when "
                        "align_with_eye is true"
                    )
                output.write(
                    f"eye_view_distance = {eye_view_distance:.9f};\n"
                )
                output.write(
                    "lighting_eye_position = ["
                    f"{float(lighting_eye_position[0]):.9f}, "
                    f"{float(lighting_eye_position[1]):.9f}, "
                    f"{float(lighting_eye_position[2]):.9f}];\n"
                )
                output.write(
                    "lighting_eye_direction = ["
                    f"{float(lighting_eye_direction[0]):.9f}, "
                    f"{float(lighting_eye_direction[1]):.9f}, "
                    f"{float(lighting_eye_direction[2]):.9f}];\n"
                )
                output.write(
                    f"lighting_eye_fov_degrees = {lighting_eye_fov:.9f};\n"
                )
            output.write(f"radius = {self.radius:.9f};\n")
            output.write(f"num_particles = {self.number_particles};\n")
            output.write("particles_per_cell = 0;\n")
            output.write("num_particle_colliding = 0;\n")
            output.write("exp_collisions_per_cell = 0;\n")
            output.write("act_collisions_per_cell = 0;\n")
            output.write("particles_in_row = 0;\n")
            output.write("collsion_density = 0.0;\n")
            output.write("pdensity = 0.0;\n")
            output.write(
                f'particle_data_bin_file = "{particle_data_bin_file}";\n'
            )
            output.write(f'report_file = "{report_file}";\n')
            workgroups_local_size = int(
                self.itemcfg.get(
                    "workgroups_localSize",
                    self.itemcfg.get("workGroupsx", 128),
                )
            )
            if workgroups_local_size <= 0:
                raise ValueError("workgroups_localSize must be positive")
            group_count_x = (
                self.number_particles + 1 + workgroups_local_size - 1
            ) // workgroups_local_size
            output.write(f"workGroupsx = {workgroups_local_size};\n")
            output.write("workGroupsy = 1;\n")
            output.write("workGroupsz = 1;\n")
            output.write(f"groupCountX = {group_count_x};\n")
            output.write("groupCountY = 1;\n")
            output.write("groupCountZ = 1;\n")
            output.write(
                "cell_occupancy_list_size = "
                f"{self.cell_occupancy_list_size};\n"
            )
            duplicates_list_size = int(self.itemcfg.duplicates_list_size)
            if duplicates_list_size <= 0:
                raise ValueError("duplicates_list_size must be positive")
            output.write(f"duplicates_list_size = {duplicates_list_size};\n")

            output.write(f"death_x_min = {death_x_min:.9f};\n")
            output.write(f"death_x_max = {death_x_max:.9f};\n")
            output.write(f"death_y_min = {death_y_min:.9f};\n")
            output.write(f"death_y_max = {death_y_max:.9f};\n")
            output.write(f"death_z_min = {death_z_min:.9f};\n")
            output.write(f"death_z_max = {death_z_max:.9f};\n")
            photon_periodic_recycle_enabled = self.itemcfg.get(
                "photon_periodic_recycle_enabled",
                False,
            )
            if not isinstance(photon_periodic_recycle_enabled, bool):
                raise ValueError("photon_periodic_recycle_enabled must be a boolean")
            output.write(
                "photon_periodic_recycle_enabled = "
                f"{'true' if photon_periodic_recycle_enabled else 'false'};\n"
            )

            lighting_ball = self.itemcfg.get("Lighting_ball")
            if lighting_ball is not None:
                if hasattr(lighting_ball, "get"):
                    ball_x = float(lighting_ball.get("x"))
                    ball_y = float(lighting_ball.get("y"))
                    ball_z = float(lighting_ball.get("z"))
                    ball_radius = float(lighting_ball.get("radius"))
                    ball_material_id = int(lighting_ball.get("material_id", 0))
                    ball_wall_flag = int(lighting_ball.get("wall_flag", 1000))
                else:
                    if len(lighting_ball) < 4:
                        raise ValueError(
                            "Lighting_ball must contain at least x, y, z, and radius"
                        )
                    ball_x = float(lighting_ball[0])
                    ball_y = float(lighting_ball[1])
                    ball_z = float(lighting_ball[2])
                    ball_radius = float(lighting_ball[3])
                    ball_material_id = int(lighting_ball[4]) if len(lighting_ball) >= 5 else 0
                    ball_wall_flag = int(
                        self.itemcfg.get("lighting_ball_wall_flag", 1000)
                    )
                if ball_radius <= 0.0:
                    raise ValueError("Lighting_ball.radius must be greater than zero")
                output.write("Lighting_ball = {\n")
                output.write(f"    x = {ball_x:.9f};\n")
                output.write(f"    y = {ball_y:.9f};\n")
                output.write(f"    z = {ball_z:.9f};\n")
                output.write(f"    radius = {ball_radius:.9f};\n")
                output.write(f"    material_id = {ball_material_id};\n")
                output.write(f"    wall_flag = {ball_wall_flag};\n")
                output.write("};\n")

            rectangle_wall_segments = getattr(self, "rectangle_wall_segments", ())
            output.write("rectangle_wall_segments = (\n")
            for segment_index, segment in enumerate(rectangle_wall_segments):
                separator = (
                    ","
                    if segment_index + 1 < len(rectangle_wall_segments)
                    else ""
                )
                values = (
                    *segment["origin"],
                    *segment["u_axis"],
                    *segment["v_axis"],
                    segment["u_length"],
                    segment["v_length"],
                    *segment["normal"],
                    float(segment["wall_flag"]),
                    float(segment.get("material_id", 0)),
                )
                output.write(
                    "    ["
                    + ", ".join(f"{float(value):.9f}" for value in values)
                    + f"]{separator}\n"
                )
            output.write(");\n")

            active_curve_wall_segments = (
                () if rectangle_wall_segments else self.curve_wall_segments
            )
            output.write("curve_wall_segments = (\n")
            for segment_index, segment in enumerate(active_curve_wall_segments):
                separator = (
                    "," if segment_index + 1 < len(active_curve_wall_segments) else ""
                )
                values = ", ".join(f"{float(value):.9f}" for value in segment[:10])
                output.write(f"    [{values}]{separator}\n")
            output.write(");\n")

            lighting_surface_objects = self.itemcfg.get(
                "lighting_surface_objects",
                (),
            )
            output.write("lighting_surface_objects = (\n")
            for object_index, surface_object in enumerate(lighting_surface_objects):
                separator = (
                    "," if object_index + 1 < len(lighting_surface_objects) else ""
                )
                output.write("    {\n")
                output.write(f'        name = "{surface_object["name"]}";\n')
                output.write('        source = "obj";\n')
                output.write(
                    "        obj_file = "
                    f'"{self.lighting_surface_obj_file_for_export(surface_object)}";\n'
                )
                if (
                    surface_object["surface_type"] == "SPHERE"
                    or surface_object.get("mesh_file")
                ):
                    output.write(
                        "        mesh_file = "
                        f'"{self.lighting_surface_mesh_file_for_export(surface_object)}";\n'
                    )
                output.write(
                    f'        surface_type = "{surface_object["surface_type"]}";\n'
                )
                output.write(f'        surface_id = {int(surface_object["surface_id"])};\n')
                output.write(f'        material_id = {int(surface_object["material_id"])};\n')
                initial_surface_color = surface_object.get(
                    "initial_surface_color",
                    (0.0, 0.0, 0.0, 1.0),
                )
                if len(initial_surface_color) != 4:
                    raise ValueError(
                        "lighting_surface_objects."
                        f"{surface_object['name']}.initial_surface_color "
                        "must contain exactly 4 values"
                    )
                output.write(
                    "        initial_surface_color = ["
                    + ", ".join(
                        f"{float(value):.9f}" for value in initial_surface_color
                    )
                    + "];\n"
                )
                output.write(
                    "        deposit_radius = "
                    f"{float(surface_object.get('deposit_radius', 0.0)):.9f};\n"
                )
                if "rectangle_u_segments" in surface_object:
                    output.write(
                        "        rectangle_u_segments = "
                        f"{int(surface_object['rectangle_u_segments'])};\n"
                    )
                if "rectangle_v_segments" in surface_object:
                    output.write(
                        "        rectangle_v_segments = "
                        f"{int(surface_object['rectangle_v_segments'])};\n"
                    )
                if "sphere_lat_segments" in surface_object:
                    output.write(
                        "        sphere_lat_segments = "
                        f"{int(surface_object['sphere_lat_segments'])};\n"
                    )
                if "sphere_lon_segments" in surface_object:
                    output.write(
                        "        sphere_lon_segments = "
                        f"{int(surface_object['sphere_lon_segments'])};\n"
                    )
                output.write(f"    }}{separator}\n")
            output.write(");\n")

            output.write(f"wall_contact_offset = {self.wall_contact_offset:.9f};\n")
            output.write(
                "target_penetration_fraction = "
                f"{float(getattr(self, 'target_penetration_fraction', self.itemcfg.get('target_penetration_fraction', self.itemcfg.get('max_penetration_fraction', 0.5)))):.9f};\n"
            )
            output.write(
                "hard_penetration_fraction = "
                f"{float(getattr(self, 'hard_penetration_fraction', self.itemcfg.get('hard_penetration_fraction', 0.75))):.9f};\n"
            )
            output.write(
                "min_compression_frames = "
                f"{float(getattr(self, 'min_compression_frames', self.itemcfg.get('min_compression_frames', 3.0))):.9f};\n"
            )
            output.write(
                "compression_stiffness_gain = "
                f"{float(getattr(self, 'compression_stiffness_gain', self.itemcfg.get('compression_stiffness_gain', 0.0))):.9f};\n"
            )
            output.write(
                "compression_stiffness_power = "
                f"{float(getattr(self, 'compression_stiffness_power', self.itemcfg.get('compression_stiffness_power', 2.0))):.9f};\n"
            )
            output.write(f"DT = {self.dt:.9f};\n")
            output.write(
                "contact_force_measure = "
                f'"{self.itemcfg.get("contact_force_measure", "depth")}";\n'
            )
            output.write(f"hsv_sat = {float(self.itemcfg.get('hsv_sat', 1.0)):.9f};\n")
            output.write(f"hsv_val = {float(self.itemcfg.get('hsv_val', 1.0)):.9f};\n")
            self.write_color_mode_defines(output)
            self.write_material_properties(output)
            self.write_boundary_space_lighting(output)
            self.write_reflecting_wall_light_map(output)
            output.write(
                f"as_points = {1 if self.itemcfg.get('as_points', False) else 0};\n"
            )
            output.write(
                "presentation_quality = "
                f"{1 if self.itemcfg.get('presentation_quality', False) else 0};\n"
            )
            output.write(
                "dynamics_diagnostics = "
                f"{1 if self.itemcfg.get('dynamics_diagnostics', True) else 0};\n"
            )
            output.write(
                f"grid_on = {1 if self.itemcfg.get('grid_on', False) else 0};\n"
            )

        report_text = (
            "Function-wall particle test-file report:\n"
            f"  file: {self.test_file_name}\n"
            f"  particle records excluding null: {self.number_particles}\n"
            f"  mobile compute records including null: "
            f"{self.number_active_particles + 1}\n"
            f"  curve segments: {len(self.curve_wall_segments)}\n"
            f"  rectangle segments: {len(getattr(self, 'rectangle_wall_segments', ()))}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.test_file_name

    def runner(self):
        try:
            self.validate_simulation_configuration()
        except (AttributeError, TypeError, ValueError) as error:
            print(
                "Function-wall particle configuration validation stopped:\n"
                f"{error}"
            )
            return False

        self.initialize_generation()
        try:
            self.report_scene_model_toggles()
            self.report_collision_feasibility()
            self.add_null_particle()
            self.add_explicit_mobile_particles()
            self.add_configured_wall_markers()
            self.report_boundary_space_lighting()
            self.report_cell_occupancy_capacity()
            self.write_particle_bin()
            self.write_lighting_surface_objs()
            self.write_test_file()
            self.report_generated_bounds()
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self.close_bin_file()
            print(
                "Generic particle generation stopped:\n"
                f"{type(error).__name__}: {error}"
            )
            return False

        report_text = (
            "Generic particle generation complete:\n"
            f"  binary file: {self.test_bin_name}\n"
            f"  records: {self.count}\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  boundary markers: {self.number_boundary_particles}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        self.report_generation_inventory()
        return True
