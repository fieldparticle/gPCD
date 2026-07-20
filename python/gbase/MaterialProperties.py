import math


COLOR_MODE_COLLISION = 0
COLOR_MODE_VELOCITY = 1
COLOR_MODE_SOLID = 2
COLOR_MODE_LUMENS = 3

COLOR_MODE_NAMES = {
    "COLLISION": COLOR_MODE_COLLISION,
    "VELOCITY": COLOR_MODE_VELOCITY,
    "SOLID": COLOR_MODE_SOLID,
    "LUMENS": COLOR_MODE_LUMENS,
    "COLOR_MODE_COLLISION": COLOR_MODE_COLLISION,
    "COLOR_MODE_VELOCITY": COLOR_MODE_VELOCITY,
    "COLOR_MODE_SOLID": COLOR_MODE_SOLID,
    "COLOR_MODE_LUMENS": COLOR_MODE_LUMENS,
}

DEFAULT_COLOR_BY_MODE = {
    COLOR_MODE_COLLISION: (0.0, 1.0, 0.0, 1.0),
    COLOR_MODE_VELOCITY: (1.0, 1.0, 1.0, 1.0),
    COLOR_MODE_SOLID: (1.0, 1.0, 1.0, 1.0),
    COLOR_MODE_LUMENS: (1.0, 1.0, 1.0, 1.0),
}

PARTICLE_TYPE_REGULAR = 0
PARTICLE_TYPE_PHOTON = 1

PARTICLE_TYPE_NAMES = {
    "REGULAR": PARTICLE_TYPE_REGULAR,
    "PHOTON": PARTICLE_TYPE_PHOTON,
    "PARTICLE_TYPE_REGULAR": PARTICLE_TYPE_REGULAR,
    "PARTICLE_TYPE_PHOTON": PARTICLE_TYPE_PHOTON,
}


def parse_color_mode(raw_value):
    if isinstance(raw_value, str):
        color_mode = COLOR_MODE_NAMES.get(raw_value.strip().upper())
        if color_mode is None:
            raise ValueError(f"unknown color_mode: {raw_value}")
        return color_mode
    return int(raw_value)


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


def parse_particle_type(raw_value):
    if isinstance(raw_value, str):
        particle_type = PARTICLE_TYPE_NAMES.get(raw_value.strip().upper())
        if particle_type is None:
            raise ValueError(f"unknown particle_type: {raw_value}")
        return particle_type
    return int(raw_value)


DEFAULT_MATERIAL_PROPERTIES = (
    {
        "material_id": 0,
        "name": "substance",
        "particle_type": PARTICLE_TYPE_REGULAR,
        "relative_mass": 1.0,
        "thermal_velocity": 0.0,
        "color_mode": COLOR_MODE_VELOCITY,
        "color": default_color_for_mode(COLOR_MODE_VELOCITY),
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
                COLOR_MODE_VELOCITY,
            )
        )
        color = parse_material_color(_material_get(raw_material, "color", None), color_mode)
        cell_density = float(_material_get(raw_material, "cell_density", 0.0))
        name = str(_material_get(raw_material, "name", f"material_{material_id}"))
        particle_type = parse_particle_type(
            _material_get(raw_material, "particle_type", PARTICLE_TYPE_REGULAR)
        )

        if not all(
            math.isfinite(value)
            for value in (relative_mass, thermal_velocity, cell_density)
        ):
            raise ValueError("material_properties values must be finite")

        materials.append(
            {
                "material_id": material_id,
                "name": name,
                "particle_type": particle_type,
                "relative_mass": relative_mass,
                "thermal_velocity": thermal_velocity,
                "color_mode": color_mode,
                "color": color,
                "cell_density": cell_density,
            }
        )

    return sorted(materials, key=lambda material: int(material["material_id"]))


def write_color_mode_defines(output):
    output.write(f"COLOR_MODE_COLLISION = {COLOR_MODE_COLLISION};\n")
    output.write(f"COLOR_MODE_VELOCITY = {COLOR_MODE_VELOCITY};\n")
    output.write(f"COLOR_MODE_SOLID = {COLOR_MODE_SOLID};\n")
    output.write(f"COLOR_MODE_LUMENS = {COLOR_MODE_LUMENS};\n")


def write_particle_type_defines(output):
    output.write(f"PARTICLE_TYPE_REGULAR = {PARTICLE_TYPE_REGULAR};\n")
    output.write(f"PARTICLE_TYPE_PHOTON = {PARTICLE_TYPE_PHOTON};\n")


def write_material_properties(output, source=None):
    materials = normalized_material_properties(source)
    write_particle_type_defines(output)
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
        output.write(
            "        color = "
            f"[{float(material['color'][0]):.9f}, "
            f"{float(material['color'][1]):.9f}, "
            f"{float(material['color'][2]):.9f}, "
            f"{float(material['color'][3]):.9f}];\n"
        )
        output.write(f"        cell_density = {float(material['cell_density']):.9f};\n")
        output.write(f"    }}{separator}\n")
    output.write(");\n")
