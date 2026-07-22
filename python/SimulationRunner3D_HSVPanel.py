"""Open3D GUI particle viewer for Python dynamics."""

from pathlib import Path
import math
import time

from base.ForceDynamicsBase import ForceDynamics
from gbase.MaterialProperties import (
    COLOR_MODE_COLLISION,
    COLOR_MODE_LUMENS,
    COLOR_MODE_SOLID,
    COLOR_MODE_VELOCITY,
    normalized_material_properties,
)
from gbase.pdata import PTYPE_PHOTON
from gbase.MonitorSelection import preferred_window_position
from gbase.utilities import get_cell_dimensions, hsv_angle


def _require_open3d():
    try:
        import open3d as o3d
        import open3d.visualization.gui as gui
        import open3d.visualization.rendering as rendering
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "SimulationRunner3D_HSVPanel requires Open3D. Install it in the "
            "project venv with: .\\.venv\\Scripts\\python.exe -m pip install open3d"
        ) from exc
    return o3d, gui, rendering


def _unit_color(rgb255):
    return [max(0.0, min(1.0, float(component) / 255.0)) for component in rgb255]


def _wrap_angle_radians(angle):
    return (float(angle) + math.pi) % (2.0 * math.pi) - math.pi


def _unit_vector_from_angle(angle_radians):
    return math.cos(angle_radians), math.sin(angle_radians)


def _vector3_from_config(raw_value, default):
    if raw_value is None:
        return tuple(default)
    values = [float(raw_value[index]) for index in range(min(3, len(raw_value)))]
    while len(values) < 3:
        values.append(0.0)
    return tuple(values)


def _normalize3(vector):
    length = math.sqrt(sum(component * component for component in vector))
    if length <= 1.0e-12:
        return None
    return tuple(component / length for component in vector)


def _lighting_eye_position3(run_configuration):
    return _vector3_from_config(
        run_configuration.get("lighting_eye_position"),
        (0.0, 0.0, 0.0),
    )


def _lighting_eye_direction3(run_configuration):
    eye_position = _lighting_eye_position3(run_configuration)
    target = run_configuration.get("lighting_eye_target")
    if target is not None:
        target_position = _vector3_from_config(target, (0.0, 0.0, 0.0))
        direction = tuple(
            target_position[index] - eye_position[index]
            for index in range(3)
        )
        normalized = _normalize3(direction)
        if normalized is not None:
            return normalized

    raw_direction = run_configuration.get("lighting_eye_direction")
    if raw_direction is not None:
        normalized = _normalize3(_vector3_from_config(raw_direction, (1.0, 0.0, 0.0)))
        if normalized is not None:
            return normalized

    eye_angle = math.radians(
        float(run_configuration.get("lighting_eye_angle_degrees", 0.0))
    )
    return math.cos(eye_angle), math.sin(eye_angle), 0.0


def _reflect3(vector, normal):
    dot_value = (
        vector[0] * normal[0]
        + vector[1] * normal[1]
        + vector[2] * normal[2]
    )
    return (
        vector[0] - 2.0 * dot_value * normal[0],
        vector[1] - 2.0 * dot_value * normal[1],
        vector[2] - 2.0 * dot_value * normal[2],
    )


def _lighting_surface_brightness3(
    incoming_light,
    surface_normal,
    view_vector,
    run_configuration,
):
    shininess = max(1.0, float(run_configuration.get("lighting_specular_shininess", 32.0)))
    diffuse_strength = max(
        0.0,
        float(run_configuration.get("lighting_diffuse_strength", 0.20)),
    )
    specular_strength = max(
        0.0,
        float(run_configuration.get("lighting_specular_strength", 1.0)),
    )

    best = 0.0
    inverted_normal = (
        -surface_normal[0],
        -surface_normal[1],
        -surface_normal[2],
    )
    for normal in (surface_normal, inverted_normal):
        surface_to_light = (
            -incoming_light[0],
            -incoming_light[1],
            -incoming_light[2],
        )
        diffuse = max(
            0.0,
            normal[0] * surface_to_light[0]
            + normal[1] * surface_to_light[1]
            + normal[2] * surface_to_light[2],
        )
        reflected = _reflect3(incoming_light, normal)
        specular_alignment = max(
            0.0,
            reflected[0] * view_vector[0]
            + reflected[1] * view_vector[1]
            + reflected[2] * view_vector[2],
        )
        specular = specular_alignment ** shininess
        best = max(best, diffuse_strength * diffuse + specular_strength * specular)
    return max(0.0, min(1.0, best))


def _runtime_particle_velocity(particle_id, particle, dynamics):
    if dynamics is not None and hasattr(dynamics, "GetCurrentParticleVelocity"):
        return dynamics.GetCurrentParticleVelocity(particle_id)
    return getattr(particle, "VelRad", None)


