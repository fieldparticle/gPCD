"""PyVista particle viewer for Python 3D dynamics."""

from pathlib import Path
import math
import os
import subprocess
import sys
import time

from base.DynamicsFactory import create_dynamics_for_cfg
from base.Reporting import Reporting
from gbase.MonitorSelection import preferred_window_position
from gbase.utilities import get_cell_dimensions
from SimulationRunner3D_HSVPanel import (
    _axis_vector,
    _camera_eye_up_from_view,
    _collect_particles,
    _is_visible_particle,
    _lighting_eye_geometry,
)
from SimulationRunner_HSVPanel import (
    _report_particles,
    _run_start_diagnostics,
)


def _require_pyvista():
    try:
        import numpy as np
        import pyvista as pv
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "SimulationRunner3D_PyVista requires PyVista. Install it in the "
            "project venv with: .\\.venv\\Scripts\\python.exe -m pip install pyvista"
        ) from exc
    return np, pv


def _window_size(run_configuration):
    window_size = run_configuration.get("window_size", (1200, 900))
    return max(500, int(window_size[0])), max(400, int(window_size[1]))


def _disable_windows_close_button(window_title):
    if os.name != "nt":
        return
    try:
        import ctypes
    except ImportError:
        return

    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, window_title)
    if not hwnd:
        return

    SC_CLOSE = 0xF060
    MF_BYCOMMAND = 0x00000000
    GWL_STYLE = -16
    WS_SYSMENU = 0x00080000

    menu = user32.GetSystemMenu(hwnd, False)
    if menu:
        user32.RemoveMenu(menu, SC_CLOSE, MF_BYCOMMAND)
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    if style:
        user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_SYSMENU)
    user32.DrawMenuBar(hwnd)


def _vector3(raw_value, default=None):
    if raw_value is None:
        return default
    if len(raw_value) != 3:
        raise ValueError("rectangle wall vectors must have exactly 3 values")
    return [float(value) for value in raw_value]


def _line_polydata(np, pv, points, line_pairs):
    line_data = []
    for first, second in line_pairs:
        line_data.extend((2, int(first), int(second)))
    polydata = pv.PolyData(np.array(points, dtype=float))
    polydata.lines = np.array(line_data, dtype=np.int_)
    return polydata


def _cell_box_polydata(np, pv, width, height, depth):
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
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    ]
    return _line_polydata(np, pv, points, lines)


def _origin_axes_polydata(np, pv, width, height, depth):
    points = [
        [0.0, 0.0, 0.0],
        [float(width), 0.0, 0.0],
        [0.0, float(height), 0.0],
        [0.0, 0.0, float(depth)],
    ]
    return _line_polydata(np, pv, points, [(0, 1), (0, 2), (0, 3)])


def _box_polydata_from_bounds(np, pv, bounds):
    xmin, xmax, ymin, ymax, zmin, zmax = [float(value) for value in bounds]
    return _cell_box_polydata(np, pv, xmax - xmin, ymax - ymin, zmax - zmin).translate(
        (xmin, ymin, zmin),
        inplace=False,
    )


def _rectangle_wall_polydata(np, pv, rectangle_wall_segments):
    if not isinstance(rectangle_wall_segments, dict):
        return []

    walls = []
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
        walls.append(
            (
                str(wall_name),
                _line_polydata(np, pv, points, [(0, 1), (1, 2), (2, 3), (3, 0)]),
            )
        )
    return walls


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


def _axis_label_origin_distance(width, height, depth, offset):
    extent = max(float(width), float(height), float(depth))
    return max(float(offset), extent * 0.08)


def _axis_label_points(width, height, depth, offset):
    distance = _axis_label_origin_distance(width, height, depth, offset)
    return [
        [distance, 0.0, 0.0],
        [0.0, distance, 0.0],
        [0.0, 0.0, distance],
    ]


def _point_cloud(np, pv, points, colors):
    cloud = pv.PolyData(np.array(points, dtype=float))
    rgb = np.clip(np.array(colors, dtype=float) * 255.0, 0.0, 255.0).astype(np.uint8)
    cloud["rgb"] = rgb
    return cloud


