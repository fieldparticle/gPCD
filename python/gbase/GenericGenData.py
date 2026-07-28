import os

from gbase.BoundarySpaceLighting import (
    BOUNDARY_SPACE_SURFACE_RECTANGLE_WALL,
    BOUNDARY_SPACE_SURFACE_SPHERE,
    RETIRED_BOUNDARY_LIGHTING_CONFIG_KEYS,
)
from gbase.FunctionWall import bounds as wall_bounds
from gbase.FunctionWall import evaluate_wall_at_point
from gbase.FunctionWall import parse_keyed_curve_wall_segments
from gbase.FunctionWall import sample_points
from gbase.MaterialProperties import (
    COLOR_MODE_COLLISION,
    COLOR_MODE_LUMENS,
    COLOR_MODE_NAMES,
    COLOR_MODE_SOLID,
    COLOR_MODE_VELOCITY_ANGLE,
    DEFAULT_MATERIAL_PROPERTIES,
    PARTICLE_TYPE_BOUNDARY,
    PARTICLE_TYPE_PHOTON,
    PHOTON_SURFACE_BEHAVIOR_NONE,
    PHOTON_SURFACE_BEHAVIOR_REFLECT,
    parse_debug_visible,
    parse_material_color,
    parse_particle_type,
    parse_photon_surface_behavior,
    parse_spectral_rgb,
    write_color_mode_defines,
    write_material_properties,
)
from gbase.SceneModel import apply_scene_model
from gbase.pdata import PTYPE_BOUNDARY, PTYPE_MOBILE, PTYPE_NULL, PTYPE_PHOTON, pdata
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
            color = None
            if color_mode is not None:
                try:
                    color = parse_material_color(
                        raw_material.get("color"),
                        color_mode,
                    )
                except (TypeError, ValueError) as exc:
                    errors.append(f"{context}.color is invalid: {exc}")

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

            if (
                material_id >= 0
                and relative_mass is not None
                and thermal_velocity is not None
                and cell_density is not None
                and color_mode is not None
                and color is not None
                and particle_type is not None
                and debug_visible is not None
                and debug_color is not None
                and spectral_response is not None
                and spectral_emission is not None
                and photon_coupling is not None
                and photon_min_relative_mass is not None
                and photon_surface_behavior is not None
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
                        "debug_visible": debug_visible,
                        "debug_color": debug_color,
                        "spectral_response": spectral_response,
                        "spectral_emission": spectral_emission,
                        "photon_coupling": photon_coupling,
                        "photon_min_relative_mass": photon_min_relative_mass,
                        "photon_surface_behavior": photon_surface_behavior,
                        "cell_density": cell_density,
                    }
                )

        if material_count == 0:
            errors.append("material_properties must not be empty")
        if 0 not in material_ids:
            errors.append("material_properties must define material_id 0")

        if not errors:
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

        try:
            target_penetration_fraction = float(
                self.itemcfg.get(
                    "target_penetration_fraction",
                    self.itemcfg.get("max_penetration_fraction", 0.5),
                )
            )
        except (TypeError, ValueError):
            errors.append("target_penetration_fraction must be numeric")
            target_penetration_fraction = None

        try:
            hard_penetration_fraction = float(
                self.itemcfg.get("hard_penetration_fraction", 0.75)
            )
        except (TypeError, ValueError):
            errors.append("hard_penetration_fraction must be numeric")
            hard_penetration_fraction = None

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

        particle_data = self.itemcfg.get("PARTICLE_DATA")
        particles = []
        if not particle_data:
            errors.append("PARTICLE_DATA is required and must not be empty")
        else:
            for index in range(len(particle_data)):
                name = f"p{index + 1}"
                particle = particle_data.get(name)
                if particle is None:
                    errors.append(f"PARTICLE_DATA.{name} is required")
                    continue
                try:
                    material_id = int(particle.get("material_id", 0))
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
                                self.itemcfg.get("collision_stiffness_q", 0.0),
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
        return True

    def report_collision_feasibility(self):
        """Print a kinematic collision timing estimate for configured particles."""
        if len(self.explicit_particles) < 2:
            report_text = "Collision Feasibility: fewer than two mobile particles"
            print(report_text)
            self.write_validation_log(report_text)
            return []

        dt = float(self.dt)
        target_penetration_fraction = float(
            self.itemcfg.get(
                "target_penetration_fraction",
                self.itemcfg.get("max_penetration_fraction", 0.5),
            )
        )
        hard_penetration_fraction = float(
            self.itemcfg.get("hard_penetration_fraction", 0.75)
        )
        min_compression_frames = float(
            self.itemcfg.get("min_compression_frames", 3.0)
        )
        compression_stiffness_gain = max(
            0.0,
            float(self.itemcfg.get("compression_stiffness_gain", 0.0)),
        )
        compression_stiffness_power = max(
            0.0,
            float(self.itemcfg.get("compression_stiffness_power", 2.0)),
        )
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

        output_prefix = str(
            self.itemcfg.get("output_file_prefix", self.itemcfg.STUDY_NAME)
        )
        output_directory = str(self.itemcfg.data_dir)
        os.makedirs(output_directory, exist_ok=True)
        self.test_bin_name = os.path.join(output_directory, f"{output_prefix}.bin")
        self.test_file_name = os.path.join(output_directory, f"{output_prefix}.tst")
        self.report_file = os.path.join(output_directory, f"{output_prefix}.rpt")
        self.validation_log_name = os.path.join(output_directory, f"{output_prefix}.log")
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
            ptype = (
                PTYPE_PHOTON
                if material_particle_type == PARTICLE_TYPE_PHOTON
                else PTYPE_BOUNDARY
                if material_particle_type == PARTICLE_TYPE_BOUNDARY
                else PTYPE_MOBILE
            )
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
            material_id = int(round(segment[10])) if len(segment) >= 11 else 0
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
        faces = []

        for segment in self.curve_wall_segments:
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
                vertices.append(
                    (
                        point_x - half_thickness * normal_x,
                        point_y - half_thickness * normal_y,
                        self.particle_plane_z,
                    )
                )
                segment_vertices.append((first_index, first_index + 1))

            for index in range(len(segment_vertices) - 1):
                outer_a, inner_a = segment_vertices[index]
                outer_b, inner_b = segment_vertices[index + 1]
                faces.append((outer_a, outer_b, inner_b))
                faces.append((outer_a, inner_b, inner_a))

        os.makedirs(os.path.dirname(self.obj_file_name), exist_ok=True)
        with open(self.obj_file_name, "w", encoding="ascii", newline="\n") as output:
            output.write("# Generated from function-wall curve_wall_segments.\n")
            output.write("# Dynamics use boundary particles; this mesh is visual only.\n")
            output.write("o GeneratedFunctionWalls\n")
            for vertex_x, vertex_y, vertex_z in vertices:
                output.write(
                    f"v {vertex_x:.9f} {vertex_y:.9f} {vertex_z:.9f}\n"
                )
            for _ in vertices:
                output.write("vt 0.0 0.0\n")
            output.write("vn 0.0 0.0 1.0\n")
            output.write("vn 0.0 0.0 -1.0\n")
            for first, second, third in faces:
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
            f"  triangles: {2 * len(faces)}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.obj_file_name

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
                    "material_id": lighting_ball["material_id"],
                    "surface_id": lighting_ball["surface_id"],
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
            surface_object = {
                "name": str(segment["name"]),
                "material_id": int(segment.get("material_id", 0)),
                "surface_id": int(segment["wall_flag"]),
                "faces": [],
            }
            obj_data["objects"].append(surface_object)
            origin = segment["origin"]
            u_axis = segment["u_axis"]
            v_axis = segment["v_axis"]
            normal = segment["normal"]
            u_length = float(segment["u_length"])
            v_length = float(segment["v_length"])
            lighting_surface = self._lighting_surface_object_by_type_and_id(
                "RECTANGLE_WALL",
                int(segment["wall_flag"]),
            )
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
                        "material_id": surface_object["material_id"],
                        "surface_id": surface_object["surface_id"],
                        "faces": tuple(
                            tuple(vertex_id + vertex_offset for vertex_id in face)
                            for face in surface_object["faces"]
                        ),
                    }
                )
            vertex_offset += len(obj_data["vertices"])
        return merged

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
        if wall_obj is not None:
            written_paths.append(
                self._write_surface_obj(
                    self.surface_wall_obj_name,
                    wall_obj,
                    "Generated LightingBall rectangle wall surface",
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

        if written_paths:
            report_text = (
                "Lighting surface OBJ report:\n"
                + "\n".join(f"  file: {path}" for path in written_paths)
            )
            print(report_text)
            self.write_validation_log(report_text)
        return tuple(written_paths)

    def lighting_surface_obj_file_for_export(self, surface_object):
        surface_type = str(surface_object["surface_type"]).upper()
        if surface_type == "SPHERE":
            return self.surface_sphere_obj_name.replace("\\", "/")
        if surface_type == "RECTANGLE_WALL":
            return self.surface_wall_obj_name.replace("\\", "/")
        return self.surface_combined_obj_name.replace("\\", "/")

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
                output.write(
                    f'        surface_type = "{surface_object["surface_type"]}";\n'
                )
                output.write(f'        surface_id = {int(surface_object["surface_id"])};\n')
                output.write(f'        material_id = {int(surface_object["material_id"])};\n')
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
                "compression_stiffness_gain = "
                f"{float(self.itemcfg.get('compression_stiffness_gain', 0.0)):.9f};\n"
            )
            output.write(
                "compression_stiffness_power = "
                f"{float(self.itemcfg.get('compression_stiffness_power', 2.0)):.9f};\n"
            )
            output.write(f"DT = {self.dt:.9f};\n")
            output.write(
                "contact_force_measure = "
                f'"{self.itemcfg.get("contact_force_measure", "depth")}";\n'
            )
            output.write(f"hsv_sat = {float(self.itemcfg.hsv_sat):.9f};\n")
            output.write(f"hsv_val = {float(self.itemcfg.hsv_val):.9f};\n")
            self.write_color_mode_defines(output)
            self.write_material_properties(output)
            self.write_boundary_space_lighting(output)
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
            self.report_collision_feasibility()
            self.add_null_particle()
            self.add_explicit_mobile_particles()
            self.add_configured_wall_markers()
            self.report_boundary_space_lighting()
            self.report_cell_occupancy_capacity()
            self.write_particle_bin()
            self.write_test_file()
            self.write_lighting_surface_objs()
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
        return True
