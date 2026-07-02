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
        reservoir_x_start, _reservoir_x_end, reservoir_y_bottom, reservoir_y_top, _, _ = self.reservoir_bounds
        _pipe_x_start, pipe_x_end, pipe_y_bottom, pipe_y_top, _, _ = self.pipe_bounds
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
        fstr = f"boundary_x_min = {reservoir_x_start:0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_x_max = {pipe_x_end:0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_y_min = {min(reservoir_y_bottom, pipe_y_bottom):0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_y_max = {max(reservoir_y_top, pipe_y_top):0.6f};\n"
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
        fstr = f"wall_contact_offset = {float(run_cfg.wall_contact_offset):0.6f};\n"
        f.write(fstr)
        f.write('wall_type = "WALL_MODEL_BOUNDARY_PARTICLE";\n')
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
            self.calculate_reservoir_packing()
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
        """Validate horizontal 2D reservoir and pipe bounds."""
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

        reservoir = read_bounds("reservoir_bounds")
        pipe = read_bounds("pipe_bounds")
        death = read_bounds("death_bounds")

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
        if radius is not None and radius <= 0.0:
            errors.append("radius must be positive")
        if separation is not None and separation < 0.0:
            errors.append("particle_separation_distance must not be negative")
        if wall_contact_offset is not None and wall_contact_offset < 0.0:
            errors.append("wall_contact_offset must not be negative")
        if collision_stiffness_q is not None and collision_stiffness_q < 0.0:
            errors.append("collision_stiffness_q must not be negative")

        raw_velocity = self.itemcfg.get("reservoir_velocity")
        reservoir_velocity = None
        if raw_velocity is None:
            errors.append("reservoir_velocity is required")
        elif len(raw_velocity) != 3:
            errors.append("reservoir_velocity must contain exactly three values")
        else:
            try:
                reservoir_velocity = tuple(float(value) for value in raw_velocity)
            except (TypeError, ValueError):
                errors.append("reservoir_velocity values must be numeric")
            else:
                if not all(math.isfinite(value) for value in reservoir_velocity):
                    errors.append("reservoir_velocity values must be finite")

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

        validate_order("reservoir_bounds", reservoir)
        validate_order("pipe_bounds", pipe)

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

        validate_domain("reservoir_bounds", reservoir)
        validate_domain("pipe_bounds", pipe)

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

        if reservoir is not None and pipe is not None:
            if not math.isclose(reservoir[1], pipe[0], abs_tol=1.0e-9):
                errors.append(
                    "reservoir x_end must equal pipe x_start for a connected "
                    "horizontal conduit"
                )
            if pipe[2] < reservoir[2] or pipe[3] > reservoir[3]:
                errors.append(
                    "pipe y bounds must fit within the reservoir outlet face"
                )
            if pipe[4] < reservoir[4] or pipe[5] > reservoir[5]:
                errors.append(
                    "pipe z bounds must fit within the reservoir outlet face"
                )

        if death is not None:
            for key, bounds in (
                ("reservoir_bounds", reservoir),
                ("pipe_bounds", pipe),
            ):
                if bounds is None:
                    continue
                if (
                    bounds[0] < death[0] or bounds[1] > death[1]
                    or bounds[2] < death[2] or bounds[3] > death[3]
                    or bounds[4] < death[4] or bounds[5] > death[5]
                ):
                    errors.append(f"{key} must fit inside death_bounds")

        particle_plane_z = 1.0
        if death is not None and radius is not None and radius > 0.0:
            if (
                particle_plane_z - radius < death[4]
                or particle_plane_z + radius >= death[5]
            ):
                errors.append(
                    "the full particle extent at z=1 must fit inside death_bounds"
                )

        if (
            reservoir is not None
            and radius is not None
            and radius > 0.0
            and wall_contact_offset is not None
            and wall_contact_offset >= 0.0
        ):
            clearance = radius * (1.0 + wall_contact_offset) + 1.0e-9
            if reservoir[1] - reservoir[0] < 2.0 * clearance:
                errors.append("reservoir x span is too small for wall clearance")
            if reservoir[3] - reservoir[2] < 2.0 * clearance:
                errors.append("reservoir y span is too small for wall clearance")

        if errors:
            raise ValueError(
                "BoundaryParticleReservoirHorizontal configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )

        self.cell_array_width = width
        self.cell_array_height = height
        self.cell_array_depth = depth
        self.reservoir_bounds = reservoir
        self.pipe_bounds = pipe
        self.death_bounds = death
        self.particle_plane_z = particle_plane_z
        self.reservoir_velocity = reservoir_velocity
        self.view_center = view_center
        self.collision_stiffness_q = collision_stiffness_q
        print(
            "BoundaryParticleReservoirHorizontal configuration: PASS\n"
            f"  cell array: {width}x{height}x{depth}\n"
            f"  reservoir bounds: {reservoir}\n"
            f"  pipe bounds: {pipe}\n"
            f"  death bounds: {death}\n"
            f"  reservoir velocity: {reservoir_velocity}\n"
            f"  view center: {view_center}\n"
            "  particle plane: z=1"
        )
        return True

    def calculate_reservoir_packing(self):
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
            self.reservoir_bounds
        )
        x_center_min = x_start + boundary_clearance
        x_center_max = x_end - boundary_clearance
        y_center_min = y_bottom + boundary_clearance
        y_center_max = y_top - boundary_clearance
        usable_x = x_center_max - x_center_min
        usable_y = y_center_max - y_center_min
        if usable_x < 0.0 or usable_y < 0.0:
            raise ValueError("reservoir bounds are too small for the particle diameter")

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
        """Materialize the calculated centered reservoir packing grid."""
        first_x, first_y, particle_z = self.packing_first_center
        velocity_x, velocity_y, velocity_z = self.reservoir_velocity

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
            f"  velocity: {self.reservoir_velocity}\n"
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
        """Create closed-reservoir and open-ended pipe marker walls."""
        reservoir_x_start, reservoir_x_end, reservoir_y_bottom, reservoir_y_top, _, _ = (
            self.reservoir_bounds
        )
        pipe_x_start, pipe_x_end, pipe_y_bottom, pipe_y_top, _, _ = self.pipe_bounds
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

        # The reservoir inlet is closed. The pipe outlet intentionally has no
        # corresponding vertical marker line.
        for y in self.marker_axis_positions(reservoir_y_bottom, reservoir_y_top):
            add_marker(
                reservoir_x_start,
                y,
                BOUNDARY_EVALUATOR_VERTICAL,
            )

        # If the pipe is narrower than the reservoir, close the two shoulder
        # portions of the shared interface while leaving the pipe opening clear.
        if pipe_y_bottom > reservoir_y_bottom:
            for y in self.marker_axis_positions(reservoir_y_bottom, pipe_y_bottom):
                add_marker(pipe_x_start, y, BOUNDARY_EVALUATOR_VERTICAL)
        if pipe_y_top < reservoir_y_top:
            for y in self.marker_axis_positions(pipe_y_top, reservoir_y_top):
                add_marker(pipe_x_start, y, BOUNDARY_EVALUATOR_VERTICAL)

        for x_min, x_max, y in (
            (reservoir_x_start, reservoir_x_end, reservoir_y_bottom),
            (reservoir_x_start, reservoir_x_end, reservoir_y_top),
            (pipe_x_start, pipe_x_end, pipe_y_bottom),
            (pipe_x_start, pipe_x_end, pipe_y_top),
        ):
            for x in self.marker_axis_positions(x_min, x_max):
                add_marker(x, y, BOUNDARY_EVALUATOR_HORIZONTAL)

        print(
            "BoundaryParticleReservoirHorizontal boundary report:\n"
            f"  boundary particles: {self.number_boundary_particles}\n"
            f"  closed inlet x: {reservoir_x_start:g}\n"
            f"  reservoir/pipe interface x: {pipe_x_start:g}\n"
            f"  open pipe outlet x: {pipe_x_end:g}"
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
        print(f"PipeReservoirEntry: Wrote {self.number_particles} reservoir particles to {self.test_bin_name}")