def _unit_rgb_from_config(run_configuration, key, default):
    raw_color = run_configuration.get(key, default)
    if raw_color is None or len(raw_color) < 3:
        raw_color = default
    values = [float(raw_color[index]) for index in range(3)]
    if max(values) > 1.0:
        values = [value / 255.0 for value in values]
    return [max(0.0, min(1.0, value)) for value in values]


def _lighting_brightness(particle_id, particle, dynamics, run_configuration):
    if int(getattr(particle, "report_contacts", 0)) <= 0:
        return None

    position = dynamics.GetCurrentParticlePosition(particle_id)
    eye_x, eye_y, eye_z = _lighting_eye_position3(run_configuration)

    to_eye_x = eye_x - float(position.x)
    to_eye_y = eye_y - float(position.y)
    to_eye_z = eye_z - float(position.z)
    eye_distance = math.sqrt(
        to_eye_x * to_eye_x + to_eye_y * to_eye_y + to_eye_z * to_eye_z
    )
    if eye_distance <= 1.0e-12:
        return None

    eye_look = _lighting_eye_direction3(run_configuration)
    to_surface_x = -to_eye_x / eye_distance
    to_surface_y = -to_eye_y / eye_distance
    to_surface_z = -to_eye_z / eye_distance
    direction_dot = max(
        -1.0,
        min(
            1.0,
            to_surface_x * eye_look[0]
            + to_surface_y * eye_look[1]
            + to_surface_z * eye_look[2],
        ),
    )
    if direction_dot < 0.0:
        return None

    fov = math.radians(float(run_configuration.get("lighting_eye_fov_degrees", 90.0)))
    half_fov = max(0.0, fov * 0.5)
    angle_delta = math.acos(direction_dot)
    if angle_delta > half_fov:
        return None

    if half_fov <= 1.0e-12:
        angle_factor = 1.0
    else:
        angle_factor = 1.0 - angle_delta / half_fov

    normal_x = float(getattr(particle, "report_normal_x", 0.0))
    normal_y = float(getattr(particle, "report_normal_y", 0.0))
    normal_z = float(getattr(particle, "report_normal_z", 0.0))
    normal_length = math.sqrt(
        normal_x * normal_x + normal_y * normal_y + normal_z * normal_z
    )
    if normal_length <= 1.0e-12:
        return None

    normal_x /= normal_length
    normal_y /= normal_length
    normal_z /= normal_length
    eye_vector_x = to_eye_x / eye_distance
    eye_vector_y = to_eye_y / eye_distance
    eye_vector_z = to_eye_z / eye_distance
    velocity = _runtime_particle_velocity(particle_id, particle, dynamics)
    velocity_x = float(getattr(velocity, "x", 0.0))
    velocity_y = float(getattr(velocity, "y", 0.0))
    velocity_z = float(getattr(velocity, "z", 0.0))
    velocity_length = math.sqrt(
        velocity_x * velocity_x
        + velocity_y * velocity_y
        + velocity_z * velocity_z
    )
    if velocity_length <= 1.0e-12:
        return None

    incoming_light = (
        velocity_x / velocity_length,
        velocity_y / velocity_length,
        velocity_z / velocity_length,
    )
    surface_normal = (normal_x, normal_y, normal_z)
    view_vector = (eye_vector_x, eye_vector_y, eye_vector_z)
    return angle_factor * _lighting_surface_brightness3(
        incoming_light,
        surface_normal,
        view_vector,
        run_configuration,
    )


def _lighting_color(particle_id, particle, dynamics, run_configuration):
    material_id = int(round(float(getattr(particle, "material_id", 0.0))))
    material = _material_property_by_id(material_id, run_configuration)
    surface_color = (
        _material_unit_color_by_id(material_id, run_configuration)
        if material is not None
        else _unit_rgb_from_config(
            run_configuration,
            "lighting_surface_color",
            (1.0, 1.0, 1.0),
        )
    )
    brightness = _lighting_brightness(
        particle_id,
        particle,
        dynamics,
        run_configuration,
    )
    if brightness is None:
        return None
    return [component * brightness for component in surface_color]


def _material_property_by_id(material_id, run_configuration):
    material_id = int(material_id)
    try:
        materials = normalized_material_properties(run_configuration)
    except ValueError:
        return None
    for material in materials:
        if int(material["material_id"]) == material_id:
            return material
    return None


def _material_property(particle, run_configuration):
    material_id = int(getattr(particle, "material_id", 0))
    return _material_property_by_id(material_id, run_configuration)


def _material_color_mode(particle, run_configuration):
    material = _material_property(particle, run_configuration)
    if material is not None:
        return int(material["color_mode"])
    return COLOR_MODE_VELOCITY


def _material_unit_color(particle, run_configuration):
    material_id = int(getattr(particle, "material_id", 0))
    return _material_unit_color_by_id(material_id, run_configuration)


def _material_unit_color_by_id(material_id, run_configuration):
    material = _material_property_by_id(material_id, run_configuration)
    if material is None:
        return _unit_color((65, 125, 255))
    color = material.get("color", (0.25, 0.49, 1.0, 1.0))
    return [max(0.0, min(1.0, float(color[index]))) for index in range(3)]


