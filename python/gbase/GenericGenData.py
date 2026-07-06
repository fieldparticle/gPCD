import math
import os

from gbase.ParametricCurve import bounds as curve_bounds
from gbase.ParametricCurve import evaluate_point
from gbase.ParametricCurve import evaluate_tangent
from gbase.ParametricCurve import marker_parameters
from gbase.pdata import PTYPE_MOBILE, PTYPE_NULL, pdata


class GenericGenData:
    """Generate particle data from declarative particle and wall configuration."""

    BOUNDARY_EVALUATOR_PARAMETRIC = 5.0

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

    def create(self, parent, itemcfg):
        self.parent = parent
        self.bobj = parent.bobj
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.itemcfg = itemcfg

    def openSelectionsFile(self):
        """This generator does not use a selections file."""

    def clear_selections(self):
        """This generator does not use selection records."""

    def clear_files(self):
        """Output replacement occurs only after configuration verification."""

    def do_all_files_dbg(self):
        return self.runner()

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
        curve_segments = []
        if not raw_segments:
            errors.append("curve_wall_segments is required and must not be empty")
        else:
            for index, raw_segment in enumerate(raw_segments):
                if len(raw_segment) != 9:
                    errors.append(
                        f"curve_wall_segments[{index}] must contain 9 values"
                    )
                    continue
                try:
                    segment = tuple(float(value) for value in raw_segment)
                except (TypeError, ValueError):
                    errors.append(
                        f"curve_wall_segments[{index}] values must be numeric"
                    )
                    continue
                if not all(math.isfinite(value) for value in segment):
                    errors.append(
                        f"curve_wall_segments[{index}] values must be finite"
                    )
                    continue
                wall_flag = segment[8]
                if not wall_flag.is_integer() or int(wall_flag) <= 0:
                    errors.append(
                        f"curve_wall_segments[{index}] wall_flag must be a positive integer"
                    )
                if all(abs(value) <= 1.0e-12 for value in segment[1:4] + segment[5:8]):
                    errors.append(f"curve_wall_segments[{index}] has zero length")
                curve_segments.append(segment)

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
                    values = {
                        "x": float(particle.location.x1),
                        "y": float(particle.location.y1),
                        "z": float(particle.location.z1),
                        "vx": float(particle.vx),
                        "vy": float(particle.vy),
                        "vz": float(particle.get("vz", 0.0)),
                        "mass": float(particle.mass),
                        "radius": float(particle.radius),
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
                if not all(math.isfinite(value) for value in values.values()):
                    errors.append(f"PARTICLE_DATA.{name} values must be finite")
                if values["radius"] <= 0.0:
                    errors.append(f"PARTICLE_DATA.{name}.radius must be positive")
                if values["mass"] <= 0.0:
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
                x_min, x_max, y_min, y_max = curve_bounds(segment)
                if x_min < 0.0 or x_max > width:
                    errors.append(
                        f"curve_wall_segments[{index}] x extent is outside the cell array"
                    )
                if y_min < 0.0 or y_max > height:
                    errors.append(
                        f"curve_wall_segments[{index}] y extent is outside the cell array"
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

        if errors:
            raise ValueError(
                "GenericGenData configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )

        self.cell_array_width, self.cell_array_height, self.cell_array_depth = dimensions
        self.death_bounds = death_bounds
        self.curve_wall_segments = curve_segments
        self.explicit_particles = particles
        self.number_configured_particles = len(particles)
        self.particle_plane_z = particles[0]["z"]
        self.radius = float(self.itemcfg.radius)
        self.wall_contact_offset = float(self.itemcfg.wall_contact_offset)
        self.dt = float(self.itemcfg.dt)
        self.cell_occupancy_list_size = int(self.itemcfg.cell_occupancy_list_size)
        return True

    def initialize_generation(self):
        self.p_list = []
        self.bin_file = None
        self.count = 0
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0

        output_prefix = str(
            self.itemcfg.get("output_file_prefix", self.itemcfg.STUDY_NAME)
        )
        output_directory = str(self.itemcfg.data_dir)
        self.test_bin_name = os.path.join(output_directory, f"{output_prefix}.bin")
        self.test_file_name = os.path.join(output_directory, f"{output_prefix}.tst")
        self.report_file = os.path.join(output_directory, f"{output_prefix}.rpt")
        configured_obj_file = self.itemcfg.get("obj_file_name")
        if configured_obj_file:
            self.obj_file_name = os.path.normpath(str(configured_obj_file))
        else:
            self.obj_file_name = os.path.join(
                output_directory,
                f"{output_prefix}.obj",
            )

    def add_null_particle(self):
        particle = pdata()
        particle.pnum = 0
        particle.ptype = PTYPE_NULL
        self.p_list.append(particle)
        return particle

    def add_mobile_particle(
        self,
        position,
        velocity,
        radius=None,
        mass=1.0,
        collision_stiffness_q=None,
    ):
        particle = pdata()
        self.number_particles += 1
        self.number_active_particles += 1
        particle.pnum = self.number_particles
        particle.ptype = PTYPE_MOBILE
        particle.rx, particle.ry, particle.rz = position
        particle.vx, particle.vy, particle.vz = velocity
        particle.radius = self.radius if radius is None else radius
        particle.molar_mass = mass
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
                collision_stiffness_q=configured["collision_stiffness_q"],
            )

        if self.number_active_particles != self.number_configured_particles:
            raise RuntimeError(
                "generated mobile-particle count does not match PARTICLE_DATA"
            )
        return self.number_active_particles

    def add_boundary_particle(self, position):
        particle = pdata()
        self.number_particles += 1
        self.number_boundary_particles += 1
        particle.pnum = self.number_particles
        particle.ptype = self.BOUNDARY_EVALUATOR_PARAMETRIC
        particle.rx, particle.ry, particle.rz = position
        particle.vx = 0.0
        particle.vy = 0.0
        particle.vz = 0.0
        particle.radius = self.radius
        particle.molar_mass = 1.0
        particle.state_flg = 0.0
        particle.collision_stiffness_q = 0.0
        self.p_list.append(particle)
        return particle

    def curve_marker_parameters(self, segment, maximum_spacing=1.0):
        """Return parameters using the shared runtime marker policy."""
        return marker_parameters(segment, maximum_spacing)

    def add_parametric_wall_markers(self):
        """Create deduplicated locality markers along all wall segments."""
        marker_cells = set()
        segment_marker_counts = []

        for segment in self.curve_wall_segments:
            wall_flag = int(round(segment[8]))
            parameters = self.curve_marker_parameters(segment)
            added_for_segment = 0
            for parameter in parameters:
                marker_x, marker_y = evaluate_point(segment, parameter)
                cell_x = round(marker_x)
                cell_y = round(marker_y)
                cell_z = round(self.particle_plane_z)
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
                    (float(cell_x), float(cell_y), float(cell_z))
                )
                added_for_segment += 1
            segment_marker_counts.append(added_for_segment)

        print(
            "Parametric wall-marker report:\n"
            f"  curve segments: {len(self.curve_wall_segments)}\n"
            f"  unique boundary markers: {self.number_boundary_particles}\n"
            f"  evaluator ID: {self.BOUNDARY_EVALUATOR_PARAMETRIC:g}\n"
            f"  markers added per segment: {segment_marker_counts}\n"
            "  occupancy rule: one marker per cell per physical wall\n"
            "  marker position: integer cell center\n"
            "  maximum sampled curve chord: 1 cell"
        )
        return self.number_boundary_particles

    def write_parametric_wall_obj(self):
        """Write triangle ribbons sampled from the wall-marker curve paths."""
        half_thickness = 0.25
        vertices = []
        faces = []

        for segment in self.curve_wall_segments:
            parameters = self.curve_marker_parameters(segment)
            segment_vertices = []

            for parameter in parameters:
                point_x, point_y = evaluate_point(segment, parameter)
                tangent_x, tangent_y = evaluate_tangent(segment, parameter)
                tangent_length = math.hypot(tangent_x, tangent_y)
                if tangent_length <= 1.0e-12:
                    raise RuntimeError(
                        "cannot generate OBJ ribbon from a zero-length tangent"
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
            output.write("# Generated from curve_wall_segments.\n")
            output.write("# Dynamics use boundary particles; this mesh is visual only.\n")
            output.write("o GeneratedParametricWalls\n")
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

        print(
            "Parametric wall OBJ report:\n"
            f"  file: {self.obj_file_name}\n"
            f"  vertices: {len(vertices)}\n"
            f"  triangles: {2 * len(faces)}"
        )
        return self.obj_file_name

    def report_generated_bounds(self):
        """Report generated mobile-particle center and perimeter bounds."""
        mobile_particles = [
            particle
            for particle in self.p_list
            if int(round(float(particle.ptype))) == int(PTYPE_MOBILE)
            and int(round(float(particle.pnum))) != 0
        ]
        if not mobile_particles:
            print("Generic particle generated bounds: no mobile particles")
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
        print(
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
        return center_bounds, perimeter_bounds

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
        """Write Vulkan metadata for the parametric particle simulation."""
        particle_data_bin_file = self.test_bin_name.replace(os.sep, "/")
        report_file = self.report_file.replace(os.sep, "/")
        curve_extents = [
            curve_bounds(segment) for segment in self.curve_wall_segments
        ]
        boundary_x_min = min(extent[0] for extent in curve_extents)
        boundary_x_max = max(extent[1] for extent in curve_extents)
        boundary_y_min = min(extent[2] for extent in curve_extents)
        boundary_y_max = max(extent[3] for extent in curve_extents)
        view_center = self.itemcfg.get(
            "view_center",
            (
                0.5 * self.cell_array_width,
                0.5 * self.cell_array_height,
                0.5 * self.cell_array_depth,
            ),
        )
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
            output.write(f"CellAryW = {self.cell_array_width};\n")
            output.write(f"CellAryH = {self.cell_array_height};\n")
            output.write(f"CellAryL = {self.cell_array_depth};\n")
            output.write(
                "view_center = ["
                f"{float(view_center[0]):.9f}, "
                f"{float(view_center[1]):.9f}, "
                f"{float(view_center[2]):.9f}];\n"
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
            output.write(f"dispatchx = {self.number_active_particles + 1};\n")
            output.write(f"dispatchy = {int(self.itemcfg.dispatchy)};\n")
            output.write(f"dispatchz = {int(self.itemcfg.dispatchz)};\n")
            output.write(f"workGroupsx = {int(self.itemcfg.workGroupsx)};\n")
            output.write(f"workGroupsy = {int(self.itemcfg.workGroupsy)};\n")
            output.write(f"workGroupsz = {int(self.itemcfg.workGroupsz)};\n")
            output.write(
                "cell_occupancy_list_size = "
                f"{self.cell_occupancy_list_size};\n"
            )

            output.write(f"boundary_x_min = {boundary_x_min:.9f};\n")
            output.write(f"boundary_x_max = {boundary_x_max:.9f};\n")
            output.write(f"boundary_y_min = {boundary_y_min:.9f};\n")
            output.write(f"boundary_y_max = {boundary_y_max:.9f};\n")
            output.write(f"boundary_z_min = {self.particle_plane_z:.9f};\n")
            output.write(f"boundary_z_max = {self.particle_plane_z:.9f};\n")

            output.write(f"death_x_min = {death_x_min:.9f};\n")
            output.write(f"death_x_max = {death_x_max:.9f};\n")
            output.write(f"death_y_min = {death_y_min:.9f};\n")
            output.write(f"death_y_max = {death_y_max:.9f};\n")
            output.write(f"death_z_min = {death_z_min:.9f};\n")
            output.write(f"death_z_max = {death_z_max:.9f};\n")

            output.write("curve_wall_segments = (\n")
            for segment_index, segment in enumerate(self.curve_wall_segments):
                separator = (
                    "," if segment_index + 1 < len(self.curve_wall_segments) else ""
                )
                values = ", ".join(f"{float(value):.9f}" for value in segment)
                output.write(f"    [{values}]{separator}\n")
            output.write(");\n")

            output.write(f"wall_contact_offset = {self.wall_contact_offset:.9f};\n")
            output.write('wall_type = "WALL_MODEL_BOUNDARY_PARTICLE";\n')
            output.write(f"DT = {self.dt:.9f};\n")
            output.write(
                "contact_force_measure = "
                f'"{self.itemcfg.get("contact_force_measure", "depth")}";\n'
            )
            output.write(
                f"hsv_color = {1 if self.itemcfg.get('hsv_color', False) else 0};\n"
            )
            output.write(f"hsv_sat = {float(self.itemcfg.hsv_sat):.9f};\n")
            output.write(f"hsv_val = {float(self.itemcfg.hsv_val):.9f};\n")

        print(
            "Parametric particle test-file report:\n"
            f"  file: {self.test_file_name}\n"
            f"  particle records excluding null: {self.number_particles}\n"
            f"  mobile compute records including null: "
            f"{self.number_active_particles + 1}\n"
            f"  curve segments: {len(self.curve_wall_segments)}"
        )
        return self.test_file_name

    def runner(self):
        try:
            self.validate_simulation_configuration()
        except (AttributeError, TypeError, ValueError) as error:
            print(
                "Parametric particle configuration validation stopped:\n"
                f"{error}"
            )
            return False

        self.initialize_generation()
        try:
            self.add_null_particle()
            self.add_explicit_mobile_particles()
            self.add_parametric_wall_markers()
            self.write_particle_bin()
            self.write_test_file()
            self.report_generated_bounds()
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self.close_bin_file()
            print(
                "Generic particle generation stopped:\n"
                f"{type(error).__name__}: {error}"
            )
            return False

        print(
            "Generic particle generation complete:\n"
            f"  binary file: {self.test_bin_name}\n"
            f"  records: {self.count}\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  boundary markers: {self.number_boundary_particles}"
        )
        return True
