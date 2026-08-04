import math
import re


COLOR_MODE_COLLISION = 0
COLOR_MODE_VELOCITY_ANGLE = 1
COLOR_MODE_SOLID = 2
COLOR_MODE_LUMENS = 3

COLOR_MODE_NAMES = {
    "COLLISION": COLOR_MODE_COLLISION,
    "VELOCITY_ANGLE": COLOR_MODE_VELOCITY_ANGLE,
    "SOLID": COLOR_MODE_SOLID,
    "LUMENS": COLOR_MODE_LUMENS,
    "COLOR_MODE_COLLISION": COLOR_MODE_COLLISION,
    "COLOR_MODE_VELOCITY_ANGLE": COLOR_MODE_VELOCITY_ANGLE,
    "COLOR_MODE_SOLID": COLOR_MODE_SOLID,
    "COLOR_MODE_LUMENS": COLOR_MODE_LUMENS,
    "VELOCITY": COLOR_MODE_VELOCITY_ANGLE,
    "HSV": COLOR_MODE_VELOCITY_ANGLE,
    "COLOR_MODE_VELOCITY": COLOR_MODE_VELOCITY_ANGLE,
}

COLOR_MAP_HSV = 0
COLOR_MAP_GRAYSCALE = 1
COLOR_MAP_HEAT = 2
COLOR_MAP_SOLID = 3

COLOR_MAP_NAMES = {
    "HSV": COLOR_MAP_HSV,
    "GRAYSCALE": COLOR_MAP_GRAYSCALE,
    "GREYSCALE": COLOR_MAP_GRAYSCALE,
    "HEAT": COLOR_MAP_HEAT,
    "SOLID": COLOR_MAP_SOLID,
    "COLOR_MAP_HSV": COLOR_MAP_HSV,
    "COLOR_MAP_GRAYSCALE": COLOR_MAP_GRAYSCALE,
    "COLOR_MAP_GREYSCALE": COLOR_MAP_GRAYSCALE,
    "COLOR_MAP_HEAT": COLOR_MAP_HEAT,
    "COLOR_MAP_SOLID": COLOR_MAP_SOLID,
}

DEFAULT_COLOR_BY_MODE = {
    COLOR_MODE_COLLISION: (0.0, 1.0, 0.0, 1.0),
    COLOR_MODE_VELOCITY_ANGLE: (1.0, 1.0, 1.0, 1.0),
    COLOR_MODE_SOLID: (1.0, 1.0, 1.0, 1.0),
    COLOR_MODE_LUMENS: (1.0, 1.0, 1.0, 1.0),
}

PARTICLE_TYPE_REGULAR = 0
PARTICLE_TYPE_PHOTON = 1
PARTICLE_TYPE_BOUNDARY = 2
PARTICLE_TYPE_REFLECTION_PHOTON = 3

PARTICLE_TYPE_NAMES = {
    "REGULAR": PARTICLE_TYPE_REGULAR,
    "PHOTON": PARTICLE_TYPE_PHOTON,
    "BOUNDARY": PARTICLE_TYPE_BOUNDARY,
    "REFLECTION_PHOTON": PARTICLE_TYPE_REFLECTION_PHOTON,
    "PARTICLE_TYPE_REGULAR": PARTICLE_TYPE_REGULAR,
    "PARTICLE_TYPE_PHOTON": PARTICLE_TYPE_PHOTON,
    "PARTICLE_TYPE_BOUNDARY": PARTICLE_TYPE_BOUNDARY,
    "PARTICLE_TYPE_REFLECTION_PHOTON": PARTICLE_TYPE_REFLECTION_PHOTON,
}

PHOTON_SURFACE_BEHAVIOR_NONE = 0
PHOTON_SURFACE_BEHAVIOR_SURFACE_COLOR = 1
PHOTON_SURFACE_BEHAVIOR_ABSORB = 2
PHOTON_SURFACE_BEHAVIOR_REFLECT = 3