def _material_debug_color(particle, run_configuration):
    material = _material_property(particle, run_configuration)
    if material is None or not bool(material.get("debug_visible", False)):
        return None
    color = material.get("debug_color", (1.0, 1.0, 1.0, 1.0))
    return [max(0.0, min(1.0, float(color[index]))) for index in range(3)]


def _is_photon_particle(particle):
    return int(round(float(getattr(particle, "ptype", 0.0)))) == int(PTYPE_PHOTON)


def _particle_color(particle_id, particle, dynamics, run_configuration):
    color_mode = _material_color_mode(particle, run_configuration)
    if _is_photon_particle(particle):
        color_mode = COLOR_MODE_LUMENS
    if color_mode == COLOR_MODE_VELOCITY:
        hsv_sat = float(run_configuration.get("hsv_sat", 0.707))
        hsv_val = float(run_configuration.get("hsv_val", 1.0))
        return _unit_color(hsv_angle(float(particle.VelRad.w), hsv_val, hsv_sat))
    if color_mode == COLOR_MODE_SOLID:
        return _material_unit_color(particle, run_configuration)
    if color_mode == COLOR_MODE_LUMENS:
        color = _lighting_color(particle_id, particle, dynamics, run_configuration)
        if color is None:
            return _material_debug_color(particle, run_configuration)
        return color
    if color_mode == COLOR_MODE_COLLISION:
        return _unit_color((65, 125, 255))
    return _unit_color((65, 125, 255))


def _is_visible_particle(dynamics, particle_id):
    if particle_id == 0:
        return False
    if hasattr(dynamics, "IsParticleActiveForLifecycle"):
        return dynamics.IsParticleActiveForLifecycle(particle_id)
    particle = dynamics.particles[particle_id]
    data = getattr(particle, "Data", None)
    if data is not None and float(getattr(data, "w", 0.0)) < 0.0:
        return False
    return True


def _particle_radius(particle):
    data = getattr(particle, "Data", None)
    if data is not None and hasattr(data, "x"):
        return float(data.x)
    return float(getattr(particle, "radius", 0.0))


def _collect_particles(dynamics, run_configuration):
    mobile_particles = []
    boundary_points = []
    boundary_colors = []

    for particle_id, particle in enumerate(dynamics.particles):
        if not _is_visible_particle(dynamics, particle_id):
            continue
        position = dynamics.GetCurrentParticlePosition(particle_id)
        point = [float(position.x), float(position.y), float(position.z)]
        if dynamics.IsBoundaryParticle(particle_id):
            color = _particle_color(
                particle_id,
                particle,
                dynamics,
                run_configuration,
            )
            if color is None:
                continue
            boundary_points.append(point)
            boundary_colors.append(color)
        else:
            color = _particle_color(
                particle_id,
                particle,
                dynamics,
                run_configuration,
            )
            if color is None:
                continue
            mobile_particles.append(
                {
                    "particle_id": particle_id,
                    "point": point,
                    "color": color,
                    "radius": _particle_radius(particle),
                }
            )

    return mobile_particles, boundary_points, boundary_colors


def _cell_box_lines(o3d, width, height, depth):
    points = [
        [0.0, 0.0, 0.0],
        [float(width), 0.0, 0.0],
        [float(width), float(height), 0.0],
        [0.0, float(height), 0.0],
        [0.0, 0.0, float(depth)],
        [float(width), 0.0, float(depth)],
        [float(width), float(height), float(depth)],
        [0.0, float(height), float(depth)],
    ]
    lines = [
        [0, 1],
        [1, 2],
        [2, 3],
        [3, 0],
        [4, 5],
        [5, 6],
        [6, 7],
        [7, 4],
        [0, 4],
        [1, 5],
        [2, 6],
        [3, 7],
    ]
    line_set = o3d.geometry.LineSet()
    line_set.points = o3d.utility.Vector3dVector(points)
    line_set.lines = o3d.utility.Vector2iVector(lines)
    line_set.colors = o3d.utility.Vector3dVector([[0.25, 0.45, 1.0] for _ in lines])
    return line_set


def _origin_axis_lines(o3d, width, height, depth):
    points = [
        [0.0, 0.0, 0.0],
        [float(width), 0.0, 0.0],
        [0.0, float(height), 0.0],
        [0.0, 0.0, float(depth)],
    ]
    lines = [
        [0, 1],
        [0, 2],
        [0, 3],
    ]
    colors = [
        [0.25, 0.45, 1.0],
        [0.25, 0.45, 1.0],
        [0.25, 0.45, 1.0],
    ]
    line_set = o3d.geometry.LineSet()
    line_set.points = o3d.utility.Vector3dVector(points)
    line_set.lines = o3d.utility.Vector2iVector(lines)
    line_set.colors = o3d.utility.Vector3dVector(colors)
    return line_set