class SimulationRunner3DPyVistaApp:
    def __init__(self, cfg_file, batch_mode=False, end_frame=None):
        self.np, self.pv = _require_pyvista()
        self.cfg_file = cfg_file
        self.dynamics = create_dynamics_for_cfg(cfg_file)
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
        self.show_boundaries = bool(
            self.run_configuration.get("pyvista_show_boundaries", True)
        )
        self.frame = 0
        self.paused = False
        self.closed = False
        self.closing = False
        self.native_window_closed = False
        self.programmatic_close = False
        self.last_particles = self.dynamics.particles
        self.frame_rate = float(self.run_configuration.get("frame_rate", 0.0))
        self.frame_interval = 1.0 / self.frame_rate if self.frame_rate > 0.0 else 0.0
        self.next_step_time = 0.0
        configured_end_frame = self.run_configuration.get("end_frame", 0)
        self.stop_frame = end_frame
        if self.stop_frame is None:
            self.stop_frame = int(configured_end_frame) if configured_end_frame else None

        self.dynamics_diagnostics = bool(
            self.run_configuration.get("dynamics_diagnostics", False)
        )
        self.reporting = None
        self.start_diagnostics = None
        if self.dynamics_diagnostics:
            if "run_debug_dir" not in self.run_configuration:
                raise RuntimeError(
                    "SimulationRunner3D_PyVista requires run_debug_dir when "
                    "dynamics_diagnostics is enabled"
                )
            self.reporting = Reporting(
                Path(self.run_configuration["run_debug_dir"]),
                self.run_configuration.get("rpt_frames"),
            )
            self.start_diagnostics = _run_start_diagnostics(self.dynamics)
            print(
                "SimulationRunner3D_PyVista cleared "
                f"{self.reporting.cleared_report_count} report file(s): "
                f"{self.reporting.output_dir}"
            )

        self.plotter = None
        self.status_actor = None
        self.static_geometry_rendered = False

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

    def _apply_view_pan(self, eye, target, up):
        view_pan = self.run_configuration.get("view_pan", (0.0, 0.0))
        if len(view_pan) != 2:
            raise ValueError("view_pan must contain exactly 2 values")
        pan_right = float(view_pan[0])
        pan_up = float(view_pan[1])
        if not math.isfinite(pan_right) or not math.isfinite(pan_up):
            raise ValueError("view_pan values must be finite")
        if abs(pan_right) <= 1.0e-12 and abs(pan_up) <= 1.0e-12:
            return eye, target

        view_dir = [
            float(target[0]) - float(eye[0]),
            float(target[1]) - float(eye[1]),
            float(target[2]) - float(eye[2]),
        ]
        view_len = math.sqrt(sum(value * value for value in view_dir))
        up_len = math.sqrt(sum(float(value) * float(value) for value in up))
        if view_len <= 1.0e-12 or up_len <= 1.0e-12:
            return eye, target
        view_dir = [value / view_len for value in view_dir]
        up_unit = [float(value) / up_len for value in up]
        screen_right = [
            up_unit[1] * view_dir[2] - up_unit[2] * view_dir[1],
            up_unit[2] * view_dir[0] - up_unit[0] * view_dir[2],
            up_unit[0] * view_dir[1] - up_unit[1] * view_dir[0],
        ]
        right_len = math.sqrt(sum(value * value for value in screen_right))
        if right_len <= 1.0e-12:
            return eye, target
        screen_right = [value / right_len for value in screen_right]
        pan = [
            pan_right * screen_right[index] + pan_up * up_unit[index]
            for index in range(3)
        ]
        return (
            [float(eye[index]) + pan[index] for index in range(3)],
            [float(target[index]) + pan[index] for index in range(3)],
        )

    def _camera_scale(self):
        extent = max(float(self.width), float(self.height), float(self.depth))
        zoom = float(self.run_configuration.get("zoom", 1.0))
        if zoom <= 0.0:
            zoom = 1.0
        scale = float(self.run_configuration.get("camera_ortho_scale", extent * 1.15))
        return max(0.1, scale / zoom)

    def _setup_camera(self):
        target = self._camera_target()
        eye, up = self._camera_eye_up(target)
        eye, target = self._apply_view_pan(eye, target, up)
        self.plotter.camera_position = (eye, target, up)
        self.plotter.enable_parallel_projection()
        self.plotter.camera.parallel_scale = self._camera_scale()

    def _current_camera_view_zoom_hint(self):
        if self.plotter is None:
            return (
                f"view={self.run_configuration.get('view')}, "
                f"zoom={self.run_configuration.get('zoom', 1.0)}"
            )
        camera = self.plotter.camera
        eye = camera.position
        target = camera.focal_point
        up = camera.up
        offset = (
            float(eye[0]) - float(target[0]),
            float(eye[1]) - float(target[1]),
            float(eye[2]) - float(target[2]),
        )
        offset_len = math.sqrt(
            offset[0] * offset[0]
            + offset[1] * offset[1]
            + offset[2] * offset[2]
        )
        up_len = math.sqrt(
            float(up[0]) * float(up[0])
            + float(up[1]) * float(up[1])
            + float(up[2]) * float(up[2])
        )
        view_text = str(self.run_configuration.get("view"))
        if offset_len > 1.0e-12 and up_len > 1.0e-12:
            z_axis = tuple(value / offset_len for value in offset)
            y_axis = tuple(float(value) / up_len for value in up)
            x_axis = (
                y_axis[1] * z_axis[2] - y_axis[2] * z_axis[1],
                y_axis[2] * z_axis[0] - y_axis[0] * z_axis[2],
                y_axis[0] * z_axis[1] - y_axis[1] * z_axis[0],
            )
            x_len = math.sqrt(
                x_axis[0] * x_axis[0]
                + x_axis[1] * x_axis[1]
                + x_axis[2] * x_axis[2]
            )
            if x_len > 1.0e-12:
                x_axis = tuple(value / x_len for value in x_axis)
                # Rotation matrix columns are x_axis, y_axis, z_axis. This
                # inverts the same Rz * Ry * Rx order used by Python view.
                r20 = x_axis[2]
                r20 = max(-1.0, min(1.0, r20))
                rot_y = math.asin(-r20)
                cos_y = math.cos(rot_y)
                if abs(cos_y) > 1.0e-8:
                    rot_x = math.atan2(y_axis[2], z_axis[2])
                    rot_z = math.atan2(x_axis[1], x_axis[0])
                else:
                    rot_x = 0.0
                    rot_z = math.atan2(-y_axis[0], y_axis[1])
                view_text = (
                    f"[{math.degrees(rot_x):.1f}, "
                    f"{math.degrees(rot_y):.1f}, "
                    f"{math.degrees(rot_z):.1f}]"
                )

        extent = max(float(self.width), float(self.height), float(self.depth))
        base_scale = float(
            self.run_configuration.get("camera_ortho_scale", extent * 1.15)
        )
        parallel_scale = max(1.0e-12, float(camera.parallel_scale))
        zoom = base_scale / parallel_scale
        return f"view={view_text}   zoom={zoom:.3f}"

    def _build_plotter(self):
        window_width, window_height = _window_size(self.run_configuration)
        self.window_title = f"SimulationRunner3D PyVista - {self.study_name}"
        self.plotter = self.pv.Plotter(
            window_size=(window_width, window_height),
            title=self.window_title,
        )
        position = preferred_window_position(window_width, window_height)
        if position is not None:
            self.plotter.ren_win.SetPosition(position[0], position[1])
        self.plotter.set_background("black")
        self.plotter.add_key_event("space", self._toggle_pause)
        self.plotter.add_key_event("Escape", self._close)
        self._render_scene(reset_camera=True)

    def _close_quietly_on_window_error(self, exc):
        self._mark_closed()
        print(f"SimulationRunner3D PyVista window closed: {exc}")

    def _mark_closed(self, *_args):
        self.closed = True
        self.closing = True

    def _mark_native_window_closed(self, *_args):
        self.native_window_closed = True
        self._mark_closed()

    def _install_close_observers(self):
        if self.plotter is None:
            return
        iren = getattr(self.plotter, "iren", None)
        render_window = getattr(self.plotter, "ren_win", None)
        observer_sources = []
        if render_window is not None:
            observer_sources.append((render_window, "AddObserver"))
        if iren is not None:
            observer_sources.append((iren, "add_observer"))
            interactor = getattr(iren, "interactor", None)
            if interactor is not None:
                observer_sources.append((interactor, "AddObserver"))

        for observer_source, method_name in observer_sources:
            add_observer = getattr(observer_source, method_name, None)
            if add_observer is None:
                continue
            for event_name in ("ExitEvent", "WindowCloseEvent", "DeleteEvent"):
                try:
                    add_observer(event_name, self._mark_native_window_closed)
                except (AttributeError, TypeError, RuntimeError):
                    pass

    def _toggle_pause(self):
        if self.closing:
            return
        self.paused = not self.paused
        self._update_status()

    def _close(self):
        self.programmatic_close = True
        self._mark_closed()
        if self.plotter is not None:
            try:
                self.plotter.close()
            except (AttributeError, RuntimeError, TypeError, ValueError):
                pass

    def _is_plotter_closed(self):
        if self.closed or self.closing:
            return True
        if self.plotter is None:
            return True
        iren = getattr(self.plotter, "iren", None)
        interactor = getattr(iren, "interactor", None)
        if interactor is not None and hasattr(interactor, "GetDone"):
            return bool(interactor.GetDone())
        return False

    def _render_static_geometry(self):
        if self.static_geometry_rendered:
            return
        line_width = float(self.run_configuration.get("pyvista_line_width", 2.0))
        self.plotter.add_mesh(
            _cell_box_polydata(self.np, self.pv, self.width, self.height, self.depth),
            color=(0.25, 0.45, 1.0),
            line_width=line_width,
            name="cell_box",
        )
        self.plotter.add_mesh(
            _origin_axes_polydata(self.np, self.pv, self.width, self.height, self.depth),
            color=(0.45, 0.65, 1.0),
            line_width=line_width,
            name="origin_axes",
        )
        death_bounds = self.run_configuration.get("death_bounds")
        if death_bounds is not None and len(death_bounds) == 6:
            self.plotter.add_mesh(
                _box_polydata_from_bounds(self.np, self.pv, death_bounds),
                color=(1.0, 0.2, 0.2),
                line_width=line_width,
                name="death_bounds",
            )
        if self.show_boundaries and not self.boundary_as_particles:
            for wall_name, wall_mesh in _rectangle_wall_polydata(
                self.np,
                self.pv,
                self.run_configuration.get("rectangle_wall_segments"),
            ):
                self.plotter.add_mesh(
                    wall_mesh,
                    color=(0.2, 1.0, 0.2),
                    line_width=line_width,
                    name=f"rectangle_wall_{wall_name}",
                )
        lighting_ball = _lighting_ball_config(self.run_configuration)
        if lighting_ball is not None:
            center, radius = lighting_ball
            self.plotter.add_mesh(
                self.pv.Sphere(
                    radius=radius,
                    center=center,
                    theta_resolution=int(
                        self.run_configuration.get(
                            "pyvista_lighting_ball_theta_resolution",
                            48,
                        )
                    ),
                    phi_resolution=int(
                        self.run_configuration.get(
                            "pyvista_lighting_ball_phi_resolution",
                            24,
                        )
                    ),
                ),
                color=tuple(
                    float(value)
                    for value in self.run_configuration.get(
                        "pyvista_lighting_ball_color",
                        (0.2, 1.0, 0.35),
                    )[:3]
                ),
                opacity=float(
                    self.run_configuration.get("pyvista_lighting_ball_opacity", 0.18)
                ),
                smooth_shading=True,
                name="lighting_ball_shell",
            )
        lighting_eye = _lighting_eye_geometry(self.run_configuration)
        if lighting_eye is not None:
            points, lines = lighting_eye
            if lines:
                self.plotter.add_mesh(
                    _line_polydata(self.np, self.pv, points, lines),
                    color=(1.0, 0.94, 0.47),
                    line_width=line_width,
                    name="lighting_eye_vector",
                )
            self.plotter.add_points(
                self.np.array([points[0]], dtype=float),
                color=(1.0, 0.94, 0.47),
                point_size=float(
                    self.run_configuration.get("pyvista_lighting_eye_point_size", 10.0)
                ),
                render_points_as_spheres=True,
                name="lighting_eye_center",
            )
        self._render_axis_labels()
        self.static_geometry_rendered = True

    def _render_axis_labels(self):
        if not bool(self.run_configuration.get("pyvista_show_axis_labels", True)):
            return
        offset = float(
            self.run_configuration.get(
                "pyvista_axis_label_offset",
                self.run_configuration.get("open3d_axis_label_offset", 0.15),
            )
        )
        font_size = int(self.run_configuration.get("pyvista_axis_label_font_size", 16))
        self.plotter.add_point_labels(
            _axis_label_points(self.width, self.height, self.depth, offset),
            ["X", "Y", "Z"],
            name="axis_labels",
            font_size=font_size,
            text_color="white",
            point_color="white",
            point_size=0,
            shape=None,
            always_visible=True,
        )

    def _remove_actor(self, actor_name):
        if self.closing or self.plotter is None:
            return
        try:
            self.plotter.remove_actor(actor_name, reset_camera=False, render=False)
        except (AttributeError, KeyError, RuntimeError, ValueError, TypeError):
            pass

    def _render_particles(self):
        if self.closing:
            return
        mobile_particles, boundary_points, boundary_colors = _collect_particles(
            self.dynamics,
            self.run_configuration,
        )
        mobile_points = [item["point"] for item in mobile_particles]
        mobile_colors = [item["color"] for item in mobile_particles]
        if mobile_points:
            point_size = float(
                self.run_configuration.get(
                    "pyvista_point_size",
                    self.run_configuration.get("open3d_point_size", 14.0),
                )
            )
            try:
                self.plotter.add_points(
                    _point_cloud(self.np, self.pv, mobile_points, mobile_colors),
                    scalars="rgb",
                    rgb=True,
                    point_size=point_size,
                    render_points_as_spheres=True,
                    name="mobile_particles",
                )
            except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                self._close_quietly_on_window_error(exc)
                return
        else:
            self._remove_actor("mobile_particles")
        if self.show_boundaries and self.boundary_as_particles and boundary_points:
            boundary_point_size = float(
                self.run_configuration.get(
                    "pyvista_boundary_point_size",
                    self.run_configuration.get("open3d_boundary_point_size", 12.0),
                )
            )
            try:
                self.plotter.add_points(
                    _point_cloud(self.np, self.pv, boundary_points, boundary_colors),
                    scalars="rgb",
                    rgb=True,
                    point_size=boundary_point_size,
                    render_points_as_spheres=True,
                    name="boundary_particles",
                )
            except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                self._close_quietly_on_window_error(exc)
        else:
            self._remove_actor("boundary_particles")

    def _render_scene(self, reset_camera=False):
        if self.closing:
            return
        self._render_static_geometry()
        self._render_particles()
        if reset_camera:
            self._setup_camera()
        self._update_status()

    def _update_status(self):
        if self.closing:
            return
        self._remove_actor("status_text")
        self.status_actor = None

        dt = float(self.run_configuration.get("dt", 0.0))
        mobile_count = 0
        boundary_count = 0
        for particle_id, _particle in enumerate(self.dynamics.particles):
            if not _is_visible_particle(self.dynamics, particle_id):
                continue
            if self.dynamics.IsBoundaryParticle(particle_id):
                boundary_count += 1
            else:
                mobile_count += 1
        state = "PAUSED" if self.paused else "RUNNING"
        error_code = int(self.dynamics.collIn.ErrorReturn)
        error_text = (
            "NONE"
            if error_code == self.dynamics.constants.ERROR_NONE
            else self.dynamics.ErrorDescription()
        )
        text = (
            f"Frame: {self.frame}   Time: {self.frame * dt:.6f}   "
            f"Mobile: {mobile_count}   Boundary: {boundary_count}   "
            f"{state}   Error: {error_text}\n"
            f"{self._current_camera_view_zoom_hint()}"
        )
        try:
            self.status_actor = self.plotter.add_text(
                text,
                position="upper_left",
                font_size=int(self.run_configuration.get("pyvista_status_font_size", 10)),
                color="white",
                name="status_text",
            )
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            self._close_quietly_on_window_error(exc)

    def _step(self):
        if self.closing:
            return
        if self.paused:
            return
        now = time.perf_counter()
        if self.frame_interval > 0.0 and now < self.next_step_time:
            return

        self.dynamics.ShaderFlags.frameNum = self.frame
        self.last_particles = self.dynamics.CollisionRun()
        if self.reporting is not None:
            _report_particles(
                self.reporting,
                self.frame,
                self.last_particles,
                self.start_diagnostics,
                self.dynamics,
            )
        self._render_scene(reset_camera=False)
        if self.frame_interval > 0.0:
            self.next_step_time = now + self.frame_interval

        if self.dynamics.collIn.ErrorReturn != self.dynamics.constants.ERROR_NONE:
            self.paused = True
            self._update_status()
        elif self.stop_frame is not None and self.frame >= self.stop_frame:
            self._close()
        else:
            self.frame += 1

    def run(self):
        self._build_plotter()
        print("SimulationRunner3D PyVista controls: mouse orbit/pan/zoom, SPACE pause, ESC quit")
        print(
            "SimulationRunner3D PyVista view hint: "
            f"view={self.run_configuration.get('view')}, "
            f"zoom={self.run_configuration.get('zoom', 1.0)}"
        )
        try:
            self._install_close_observers()
            self.plotter.show(interactive_update=True, auto_close=False)
            _disable_windows_close_button(self.window_title)
            self._install_close_observers()
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            self._close_quietly_on_window_error(exc)
        try:
            while not self._is_plotter_closed():
                self._step()
                if self._is_plotter_closed():
                    break
                if self.paused:
                    self._update_status()
                try:
                    self.plotter.update(stime=1, force_redraw=True)
                except TypeError:
                    try:
                        self.plotter.update()
                    except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                        self._close_quietly_on_window_error(exc)
                except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                    self._close_quietly_on_window_error(exc)
        finally:
            self._mark_closed()
            if self.reporting is not None:
                self.reporting.close()
        return self.last_particles