PHOTON_SURFACE_BEHAVIOR_NAMES = {
    "NONE": PHOTON_SURFACE_BEHAVIOR_NONE,
    "SURFACE_COLOR": PHOTON_SURFACE_BEHAVIOR_SURFACE_COLOR,
    "ABSORB": PHOTON_SURFACE_BEHAVIOR_ABSORB,
    "REFLECT": PHOTON_SURFACE_BEHAVIOR_REFLECT,
    "PHOTON_SURFACE_BEHAVIOR_NONE": PHOTON_SURFACE_BEHAVIOR_NONE,
    "PHOTON_SURFACE_BEHAVIOR_SURFACE_COLOR": PHOTON_SURFACE_BEHAVIOR_SURFACE_COLOR,
    "PHOTON_SURFACE_BEHAVIOR_ABSORB": PHOTON_SURFACE_BEHAVIOR_ABSORB,
    "PHOTON_SURFACE_BEHAVIOR_REFLECT": PHOTON_SURFACE_BEHAVIOR_REFLECT,
}

CONTACT_ILLUMINATION_MAX = 0
CONTACT_ILLUMINATION_MIN = 1
CONTACT_ILLUMINATION_CURRENT = 2
CONTACT_ILLUMINATION_FIRST = 3

CONTACT_ILLUMINATION_NAMES = {
    "MAX": CONTACT_ILLUMINATION_MAX,
    "MIN": CONTACT_ILLUMINATION_MIN,
    "CURRENT": CONTACT_ILLUMINATION_CURRENT,
    "FIRST": CONTACT_ILLUMINATION_FIRST,
    "CONTACT_ILLUMINATION_MAX": CONTACT_ILLUMINATION_MAX,
    "CONTACT_ILLUMINATION_MIN": CONTACT_ILLUMINATION_MIN,
    "CONTACT_ILLUMINATION_CURRENT": CONTACT_ILLUMINATION_CURRENT,
    "CONTACT_ILLUMINATION_FIRST": CONTACT_ILLUMINATION_FIRST,
}

PHOTON_LIFE_TIME_PERIODIC = 0
PHOTON_LIFE_TIME_PERISH = 1

PHOTON_LIFE_TIME_NAMES = {
    "PERIODIC": PHOTON_LIFE_TIME_PERIODIC,
    "PERISH": PHOTON_LIFE_TIME_PERISH,
    "PHOTON_LIFE_TIME_PERIODIC": PHOTON_LIFE_TIME_PERIODIC,
    "PHOTON_LIFE_TIME_PERISH": PHOTON_LIFE_TIME_PERISH,
}


def parse_color_mode(raw_value):
    if isinstance(raw_value, str):
        color_mode = COLOR_MODE_NAMES.get(raw_value.strip().upper())
        if color_mode is None:
            raise ValueError(f"unknown color_mode: {raw_value}")
        return color_mode
    return int(raw_value)


def parse_color_map(raw_value):
    if raw_value is None:
        return None
    if isinstance(raw_value, str):
        color_map = COLOR_MAP_NAMES.get(raw_value.strip().upper())
        if color_map is None:
            raise ValueError(f"unknown color_map: {raw_value}")
        return color_map
    color_map = int(raw_value)
    if color_map not in COLOR_MAP_NAMES.values():
        raise ValueError(f"unknown color_map: {raw_value}")
    return color_map


def parse_material_point_size(raw_value):
    if raw_value is None:
        return None
    point_size = float(raw_value)
    if not math.isfinite(point_size) or point_size <= 0.0:
        raise ValueError("point_size must be a positive finite number")
    return point_size


def _material_keys(material):
    if hasattr(material, "keys"):
        return list(material.keys())
    if hasattr(material, "__dict__"):
        return list(vars(material).keys())
    return []


def parse_capture_angles(material):
    raw_capture_angles = _material_get(material, "capture_angles", None)
    indexed_angles = []

    if raw_capture_angles is not None:
        for index, raw_angle in enumerate(raw_capture_angles):
            indexed_angles.append((index, raw_angle))

    seen_numbered_keys = set()
    for key in _material_keys(material):
        match = re.fullmatch(r"capture_angle(\d+)", str(key))
        if match is None:
            continue
        capture_index = int(match.group(1))
        seen_numbered_keys.add(capture_index)
        indexed_angles.append((capture_index, _material_get(material, key, None)))

    for capture_index in range(128):
        if capture_index in seen_numbered_keys:
            continue
        key = f"capture_angle{capture_index}"
        raw_angle = _material_get(material, key, None)
        if raw_angle is not None:
            indexed_angles.append((capture_index, raw_angle))

    capture_angles = []
    for _index, raw_angle in sorted(indexed_angles, key=lambda item: item[0]):
        if raw_angle is None or len(raw_angle) != 3:
            raise ValueError("capture_angle values must contain exactly 3 values")
        center = float(raw_angle[0])
        plus_range = float(raw_angle[1])
        minus_range = float(raw_angle[2])
        if not all(math.isfinite(value) for value in (center, plus_range, minus_range)):
            raise ValueError("capture_angle values must be finite")
        if plus_range < 0.0 or minus_range < 0.0:
            raise ValueError("capture_angle ranges must not be negative")
        capture_angles.append((center, plus_range, minus_range))

    return tuple(capture_angles)