def _box_lines_from_bounds(o3d, bounds, color):
    xmin, xmax, ymin, ymax, zmin, zmax = [float(value) for value in bounds]
    points = [
        [xmin, ymin, zmin],
        [xmax, ymin, zmin],
        [xmax, ymax, zmin],
        [xmin, ymax, zmin],
        [xmin, ymin, zmax],
        [xmax, ymin, zmax],
        [xmax, ymax, zmax],
        [xmin, ymax, zmax],
    ]
    lines = [
        [0, 1],
        [1, 2],
        [2, 3],
        [3, 0],
        [4, 5],
        [5, 6],
        [6, 7],
        [7, 4],
        [0, 4],
        [1, 5],
        [2, 6],
        [3, 7],
    ]
    line_set = o3d.geometry.LineSet()
    line_set.points = o3d.utility.Vector3dVector(points)
    line_set.lines = o3d.utility.Vector2iVector(lines)
    line_set.colors = o3d.utility.Vector3dVector([color for _ in lines])
    return line_set


def _lighting_eye_geometry(run_configuration, segment_count=96):
    if not bool(run_configuration.get("lighting_draw_eye_vector", True)):
        return None
    eye_x, eye_y, eye_z = _lighting_eye_position3(run_configuration)
    vector_length = max(0.0, float(run_configuration.get("lighting_eye_vector_length", 3.0)))
    points = [[eye_x, eye_y, eye_z]]
    lines = []
    if vector_length > 0.0:
        eye_direction = _lighting_eye_direction3(run_configuration)
        vector_endpoint = [
            eye_x + vector_length * eye_direction[0],
            eye_y + vector_length * eye_direction[1],
            eye_z + vector_length * eye_direction[2],
        ]
        points.append(vector_endpoint)
        lines.append((0, len(points) - 1))
    return points, lines


def _lighting_eye_line_set(o3d, run_configuration, color):
    geometry = _lighting_eye_geometry(run_configuration)
    if geometry is None:
        return None
    points, lines = geometry
    line_set = o3d.geometry.LineSet()
    line_set.points = o3d.utility.Vector3dVector(points)
    line_set.lines = o3d.utility.Vector2iVector(lines)
    line_set.colors = o3d.utility.Vector3dVector([color for _ in lines])
    return line_set


def _lighting_ball_config(run_configuration):
    values = run_configuration.get("Lighting_ball")
    if values is None:
        return None
    if hasattr(values, "get"):
        center = [
            float(values.get("x")),
            float(values.get("y")),
            float(values.get("z")),
        ]
        radius = float(values.get("radius"))
    else:
        if len(values) < 4:
            return None
        center = [float(values[index]) for index in range(3)]
        radius = float(values[3])
    if radius <= 0.0:
        return None
    return center, radius


def _axis_vector(axis_name):
    axis_key = str(axis_name).strip().upper()
    if axis_key == "X":
        return [1.0, 0.0, 0.0]
    if axis_key == "Y":
        return [0.0, 1.0, 0.0]
    if axis_key == "Z":
        return [0.0, 0.0, 1.0]
    raise ValueError("rectangle_wall_segments axis values must be X, Y, or Z")


def _view_rotation(raw_view):
    if raw_view is None:
        return None
    if len(raw_view) != 3:
        raise ValueError("view must be [rotx, roty, rotz] in degrees")
    return [math.radians(float(value)) for value in raw_view[:3]]


def _rotate_view_vector(vector, view_radians):
    x, y, z = [float(value) for value in vector]
    rotx, roty, rotz = view_radians

    cos_x = math.cos(rotx)
    sin_x = math.sin(rotx)
    y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x

    cos_y = math.cos(roty)
    sin_y = math.sin(roty)
    x, z = x * cos_y + z * sin_y, -x * sin_y + z * cos_y

    cos_z = math.cos(rotz)
    sin_z = math.sin(rotz)
    x, y = x * cos_z - y * sin_z, x * sin_z + y * cos_z
    return [x, y, z]


def _camera_eye_up_from_view(target, distance, raw_view):
    view_radians = _view_rotation(raw_view)
    if view_radians is None:
        return None
    eye_offset = _rotate_view_vector([0.0, 0.0, float(distance)], view_radians)
    up = _rotate_view_vector([0.0, 1.0, 0.0], view_radians)
    eye = [
        float(target[0]) + eye_offset[0],
        float(target[1]) + eye_offset[1],
        float(target[2]) + eye_offset[2],
    ]
    return eye, up


def _vector3(raw_value, default=None):
    if raw_value is None:
        return default
    if len(raw_value) != 3:
        raise ValueError("rectangle wall vectors must have exactly 3 values")
    return [float(value) for value in raw_value]


