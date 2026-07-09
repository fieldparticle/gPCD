import random

from gbase.utilities import *
from gbase.GenDataBase import *
from gbase.BinaryFileUtilities import *
import math
from gbase.pdata import *
from gbase.libconf import AttrDict
import io
from gbase.msg_box import verify_dialog
class BoundaryParticleReservoirHorizontal():

   
    def __init__(self):
        super().__init__()
        self.p_list = []
        self.bin_file = None

    def clear_selections(self):
        pass
    def openSelectionsFile(self):
        pass

    #******************************************************************
    # Always add a null particle to the beginging of the particles
    # bnary file. The particle.exe code ignores 0 so that it can be used
    # to indeicvate an emply ellement of an array.
    #
    def add_null_particle(self,p_list):
        particle_struct = pdata()
        particle_struct.pnum = 0
        particle_struct.ptype = PTYPE_NULL
        p_list.append(particle_struct)


    ## JMB assign config to self.itemcfg and use that for 
    ## all config items!
    def create(self,parent,itemcfg):
        self.parent = parent
        self.bobj = parent.bobj
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.itemcfg = itemcfg

   
    def do_all_files_dbg(self):
        return self.runner()
    
    def create_bin_file(self):
        try:
            self.bin_file = open(self.test_bin_name,"wb")
        except BaseException as e:
            self.log.log(self,e)
            return
        self.count = 0

    def clear_files(self):
        res = verify_dialog(None, "Delete Verification", 
                        "Are you sure you want to delete all of the files in the data directory?", 
                        "Yes", "No")

        if res == False:
            return
        cfg_data_name = self.itemcfg["output_file_prefix"]
        
        self.test_file_name = f"{self.itemcfg.data_dir}/{cfg_data_name}.tst"
        try:
            os.remove(self.test_file_name)
        except BaseException as e:
            print(f"Delete bin file:{e}")
        self.test_bin_name = f"{self.itemcfg.data_dir}/{cfg_data_name}.bin"
        try:
            os.remove(self.test_bin_name)
        except BaseException as e:
            print(f"Delete tst file:{e}")
        self.report_file = f"{self.itemcfg.data_dir}/{cfg_data_name}.rpt"
        

    def close_bin_file(self):
        self.bin_file.flush()
        self.bin_file.close()
        if(self.bin_file.closed != True):
            self.bobj.log.log("File:{self.test_bin_name} not closed")
        
    #******************************************************************
    # Caluate side length based on number of particles and particle per 
    # cell
    #
    def write_bin_file(self,p_lst):
        for particle in p_lst:
            self.bin_file.write(particle)
            self.count += 1

    #******************************************************************
    # Write the tst files taht are read by particle.exe for tests
    # 
    #
    def write_test_file(self):
        """Write the Vulkan test configuration for the generated binary."""
        output_name = str(self.itemcfg.output_file_prefix)
        self.test_file_name = os.path.join(
            str(self.itemcfg.data_dir),
            f"{output_name}.tst",
        )
        self.report_file = os.path.join(
            str(self.itemcfg.data_dir),
            f"{output_name}.rpt",
        )
        try:
            f = open(self.test_file_name,'w')
        except OSError as e:
            raise OSError(f"Can't open test file {self.test_file_name}: {e}") from e

        run_cfg = self.itemcfg
        boundary_x_values = [
            value
            for segment in self.all_linear_segments
            for value in (segment[3], segment[5])
        ]
        boundary_y_values = [
            value
            for segment in self.all_linear_segments
            for value in (segment[4], segment[6])
        ]
        fstr = f"index = {self.index};\n"     
        f.write(fstr)
        # Cell counts are explicit for each axis. Valid cell coordinates run
        # from zero through the corresponding count minus one.
        fstr = f"CellAryW = {self.cell_array_width};\n"     
        f.write(fstr)
        fstr = f"CellAryH = {self.cell_array_height};\n"     
        f.write(fstr)
        fstr = f"CellAryL = {self.cell_array_depth};\n"     
        f.write(fstr)
        fstr = (
            "view_center = ["
            f"{self.view_center[0]:0.6f}, "
            f"{self.view_center[1]:0.6f}, "
            f"{self.view_center[2]:0.6f}];\n"
        )
        f.write(fstr)
        fstr = f"radius = {run_cfg.radius};\n"
        f.write(fstr)
        fstr = f"num_particles = {self.number_particles};\n"
        f.write(fstr)
        fstr = f"num_particle_colliding =  0;\n"
        f.write(fstr)
        fstr = f"exp_collisions_per_cell = 0;\n"
        f.write(fstr)
        fstr = f"act_collisions_per_cell = 0;\n"
        f.write(fstr)
        fstr = f"particles_in_row =  0;\n"
        f.write(fstr)
        fstr = f"particle_data_bin_file = \"{self.test_bin_name}\";\n"
        f.write(fstr)
        fstr = f"report_file = \"{self.report_file}\";\n"
        f.write(fstr)
        fstr = f"dispatchx = {self.number_active_particles+1};\n"
        f.write(fstr)
        fstr = f"dispatchy = {run_cfg.dispatchy};\n"
        f.write(fstr)
        fstr = f"dispatchz = {run_cfg.dispatchz};\n"
        f.write(fstr)
        fstr = f"workGroupsx = {run_cfg.workGroupsx};\n"
        f.write(fstr)
        fstr = f"workGroupsy = {run_cfg.workGroupsy};\n"
        f.write(fstr)
        fstr = f"workGroupsz = {run_cfg.workGroupsz};\n"
        f.write(fstr)
        fstr = f"cell_occupancy_list_size = {run_cfg.cell_occupancy_list_size};\n"
        f.write(fstr)
        fstr = f"boundary_x_min = {min(boundary_x_values):0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_x_max = {max(boundary_x_values):0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_y_min = {min(boundary_y_values):0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_y_max = {max(boundary_y_values):0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_z_min = {self.particle_plane_z:0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_z_max = {self.particle_plane_z:0.6f};\n"
        f.write(fstr)
        (
            death_x_min,
            death_x_max,
            death_y_min,
            death_y_max,
            death_z_min,
            death_z_max,
        ) = self.death_bounds
        f.write(f"death_x_min = {death_x_min:0.6f};\n")
        f.write(f"death_x_max = {death_x_max:0.6f};\n")
        f.write(f"death_y_min = {death_y_min:0.6f};\n")
        f.write(f"death_y_max = {death_y_max:0.6f};\n")
        f.write(f"death_z_min = {death_z_min:0.6f};\n")
        f.write(f"death_z_max = {death_z_max:0.6f};\n")
        (
            chamber_x_start,
            chamber_x_end,
            chamber_y_bottom,
            chamber_y_top,
            chamber_z_front,
            chamber_z_back,
        ) = self.chamber_bounds
        f.write(f"chamber_x_start = {chamber_x_start:0.6f};\n")
        f.write(f"chamber_x_end = {chamber_x_end:0.6f};\n")
        f.write(f"chamber_y_bottom = {chamber_y_bottom:0.6f};\n")
        f.write(f"chamber_y_top = {chamber_y_top:0.6f};\n")
        f.write(f"chamber_z_front = {chamber_z_front:0.6f};\n")
        f.write(f"chamber_z_back = {chamber_z_back:0.6f};\n")
        f.write(f"piston_start_frame = {self.piston_start_frame};\n")
        f.write(f"piston_initial_x = {self.chamber_bounds[0]:0.6f};\n")
        f.write(f"piston_stop_x = {self.chamber_bounds[1]:0.6f};\n")
        f.write(f"piston_velocity_x = {self.piston_velocity[0]:0.6f};\n")
        f.write(f"piston_velocity_y = {self.piston_velocity[1]:0.6f};\n")
        f.write(f"piston_velocity_z = {self.piston_velocity[2]:0.6f};\n")
        for segment_key, segments in (
            ("linear_chamber_segments", self.linear_chamber_segments),
            ("linear_wall_segments", self.linear_wall_segments),
        ):
            f.write(f"{segment_key} = (\n")
            for segment_index, segment in enumerate(segments):
                separator = "," if segment_index + 1 < len(segments) else ""
                values = ", ".join(f"{value:0.6f}" for value in segment)
                f.write(f"    [{values}]{separator}\n")
            f.write(");\n")
        fstr = f"wall_contact_offset = {float(run_cfg.wall_contact_offset):0.6f};\n"
        f.write(fstr)
        fstr = f"DT = {run_cfg.dt};\n"
        f.write(fstr)
        contact_force_measure = getattr(run_cfg, "contact_force_measure", "area")
        fstr = f"contact_force_measure = \"{contact_force_measure}\";\n"
        f.write(fstr)
        if run_cfg.hsv_color == True:
            fstr = f"hsv_color = 1;\n"
        else:
            fstr = f"hsv_color = 0;\n"
        f.write(fstr)
        fstr = f"hsv_sat = {run_cfg.hsv_sat:0.4f};\n"
        f.write(fstr)
        fstr = f"hsv_val = {run_cfg.hsv_val:0.4f};\n"
        f.write(fstr)
        f.flush()
        f.close()
        print(
            "BoundaryParticleReservoirHorizontal test-file report:\n"
            f"  file: {self.test_file_name}\n"
            f"  particle records excluding null: {self.number_particles}\n"
            f"  compute dispatch records: {self.number_active_particles + 1}"
        )
        return self.test_file_name
        

    def runner(self):
        self.p_list = []
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0
        self.index = 0
        try:
            self.validate_simulation_configuration()
        except (AttributeError, TypeError, ValueError) as error:
            print(
                "BoundaryParticleReservoirHorizontal generation stopped:\n"
                f"{error}"
            )
            return False

        try:
            self.add_null_particle(self.p_list)
            self.calculate_chamber_packing()
            self.add_mobile_particles()
            self.add_boundary_particles()
            self.write_particle_bin()
            self.write_test_file()
        except (AttributeError, OSError, TypeError, ValueError) as error:
            print(
                "BoundaryParticleReservoirHorizontal generation failed:\n"
                f"{error}"
            )
            return False
        return True
        
    # ------------------------------------------------------------------
    # Simulation configuration checks
    # ------------------------------------------------------------------
    def validate_simulation_configuration(self):
        """Validate the horizontal 2D piston chamber and linear walls."""
        errors = []
        try:
            width, height, depth = get_cell_dimensions(self.itemcfg)
        except (TypeError, ValueError) as error:
            errors.append(str(error))
            width = height = depth = 0

        def read_bounds(key):
            raw_bounds = self.itemcfg.get(key)
            if raw_bounds is None:
                errors.append(f"{key} is required")
                return None
            if len(raw_bounds) != 6:
                errors.append(f"{key} must contain exactly six values")
                return None
            try:
                bounds = tuple(float(value) for value in raw_bounds)
            except (TypeError, ValueError):
                errors.append(f"{key} values must be numeric")
                return None
            if not all(math.isfinite(value) for value in bounds):
                errors.append(f"{key} values must be finite")
                return None
            return bounds

        chamber = read_bounds("chamber_bounds")
        death = read_bounds("death_bounds")

        def read_linear_segments(key):
            raw_segments = self.itemcfg.get(key)
            segments = []
            if raw_segments is None:
                errors.append(f"{key} is required")
                return segments
            for segment_index, raw_segment in enumerate(raw_segments):
                if len(raw_segment) != 8:
                    errors.append(
                        f"{key}[{segment_index}] must contain "
                        "exactly eight values"
                    )
                    continue
                try:
                    segment = tuple(float(value) for value in raw_segment)
                except (TypeError, ValueError):
                    errors.append(f"{key}[{segment_index}] must be numeric")
                    continue
                if not all(math.isfinite(value) for value in segment):
                    errors.append(f"{key}[{segment_index}] must be finite")
                    continue
                a, b, c, x_start, y_start, x_end, y_end, wall_flag = segment
                if math.hypot(a, b) <= 1.0e-12:
                    errors.append(
                        f"{key}[{segment_index}] requires nonzero A or B"
                    )
                if math.hypot(x_end - x_start, y_end - y_start) <= 1.0e-12:
                    errors.append(
                        f"{key}[{segment_index}] endpoints must differ"
                    )
                for endpoint_name, x_value, y_value in (
                    ("start", x_start, y_start),
                    ("end", x_end, y_end),
                ):
                    if abs(a * x_value + b * y_value + c) > 1.0e-8:
                        errors.append(
                            f"{key}[{segment_index}] {endpoint_name} "
                            "point is not on its line"
                        )
                if not wall_flag.is_integer() or int(wall_flag) not in (1, 2, 3, 4):
                    errors.append(
                        f"{key}[{segment_index}] wall_flag must be 1..4"
                    )
                segments.append(segment)
            return segments

        linear_chamber_segments = read_linear_segments("linear_chamber_segments")
        linear_wall_segments = read_linear_segments("linear_wall_segments")
        all_linear_segments = linear_chamber_segments + linear_wall_segments

        def read_number(key):
            raw_value = self.itemcfg.get(key)
            if raw_value is None:
                errors.append(f"{key} is required")
                return None
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                errors.append(f"{key} must be numeric")
                return None
            if not math.isfinite(value):
                errors.append(f"{key} must be finite")
                return None
            return value

        radius = read_number("radius")
        separation = read_number("particle_separation_distance")
        wall_contact_offset = read_number("wall_contact_offset")
        collision_stiffness_q = read_number("collision_stiffness_q")
        piston_start_frame_value = read_number("piston_start_frame")
        if radius is not None and radius <= 0.0:
            errors.append("radius must be positive")
        if separation is not None and separation < 0.0:
            errors.append("particle_separation_distance must not be negative")
        if wall_contact_offset is not None and wall_contact_offset < 0.0:
            errors.append("wall_contact_offset must not be negative")
        if collision_stiffness_q is not None and collision_stiffness_q < 0.0:
            errors.append("collision_stiffness_q must not be negative")
        piston_start_frame = None
        if piston_start_frame_value is not None:
            if piston_start_frame_value < 0.0:
                errors.append("piston_start_frame must not be negative")
            elif not piston_start_frame_value.is_integer():
                errors.append("piston_start_frame must be an integer")
            else:
                piston_start_frame = int(piston_start_frame_value)

        raw_velocity = self.itemcfg.get("piston_velocity")
        piston_velocity = None
        if raw_velocity is None:
            errors.append("piston_velocity is required")
        elif len(raw_velocity) != 3:
            errors.append("piston_velocity must contain exactly three values")
        else:
            try:
                piston_velocity = tuple(float(value) for value in raw_velocity)
            except (TypeError, ValueError):
                errors.append("piston_velocity values must be numeric")
            else:
                if not all(math.isfinite(value) for value in piston_velocity):
                    errors.append("piston_velocity values must be finite")
                elif piston_velocity[0] <= 0.0:
                    errors.append(
                        "piston_velocity x must be positive so the piston can "
                        "move across chamber_bounds"
                    )

        raw_view_center = self.itemcfg.get("view_center")
        view_center = None
        if raw_view_center is None:
            view_center = (
                0.5 * float(width),
                0.5 * float(height),
                0.5 * float(depth),
            )
        elif len(raw_view_center) != 3:
            errors.append("view_center must contain exactly three values")
        else:
            try:
                view_center = tuple(float(value) for value in raw_view_center)
            except (TypeError, ValueError):
                errors.append("view_center values must be numeric")
            else:
                if not all(math.isfinite(value) for value in view_center):
                    errors.append("view_center values must be finite")

        for key in ("data_dir", "output_file_prefix"):
            value = self.itemcfg.get(key)
            if value is None or not str(value).strip():
                errors.append(f"{key} is required")

        def validate_order(key, bounds):
            if bounds is None:
                return
            x_start, x_end, y_bottom, y_top, z_front, z_back = bounds
            if x_start >= x_end:
                errors.append(f"{key}: x_start must be less than x_end")
            if y_bottom >= y_top:
                errors.append(f"{key}: y_bottom must be less than y_top")
            if z_front != 0.0 or z_back != 3.0:
                errors.append(
                    f"{key}: 2D bounds require z_front=0 and z_back=3"
                )

        validate_order("chamber_bounds", chamber)

        if death is not None:
            if death[0] >= death[1]:
                errors.append("death_bounds: x_min must be less than x_max")
            if death[2] >= death[3]:
                errors.append("death_bounds: y_min must be less than y_max")
            if death[4] >= death[5]:
                errors.append("death_bounds: z_min must be less than z_max")

        if depth and depth <= 3:
            errors.append("cell_array_depth must be greater than 3 for 2D bounds")

        def validate_domain(key, bounds):
            if bounds is None or not width or not height or not depth:
                return
            limits = (
                ("x_start", bounds[0], 0.0, width - 1.0),
                ("x_end", bounds[1], 0.0, width - 1.0),
                ("y_bottom", bounds[2], 0.0, height - 1.0),
                ("y_top", bounds[3], 0.0, height - 1.0),
                ("z_front", bounds[4], 0.0, depth - 1.0),
                ("z_back", bounds[5], 0.0, depth - 1.0),
            )
            for name, value, lower, upper in limits:
                if value < lower or value > upper:
                    errors.append(
                        f"{key}: {name}={value:g} is outside "
                        f"[{lower:g}, {upper:g}]"
                    )

        validate_domain("chamber_bounds", chamber)

        if death is not None and width and height and depth:
            death_limits = (
                ("x_min", death[0], 0.0, float(width)),
                ("x_max", death[1], 0.0, float(width)),
                ("y_min", death[2], 0.0, float(height)),
                ("y_max", death[3], 0.0, float(height)),
                ("z_min", death[4], 0.0, float(depth)),
                ("z_max", death[5], 0.0, float(depth)),
            )
            for name, value, lower, upper in death_limits:
                if value < lower or value > upper:
                    errors.append(
                        f"death_bounds: {name}={value:g} is outside "
                        f"[{lower:g}, {upper:g}]"
                    )

        if death is not None:
            if chamber is not None:
                if (
                    chamber[0] < death[0] or chamber[1] > death[1]
                    or chamber[2] < death[2] or chamber[3] > death[3]
                    or chamber[4] < death[4] or chamber[5] > death[5]
                ):
                    errors.append("chamber_bounds must fit inside death_bounds")

        particle_plane_z = 1.0
        for segment_index, segment in enumerate(all_linear_segments):
            _a, _b, _c, x_start, y_start, x_end, y_end, _wall_flag = segment
            for endpoint_name, x_value, y_value in (
                ("start", x_start, y_start),
                ("end", x_end, y_end),
            ):
                if width and (x_value < 0.0 or x_value > width - 1.0):
                    errors.append(
                        f"linear segment {segment_index} {endpoint_name} "
                        "x is outside the cell array"
                    )
                if height and (y_value < 0.0 or y_value > height - 1.0):
                    errors.append(
                        f"linear segment {segment_index} {endpoint_name} "
                        "y is outside the cell array"
                    )
                if death is not None and (
                    x_value < death[0] or x_value > death[1]
                    or y_value < death[2] or y_value > death[3]
                    or particle_plane_z < death[4] or particle_plane_z > death[5]
                ):
                    errors.append(
                        f"linear segment {segment_index} {endpoint_name} "
                        "is outside death_bounds"
                    )

        if death is not None and radius is not None and radius > 0.0:
            if (
                particle_plane_z - radius < death[4]
                or particle_plane_z + radius >= death[5]
            ):
                errors.append(
                    "the full particle extent at z=1 must fit inside death_bounds"
                )

        if (
            chamber is not None
            and radius is not None
            and radius > 0.0
            and wall_contact_offset is not None
            and wall_contact_offset >= 0.0
        ):
            clearance = radius * (1.0 + wall_contact_offset) + 1.0e-9
            if chamber[1] - chamber[0] < 2.0 * clearance:
                errors.append("chamber x span is too small for wall clearance")
            if chamber[3] - chamber[2] < 2.0 * clearance:
                errors.append("chamber y span is too small for wall clearance")

        if errors:
            raise ValueError(
                "BoundaryParticleReservoirHorizontal configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )

        self.cell_array_width = width
        self.cell_array_height = height
        self.cell_array_depth = depth
        self.chamber_bounds = chamber
        self.death_bounds = death
        self.linear_chamber_segments = linear_chamber_segments
        self.linear_wall_segments = linear_wall_segments
        self.all_linear_segments = all_linear_segments
        self.particle_plane_z = particle_plane_z
        self.piston_velocity = piston_velocity
        self.view_center = view_center
        self.collision_stiffness_q = collision_stiffness_q
        self.piston_start_frame = piston_start_frame
        print(
            "BoundaryParticleReservoirHorizontal configuration: PASS\n"
            f"  cell array: {width}x{height}x{depth}\n"
            f"  chamber bounds: {chamber}\n"
            f"  chamber segments: {len(linear_chamber_segments)}\n"
            f"  outlet wall segments: {len(linear_wall_segments)}\n"
            f"  death bounds: {death}\n"
            f"  piston velocity: {piston_velocity}\n"
            f"  piston start frame: {piston_start_frame}\n"
            f"  view center: {view_center}\n"
            "  particle plane: z=1"
        )
        return True

    def calculate_chamber_packing(self):
        """Calculate and report a centered 2D particle grid without creating it."""
        radius = float(self.itemcfg.radius)
        separation = float(self.itemcfg.particle_separation_distance)
        wall_contact_offset = float(self.itemcfg.wall_contact_offset)
        if radius <= 0.0:
            raise ValueError("radius must be positive")
        if separation < 0.0:
            raise ValueError("particle_separation_distance must not be negative")
        if wall_contact_offset < 0.0:
            raise ValueError("wall_contact_offset must not be negative")

        diameter = 2.0 * radius
        center_spacing = diameter + separation
        boundary_clearance = radius * (1.0 + wall_contact_offset) + 1.0e-9
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
            raise ValueError("chamber bounds are too small for the particle diameter")

        x_count = int(math.floor((usable_x / center_spacing) + 1.0e-12)) + 1
        y_count = int(math.floor((usable_y / center_spacing) + 1.0e-12)) + 1
        occupied_x = (x_count - 1) * center_spacing
        occupied_y = (y_count - 1) * center_spacing
        first_x = x_center_min + 0.5 * (usable_x - occupied_x)
        first_y = y_center_min + 0.5 * (usable_y - occupied_y)

        self.packing_radius = radius
        self.particle_separation_distance = separation
        self.particle_center_spacing = center_spacing
        self.boundary_particle_clearance = boundary_clearance
        self.packing_x_count = x_count
        self.packing_y_count = y_count
        self.packing_particle_count = x_count * y_count
        self.packing_first_center = (first_x, first_y, self.particle_plane_z)
        self.packing_last_center = (
            first_x + occupied_x,
            first_y + occupied_y,
            self.particle_plane_z,
        )

        print(
            "BoundaryParticleReservoirHorizontal packing report:\n"
            f"  radius: {radius:g}\n"
            f"  surface separation: {separation:g}\n"
            f"  center spacing: {center_spacing:g}\n"
            f"  boundary clearance: {boundary_clearance:g}\n"
            f"  grid: {x_count} columns x {y_count} rows\n"
            f"  particle count: {self.packing_particle_count}\n"
            f"  first center: {self.packing_first_center}\n"
            f"  last center: {self.packing_last_center}"
        )
        return self.packing_particle_count

    def add_mobile_particles(self):
        """Materialize the calculated centered piston-chamber packing grid."""
        first_x, first_y, particle_z = self.packing_first_center
        velocity_x, velocity_y, velocity_z = self.piston_velocity

        for column in range(self.packing_x_count):
            particle_x = first_x + column * self.particle_center_spacing
            for row in range(self.packing_y_count):
                particle_y = first_y + row * self.particle_center_spacing
                particle_struct = pdata()
                self.number_active_particles += 1
                self.number_particles += 1
                particle_struct.pnum = self.number_particles
                particle_struct.rx = particle_x
                particle_struct.ry = particle_y
                particle_struct.rz = particle_z
                particle_struct.vx = velocity_x
                particle_struct.vy = velocity_y
                particle_struct.vz = velocity_z
                particle_struct.ptype = PTYPE_MOBILE
                particle_struct.molar_mass = 1.0
                particle_struct.radius = self.packing_radius
                particle_struct.state_flg = 0.0
                particle_struct.collision_stiffness_q = self.collision_stiffness_q
                self.p_list.append(particle_struct)

        print(
            "BoundaryParticleReservoirHorizontal mobile-particle report:\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  velocity: {self.piston_velocity}\n"
            f"  first particle number: 1\n"
            f"  last particle number: {self.number_active_particles}"
        )
        return self.number_active_particles

    @staticmethod
    def marker_axis_positions(axis_min, axis_max):
        """Return marker coordinates no farther than one cell apart."""
        lower = float(axis_min)
        upper = float(axis_max)
        if upper < lower:
            raise ValueError("marker axis maximum must not be below its minimum")
        positions = [lower]
        position = lower + 1.0
        while position < upper - 1.0e-9:
            positions.append(position)
            position += 1.0
        if not math.isclose(positions[-1], upper, abs_tol=1.0e-9):
            positions.append(upper)
        return positions

    def add_boundary_particles(self):
        """Create markers along every configured finite linear wall."""
        marker_locations = set()

        def add_marker(x, y, evaluator_id):
            key = (round(float(x), 9), round(float(y), 9), self.particle_plane_z)
            if key in marker_locations:
                return
            marker_locations.add(key)
            self.addBoundaryParticle(
                float(x),
                float(y),
                self.particle_plane_z,
                evaluator_id,
            )

        for segment in self.all_linear_segments:
            _a, _b, _c, x_start, y_start, x_end, y_end, _wall_flag = segment
            marker_intervals = max(
                1,
                int(math.ceil(max(abs(x_end - x_start), abs(y_end - y_start)))),
            )
            for marker_index in range(marker_intervals + 1):
                fraction = marker_index / marker_intervals
                marker_x = x_start + fraction * (x_end - x_start)
                marker_y = y_start + fraction * (y_end - y_start)
                add_marker(marker_x, marker_y, BOUNDARY_EVALUATOR_LINEAR)

        print(
            "BoundaryParticleReservoirHorizontal boundary report:\n"
            f"  boundary particles: {self.number_boundary_particles}\n"
            f"  chamber segments: {len(self.linear_chamber_segments)}\n"
            f"  outlet wall segments: {len(self.linear_wall_segments)}\n"
            f"  piston initial x: {self.chamber_bounds[0]:g}\n"
            f"  piston stop/nozzle start x: {self.chamber_bounds[1]:g}"
        )
        return self.number_boundary_particles

    def write_particle_bin(self):
        """Write null, mobile, and boundary records."""
        output_name = str(self.itemcfg.output_file_prefix)
        os.makedirs(self.itemcfg.data_dir, exist_ok=True)
        self.test_bin_name = os.path.join(
            str(self.itemcfg.data_dir),
            f"{output_name}.bin",
        )
        self.create_bin_file()
        if self.bin_file is None:
            raise OSError(f"Could not create binary file {self.test_bin_name}")
        try:
            self.write_bin_file(self.p_list)
        finally:
            self.close_bin_file()
        print(
            "BoundaryParticleReservoirHorizontal binary report:\n"
            f"  file: {self.test_bin_name}\n"
            f"  records: {self.count}"
        )
        return self.test_bin_name

   
    def addBoundaryParticle(
        self,
        rx,
        ry,
        rz=2.0,
        evaluator_id=BOUNDARY_EVALUATOR_NONE,
    ):
        particle_struct = pdata()
        self.number_boundary_particles += 1
        self.number_particles += 1
        particle_struct.pnum = self.number_particles
        particle_struct.rx = rx
        particle_struct.ry = ry
        particle_struct.rz = rz
        particle_struct.vx = 0.0
        particle_struct.vy = 0.0
        particle_struct.vz = 0.0
        particle_struct.ptype = float(evaluator_id)
        particle_struct.molar_mass = 1.0
        particle_struct.radius = 0.25
        particle_struct.state_flg = 0.0
        particle_struct.collision_stiffness_q = 0.0
        self.p_list.append(particle_struct)

    
    def writeCFGData(self,run_cfg):
        self.write_test_file(run_cfg)
        self.create_bin_file()
        self.write_bin_file(self.p_list)
        self.close_bin_file()
        self.report_generated_bounds()
        print(f"Piston chamber: wrote {self.number_particles} particles to {self.test_bin_name}")
