"""Open3D GUI particle viewer for Python dynamics."""

from pathlib import Path
import math
import time

from base.ForceDynamicsBase import ForceDynamics
from gbase.MaterialProperties import (
    COLOR_SCHEME_BLUE,
    COLOR_SCHEME_COLLISION,
    COLOR_SCHEME_GREEN,
    COLOR_SCHEME_HSV,
    COLOR_SCHEME_LUMENS,
    COLOR_SCHEME_RED,
    COLOR_SCHEME_WHITE,
    normalized_material_properties,
)
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


def _unit_rgb_from_config(run_configuration, key, default):
    raw_color = run_configuration.get(key, default)
    if raw_color is None or len(raw_color) < 3:
        raw_color = default
    values = [float(raw_color[index]) for index in range(3)]
    if max(values) > 1.0:
        values = [value / 255.0 for value in values]
    return [max(0.0, min(1.0, value)) for value in values]


def _lumens_brightness(particle_id, particle, dynamics, run_configuration):
    position = dynamics.GetCurrentParticlePosition(particle_id)
    eye_position = run_configuration.get("lumens_eye_position", (0.0, 0.0))
    eye_x = float(eye_position[0])
    eye_y = float(eye_position[1])
    photon_x = float(position.x)
    photon_y = float(position.y)

    current_eye_distance = math.hypot(eye_x - photon_x, eye_y - photon_y)
    eye_radius = max(0.0, float(run_configuration.get("lumens_eye_radius", 0.10)))
    if current_eye_distance > eye_radius:
        return None

    photon_angle = float(particle.VelRad.w)
    photon_dir_x, photon_dir_y = _unit_vector_from_angle(photon_angle)
    to_eye_x = eye_x - photon_x
    to_eye_y = eye_y - photon_y
    along_path = to_eye_x * photon_dir_x + to_eye_y * photon_dir_y
    if along_path < 0.0:
        return None

    closest_x = photon_x + photon_dir_x * along_path
    closest_y = photon_y + photon_dir_y * along_path
    miss_distance = math.hypot(eye_x - closest_x, eye_y - closest_y)
    if miss_distance > eye_radius:
        return None

    if eye_radius <= 1.0e-12 or not bool(run_configuration.get("lumens_fade_in", True)):
        distance_factor = 1.0
    else:
        distance_factor = 1.0 - current_eye_distance / eye_radius

    eye_angle = math.radians(float(run_configuration.get("lumens_eye_angle_degrees", 0.0)))
    eye_look_x, eye_look_y = _unit_vector_from_angle(eye_angle)
    arrival_x = -photon_dir_x
    arrival_y = -photon_dir_y
    if arrival_x * eye_look_x + arrival_y * eye_look_y < 0.0:
        return None

    arrival_angle = math.atan2(arrival_y, arrival_x)
    fov = math.radians(float(run_configuration.get("lumens_eye_fov_degrees", 90.0)))
    half_fov = max(0.0, fov * 0.5)
    angle_delta = abs(_wrap_angle_radians(arrival_angle - eye_angle))
    if angle_delta > half_fov:
        return None

    if half_fov <= 1.0e-12:
        angle_factor = 1.0
    else:
        angle_factor = 1.0 - angle_delta / half_fov
    return max(0.0, min(1.0, distance_factor * angle_factor))


def _lumens_color(particle_id, particle, dynamics, run_configuration):
    surface_color = _unit_rgb_from_config(
        run_configuration,
        "lumens_surface_color",
        (1.0, 1.0, 1.0),
    )
    brightness = _lumens_brightness(
        particle_id,
        particle,
        dynamics,
        run_configuration,
    )
    if brightness is None:
        if not bool(run_configuration.get("lumens_debug_dim", False)):
            return None
        brightness = 0.08
    return [component * brightness for component in surface_color]


