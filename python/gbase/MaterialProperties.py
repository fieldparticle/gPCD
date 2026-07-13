import math


COLOR_SCHEME_COLLISION = 0
COLOR_SCHEME_HSV = 1
COLOR_SCHEME_WHITE = 2
COLOR_SCHEME_RED = 3
COLOR_SCHEME_GREEN = 4
COLOR_SCHEME_BLUE = 5

DEFAULT_MATERIAL_PROPERTIES = (
    {
        "material_id": 0,
        "name": "substance",
        "relative_mass": 1.0,
        "thermal_velocity": 0.0,
        "color_scheme": COLOR_SCHEME_HSV,
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
        color_scheme = int(_material_get(raw_material, "color_scheme", COLOR_SCHEME_HSV))
        cell_density = float(_material_get(raw_material, "cell_density", 0.0))
        name = str(_material_get(raw_material, "name", f"material_{material_id}"))

        if not all(
            math.isfinite(value)
            for value in (relative_mass, thermal_velocity, cell_density)
        ):
            raise ValueError("material_properties values must be finite")

        materials.append(
            {
                "material_id": material_id,
                "name": name,
                "relative_mass": relative_mass,
                "thermal_velocity": thermal_velocity,
                "color_scheme": color_scheme,
                "cell_density": cell_density,
            }
        )

    return sorted(materials, key=lambda material: int(material["material_id"]))


def write_color_scheme_defines(output):
    output.write(f"COLOR_SCHEME_COLLISION = {COLOR_SCHEME_COLLISION};\n")
    output.write(f"COLOR_SCHEME_HSV = {COLOR_SCHEME_HSV};\n")
    output.write(f"COLOR_SCHEME_WHITE = {COLOR_SCHEME_WHITE};\n")
    output.write(f"COLOR_SCHEME_RED = {COLOR_SCHEME_RED};\n")
    output.write(f"COLOR_SCHEME_GREEN = {COLOR_SCHEME_GREEN};\n")
    output.write(f"COLOR_SCHEME_BLUE = {COLOR_SCHEME_BLUE};\n")


def write_material_properties(output, source=None):
    materials = normalized_material_properties(source)
    output.write(f"num_material_properties = {len(materials)};\n")
    output.write("material_properties = (\n")
    for material_index, material in enumerate(materials):
        separator = "," if material_index + 1 < len(materials) else ""
        output.write("    {\n")
        output.write(f"        material_id = {int(material['material_id'])};\n")
        output.write(f"        name = \"{material['name']}\";\n")
        output.write(f"        relative_mass = {float(material['relative_mass']):.9f};\n")
        output.write(
            f"        thermal_velocity = {float(material['thermal_velocity']):.9f};\n"
        )
        output.write(f"        color_scheme = {int(material['color_scheme'])};\n")
        output.write(f"        cell_density = {float(material['cell_density']):.9f};\n")
        output.write(f"    }}{separator}\n")
    output.write(");\n")
