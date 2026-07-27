"""Boundary-space lighting configuration shared by Python and Vulkan export."""


BOUNDARY_SPACE_SURFACE_NONE = 0
BOUNDARY_SPACE_SURFACE_SPHERE = 1
BOUNDARY_SPACE_SURFACE_RECTANGLE_WALL = 2

RETIRED_BOUNDARY_LIGHTING_CONFIG_KEYS = (
    "boundary_lighting_enabled",
    "boundary_lighting_model",
    "boundary_light_initial_rgb",
    "boundary_light_render_ambient",
    "boundary_light_render_gain",
    "boundary_space_patch_angle",
    "boundary_space_patch_radius",
    "boundary_space_patch_falloff",
    "lumens_debug_always_visible",
    "lumens_debug_color",
)
