"""Boundary-space lighting configuration shared by Python and future Vulkan export."""

import math


BOUNDARY_LIGHT_MODEL_NONE = 0
BOUNDARY_LIGHT_MODEL_LIGHTING_BALL = 1

BOUNDARY_LIGHT_MODEL_NAMES = {
    "NONE": BOUNDARY_LIGHT_MODEL_NONE,
    "LIGHTINGBALL": BOUNDARY_LIGHT_MODEL_LIGHTING_BALL,
    "LIGHTING_BALL": BOUNDARY_LIGHT_MODEL_LIGHTING_BALL,
}

BOUNDARY_LIGHT_SURFACE_NONE = 0
BOUNDARY_LIGHT_SURFACE_SPHERE = 1
BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL = 2


def parse_boundary_light_model(raw_value):
    if isinstance(raw_value, str):
        model = BOUNDARY_LIGHT_MODEL_NAMES.get(raw_value.strip().upper())
        if model is None:
            raise ValueError(f"unknown boundary_lighting_model: {raw_value}")
        return model
    return int(raw_value)


def parse_boundary_light_rgb(raw_value):
    if raw_value is None:
        return 0.0, 0.0, 0.0
    if len(raw_value) not in (3, 4):
        raise ValueError("boundary_light_initial_rgb must contain 3 or 4 values")
    values = tuple(float(raw_value[index]) for index in range(3))
    if not all(math.isfinite(value) for value in values):
        raise ValueError("boundary_light_initial_rgb values must be finite")
    return tuple(max(0.0, min(1.0, value)) for value in values)