def _rectangle_wall_line_sets(o3d, rectangle_wall_segments, color):
    if not isinstance(rectangle_wall_segments, dict):
        return []

    line_sets = []
    for wall_name, wall_config in rectangle_wall_segments.items():
        origin = _vector3(wall_config.get("origin"))
        u_axis = _axis_vector(wall_config.get("u_axis"))
        v_axis = _axis_vector(wall_config.get("v_axis"))
        u_length = float(wall_config.get("u_length", 0.0))
        v_length = float(wall_config.get("v_length", 0.0))
        points = [
            origin,
            [
                origin[0] + u_axis[0] * u_length,
                origin[1] + u_axis[1] * u_length,
                origin[2] + u_axis[2] * u_length,
            ],
            [
                origin[0] + u_axis[0] * u_length + v_axis[0] * v_length,
                origin[1] + u_axis[1] * u_length + v_axis[1] * v_length,
                origin[2] + u_axis[2] * u_length + v_axis[2] * v_length,
            ],
            [
                origin[0] + v_axis[0] * v_length,
                origin[1] + v_axis[1] * v_length,
                origin[2] + v_axis[2] * v_length,
            ],
        ]
        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(points)
        line_set.lines = o3d.utility.Vector2iVector(
            [
                [0, 1],
                [1, 2],
                [2, 3],
                [3, 0],
            ]
        )
        line_set.colors = o3d.utility.Vector3dVector([color for _ in range(4)])
        line_sets.append((str(wall_name), line_set))
    return line_sets


def _point_cloud(o3d, points, colors):
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(points)
    cloud.colors = o3d.utility.Vector3dVector(colors)
    return cloud


def _particle_sphere(o3d, item, run_configuration):
    resolution = int(run_configuration.get("open3d_sphere_resolution", 16))
    resolution = max(6, min(32, resolution))
    mesh = o3d.geometry.TriangleMesh.create_sphere(
        radius=max(0.0, float(item["radius"])),
        resolution=resolution,
    )
    mesh.compute_vertex_normals()
    mesh.translate(item["point"])
    mesh.paint_uniform_color(item["color"])
    return mesh


def _material(rendering, shader="defaultUnlit", color=None, point_size=None, line_width=None):
    material = rendering.MaterialRecord()
    material.shader = shader
    if color is not None:
        alpha = float(color[3]) if len(color) >= 4 else 1.0
        material.base_color = [float(color[0]), float(color[1]), float(color[2]), alpha]
    if point_size is not None:
        material.point_size = float(point_size)
    if line_width is not None:
        material.line_width = float(line_width)
    return material


