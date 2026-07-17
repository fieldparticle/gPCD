"""PyVista particle viewer for Python 3D dynamics."""

from pathlib import Path
import math
import time

from base.ForceDynamicsBase import ForceDynamics
from base.Reporting import Reporting
from gbase.utilities import get_cell_dimensions
from SimulationRunner3D_HSVPanel import (
    _axis_vector,
    _collect_particles,
    _is_visible_particle,
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
        self.show_boundaries = bool(
            self.run_configuration.get("pyvista_show_boundaries", True)
        )
        self.frame = 0
        self.paused = False
        self.closed = False
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

    def _camera_scale(self):
        extent = max(float(self.width), float(self.height), float(self.depth))
        return max(0.1, float(self.run_configuration.get("camera_ortho_scale", extent * 1.15)))

    def _setup_camera(self):
        target = self._camera_target()
        eye = self._camera_eye(target)
        self.plotter.camera_position = (eye, target, (0.0, 0.0, 1.0))
        self.plotter.enable_parallel_projection()
        self.plotter.camera.parallel_scale = self._camera_scale()

    def _build_plotter(self):
        window_width, window_height = _window_size(self.run_configuration)
        self.plotter = self.pv.Plotter(
            window_size=(window_width, window_height),
            title=f"SimulationRunner3D PyVista - {self.study_name}",
        )
        self.plotter.set_background("black")
        self.plotter.add_key_event("space", self._toggle_pause)
        self.plotter.add_key_event("Escape", self._close)
        self._render_scene(reset_camera=True)

    def _toggle_pause(self):
        self.paused = not self.paused
        self._update_status()

    def _close(self):
        self.closed = True
        if self.plotter is not None:
            self.plotter.close()

    def _is_plotter_closed(self):
        if self.closed:
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
        try:
            self.plotter.remove_actor(actor_name, reset_camera=False, render=False)
        except (KeyError, ValueError, TypeError):
            pass

    def _render_particles(self):
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
            self.plotter.add_points(
                _point_cloud(self.np, self.pv, mobile_points, mobile_colors),
                scalars="rgb",
                rgb=True,
                point_size=point_size,
                render_points_as_spheres=True,
                name="mobile_particles",
            )
        else:
            self._remove_actor("mobile_particles")
        if self.show_boundaries and self.boundary_as_particles and boundary_points:
            boundary_point_size = float(
                self.run_configuration.get(
                    "pyvista_boundary_point_size",
                    self.run_configuration.get("open3d_boundary_point_size", 12.0),
                )
            )
            self.plotter.add_points(
                _point_cloud(self.np, self.pv, boundary_points, boundary_colors),
                scalars="rgb",
                rgb=True,
                point_size=boundary_point_size,
                render_points_as_spheres=True,
                name="boundary_particles",
            )
        else:
            self._remove_actor("boundary_particles")

    def _render_scene(self, reset_camera=False):
        self._render_static_geometry()
        self._render_particles()
        self._update_status()
        if reset_camera:
            self._setup_camera()

    def _update_status(self):
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
            f"{state}   Error: {error_text}"
        )
        self.status_actor = self.plotter.add_text(
            text,
            position="upper_left",
            font_size=int(self.run_configuration.get("pyvista_status_font_size", 10)),
            color="white",
            name="status_text",
        )

    def _step(self):
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
        self.plotter.show(interactive_update=True, auto_close=False)
        try:
            while not self._is_plotter_closed():
                self._step()
                try:
                    self.plotter.update(stime=1, force_redraw=True)
                except TypeError:
                    self.plotter.update()
        finally:
            if self.reporting is not None:
                self.reporting.close()
        return self.last_particles


def run_analysis(cfg_file, batch_mode=False, end_frame=None, study=False, study_number=None):
    app = SimulationRunner3DPyVistaApp(cfg_file, batch_mode=batch_mode, end_frame=end_frame)
    return app.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the PyVista 3D particle viewer.")
    parser.add_argument(
        "cfg_file",
        nargs="?",
        default="C:/_DJ/gPCD/python/cfg_gendata/Cathedral.cfg",
    )
    parser.add_argument("--end-frame", type=int, default=None)
    args = parser.parse_args()
    run_analysis(args.cfg_file, end_frame=args.end_frame)
