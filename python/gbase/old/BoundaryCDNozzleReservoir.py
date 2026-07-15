import math
import os

from gbase.ParametricCurve import bounds as curve_bounds
from gbase.ParametricCurve import evaluate_point
from gbase.ParametricCurve import evaluate_tangent
from gbase.ParametricParticleVerifiyer import ParametricParticleVerifiyer
from gbase.pdata import PTYPE_MOBILE, PTYPE_NULL, pdata


class BoundaryCDNozzleReservoir:
    """Generate particles and parametric wall markers for this scenario."""

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
        verified = ParametricParticleVerifiyer().verify(self.itemcfg)
        for name, value in verified.items():
            setattr(self, name, value)
        return True

    def initialize_generation(self):
        self.p_list = []
        self.bin_file = None
        self.count = 0
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0

        output_prefix = str(self.itemcfg.output_file_prefix)
        output_directory = str(self.itemcfg.data_dir)
        self.test_bin_name = os.path.join(output_directory, f"{output_prefix}.bin")
        self.test_file_name = os.path.join(output_directory, f"{output_prefix}.tst")
        self.report_file = os.path.join(output_directory, f"{output_prefix}.rpt")
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.obj_file_name = os.path.join(
            project_root,
            "vulkan",
            "sim",
            "BoundaryCDNozzleReservoir",
            "CDNozzleGenerated.obj",
        )

    def add_null_particle(self):
        particle = pdata()
        particle.pnum = 0
        particle.ptype = PTYPE_NULL
        self.p_list.append(particle)
        return particle

    def add_mobile_particle(self, position, velocity):
        particle = pdata()
        self.number_particles += 1
        self.number_active_particles += 1
        particle.pnum = self.number_particles
        particle.ptype = PTYPE_MOBILE
        particle.rx, particle.ry, particle.rz = position
        particle.vx, particle.vy, particle.vz = velocity
        particle.radius = self.radius
        particle.molar_mass = 1.0
        particle.state_flg = 0.0
        particle.collision_stiffness_q = self.collision_stiffness_q
        self.p_list.append(particle)
        return particle

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
        particle.radius = 0.25
        particle.molar_mass = 1.0
        particle.state_flg = 0.0
        particle.collision_stiffness_q = 0.0
        self.p_list.append(particle)
        return particle

    def calculate_chamber_packing(self):
        """Calculate a centered, nonoverlapping 2D chamber packing."""
        diameter = 2.0 * self.radius
        center_spacing = diameter + self.particle_separation_distance
        boundary_clearance = (
            self.radius * (1.0 + self.wall_contact_offset) + 1.0e-9
        )

        x_start, x_end, y_bottom, y_top, _z_front, _z_back = (
            self.chamber_bounds
        )
        x_center_min = x_start + boundary_clearance
        x_center_max = x_end - boundary_clearance
        y_center_min = y_bottom + boundary_clearance
        y_center_max = y_top - boundary_clearance
        usable_x = x_center_max - x_center_min
        usable_y = y_center_max - y_center_min
        if usable_x < 0.0 or usable_y < 0.0:
            raise ValueError(
                "chamber_bounds are too small for the configured particle "
                "radius and wall clearance"
            )

        x_count = int(math.floor((usable_x / center_spacing) + 1.0e-12)) + 1
        y_count = int(math.floor((usable_y / center_spacing) + 1.0e-12)) + 1
        occupied_x = (x_count - 1) * center_spacing
        occupied_y = (y_count - 1) * center_spacing
        first_x = x_center_min + 0.5 * (usable_x - occupied_x)
        first_y = y_center_min + 0.5 * (usable_y - occupied_y)

        self.particle_diameter = diameter
        self.particle_center_spacing = center_spacing
        self.boundary_particle_clearance = boundary_clearance
        self.packing_x_count = x_count
        self.packing_y_count = y_count
        self.packing_particle_count = x_count * y_count
        self.packing_first_center = (
            first_x,
            first_y,
            self.particle_plane_z,
        )
        self.packing_last_center = (
            first_x + occupied_x,
            first_y + occupied_y,
            self.particle_plane_z,
        )

        print(
            "Parametric chamber packing report:\n"
            f"  radius: {self.radius:g}\n"
            f"  diameter: {diameter:g}\n"
            f"  surface separation: {self.particle_separation_distance:g}\n"
            f"  center spacing: {center_spacing:g}\n"
            f"  boundary clearance: {boundary_clearance:g}\n"
            f"  grid: {x_count} columns x {y_count} rows\n"
            f"  mobile particles: {self.packing_particle_count}\n"
            f"  first center: {self.packing_first_center}\n"
            f"  last center: {self.packing_last_center}"
        )
        return self.packing_particle_count

    def add_mobile_particles(self):
        """Materialize the calculated chamber packing."""
        first_x, first_y, particle_z = self.packing_first_center
        for column in range(self.packing_x_count):
            particle_x = first_x + column * self.particle_center_spacing
            for row in range(self.packing_y_count):
                particle_y = first_y + row * self.particle_center_spacing
                self.add_mobile_particle(
                    (particle_x, particle_y, particle_z),
                    self.piston_velocity,
                )

        if self.number_active_particles != self.packing_particle_count:
            raise RuntimeError(
                "generated mobile-particle count does not match packing count"
            )
        print(
            "Parametric chamber mobile-particle report:\n"
            f"  generated particles: {self.number_active_particles}\n"
            f"  particle numbers: 1 through {self.number_active_particles}\n"
            f"  velocity: {self.piston_velocity}"
        )
        return self.number_active_particles

    @staticmethod
    def _distance_between_points(first, second):
        return math.hypot(second[0] - first[0], second[1] - first[1])

    def curve_marker_parameters(self, segment, maximum_spacing=1.0):
        """Return uniform parameters whose adjacent chords fit one cell."""
        x_min, x_max, y_min, y_max = curve_bounds(segment)
        intervals = max(
            1,
            int(math.ceil(max(x_max - x_min, y_max - y_min))),
        )

        while True:
            parameters = [index / intervals for index in range(intervals + 1)]
            points = [evaluate_point(segment, value) for value in parameters]
            largest_spacing = max(
                self._distance_between_points(points[index], points[index + 1])
                for index in range(intervals)
            )
            if largest_spacing <= maximum_spacing + 1.0e-9:
                return parameters
            intervals *= 2
            if intervals > 1048576:
                raise RuntimeError(
                    "curve marker refinement exceeded the interval limit"
                )

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
            output.write("o CDNozzleGenerated\n")
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
            print("Parametric chamber generated bounds: no mobile particles")
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
            "Parametric chamber generated bounds:\n"
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
            chamber_x_start,
            chamber_x_end,
            chamber_y_bottom,
            chamber_y_top,
            chamber_z_front,
            chamber_z_back,
        ) = self.chamber_bounds
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
                f'particle_data_bin_file = "{self.test_bin_name}";\n'
            )
            output.write(f'report_file = "{self.report_file}";\n')
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

            output.write(f"chamber_x_start = {chamber_x_start:.9f};\n")
            output.write(f"chamber_x_end = {chamber_x_end:.9f};\n")
            output.write(f"chamber_y_bottom = {chamber_y_bottom:.9f};\n")
            output.write(f"chamber_y_top = {chamber_y_top:.9f};\n")
            output.write(f"chamber_z_front = {chamber_z_front:.9f};\n")
            output.write(f"chamber_z_back = {chamber_z_back:.9f};\n")
            output.write(f"piston_start_frame = {self.piston_start_frame};\n")
            output.write(f"piston_initial_x = {chamber_x_start:.9f};\n")
            output.write(f"piston_stop_x = {chamber_x_end:.9f};\n")
            output.write(f"piston_velocity_x = {self.piston_velocity[0]:.9f};\n")
            output.write(f"piston_velocity_y = {self.piston_velocity[1]:.9f};\n")
            output.write(f"piston_velocity_z = {self.piston_velocity[2]:.9f};\n")

            output.write("curve_wall_segments = (\n")
            for segment_index, segment in enumerate(self.curve_wall_segments):
                separator = (
                    "," if segment_index + 1 < len(self.curve_wall_segments) else ""
                )
                values = ", ".join(f"{float(value):.9f}" for value in segment)
                output.write(f"    [{values}]{separator}\n")
            output.write(");\n")

            output.write(f"wall_contact_offset = {self.wall_contact_offset:.9f};\n")
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
            self.calculate_chamber_packing()
            self.add_mobile_particles()
            self.add_parametric_wall_markers()
            self.write_parametric_wall_obj()
            self.write_particle_bin()
            self.write_test_file()
            self.report_generated_bounds()
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self.close_bin_file()
            print(
                "Parametric chamber particle generation stopped:\n"
                f"{type(error).__name__}: {error}"
            )
            return False

        print(
            "Parametric chamber packing complete:\n"
            f"  binary file: {self.test_bin_name}\n"
            f"  records: {self.count}\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  boundary markers: {self.number_boundary_particles}"
        )
        return True