def _material_color_scheme(particle, run_configuration):
    material_id = int(getattr(particle, "material_id", 0))
    try:
        materials = normalized_material_properties(run_configuration)
    except ValueError:
        return COLOR_SCHEME_HSV
    for material in materials:
        if int(material["material_id"]) == material_id:
            return int(material["color_scheme"])
    return COLOR_SCHEME_HSV


def _particle_color(particle_id, particle, dynamics, run_configuration):
    color_scheme = _material_color_scheme(particle, run_configuration)
    if color_scheme == COLOR_SCHEME_HSV:
        hsv_sat = float(run_configuration.get("hsv_sat", 0.707))
        hsv_val = float(run_configuration.get("hsv_val", 1.0))
        return _unit_color(hsv_angle(float(particle.VelRad.w), hsv_val, hsv_sat))
    if color_scheme == COLOR_SCHEME_WHITE:
        return _unit_color((255, 255, 255))
    if color_scheme == COLOR_SCHEME_RED:
        return _unit_color((255, 60, 60))
    if color_scheme == COLOR_SCHEME_GREEN:
        return _unit_color((60, 220, 90))
    if color_scheme == COLOR_SCHEME_BLUE:
        return _unit_color((65, 125, 255))
    if color_scheme == COLOR_SCHEME_LUMENS:
        return _lumens_color(particle_id, particle, dynamics, run_configuration)
    if color_scheme == COLOR_SCHEME_COLLISION:
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
            boundary_points.append(point)
            boundary_colors.append(_unit_color((255, 255, 255)))
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


def _axis_vector(axis_name):
    axis_key = str(axis_name).strip().upper()
    if axis_key == "X":
        return [1.0, 0.0, 0.0]
    if axis_key == "Y":
        return [0.0, 1.0, 0.0]
    if axis_key == "Z":
        return [0.0, 0.0, 1.0]
    raise ValueError("rectangle_wall_segments axis values must be X, Y, or Z")


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
        material.base_color = [float(color[0]), float(color[1]), float(color[2]), 1.0]
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
        target = self.run_configuration.get("camera_target")
        if target is None:
            return [0.5 * self.width, 0.5 * self.height, 0.5 * self.depth]
        return [float(value) for value in target[:3]]

    def _camera_eye(self, target):
        yaw = math.radians(float(self.run_configuration.get("camera_yaw_degrees", 35.0)))
        pitch = math.radians(float(self.run_configuration.get("camera_pitch_degrees", 25.0)))
        distance = float(
            self.run_configuration.get(
                "camera_distance",
                max(self.width, self.height, self.depth) * 2.5,
            )
        )
        return [
            target[0] + distance * math.cos(pitch) * math.cos(yaw),
            target[1] + distance * math.cos(pitch) * math.sin(yaw),
            target[2] + distance * math.sin(pitch),
        ]

    def _camera_aspect_ratio(self):
        frame = self.scene_widget.frame
        if frame.height > 0:
            return max(0.1, float(frame.width) / float(frame.height))
        window_size = self.run_configuration.get("window_size", (1200, 900))
        return max(0.1, float(window_size[0]) / float(window_size[1]))

    def _setup_camera(self):
        bounds = self._scene_bounds()
        target = self._camera_target()
        eye = self._camera_eye(target)
        projection = str(
            self.run_configuration.get("camera_projection", "orthographic")
        ).strip().lower()
        if projection in ("perspective", "persp"):
            self.scene_widget.setup_camera(
                float(self.run_configuration.get("camera_fov_degrees", 60.0)),
                bounds,
                target,
            )
            self.scene_widget.look_at(target, eye, [0.0, 0.0, 1.0])
            return

        extent = max(float(self.width), float(self.height), float(self.depth))
        ortho_scale = float(
            self.run_configuration.get("camera_ortho_scale", extent * 1.15)
        )
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
        self.scene_widget.scene.camera.look_at(target, eye, [0.0, 0.0, 1.0])

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
