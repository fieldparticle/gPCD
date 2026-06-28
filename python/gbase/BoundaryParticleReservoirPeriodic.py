import random

from gbase.utilities import *
from gbase.GenDataBase import *
from gbase.BinaryFileUtilities import *
import math
from gbase.pdata import *
from gbase.libconf import AttrDict
import io
from gbase.msg_box import verify_dialog
class BoundaryParticleReservoirPeriodic():

    local_particles_in_row = 0
    local_particles_in_col = 0
    local_particles_in_layer = 0
    sel_file = None
    cell_items = []
    name = "genPCDData"
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
        p_list.append(particle_struct)

    def create(self,parent,itemcfg):
        self.parent = parent
        self.bobj = parent.bobj
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.itemcfg = itemcfg

   
    def do_all_files_dbg(self):
        self.runner()
    
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
        try:
            for ii in p_lst:
                self.bin_file.write(ii)
                self.count+=1
        except BaseException as e:
            self.log.log(self,e)

    def cfg_value(self, cfg, key, default):
        if key in cfg:
            return cfg[key]
        return default

    def frames_between_waves(
        self,
        particle_radius,
        inlet_velocity,
        dt,
        spacing_factor=1.1,
    ):
        """Return minimum whole-frame wait between release waves.

        The previous wave must move at least spacing_factor diameters before
        the next wave is born at the inlet.
        """
        radius = float(particle_radius)
        velocity = float(inlet_velocity)
        timestep = float(dt)
        spacing = float(spacing_factor)
        if radius <= 0.0:
            raise ValueError("particle_radius must be positive")
        if velocity <= 0.0:
            raise ValueError("inlet_velocity must be positive")
        if timestep <= 0.0:
            raise ValueError("dt must be positive")
        if spacing <= 0.0:
            raise ValueError("spacing_factor must be positive")

        clearance_distance = spacing * (2.0 * radius)
        distance_per_frame = velocity * timestep
        return int(math.ceil(clearance_distance / distance_per_frame))

    def build_release_config(
        self,
        run_cfg,
        radius,
        dt,
        particle_length,
        particles_per_row,
    ):
        starting_vx = float(self.cfg_value(run_cfg, "reservoir_starting_vx", 0.02))
        start_birth = float(self.cfg_value(run_cfg, "reservoir_start_birth", 10.0))
        spacing_factor = float(self.cfg_value(run_cfg, "reservoir_spacing_factor", 1.05))
        birth_jitter_frames = int(self.cfg_value(run_cfg, "reservoir_birth_jitter_frames", 0))
        position_jitter_fraction = float(self.cfg_value(run_cfg, "reservoir_position_jitter_fraction", 0.0))
        lateral_velocity = float(self.cfg_value(run_cfg, "reservoir_lateral_velocity", 0.05))
        random_lateral_velocity = bool(self.cfg_value(run_cfg, "reservoir_random_lateral_velocity", False))
        random_seed = int(self.cfg_value(run_cfg, "reservoir_random_seed", 12345))
        flow_angle_degrees = float(self.cfg_value(run_cfg, "flow_angle", 0.0))
        flow_angle = math.radians(flow_angle_degrees)
        flow_alignment = float(self.cfg_value(run_cfg, "flow_alignment", 1.0))
        flow_alignment = max(0.0, min(1.0, flow_alignment))
        flow_speed = float(self.cfg_value(run_cfg, "reservoir_flow_speed", abs(starting_vx)))
        forward_speed_for_spacing = float(
            self.cfg_value(
                run_cfg,
                "reservoir_forward_speed_for_spacing",
                flow_speed * max(flow_alignment, 0.1),
            )
        )

        frames_between = self.frames_between_waves(
            radius,
            abs(forward_speed_for_spacing),
            dt,
            spacing_factor=spacing_factor,
        )

        birth_step = frames_between + max(0, birth_jitter_frames)
        diameter = 2.0 * radius
        spacing_gap = max(0.0, particle_length - diameter)
        max_position_jitter = 0.5 * spacing_gap * max(0.0, min(1.0, position_jitter_fraction))

        return {
            "start_birth": start_birth,
            "frames_between_waves": frames_between,
            "birth_step": birth_step,
            "birth_jitter_frames": max(0, birth_jitter_frames),
            "inlet_x": float(self.cfg_value(run_cfg, "reservoir_inlet_x", 0.5)),
            "inlet_y": float(self.cfg_value(run_cfg, "reservoir_inlet_y", 0.5)),
            "base_x": float(self.cfg_value(run_cfg, "reservoir_base_x", 1.0)),
            "base_y": float(self.cfg_value(run_cfg, "reservoir_base_y", 1.0)),
            "z": float(self.cfg_value(run_cfg, "reservoir_z", 2.0)),
            "particle_length": particle_length,
            "starting_vx": starting_vx,
            "flow_angle": flow_angle,
            "flow_alignment": flow_alignment,
            "flow_speed": flow_speed,
            "lateral_velocity": lateral_velocity,
            "random_lateral_velocity": random_lateral_velocity,
            "halfway_row": math.ceil((particles_per_row - 1) / 2),
            "max_position_jitter": max_position_jitter,
            "rng": random.Random(random_seed),
        }

    def flow_velocity_for_particle(self, release_cfg):
        flow_alignment = release_cfg["flow_alignment"]
        flow_angle = release_cfg["flow_angle"]
        flow_speed = release_cfg["flow_speed"]
        rng = release_cfg["rng"]

        flow_x = math.cos(flow_angle)
        flow_y = math.sin(flow_angle)
        random_angle = rng.uniform(0.0, 2.0 * math.pi)
        random_x = math.cos(random_angle)
        random_y = math.sin(random_angle)

        dir_x = flow_alignment * flow_x + (1.0 - flow_alignment) * random_x
        dir_y = flow_alignment * flow_y + (1.0 - flow_alignment) * random_y
        dir_mag = math.hypot(dir_x, dir_y)
        if dir_mag <= 1.0e-12:
            dir_x = flow_x
            dir_y = flow_y
        else:
            dir_x /= dir_mag
            dir_y /= dir_mag

        return flow_speed * dir_x, flow_speed * dir_y

    def release_state_for_particle(self, row, col, release_cfg):
        rng = release_cfg["rng"]
        jitter = 0
        if release_cfg["birth_jitter_frames"] > 0:
            jitter = rng.randint(0, release_cfg["birth_jitter_frames"])

        birth_frame = (
            release_cfg["start_birth"]
            + release_cfg["birth_step"] * (col - 1.0)
            + jitter
        )

        y_jitter = 0.0
        if release_cfg["max_position_jitter"] > 0.0:
            y_jitter = rng.uniform(
                -release_cfg["max_position_jitter"],
                release_cfg["max_position_jitter"],
            )

        if release_cfg["random_lateral_velocity"]:
            vy = rng.uniform(
                -release_cfg["lateral_velocity"],
                release_cfg["lateral_velocity"],
            )
        elif row >= release_cfg["halfway_row"]:
            vy = release_cfg["lateral_velocity"]
        else:
            vy = -release_cfg["lateral_velocity"]

        rx = release_cfg["inlet_x"]
        ry = release_cfg["base_y"] + row * release_cfg["particle_length"] + y_jitter
        rz = release_cfg["z"]
        vx, flow_vy = self.flow_velocity_for_particle(release_cfg)
        if release_cfg["flow_alignment"] < 1.0:
            vy = flow_vy
        vz = 0.0

        return birth_frame, rx, ry, rz, vx, vy, vz

    def release_state_for_particle_vert(self, row, col, release_cfg):
        birth_frame, _rx, _ry, rz, vx, vy, vz = self.release_state_for_particle(
            row,
            col,
            release_cfg,
        )

        rng = release_cfg["rng"]
        x_jitter = 0.0
        if release_cfg["max_position_jitter"] > 0.0:
            x_jitter = rng.uniform(
                -release_cfg["max_position_jitter"],
                release_cfg["max_position_jitter"],
            )

        rx = release_cfg["base_x"] + row * release_cfg["particle_length"] + x_jitter
        ry = release_cfg["inlet_y"]
        return birth_frame, rx, ry, rz, vx, vy, vz

        #******************************************************************
    # Write the tst files taht are read by particle.exe for tests
    # 
    #
    def write_test_file(self,run_cfg=None):

        try:
            f = open(self.test_file_name,'w')
        except BaseException as e:
            raise BaseException(f"Can't open testfile {self.test_file_name} err{e}")
        fstr = f"index = {self.index};\n"     
        f.write(fstr)
        # size lengths must be plus 1 since the cell locations start as <0,0,0>
        # Side length is selected before geometry is generated so walls,
        # particles, and test metadata agree.
        fstr = f"CellAryW = {int(self.side_len)};\n"     
        f.write(fstr)
        fstr = f"CellAryH = {int(self.side_len)};\n"     
        f.write(fstr)
        fstr = f"CellAryL = {int(self.side_len)};\n"     
        f.write(fstr)
        fstr = f"radius = {run_cfg.radius};\n"
        f.write(fstr)
        fstr = f"num_particles = {self.number_particles};\n"
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
        fstr = f"workGroupsx = {run_cfg.workGroupsx}\n"
        f.write(fstr)
        fstr = f"workGroupsy = {run_cfg.workGroupsy};\n"
        f.write(fstr)
        fstr = f"workGroupsz = {run_cfg.workGroupsz};\n"
        f.write(fstr)
        fstr = f"cell_occupancy_list_size = {run_cfg.cell_occupancy_list_size};\n"
        f.write(fstr)
        fstr = f"wallXMIN = {self.wallxmin};\n"
        f.write(fstr)
        fstr = f"wallXMAX = {self.wallxmax};\n"
        f.write(fstr)
        fstr = f"wallYMIN = {self.wallymin};\n"
        f.write(fstr)
        fstr = f"wallYMAX = {self.wallymax};\n"
        f.write(fstr)
        fstr = f"wallZMIN = {self.wallymin};\n"
        f.write(fstr)
        fstr = f"wallZMAX = {self.wallymax};\n"
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
        fstr = f'boundary_particle_function = "{run_cfg.boundary_particle_function}";\n'
        f.write(fstr)
        fstr = f'periodic_direction = "horizontal";\n'
        f.write(fstr)
        fstr = f'boundary_guard = "cell_guard";\n'
        f.write(fstr)
        fstr = f'wall = "horizontal";\n'
        f.write(fstr)
        fstr = f'wall_type= "{run_cfg.wall_type}";\n'
        f.write(fstr)

        f.flush()
        f.close()
        

    def runner(self):
        run_cfg = get_run_configuration(self.itemcfg)
        boundary_particle_function = str(
            self.cfg_value(
                run_cfg,
                "boundary_particle_function",
                "horizontal_wall",
            )
        ).lower()
        if boundary_particle_function == "vertical_wall":
            self.gen_vert()
        else:
            self.gen_horz()

        read_particle_data(self.test_bin_name)

    def boundary_guard_margin_cells(self):
        """Return cell-array safety margin outside the physical pipe walls."""
        return 3.0

    def base_pipe_side_len(self):
        return math.ceil(
            self.itemcfg.particles_per_row / self.itemcfg.particles_per_cell_row
        ) + 2.0

    def configured_side_len(self, run_cfg, base_side_len, margin):
        """Return the configured cell-domain side length.

        The explicit override wins when positive. Otherwise use side_len from
        the merged cfg. Derivation from packed pipe width is retained only for
        old configurations that provide neither field.
        """
        override = float(
            self.cfg_value(
                run_cfg,
                "over_ride_side_length",
                self.cfg_value(self.itemcfg, "over_ride_side_length", 0.0),
            )
        )
        if override > 0.0:
            return override
        configured = float(self.cfg_value(run_cfg, "side_len", 0.0))
        if configured > 0.0:
            return configured
        return base_side_len + (2.0 * margin)

    def centered_pipe_offset(self, side_len, base_side_len):
        return max(0.0, 0.5 * (side_len - base_side_len))

    def boundary_wall_length(self, run_cfg):
        """Return the configured physical marker-wall length."""
        wall_length = float(
            self.cfg_value(run_cfg, "wall_boundary_length", 0.0)
        )
        if wall_length <= 0.0:
            raise ValueError("wall_boundary_length must be positive")
        return wall_length

    def validate_pipe_geometry(self, cross_max, axial_max):
        """Ensure generated wall coordinates fit the selected cell domain."""
        if cross_max > self.side_len:
            raise ValueError(
                "Packed pipe width exceeds the configured cell-domain "
                f"side length: cross_max={cross_max}, side_len={self.side_len}"
            )
        if axial_max > self.side_len:
            raise ValueError(
                "wall_boundary_length exceeds the configured cell-domain "
                f"side length: axial_max={axial_max}, side_len={self.side_len}"
            )

    # ------------------------------------------------------------------
    # Simulation configuration checks
    # ------------------------------------------------------------------
    def validate_simulation_configuration(
        self,
        run_cfg,
        orientation,
        radius,
        dt,
        particle_length,
    ):
        """Validate manual cfg inputs against calculated reservoir geometry."""
        errors = []
        warnings = []
        diameter = 2.0 * radius
        packed_cell_length = (
            float(self.itemcfg.particles_per_cell_row) * particle_length
        )

        if radius <= 0.0:
            errors.append("radius must be positive")
        if dt <= 0.0:
            errors.append("dt must be positive")
        if int(self.itemcfg.particle_columns) <= 0:
            errors.append("particle_columns must be positive")
        if int(self.itemcfg.particles_per_row) <= 0:
            errors.append("particles_per_row must be positive")
        if int(self.itemcfg.particles_per_cell_row) <= 0:
            errors.append("particles_per_cell_row must be positive")
        if packed_cell_length > 1.0 + 1.0e-9:
            errors.append(
                "particles_per_cell_row does not fit in one cell: "
                f"packed length={packed_cell_length:.6g}"
            )

        if orientation == "horizontal":
            inlet_key = "reservoir_inlet_x"
            outlet_key = "reservoir_outlet_x"
            wall_min = self.wallxmin
            wall_max = self.wallxmax
        else:
            inlet_key = "reservoir_inlet_y"
            outlet_key = "reservoir_outlet_y"
            wall_min = self.wallymin
            wall_max = self.wallymax

        if inlet_key not in run_cfg:
            errors.append(f"{inlet_key} is required")
            inlet = wall_min
        else:
            inlet = float(run_cfg[inlet_key])
        if outlet_key not in run_cfg:
            errors.append(f"{outlet_key} is required")
            outlet = wall_max
        else:
            outlet = float(run_cfg[outlet_key])

        if abs(inlet - wall_min) > 1.0e-9:
            errors.append(
                f"{inlet_key}={inlet:g} does not match the calculated "
                f"inlet marker wall at {wall_min:g}"
            )
        if outlet <= wall_max:
            errors.append(
                f"{outlet_key}={outlet:g} must be beyond the XMAX/YMAX "
                f"marker wall at {wall_max:g}"
            )
        if outlet > self.side_len:
            errors.append(
                f"{outlet_key}={outlet:g} exceeds cell-domain side_len="
                f"{self.side_len:g}"
            )

        birth_factor = max(
            1.1,
            float(run_cfg.get("reservoir_birth_spacing_factor", 1.1)),
        )
        birth_position = inlet + birth_factor * diameter
        minimum_birth_position = wall_min + 1.1 * diameter
        if birth_position + 1.0e-12 < minimum_birth_position:
            errors.append(
                f"birth position {birth_position:g} does not clear the inlet "
                f"wall by 1.1 diameters ({minimum_birth_position:g})"
            )

        x_limits = run_cfg.get("x_axis_lims")
        y_limits = run_cfg.get("y_axis_lims")
        for key, limits in (
            ("x_axis_lims", x_limits),
            ("y_axis_lims", y_limits),
        ):
            if limits is None or len(limits) < 2:
                errors.append(f"{key} must contain [minimum, maximum]")
            elif float(limits[0]) >= float(limits[1]):
                errors.append(f"{key} minimum must be less than maximum")

        if x_limits is not None and len(x_limits) >= 2:
            if self.wallxmin < float(x_limits[0]) or self.wallxmax > float(x_limits[1]):
                warnings.append("x_axis_lims does not contain all marker walls")
        if y_limits is not None and len(y_limits) >= 2:
            if self.wallymin < float(y_limits[0]) or self.wallymax > float(y_limits[1]):
                warnings.append("y_axis_lims does not contain all marker walls")

        print("Simulation configuration check: BoundaryParticleReservoirPeriodic")
        print(
            f"  manual: side_len={self.side_len:g}, wall_boundary_length="
            f"{float(run_cfg.wall_boundary_length):g}, radius={radius:g}, dt={dt:g}"
        )
        print(
            f"  calculated walls: x=[{self.wallxmin:g},{self.wallxmax:g}], "
            f"y=[{self.wallymin:g},{self.wallymax:g}]"
        )
        print(
            f"  lifecycle: inlet={inlet:g}, birth={birth_position:g}, "
            f"outlet={outlet:g}; packed cell length={packed_cell_length:g}"
        )
        for warning in warnings:
            print(f"  WARNING: {warning}")
        if errors:
            raise ValueError(
                "BoundaryParticleReservoirPeriodic configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )
        print("  PASS")

    def configure_vertical_pipe_geometry(self, run_cfg):
        margin = self.boundary_guard_margin_cells()
        base_side_len = self.base_pipe_side_len()
        self.side_len = self.configured_side_len(run_cfg, base_side_len, margin)
        pipe_offset = self.centered_pipe_offset(self.side_len, base_side_len)
        wall_length = self.boundary_wall_length(run_cfg)
        self.wallxmin = pipe_offset + 0.5
        self.wallxmax = pipe_offset + base_side_len - 1.0
        self.wallymin = 0.5
        self.wallymax = self.wallymin + wall_length
        self.validate_pipe_geometry(self.wallxmax, self.wallymax)
        return margin, base_side_len, pipe_offset, wall_length

    def configure_horizontal_pipe_geometry(self, run_cfg):
        margin = self.boundary_guard_margin_cells()
        base_side_len = self.base_pipe_side_len()
        self.side_len = self.configured_side_len(run_cfg, base_side_len, margin)
        pipe_offset = self.centered_pipe_offset(self.side_len, base_side_len)
        wall_length = self.boundary_wall_length(run_cfg)
        self.wallxmin = float(
            self.cfg_value(run_cfg, "reservoir_inlet_x", 0.5)
        )
        self.wallxmax = self.wallxmin + wall_length
        self.wallymin = pipe_offset + 0.5
        self.wallymax = pipe_offset + base_side_len - 1.0
        self.validate_pipe_geometry(self.wallymax, self.wallxmax)
        return margin, base_side_len, pipe_offset, wall_length
    
    # Generate vertical-wall boundary flow.
    def gen_vert(self):
        config = None
        self.p_list = []
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0
        self.add_null_particle(self.p_list)
        self.index = 0
        run_cfg = get_run_configuration(self.itemcfg)
        radius = float(self.cfg_value(run_cfg, "radius", 0.25))
        dt = float(self.cfg_value(run_cfg, "dt", 1.0))
        collision_stiffness_q = float(self.cfg_value(run_cfg, "collision_stiffness_q", 0.0))
        # Paticle length is twice the radius times the fraction of diameter separation.
        particle_length =2.0*radius+2.0*radius*self.itemcfg.fraction_of_diameter_separation
        # The particle row length is the number of particles per cell row times the particle length. 
        particle_cell_row_length = self.itemcfg.particles_per_cell_row*particle_length
        print(f"Paricle row length is {particle_cell_row_length:.2f} with separation distance of {self.itemcfg.fraction_of_diameter_separation} and radius of {radius}")
        # Take the difference between the particle row length and 1.0 to see how much space is 
        # left in a cell row. Then divide by the particle length to see how 
        # many more particles could fit in the row if we wanted to add more.
        particle_row_length_difference = 1.0 - particle_cell_row_length
        # See how many particles can fit in the cell row.
        can_fit = particle_row_length_difference/particle_length
        print(f"Particle row length difference is {particle_row_length_difference:.2f} can fit {can_fit:.2f} particles")
        particles_per_row = self.itemcfg.particles_per_row
        required_width = particles_per_row/self.itemcfg.particles_per_cell_row
        margin, base_side_len, pipe_offset, wall_length = self.configure_vertical_pipe_geometry(
            run_cfg
        )
        self.validate_simulation_configuration(
            run_cfg,
            "vertical",
            radius,
            dt,
            particle_length,
        )
        print(
            f"Side length is {self.side_len} for particles per row of {particles_per_row} "
            f"and particles per cell row of {self.itemcfg.particles_per_cell_row}; "
            f"vertical pipe is centered with cross-axis offset {pipe_offset} "
            f"inside base side length {base_side_len}; wall boundary length {wall_length}"
        )
        total_cell_row_length = self.itemcfg.particles_per_cell_row*particle_length
        empty_space = 1.0 - total_cell_row_length 
        empty_particle_count = math.floor(empty_space/particle_length)
        print(f"total_cell_row_length is {total_cell_row_length:.2f} empty space is {empty_space:.2f} which can fit {empty_particle_count:.2f} more particles in the row if we wanted to add more.")        
        tot_particles = self.itemcfg.particle_columns*self.itemcfg.particles_per_row
        particles_per_row = self.itemcfg.particles_per_row
        release_cfg = self.build_release_config(
            run_cfg,
            radius,
            dt,
            particle_length,
            particles_per_row,
        )
        release_cfg["base_x"] = release_cfg["base_x"] + pipe_offset
        try:
            for col in range(1,self.itemcfg.particle_columns+1):    
                for row in range(1,particles_per_row+1):     
                    birth_frame, rx, ry, rz, vx, vy, vz = self.release_state_for_particle_vert(
                        row,
                        col,
                        release_cfg,
                    )
                    particle_struct = pdata()
                    self.number_active_particles +=1
                    self.number_particles += 1
                    particle_struct.pnum = self.number_particles
                    particle_struct.rx = rx
                    particle_struct.ry = ry
                    particle_struct.rz = rz
                    particle_struct.vx = vx
                    particle_struct.vy = vy
                    particle_struct.vz = vz
                    particle_struct.ptype = 0.0
                    particle_struct.molar_mass = 1.0
                    particle_struct.radius = radius
                    particle_struct.state_flg = birth_frame
                    particle_struct.collision_stiffness_q = collision_stiffness_q
                    self.p_list.append(particle_struct)
        except BaseException as e:
            print(f"Failed adding Particle:{e} ")   
            return
        self.BoundaryParticlesVert(run_cfg)
        self.writeCFGData(run_cfg)

    # Generate horizontal flow        
    def gen_horz(self):
        config = None
        self.p_list = []
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0
        self.add_null_particle(self.p_list)
        self.index = 0
        run_cfg = get_run_configuration(self.itemcfg)
        radius = float(self.cfg_value(run_cfg, "radius", 0.25))
        dt = float(self.cfg_value(run_cfg, "dt", 1.0))
        collision_stiffness_q = float(self.cfg_value(run_cfg, "collision_stiffness_q", 0.0))
        # Paticle length is twice the radius times the fraction of diameter separation.
        particle_length =2.0*radius+2.0*radius*self.itemcfg.fraction_of_diameter_separation
        # The particle row length is the number of particles per cell row times the particle length. 
        particle_cell_row_length = self.itemcfg.particles_per_cell_row*particle_length
        print(f"Paricle row length is {particle_cell_row_length:.2f} with separation distance of {self.itemcfg.fraction_of_diameter_separation} and radius of {radius}")
        # Take the difference between the particle row length and 1.0 to see how much space is 
        # left in a cell row. Then divide by the particle length to see how 
        # many more particles could fit in the row if we wanted to add more.
        particle_row_length_difference = 1.0 - particle_cell_row_length
        # See how many particles can fit in the cell row.
        can_fit = particle_row_length_difference/particle_length
        print(f"Particle row length difference is {particle_row_length_difference:.2f} can fit {can_fit:.2f} particles")
        particles_per_row = self.itemcfg.particles_per_row
        required_width = particles_per_row/self.itemcfg.particles_per_cell_row
        margin, base_side_len, pipe_offset, wall_length = self.configure_horizontal_pipe_geometry(
            run_cfg
        )
        self.validate_simulation_configuration(
            run_cfg,
            "horizontal",
            radius,
            dt,
            particle_length,
        )
        print(
            f"Side length is {self.side_len} for particles per row of {particles_per_row} "
            f"and particles per cell row of {self.itemcfg.particles_per_cell_row}; "
            f"horizontal pipe is centered with cross-axis offset {pipe_offset} "
            f"inside base side length {base_side_len}; wall boundary length {wall_length}"
        )
        total_cell_row_length = self.itemcfg.particles_per_cell_row*particle_length
        empty_space = 1.0 - total_cell_row_length 
        empty_particle_count = math.floor(empty_space/particle_length)
        print(f"total_cell_row_length is {total_cell_row_length:.2f} empty space is {empty_space:.2f} which can fit {empty_particle_count:.2f} more particles in the row if we wanted to add more.")        
        tot_particles = self.itemcfg.particle_columns*self.itemcfg.particles_per_row
        total_colums = self.itemcfg.particle_columns
        particles_per_row = self.itemcfg.particles_per_row
        release_cfg = self.build_release_config(
            run_cfg,
            radius,
            dt,
            particle_length,
            particles_per_row,
        )
        release_cfg["base_y"] = release_cfg["base_y"] + pipe_offset
        try:
            for col in range(1,total_colums+1):    
                for row in range(1,particles_per_row+1):     
                    birth_frame, rx, ry, rz, vx, vy, vz = self.release_state_for_particle(
                        row,
                        col,
                        release_cfg,
                    )
                    particle_struct = pdata()
                    self.number_active_particles +=1
                    self.number_particles += 1
                    particle_struct.pnum = self.number_particles
                    particle_struct.rx = rx
                    particle_struct.ry = ry
                    particle_struct.rz = rz
                    particle_struct.vx = vx
                    particle_struct.vy = vy
                    particle_struct.vz = vz
                    particle_struct.ptype = 0.0
                    particle_struct.molar_mass = 1.0
                    particle_struct.radius = radius
                    particle_struct.state_flg = birth_frame
                    particle_struct.collision_stiffness_q = collision_stiffness_q
                    self.p_list.append(particle_struct)
        except BaseException as e:
            print(f"Failed adding Particle:{e} ")   
            return
        self.BoundaryParticlesHorz(run_cfg)
        self.writeCFGData(run_cfg)



    def BoundaryParticlesHorz(self,run_cfg):
        marker_locations = set()

        def add_marker(x, y, evaluator_id):
            key = (float(x), float(y), 2.0)
            if key in marker_locations:
                return
            marker_locations.add(key)
            self.addBoundaryParticle(
                run_cfg,
                key[0],
                key[1],
                key[2],
                evaluator_id=evaluator_id,
            )

        # Add the closed inlet and outlet first so exact corner coordinates
        # belong to the vertical evaluator. Horizontal insertion then skips
        # those duplicate coordinates.
        for wy in range(
            int(math.ceil(self.wallymin)),
            int(math.floor(self.wallymax)) + 1,
        ):
            add_marker(
                self.wallxmin,
                float(wy),
                BOUNDARY_EVALUATOR_VERTICAL,
            )
            add_marker(
                self.wallxmax,
                float(wy),
                BOUNDARY_EVALUATOR_VERTICAL,
            )

        for wx in range(
            int(math.ceil(self.wallxmin)),
            int(math.floor(self.wallxmax)) + 1,
        ):
            add_marker(
                float(wx),
                self.wallymin,
                BOUNDARY_EVALUATOR_HORIZONTAL,
            )
            add_marker(
                float(wx),
                self.wallymax,
                BOUNDARY_EVALUATOR_HORIZONTAL,
            )
        
    def BoundaryParticlesVert(self,run_cfg):
        for wy in range(int(self.wallymax)):
            self.addBoundaryParticle(
                run_cfg,
                self.wallxmin+0.5,
                float(wy+1.0),
                evaluator_id=BOUNDARY_EVALUATOR_VERTICAL,
            )

        for wy in range(int(self.wallymax)):
            self.addBoundaryParticle(
                run_cfg,
                self.wallxmax-0.75,
                float(wy+1.0),
                evaluator_id=BOUNDARY_EVALUATOR_VERTICAL,
            )


    def addBoundaryParticle(
        self,
        run_cfg,
        rx,
        ry,
        rz=2.0,
        evaluator_id=BOUNDARY_EVALUATOR_NONE,
    ):
        try:
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
            particle_struct.ptype = 1.0
            particle_struct.temp_vel = float(evaluator_id)
            particle_struct.molar_mass = 1.0
            particle_struct.radius = 0.25
            particle_struct.state_flg = 0.0
            particle_struct.collision_stiffness_q = 0.0
            self.p_list.append(particle_struct)
        except BaseException as e:
            print(f"Failed adding Particle:{e} ")   
            return

    
    def writeCFGData(self,run_cfg):
        
        self.write_test_file(run_cfg)
        self.create_bin_file()
        self.write_bin_file(self.p_list)
        self.close_bin_file()
        print(f"PipeReservoirEntry: Wrote {self.number_particles} reservoir particles to {self.test_bin_name}")