class SimulationRunner3DApp:
    def __init__(self, cfg_file, batch_mode=False, end_frame=None):
        self.o3d, self.gui, self.rendering = _require_open3d()
        self.cfg_file = cfg_file
        self.dynamics = ForceDynamics()
        self.dynamics.load_cfg_file(cfg_file)
        self.run_configuration = self.dynamics.run_configuration
        if batch_mode:
            self.run_configuration["end_frame"] = end_frame

        self.study_name = self.run_configuration.get("STUDY_NAME", Path(cfg_file).stem)
        self.width, self.height, self.depth = get_cell_dimensions(self.run_configuration)
        self.as_points = bool(self.run_configuration.get("as_points", False))
        self.boundary_as_particles = bool(
            self.run_configuration.get("boundary_as_particles", True)
        )
        self.show_boundaries = bool(self.run_configuration.get("open3d_show_boundaries", True))
        self.frame = 0
        self.paused = False
        self.last_particles = self.dynamics.particles
        self.closed = False
        self.axis_labels = []
        self.scene_geometry_names = set()
        self.frame_rate = float(self.run_configuration.get("frame_rate", 0.0))
        self.frame_interval = 1.0 / self.frame_rate if self.frame_rate > 0.0 else 0.0
        self.next_step_time = 0.0
        configured_end_frame = self.run_configuration.get("end_frame", 0)
        self.stop_frame = end_frame
        if self.stop_frame is None:
            self.stop_frame = int(configured_end_frame) if configured_end_frame else None

        self._build_window()

    def _build_window(self):
        app = self.gui.Application.instance
        app.initialize()

        window_size = self.run_configuration.get("window_size", (1200, 900))
        window_width = max(500, int(window_size[0]))
        window_height = max(400, int(window_size[1]))
        self.window = app.create_window(
            f"SimulationRunner3D - {self.study_name}",
            window_width,
            window_height,
        )
        position = preferred_window_position(window_width, window_height)
        if position is not None and hasattr(self.window, "os_frame"):
            self.window.os_frame = self.gui.Rect(
                position[0],
                position[1],
                window_width,
                window_height,
            )

        self.info_panel = self.gui.Horiz(
            0,
            self.gui.Margins(8, 6, 8, 6),
        )
        self.frame_label = self.gui.Label("")
        self.time_label = self.gui.Label("")
        self.count_label = self.gui.Label("")
        self.error_label = self.gui.Label("")
        for label in (
            self.frame_label,
            self.time_label,
            self.count_label,
            self.error_label,
        ):
            self.info_panel.add_child(label)
            self.info_panel.add_fixed(24)

        self.scene_widget = self.gui.SceneWidget()
        self.scene_widget.scene = self.rendering.Open3DScene(self.window.renderer)
        self.scene_widget.scene.set_background([0.0, 0.0, 0.0, 1.0])
        self.scene_widget.scene.set_lighting(
            self.rendering.Open3DScene.LightingProfile.MED_SHADOWS,
            [0.577, -0.577, -0.577],
        )
        self.scene_widget.set_view_controls(self.gui.SceneWidget.Controls.ROTATE_CAMERA)

        self.side_panel = self.gui.Vert(
            0,
            self.gui.Margins(8, 8, 8, 8),
        )
        self.side_panel.add_child(self.gui.Label("HSV panel pending"))
        self.side_panel_width = int(self.run_configuration.get("open3d_side_panel_width", 0))
        self.side_panel.visible = self.side_panel_width > 0

        self.window.add_child(self.info_panel)
        self.window.add_child(self.scene_widget)
        self.window.add_child(self.side_panel)
        self.window.set_on_layout(self._on_layout)
        self.window.set_on_key(self._on_key)
        self.window.set_on_close(self._on_close)
        self.window.set_on_tick_event(self._on_tick)

        self._render_scene(reset_camera=True)

    def _on_layout(self, _layout_context):
        rect = self.window.content_rect
        em = self.window.theme.font_size
        info_height = int(float(self.run_configuration.get("open3d_info_height_em", 3.2)) * em)
        side_width = self.side_panel_width if self.side_panel.visible else 0
        self.info_panel.frame = self.gui.Rect(
            rect.x,
            rect.y,
            rect.width,
            info_height,
        )
        self.scene_widget.frame = self.gui.Rect(
            rect.x,
            rect.y + info_height,
            rect.width - side_width,
            rect.height - info_height,
        )
        if self.side_panel.visible:
            self.side_panel.frame = self.gui.Rect(
                rect.x + rect.width - side_width,
                rect.y + info_height,
                side_width,
                rect.height - info_height,
            )

    def _on_key(self, event):
        if event.type != self.gui.KeyEvent.DOWN:
            return False
        if event.key == ord(" "):
            self.paused = not self.paused
            self._update_info()
            return True
        if event.key == 256:
            self.window.close()
            return True
        return False

    def _on_close(self):
        self.closed = True
        return True

    def _on_tick(self):
        if self.closed:
            return False
        if self.paused:
            return False
        now = time.perf_counter()
        if self.frame_interval > 0.0 and now < self.next_step_time:
            return False

        self.dynamics.ShaderFlags.frameNum = self.frame
        self.last_particles = self.dynamics.CollisionRun()
        self._render_scene(reset_camera=False)
        self._update_info()
        if self.frame_interval > 0.0:
            self.next_step_time = now + self.frame_interval

        if self.dynamics.collIn.ErrorReturn != self.dynamics.constants.ERROR_NONE:
            self.paused = True
        elif self.stop_frame is not None and self.frame >= self.stop_frame:
            self.window.close()
        else:
            self.frame += 1
        return True

    def _scene_bounds(self):
        return self.o3d.geometry.AxisAlignedBoundingBox(
            [0.0, 0.0, 0.0],
            [float(self.width), float(self.height), float(self.depth)],
        )

    def _camera_target(self):
        target = self.run_configuration.get(
            "view_center",
            self.run_configuration.get("camera_target"),
        )
        if target is None:
            return [0.5 * self.width, 0.5 * self.height, 0.5 * self.depth]
        return [float(value) for value in target[:3]]

    def _camera_distance(self):
        return float(
            self.run_configuration.get(
                "camera_distance",
                max(self.width, self.height, self.depth) * 2.5,
            )
        )

    def _camera_eye_up(self, target):
        distance = self._camera_distance()
        view_camera = _camera_eye_up_from_view(
            target,
            distance,
            self.run_configuration.get("view"),
        )
        if view_camera is not None:
            return view_camera

        yaw = math.radians(float(self.run_configuration.get("camera_yaw_degrees", 35.0)))
        pitch = math.radians(float(self.run_configuration.get("camera_pitch_degrees", 25.0)))
        eye = [
            target[0] + distance * math.cos(pitch) * math.cos(yaw),
            target[1] + distance * math.cos(pitch) * math.sin(yaw),
            target[2] + distance * math.sin(pitch),
        ]
        return eye, [0.0, 0.0, 1.0]

    def _camera_aspect_ratio(self):
        frame = self.scene_widget.frame
        if frame.height > 0:
            return max(0.1, float(frame.width) / float(frame.height))
        window_size = self.run_configuration.get("window_size", (1200, 900))
        return max(0.1, float(window_size[0]) / float(window_size[1]))

    def _setup_camera(self):
        bounds = self._scene_bounds()
        target = self._camera_target()
        eye, up = self._camera_eye_up(target)
        projection = str(
            self.run_configuration.get("camera_projection", "orthographic")
        ).strip().lower()
        if projection in ("perspective", "persp"):
            self.scene_widget.setup_camera(
                float(self.run_configuration.get("camera_fov_degrees", 60.0)),
                bounds,
                target,
            )
            self.scene_widget.look_at(target, eye, up)
            return

        extent = max(float(self.width), float(self.height), float(self.depth))
        ortho_scale = float(
            self.run_configuration.get("camera_ortho_scale", extent * 1.15)
        )
        zoom = float(self.run_configuration.get("zoom", 1.0))
        if zoom <= 0.0:
            zoom = 1.0
        ortho_scale /= zoom
        ortho_scale = max(0.1, ortho_scale)
        aspect = self._camera_aspect_ratio()
        half_height = 0.5 * ortho_scale
        half_width = half_height * aspect
        diagonal = math.sqrt(
            float(self.width) * float(self.width)
            + float(self.height) * float(self.height)
            + float(self.depth) * float(self.depth)
        )
        camera_distance = math.dist(eye, target)
        near_plane = float(self.run_configuration.get("camera_near_plane", 1.0))
        near_plane = max(1.0e-3, near_plane)
        far_plane = float(
            self.run_configuration.get(
                "camera_far_plane",
                max(near_plane + 1.0, camera_distance + diagonal * 2.0),
            )
        )
        far_plane = max(near_plane + 1.0e-3, far_plane)
        self.scene_widget.scene.camera.set_projection(
            self.rendering.Camera.Projection.Ortho,
            -half_width,
            half_width,
            -half_height,
            half_height,
            near_plane,
            far_plane,
        )
        self.scene_widget.scene.camera.look_at(target, eye, up)

    def _clear_axis_labels(self):
        if not hasattr(self.scene_widget, "remove_3d_label"):
            self.axis_labels = []
            return
        for label in self.axis_labels:
            self.scene_widget.remove_3d_label(label)
        self.axis_labels = []

    def _add_axis_labels(self):
        if not hasattr(self.scene_widget, "add_3d_label"):
            return
        offset = float(self.run_configuration.get("open3d_axis_label_offset", 0.15))
        label_scale = float(self.run_configuration.get("open3d_axis_label_scale", 2.0))
        label_distance = max(
            offset,
            0.08 * max(float(self.width), float(self.height), float(self.depth)),
        )
        labels = [
            ([label_distance, 0.0, 0.0], "X"),
            ([0.0, label_distance, 0.0], "Y"),
            ([0.0, 0.0, label_distance], "Z"),
        ]
        self.axis_labels = []
        for position, text in labels:
            label = self.scene_widget.add_3d_label(position, text)
            if hasattr(label, "color"):
                label.color = self.gui.Color(1.0, 1.0, 1.0, 1.0)
            if hasattr(label, "scale"):
                label.scale = label_scale
            self.axis_labels.append(label)

    def _clear_scene_geometry(self):
        scene = self.scene_widget.scene
        if hasattr(scene, "remove_geometry"):
            for name in list(self.scene_geometry_names):
                scene.remove_geometry(name)
            self.scene_geometry_names = set()
            return
        scene.clear_geometry()
        self.scene_geometry_names = set()

    def _add_scene_geometry(self, name, geometry, material):
        self.scene_widget.scene.add_geometry(name, geometry, material)
        self.scene_geometry_names.add(name)

    def _render_scene(self, reset_camera=False):
        self._clear_axis_labels()
        self._clear_scene_geometry()

        line_material = _material(
            self.rendering,
            shader="unlitLine",
            line_width=float(self.run_configuration.get("open3d_line_width", 1.0)),
        )
        self._add_scene_geometry(
            "cell_box",
            _cell_box_lines(self.o3d, self.width, self.height, self.depth),
            line_material,
        )
        self._add_scene_geometry(
            "origin_axes",
            _origin_axis_lines(self.o3d, self.width, self.height, self.depth),
            line_material,
        )
        death_bounds = self.run_configuration.get("death_bounds")
        if death_bounds is not None and len(death_bounds) == 6:
            self._add_scene_geometry(
                "death_bounds",
                _box_lines_from_bounds(
                    self.o3d,
                    death_bounds,
                    [1.0, 0.2, 0.2],
                ),
                line_material,
            )
        if self.show_boundaries and not self.boundary_as_particles:
            for wall_name, line_set in _rectangle_wall_line_sets(
                self.o3d,
                self.run_configuration.get("rectangle_wall_segments"),
                [0.2, 1.0, 0.2],
            ):
                self._add_scene_geometry(
                    f"rectangle_wall_{wall_name}",
                    line_set,
                    line_material,
                )
        lighting_ball = _lighting_ball_config(self.run_configuration)
        if lighting_ball is not None:
            center, radius = lighting_ball
            ball_mesh = self.o3d.geometry.TriangleMesh.create_sphere(
                radius=radius,
                resolution=int(
                    self.run_configuration.get("open3d_lighting_ball_resolution", 32)
                ),
            )
            ball_mesh.translate(center)
            ball_mesh.compute_vertex_normals()
            ball_color = self.run_configuration.get(
                "open3d_lighting_ball_color",
                (0.2, 1.0, 0.35),
            )
            ball_opacity = float(
                self.run_configuration.get("open3d_lighting_ball_opacity", 0.18)
            )
            self._add_scene_geometry(
                "lighting_ball_shell",
                ball_mesh,
                _material(
                    self.rendering,
                    shader="defaultLitTransparency",
                    color=[
                        float(ball_color[0]),
                        float(ball_color[1]),
                        float(ball_color[2]),
                        ball_opacity,
                    ],
                ),
            )
        lighting_eye = _lighting_eye_line_set(
            self.o3d,
            self.run_configuration,
            [1.0, 0.94, 0.47],
        )
        if lighting_eye is not None:
            self._add_scene_geometry("lighting_eye_vector", lighting_eye, line_material)
            eye_position = self.run_configuration.get("lighting_eye_position", (0.0, 0.0))
            eye_z = float(eye_position[2]) if len(eye_position) >= 3 else 0.0
            eye_marker = self.o3d.geometry.TriangleMesh.create_sphere(
                radius=float(self.run_configuration.get("lighting_eye_marker_radius", 0.05))
            )
            eye_marker.translate(
                [float(eye_position[0]), float(eye_position[1]), eye_z]
            )
            eye_marker.compute_vertex_normals()
            self._add_scene_geometry(
                "lighting_eye_center",
                eye_marker,
                _material(
                    self.rendering,
                    shader="defaultUnlit",
                    color=[1.0, 0.94, 0.47, 1.0],
                ),
            )
        self._add_axis_labels()

        if bool(self.run_configuration.get("open3d_show_axes", False)):
            axes = self.o3d.geometry.TriangleMesh.create_coordinate_frame(
                size=float(self.run_configuration.get("open3d_axis_size", 1.0)),
                origin=[0.0, 0.0, 0.0],
            )
            axes.compute_vertex_normals()
            self._add_scene_geometry(
                "axes",
                axes,
                _material(self.rendering, shader="defaultUnlit"),
            )

        mobile_particles, boundary_points, boundary_colors = _collect_particles(
            self.dynamics,
            self.run_configuration,
        )
        if self.as_points:
            mobile_points = [item["point"] for item in mobile_particles]
            mobile_colors = [item["color"] for item in mobile_particles]
            if mobile_points:
                self._add_scene_geometry(
                    "mobile_points",
                    _point_cloud(self.o3d, mobile_points, mobile_colors),
                    _material(
                        self.rendering,
                        shader="defaultUnlit",
                        point_size=float(self.run_configuration.get("open3d_point_size", 14.0)),
                    ),
                )
        else:
            for item in mobile_particles:
                self._add_scene_geometry(
                    f"particle_{item['particle_id']}",
                    _particle_sphere(self.o3d, item, self.run_configuration),
                    _material(self.rendering, shader="defaultUnlit", color=item["color"]),
                )

        if self.show_boundaries and self.boundary_as_particles and boundary_points:
            self._add_scene_geometry(
                "boundary_points",
                _point_cloud(self.o3d, boundary_points, boundary_colors),
                _material(
                    self.rendering,
                    shader="defaultUnlit",
                    point_size=float(
                        self.run_configuration.get("open3d_boundary_point_size", 12.0)
                    ),
                ),
            )

        if reset_camera:
            self._setup_camera()

    def _update_info(self):
        dt = float(self.run_configuration.get("dt", 0.0))
        mobile_count = 0
        boundary_count = 0
        for particle_id, particle in enumerate(self.dynamics.particles):
            if not _is_visible_particle(self.dynamics, particle_id):
                continue
            if self.dynamics.IsBoundaryParticle(particle_id):
                boundary_count += 1
            else:
                mobile_count += 1

        self.frame_label.text = f"Frame: {self.frame}"
        self.time_label.text = f"Time: {self.frame * dt:.6f}"
        self.count_label.text = f"Mobile: {mobile_count}  Boundary: {boundary_count}"
        if self.paused:
            state = "PAUSED"
        else:
            state = "RUNNING"
        error_code = int(self.dynamics.collIn.ErrorReturn)
        error_text = (
            "NONE"
            if error_code == self.dynamics.constants.ERROR_NONE
            else self.dynamics.ErrorDescription()
        )
        self.error_label.text = f"{state}  Error: {error_text}"

    def run(self):
        self._update_info()
        print("SimulationRunner3D controls: mouse orbit/pan/zoom, SPACE pause, ESC quit")
        self.gui.Application.instance.run()
        return self.last_particles


def run_analysis(cfg_file, batch_mode=False, end_frame=None, study=False, study_number=None):
    app = SimulationRunner3DApp(cfg_file, batch_mode=batch_mode, end_frame=end_frame)
    return app.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the Open3D particle viewer.")
    parser.add_argument(
        "cfg_file",
        nargs="?",
        default="C:/_DJ/gPCD/python/cfg_gendata/TwoParticleHorizontal.cfg",
    )
    parser.add_argument("--end-frame", type=int, default=None)
    args = parser.parse_args()
    run_analysis(args.cfg_file, end_frame=args.end_frame)