def _run_analysis_subprocess(cfg_file, end_frame=None):
    command = [sys.executable, str(Path(__file__).resolve()), str(cfg_file)]
    if end_frame is not None:
        command.extend(["--end-frame", str(end_frame)])
    child_env = os.environ.copy()
    child_env["GPCD_PYVISTA_CHILD"] = "1"
    completed = subprocess.run(
        command,
        cwd=str(Path(__file__).resolve().parent),
        env=child_env,
    )
    if completed.returncode != 0:
        print(
            "SimulationRunner3D PyVista child exited with "
            f"code {completed.returncode}"
        )
    return None


def run_analysis(cfg_file, batch_mode=False, end_frame=None, study=False, study_number=None):
    if os.environ.get("GPCD_PYVISTA_CHILD") != "1":
        return _run_analysis_subprocess(cfg_file, end_frame=end_frame)
    app = SimulationRunner3DPyVistaApp(cfg_file, batch_mode=batch_mode, end_frame=end_frame)
    return app.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the PyVista 3D particle viewer.")
    parser.add_argument(
        "cfg_file",
        nargs="?",
        default="C:/_DJ/gPCD/python/cfg_gendata/LightingBall.cfg",
    )
    parser.add_argument("--end-frame", type=int, default=None)
    args = parser.parse_args()
    run_analysis(args.cfg_file, end_frame=args.end_frame)
    if os.environ.get("GPCD_PYVISTA_CHILD") == "1":
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)