def default_color_for_mode(color_mode):
    return DEFAULT_COLOR_BY_MODE.get(int(color_mode), (1.0, 1.0, 1.0, 1.0))


def parse_material_color(raw_value, color_mode):
    if raw_value is None:
        return default_color_for_mode(color_mode)
    if len(raw_value) not in (3, 4):
        raise ValueError("color must contain 3 or 4 values")
    values = [float(raw_value[index]) for index in range(len(raw_value))]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("color values must be finite")
    if len(values) == 3:
        values.append(1.0)
    return tuple(max(0.0, min(1.0, value)) for value in values)


def parse_spectral_rgb(raw_value, name):
    if raw_value is None:
        return (1.0, 1.0, 1.0)
    if len(raw_value) != 3:
        raise ValueError(f"{name} must contain 3 values")
    values = [float(raw_value[index]) for index in range(3)]
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{name} values must be finite")
    return tuple(max(0.0, min(1.0, value)) for value in values)


def parse_debug_visible(raw_value):
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        normalized = raw_value.strip().lower()
        if normalized in ("true", "yes", "on", "1"):
            return True
        if normalized in ("false", "no", "off", "0"):
            return False
    return bool(raw_value)


def parse_particle_type(raw_value):
    if isinstance(raw_value, str):
        particle_type = PARTICLE_TYPE_NAMES.get(raw_value.strip().upper())
        if particle_type is None:
            raise ValueError(f"unknown particle_type: {raw_value}")
        return particle_type
    return int(raw_value)


def parse_photon_surface_behavior(raw_value):
    if isinstance(raw_value, str):
        behavior = PHOTON_SURFACE_BEHAVIOR_NAMES.get(raw_value.strip().upper())
        if behavior is None:
            raise ValueError(f"unknown photon_surface_behavior: {raw_value}")
        return behavior
    return int(raw_value)


def parse_contact_illumination(raw_value):
    if isinstance(raw_value, str):
        contact_illumination = CONTACT_ILLUMINATION_NAMES.get(raw_value.strip().upper())
        if contact_illumination is None:
            raise ValueError(f"unknown contact_illumination: {raw_value}")
        return contact_illumination
    return int(raw_value)


def parse_photon_life_time(raw_value):
    if isinstance(raw_value, str):
        photon_life_time = PHOTON_LIFE_TIME_NAMES.get(raw_value.strip().upper())
        if photon_life_time is None:
            raise ValueError(f"unknown photon_life_time: {raw_value}")
        return photon_life_time
    return int(raw_value)


DEFAULT_MATERIAL_PROPERTIES = (
    {
        "material_id": 0,
        "name": "substance",
        "particle_type": PARTICLE_TYPE_REGULAR,
        "relative_mass": 1.0,
        "thermal_velocity": 0.0,
        "color_mode": COLOR_MODE_VELOCITY_ANGLE,
        "color": default_color_for_mode(COLOR_MODE_VELOCITY_ANGLE),
        "collision_color": (1.0, 0.0, 0.0, 1.0),
        "non_collision_color": (0.0, 1.0, 0.0, 1.0),
        "debug_visible": False,
        "debug_color": (1.0, 1.0, 1.0, 1.0),
        "spectral_response": (1.0, 1.0, 1.0),
        "spectral_emission": (1.0, 1.0, 1.0),
        "photon_coupling": 1.0,
        "photon_min_relative_mass": 0.001,
        "photon_surface_behavior": PHOTON_SURFACE_BEHAVIOR_NONE,
        "photon_life_time": PHOTON_LIFE_TIME_PERIODIC,
        "contact_illumination": CONTACT_ILLUMINATION_MAX,
        "cell_density": 0.0,
    },
)


def _material_get(material, name, default):
    if hasattr(material, "get"):
        return material.get(name, default)
    return getattr(material, name, default)


def normalized_material_properties(source=None):
    raw_materials = None
    if source is not None and hasattr(source, "get"):
        raw_materials = source.get("material_properties")
    if not raw_materials:
        raw_materials = DEFAULT_MATERIAL_PROPERTIES

    materials = []
    for raw_material in raw_materials:
        material_id = int(_material_get(raw_material, "material_id", 0))
        relative_mass = float(_material_get(raw_material, "relative_mass", 1.0))
        thermal_velocity = float(_material_get(raw_material, "thermal_velocity", 0.0))
        color_mode = parse_color_mode(
            _material_get(
                raw_material,
                "color_mode",
                COLOR_MODE_VELOCITY_ANGLE,
            )
        )
        color_map = parse_color_map(_material_get(raw_material, "color_map", None))
        point_size = parse_material_point_size(
            _material_get(raw_material, "point_size", None)
        )
        capture_angles = parse_capture_angles(raw_material)
        color = parse_material_color(_material_get(raw_material, "color", None), color_mode)
        collision_color = parse_material_color(
            _material_get(raw_material, "collision_color", (1.0, 0.0, 0.0, 1.0)),
            COLOR_MODE_SOLID,
        )
        non_collision_color = parse_material_color(
            _material_get(raw_material, "non_collision_color", (0.0, 1.0, 0.0, 1.0)),
            COLOR_MODE_SOLID,
        )
        debug_visible = parse_debug_visible(
            _material_get(raw_material, "debug_visible", False)
        )
        debug_color = parse_material_color(
            _material_get(raw_material, "debug_color", None),
            COLOR_MODE_SOLID,
        )
        spectral_response = parse_spectral_rgb(
            _material_get(raw_material, "spectral_response", None),
            "spectral_response",
        )
        spectral_emission = parse_spectral_rgb(
            _material_get(raw_material, "spectral_emission", None),
            "spectral_emission",
        )
        photon_coupling = float(_material_get(raw_material, "photon_coupling", 1.0))
        photon_min_relative_mass = float(
            _material_get(raw_material, "photon_min_relative_mass", 0.001)
        )
        cell_density = float(_material_get(raw_material, "cell_density", 0.0))
        name = str(_material_get(raw_material, "name", f"material_{material_id}"))
        particle_type = parse_particle_type(
            _material_get(raw_material, "particle_type", PARTICLE_TYPE_REGULAR)
        )
        photon_surface_behavior = parse_photon_surface_behavior(
            _material_get(
                raw_material,
                "photon_surface_behavior",
                PHOTON_SURFACE_BEHAVIOR_NONE,
            )
        )
        contact_illumination = parse_contact_illumination(
            _material_get(
                raw_material,
                "contact_illumination",
                CONTACT_ILLUMINATION_MAX,
            )
        )
        photon_life_time = parse_photon_life_time(
            _material_get(
                raw_material,
                "photon_life_time",
                PHOTON_LIFE_TIME_PERIODIC,
            )
        )

        if not all(
            math.isfinite(value)
            for value in (
                relative_mass,
                thermal_velocity,
                photon_coupling,
                photon_min_relative_mass,
                cell_density,
            )
        ):
            raise ValueError("material_properties values must be finite")
        if photon_coupling < 0.0 or photon_coupling > 1.0:
            raise ValueError("photon_coupling must be between 0.0 and 1.0")
        if photon_min_relative_mass < 0.0:
            raise ValueError("photon_min_relative_mass must not be negative")
        if (
            photon_surface_behavior < PHOTON_SURFACE_BEHAVIOR_NONE
            or photon_surface_behavior > PHOTON_SURFACE_BEHAVIOR_REFLECT
        ):
            raise ValueError("photon_surface_behavior is outside the valid range")
        if (
            contact_illumination < CONTACT_ILLUMINATION_MAX
            or contact_illumination > CONTACT_ILLUMINATION_FIRST
        ):
            raise ValueError("contact_illumination is outside the valid range")
        if (
            photon_life_time < PHOTON_LIFE_TIME_PERIODIC
            or photon_life_time > PHOTON_LIFE_TIME_PERISH
        ):
            raise ValueError("photon_life_time is outside the valid range")

        materials.append(
            {
                "material_id": material_id,
                "name": name,
                "particle_type": particle_type,
                "relative_mass": relative_mass,
                "thermal_velocity": thermal_velocity,
                "color_mode": color_mode,
                "color": color,
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

    return sorted(materials, key=lambda material: int(material["material_id"]))


def write_color_mode_defines(output):
    output.write(f"COLOR_MODE_COLLISION = {COLOR_MODE_COLLISION};\n")
    output.write(f"COLOR_MODE_VELOCITY_ANGLE = {COLOR_MODE_VELOCITY_ANGLE};\n")
    output.write(f"COLOR_MODE_SOLID = {COLOR_MODE_SOLID};\n")
    output.write(f"COLOR_MODE_LUMENS = {COLOR_MODE_LUMENS};\n")


def write_color_map_defines(output):
    output.write(f"COLOR_MAP_HSV = {COLOR_MAP_HSV};\n")
    output.write(f"COLOR_MAP_GRAYSCALE = {COLOR_MAP_GRAYSCALE};\n")
    output.write(f"COLOR_MAP_HEAT = {COLOR_MAP_HEAT};\n")
    output.write(f"COLOR_MAP_SOLID = {COLOR_MAP_SOLID};\n")


def write_particle_type_defines(output):
    output.write(f"PARTICLE_TYPE_REGULAR = {PARTICLE_TYPE_REGULAR};\n")
    output.write(f"PARTICLE_TYPE_PHOTON = {PARTICLE_TYPE_PHOTON};\n")
    output.write(f"PARTICLE_TYPE_BOUNDARY = {PARTICLE_TYPE_BOUNDARY};\n")
    output.write(
        f"PARTICLE_TYPE_REFLECTION_PHOTON = {PARTICLE_TYPE_REFLECTION_PHOTON};\n"
    )


def write_photon_surface_behavior_defines(output):
    output.write(f"PHOTON_SURFACE_BEHAVIOR_NONE = {PHOTON_SURFACE_BEHAVIOR_NONE};\n")
    output.write(
        "PHOTON_SURFACE_BEHAVIOR_SURFACE_COLOR = "
        f"{PHOTON_SURFACE_BEHAVIOR_SURFACE_COLOR};\n"
    )
    output.write(f"PHOTON_SURFACE_BEHAVIOR_ABSORB = {PHOTON_SURFACE_BEHAVIOR_ABSORB};\n")
    output.write(f"PHOTON_SURFACE_BEHAVIOR_REFLECT = {PHOTON_SURFACE_BEHAVIOR_REFLECT};\n")


def write_contact_illumination_defines(output):
    output.write(f"CONTACT_ILLUMINATION_MAX = {CONTACT_ILLUMINATION_MAX};\n")
    output.write(f"CONTACT_ILLUMINATION_MIN = {CONTACT_ILLUMINATION_MIN};\n")
    output.write(f"CONTACT_ILLUMINATION_CURRENT = {CONTACT_ILLUMINATION_CURRENT};\n")
    output.write(f"CONTACT_ILLUMINATION_FIRST = {CONTACT_ILLUMINATION_FIRST};\n")


def write_photon_life_time_defines(output):
    output.write(f"PHOTON_LIFE_TIME_PERIODIC = {PHOTON_LIFE_TIME_PERIODIC};\n")
    output.write(f"PHOTON_LIFE_TIME_PERISH = {PHOTON_LIFE_TIME_PERISH};\n")


def write_material_properties(output, source=None):
    materials = normalized_material_properties(source)
    write_color_map_defines(output)
    write_particle_type_defines(output)
    write_photon_surface_behavior_defines(output)
    write_contact_illumination_defines(output)
    write_photon_life_time_defines(output)
    output.write(f"num_material_properties = {len(materials)};\n")
    output.write("material_properties = (\n")
    for material_index, material in enumerate(materials):
        separator = "," if material_index + 1 < len(materials) else ""
        output.write("    {\n")
        output.write(f"        material_id = {int(material['material_id'])};\n")
        output.write(f"        name = \"{material['name']}\";\n")
        output.write(f"        particle_type = {int(material['particle_type'])};\n")
        output.write(f"        relative_mass = {float(material['relative_mass']):.9f};\n")
        output.write(
            f"        thermal_velocity = {float(material['thermal_velocity']):.9f};\n"
        )
        output.write(f"        color_mode = {int(material['color_mode'])};\n")
        if material.get("color_map") is not None:
            output.write(f"        color_map = {int(material['color_map'])};\n")
        if material.get("point_size") is not None:
            output.write(f"        point_size = {float(material['point_size']):.9f};\n")
        capture_angles = material.get("capture_angles", ())
        if capture_angles:
            output.write("        capture_angles = (\n")
            for capture_index, capture_angle in enumerate(capture_angles):
                capture_separator = "," if capture_index + 1 < len(capture_angles) else ""
                output.write(
                    "            "
                    f"[{float(capture_angle[0]):.9f}, "
                    f"{float(capture_angle[1]):.9f}, "
                    f"{float(capture_angle[2]):.9f}]"
                    f"{capture_separator}\n"
                )
            output.write("        );\n")
        output.write(
            "        color = "
            f"[{float(material['color'][0]):.9f}, "
            f"{float(material['color'][1]):.9f}, "
            f"{float(material['color'][2]):.9f}, "
            f"{float(material['color'][3]):.9f}];\n"
        )
        collision_color = material.get("collision_color", (1.0, 0.0, 0.0, 1.0))
        output.write(
            "        collision_color = "
            f"[{float(collision_color[0]):.9f}, "
            f"{float(collision_color[1]):.9f}, "
            f"{float(collision_color[2]):.9f}, "
            f"{float(collision_color[3]):.9f}];\n"
        )
        non_collision_color = material.get("non_collision_color", (0.0, 1.0, 0.0, 1.0))
        output.write(
            "        non_collision_color = "
            f"[{float(non_collision_color[0]):.9f}, "
            f"{float(non_collision_color[1]):.9f}, "
            f"{float(non_collision_color[2]):.9f}, "
            f"{float(non_collision_color[3]):.9f}];\n"
        )
        output.write(
            "        debug_visible = "
            f"{'true' if bool(material.get('debug_visible', False)) else 'false'};\n"
        )
        debug_color = material.get("debug_color", (1.0, 1.0, 1.0, 1.0))
        output.write(
            "        debug_color = "
            f"[{float(debug_color[0]):.9f}, "
            f"{float(debug_color[1]):.9f}, "
            f"{float(debug_color[2]):.9f}, "
            f"{float(debug_color[3]):.9f}];\n"
        )
        spectral_response = material.get("spectral_response", (1.0, 1.0, 1.0))
        output.write(
            "        spectral_response = "
            f"[{float(spectral_response[0]):.9f}, "
            f"{float(spectral_response[1]):.9f}, "
            f"{float(spectral_response[2]):.9f}];\n"
        )
        spectral_emission = material.get("spectral_emission", (1.0, 1.0, 1.0))
        output.write(
            "        spectral_emission = "
            f"[{float(spectral_emission[0]):.9f}, "
            f"{float(spectral_emission[1]):.9f}, "
            f"{float(spectral_emission[2]):.9f}];\n"
        )
        output.write(
            "        photon_coupling = "
            f"{float(material.get('photon_coupling', 1.0)):.9f};\n"
        )
        output.write(
            "        photon_min_relative_mass = "
            f"{float(material.get('photon_min_relative_mass', 0.001)):.9f};\n"
        )
        output.write(
            "        photon_surface_behavior = "
            f"{int(material.get('photon_surface_behavior', PHOTON_SURFACE_BEHAVIOR_NONE))};\n"
        )
        output.write(
            "        photon_life_time = "
            f"{int(material.get('photon_life_time', PHOTON_LIFE_TIME_PERIODIC))};\n"
        )
        output.write(
            "        contact_illumination = "
            f"{int(material.get('contact_illumination', CONTACT_ILLUMINATION_MAX))};\n"
        )
        output.write(f"        cell_density = {float(material['cell_density']):.9f};\n")
        output.write(f"    }}{separator}\n")
    output.write(");\n")
