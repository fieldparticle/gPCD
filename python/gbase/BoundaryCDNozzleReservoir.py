import random
import os

from gbase.utilities import *
from gbase.GenDataBase import *
from gbase.BinaryFileUtilities import *
import math
from gbase.pdata import *
from gbase.libconf import AttrDict
import io
from gbase.msg_box import verify_dialog
class BoundaryCDNozzleReservoir():

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
            print(f"Delete bin file does not exist yet {self.test_file_name}")
        self.test_bin_name = f"{self.itemcfg.data_dir}/{cfg_data_name}.bin"
        try:
            os.remove(self.test_bin_name)
        except BaseException as e:
            print(f"Delete bin file does not exist yet {self.test_file_name}")
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
        center_min = [float("inf")] * 3
        center_max = [float("-inf")] * 3
        rendered_min = [float("inf")] * 3
        rendered_max = [float("-inf")] * 3
        try:
            for ii in p_lst:
                self.bin_file.write(ii)
                self.count+=1
                if int(ii.pnum) == 0:
                    continue
                center = (float(ii.rx), float(ii.ry), float(ii.rz))
                radius = float(ii.radius)
                for axis in range(3):
                    center_min[axis] = min(center_min[axis], center[axis])
                    center_max[axis] = max(center_max[axis], center[axis])
                    rendered_min[axis] = min(
                        rendered_min[axis], center[axis] - radius
                    )
                    rendered_max[axis] = max(
                        rendered_max[axis], center[axis] + radius
                    )
        except BaseException as e:
            self.log.log(self,e)
        if center_min[0] != float("inf"):
            self.generated_bounds = {
                "center": {
                    "x": (center_min[0], center_max[0]),
                    "y": (center_min[1], center_max[1]),
                    "z": (center_min[2], center_max[2]),
                },
                "rendered": {
                    "x": (rendered_min[0], rendered_max[0]),
                    "y": (rendered_min[1], rendered_max[1]),
                    "z": (rendered_min[2], rendered_max[2]),
                },
            }
        else:
            self.generated_bounds = None

    def report_generated_bounds(self):
        if not self.generated_bounds:
            print("Generated particle bounds: no non-null particles")
            return
        center = self.generated_bounds["center"]
        rendered = self.generated_bounds["rendered"]
        print(
            "Generated center bounds: "
            f"x=[{center['x'][0]:.6g},{center['x'][1]:.6g}], "
            f"y=[{center['y'][0]:.6g},{center['y'][1]:.6g}], "
            f"z=[{center['z'][0]:.6g},{center['z'][1]:.6g}]"
        )
        print(
            "Generated rendered bounds: "
            f"x=[{rendered['x'][0]:.6g},{rendered['x'][1]:.6g}], "
            f"y=[{rendered['y'][0]:.6g},{rendered['y'][1]:.6g}], "
            f"z=[{rendered['z'][0]:.6g},{rendered['z'][1]:.6g}]"
        )

    def cfg_value(self, cfg, key, default):
        if key in cfg:
            return cfg[key]
        return default

    def configure_cell_dimensions(self, run_cfg):
        (
            self.cell_array_width,
            self.cell_array_height,
            self.cell_array_depth,
        ) = get_cell_dimensions(run_cfg)
        print(
            "BoundaryCDNozzleReservoir cell array: "
            f"{self.cell_array_width} x {self.cell_array_height} x "
            f"{self.cell_array_depth}"
        )

        #******************************************************************
    # Write the tst files taht are read by particle.exe for tests
    # 
    #
    def write_test_file(self,run_cfg=None):

        try:
            f = open(self.test_file_name,'w')
        except BaseException as e:
            raise RuntimeError(
                f"Can't open test file {self.test_file_name}: {e}"
            ) from e
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
        fstr = f"radius = {run_cfg.radius};\n"
        f.write(fstr)
        fstr = f"particles_per_cell = {run_cfg.particles_per_cell};\n"
        f.write(fstr)
        fstr = f"num_particles = {self.number_particles};\n"
        f.write(fstr)
        fstr = f"num_particle_colliding =  {run_cfg.num_particle_colliding};\n"
        f.write(fstr)
        fstr = f"exp_collisions_per_cell = {run_cfg.exp_collisions_per_cell};\n"
        f.write(fstr)
        fstr = f"act_collisions_per_cell = {run_cfg.act_collisions_per_cell};\n"
        f.write(fstr)
        fstr = f"particles_in_row =  {run_cfg.particles_in_row};\n"
        f.write(fstr)
        fstr = f"particle_data_bin_file = \"{self.test_bin_name}\";\n"
        f.write(fstr)
        fstr = f"report_file = \"{self.report_file}\";\n"
        f.write(fstr)
        fstr = f"collsion_density = {run_cfg.collision_density};\n"
        f.write(fstr)
        fstr = f"pdensity = {run_cfg.pdensity};\n"
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
        fstr = f"boundary_x_min = {self.wallxmin:0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_x_max = {self.wallxmax:0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_y_min = {self.wallymin:0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_y_max = {self.wallymax:0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_z_min = {float(self.wallzmin):0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_z_max = {float(self.wallzmax):0.6f};\n"
        f.write(fstr)
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
        fstr = f'boundary_particle_function = "{run_cfg.boundary_particle_function}";\n'
        f.write(fstr)
        fstr = f"nozzle_start_x = {float(self.nozzle_start_x):0.6f};\n"
        f.write(fstr)
        fstr = f"nozzle_center_y = {float(self.nozzle_center_y):0.6f};\n"
        f.write(fstr)
        fstr = f"nozzle_inlet_length = {run_cfg.nozzle_inlet_length:0.6f};\n"
        f.write(fstr)
        fstr = f"nozzle_converge_length = {run_cfg.nozzle_converge_length:0.6f};\n"
        f.write(fstr)
        fstr = f"nozzle_throat_length= {run_cfg.nozzle_throat_length:0.6f};\n"
        f.write(fstr)
        fstr = f"nozzle_diverge_length= {run_cfg.nozzle_diverge_length:0.6f};\n"
        f.write(fstr)
        fstr = f"nozzle_exit_length= {run_cfg.nozzle_exit_length:0.6f};\n"
        f.write(fstr)
        fstr = f"nozzle_inlet_radius= {run_cfg.nozzle_inlet_radius:0.6f};\n"
        f.write(fstr)
        fstr = f"nozzle_throat_radius= {run_cfg.nozzle_throat_radius:0.6f};\n"
        f.write(fstr)
        fstr = f"nozzle_exit_radius= {run_cfg.nozzle_exit_radius:0.6f};\n"
        f.write(fstr)
        boundary_function = str(run_cfg.boundary_particle_function).lower()
        periodic_direction = (
            "vertical" if boundary_function == "vertical_wall" else "horizontal"
        )
        fstr = f'periodic_direction = "{periodic_direction}";\n'
        f.write(fstr)
        if periodic_direction == "vertical":
            fstr = (
                f"reservoir_inlet_y = "
                f"{float(run_cfg.reservoir_inlet_y):0.6f};\n"
            )
            f.write(fstr)
        else:
            fstr = (
                f"reservoir_inlet_x = "
                f"{float(run_cfg.reservoir_inlet_x):0.6f};\n"
            )
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
        try:
            self.gen_nozzle_boundary_only()
        except Exception as error:
            print("BoundaryCDNozzleReservoir generation failed:")
            print(f"  {type(error).__name__}: {error}")
            return False
        return True

    def cd_nozzle_radius(self, axial_position):
        x = float(axial_position)
        inlet_end = self.nozzle_inlet_length
        converge_end = inlet_end + self.nozzle_converge_length
        throat_end = converge_end + self.nozzle_throat_length
        diverge_end = throat_end + self.nozzle_diverge_length

        if 1.0 <= x < inlet_end:
            return self.nozzle_inlet_radius
        if inlet_end <= x < converge_end:
            span = max(self.nozzle_converge_length, 1.0e-12)
            throat_distance = converge_end - x
            t = throat_distance / span
            return (
                self.nozzle_throat_radius
                + (self.nozzle_inlet_radius - self.nozzle_throat_radius)
                * t
                * t
            )
        if converge_end <= x < throat_end:
            return self.nozzle_throat_radius
        if throat_end <= x < diverge_end:
            span = max(self.nozzle_diverge_length, 1.0e-12)
            t = (x - throat_end) / span
            return (
                self.nozzle_throat_radius
                + (self.nozzle_exit_radius - self.nozzle_throat_radius)
                * t
                * t
            )
        if x >= diverge_end:
            return self.nozzle_exit_radius
        return 0.0

    def configure_cd_nozzle_geometry(self, run_cfg):
        self.dim = int(self.cfg_value(run_cfg, "dim", 2))
        self.nozzle_inlet_length = float(
            self.cfg_value(run_cfg, "nozzle_inlet_length", 5.0)
        )
        self.nozzle_converge_length = float(
            self.cfg_value(run_cfg, "nozzle_converge_length", 20.0)
        )
        self.nozzle_throat_length = float(
            self.cfg_value(run_cfg, "nozzle_throat_length", 5.0)
        )
        self.nozzle_diverge_length = float(
            self.cfg_value(run_cfg, "nozzle_diverge_length", 20.0)
        )
        self.nozzle_exit_length = float(
            self.cfg_value(run_cfg, "nozzle_exit_length", 14.0)
        )
        self.nozzle_inlet_radius = float(
            self.cfg_value(run_cfg, "nozzle_inlet_radius", 10.0)
        )
        self.nozzle_throat_radius = float(
            self.cfg_value(run_cfg, "nozzle_throat_radius", 8.1)
        )
        self.nozzle_exit_radius = float(
            self.cfg_value(run_cfg, "nozzle_exit_radius", 10.0)
        )
        self.nozzle_center_x = float(
            self.cfg_value(run_cfg, "nozzle_center_x", 0.5 * self.cell_array_width)
        )
        self.nozzle_center_y = float(
            self.cfg_value(run_cfg, "nozzle_center_y", 0.5 * self.cell_array_height)
        )
        self.nozzle_center_z = float(
            self.cfg_value(run_cfg, "nozzle_center_z", 0.5 * self.cell_array_depth)
        )
        self.boundary_particle_function = str(
            self.cfg_value(run_cfg, "boundary_particle_function", "horizontal_wall")
        ).lower()
        self.nozzle_start_x = float(self.cfg_value(run_cfg, "nozzle_start_x", 1.0))
        self.nozzle_start_y = float(self.cfg_value(run_cfg, "nozzle_start_y", 1.0))
        default_profile_z = 2.0 if self.dim == 2 else self.nozzle_center_z
        self.nozzle_profile_z = float(
            self.cfg_value(run_cfg, "nozzle_profile_z", default_profile_z)
        )
        self.nozzle_theta_step = float(
            self.cfg_value(run_cfg, "nozzle_theta_step", math.pi / 100.0)
        )
        self.nozzle_total_length = int(math.ceil(
            self.nozzle_inlet_length
            + self.nozzle_converge_length
            + self.nozzle_throat_length
            + self.nozzle_diverge_length
            + self.nozzle_exit_length
        ))
        max_radius = max(
            self.cd_nozzle_radius(axial)
            for axial in range(1, self.nozzle_total_length + 1)
        )
        if self.boundary_particle_function == "vertical_wall":
            self.wallxmin = max(0.5, self.nozzle_center_x - max_radius)
            self.wallxmax = min(self.cell_array_width - 1.0, self.nozzle_center_x + max_radius)
            self.wallymin = max(0.5, self.nozzle_start_y)
            self.wallymax = min(
                self.cell_array_height - 1.0,
                self.nozzle_start_y + self.nozzle_total_length - 1.0,
            )
        else:
            self.wallxmin = max(0.5, self.nozzle_start_x)
            self.wallxmax = min(
                self.cell_array_width - 1.0,
                self.nozzle_start_x + self.nozzle_total_length - 1.0,
            )
            self.wallymin = max(0.5, self.nozzle_center_y - max_radius)
            self.wallymax = min(self.cell_array_height - 1.0, self.nozzle_center_y + max_radius)
        self.wallzmin = 0.5
        if self.dim == 3:
            self.wallzmax = min(self.cell_array_depth - 1.0, float(self.nozzle_total_length))
        else:
            self.wallzmin = self.nozzle_profile_z
            self.wallzmax = self.nozzle_profile_z

    # ------------------------------------------------------------------
    # Simulation configuration checks
    # ------------------------------------------------------------------
    def validate_simulation_configuration(self, run_cfg):
        """Validate manual cfg inputs against calculated nozzle geometry."""
        errors = []
        warnings = []
        section_lengths = (
            self.nozzle_inlet_length,
            self.nozzle_converge_length,
            self.nozzle_throat_length,
            self.nozzle_diverge_length,
            self.nozzle_exit_length,
        )
        exact_total_length = sum(section_lengths)
        configured_wall_length = float(
            self.cfg_value(run_cfg, "wall_boundary_length", exact_total_length)
        )
        radius = float(self.cfg_value(run_cfg, "radius", 0.1))
        dt = float(self.cfg_value(run_cfg, "dt", 0.0))
        spacing = self.cd_mobile_spacing(run_cfg)
        packed_cell_length = (
            int(self.itemcfg.particles_per_cell_row) * spacing
        )

        if self.dim not in (2, 3):
            errors.append("dim must be 2 or 3")
        if any(length <= 0.0 for length in section_lengths):
            errors.append("all five nozzle section lengths must be positive")
        if any(
            value <= 0.0
            for value in (
                self.nozzle_inlet_radius,
                self.nozzle_throat_radius,
                self.nozzle_exit_radius,
            )
        ):
            errors.append("all nozzle radii must be positive")
        if self.nozzle_throat_radius > min(
            self.nozzle_inlet_radius, self.nozzle_exit_radius
        ):
            errors.append(
                "nozzle_throat_radius must not exceed the inlet or exit radius"
            )
        if abs(configured_wall_length - exact_total_length) > 1.0e-9:
            errors.append(
                f"wall_boundary_length={configured_wall_length:g} must equal "
                "the sum of the nozzle section lengths "
                f"({exact_total_length:g})"
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

        if self.boundary_particle_function == "vertical_wall":
            inlet_key = "reservoir_inlet_y"
            nozzle_start = self.nozzle_start_y
        else:
            inlet_key = "reservoir_inlet_x"
            nozzle_start = self.nozzle_start_x

        if inlet_key not in run_cfg:
            errors.append(f"{inlet_key} is required")
            inlet = nozzle_start
        else:
            inlet = float(run_cfg[inlet_key])
        if abs(inlet - nozzle_start) > 1.0e-9:
            errors.append(
                f"{inlet_key}={inlet:g} must match the nozzle entrance at "
                f"{nozzle_start:g}"
            )
        for name, lower, upper, dimension in (
            ("x", self.wallxmin, self.wallxmax, self.cell_array_width),
            ("y", self.wallymin, self.wallymax, self.cell_array_height),
            ("z", self.wallzmin, self.wallzmax, self.cell_array_depth),
        ):
            if lower < 0.0 or upper >= dimension:
                errors.append(
                    f"calculated {name} wall bounds [{lower:g},{upper:g}] "
                    f"must remain inside {name} cell count={dimension}"
                )

        for key, wall_minimum, wall_maximum in (
            ("x_axis_lims", self.wallxmin, self.wallxmax),
            ("y_axis_lims", self.wallymin, self.wallymax),
        ):
            limits = run_cfg.get(key)
            if limits is None or len(limits) < 2:
                errors.append(f"{key} must contain [minimum, maximum]")
            elif float(limits[0]) >= float(limits[1]):
                errors.append(f"{key} minimum must be less than maximum")
            elif wall_minimum < float(limits[0]) or wall_maximum > float(limits[1]):
                warnings.append(f"{key} does not contain the complete nozzle")

        print("Simulation configuration check: BoundaryCDNozzleReservoir")
        print(
            "  manual: cell_array="
            f"{self.cell_array_width}x{self.cell_array_height}x"
            f"{self.cell_array_depth}, wall_boundary_length="
            f"{configured_wall_length:g}, radius={radius:g}, dt={dt:g}"
        )
        print(
            f"  calculated nozzle: length={exact_total_length:g}, "
            f"x=[{self.wallxmin:g},{self.wallxmax:g}], "
            f"y=[{self.wallymin:g},{self.wallymax:g}]"
        )
        print(
            f"  inlet={inlet:g}; packed cell length={packed_cell_length:g}"
        )
        for warning in warnings:
            print(f"  WARNING: {warning}")
        if errors:
            raise ValueError(
                "BoundaryCDNozzleReservoir configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )
        print("  PASS")

    def gen_nozzle_boundary_only(self):
        self.p_list = []
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0
        self.add_null_particle(self.p_list)
        self.index = 0
        run_cfg = get_run_configuration(self.itemcfg)
        self.configure_cell_dimensions(run_cfg)
        self.configure_cd_nozzle_geometry(run_cfg)
        self.validate_simulation_configuration(run_cfg)
        self.MobileParticlesCDNozzle(run_cfg)
        self.BoundaryParticlesCDNozzle(run_cfg)
        self.write_cd_nozzle_obj(run_cfg)
        self.writeCFGData(run_cfg)

    def cd_mobile_spacing(self, run_cfg):
        radius = float(self.cfg_value(run_cfg, "radius", 0.1))
        fraction = float(
            self.cfg_value(
                self.itemcfg,
                "fraction_of_diameter_separation",
                0.0,
            )
        )
        return 2.0 * radius * (1.0 + fraction)

    def cd_particles_per_wave(self, inlet_min, inlet_max, particle_spacing):
        max_particles = int(
            math.floor(((inlet_max - inlet_min) / particle_spacing) + 1.0e-9)
        ) + 1
        configured_particles = int(self.itemcfg.particles_per_row)
        particles_per_wave = min(configured_particles, max_particles)
        if particles_per_wave <= 0:
            raise ValueError("CD nozzle inlet is too small for mobile particle radius")

        occupied_span = (particles_per_wave - 1) * particle_spacing
        available_span = inlet_max - inlet_min
        start = inlet_min + 0.5 * (available_span - occupied_span)
        return particles_per_wave, start, max_particles

    def MobileParticlesCDNozzle(self, run_cfg):
        if self.dim != 2:
            print("BoundaryCDNozzleReservoir: mobile particles are only generated for dim=2")
            return

        radius = float(self.cfg_value(run_cfg, "radius", 0.1))
        particle_spacing = self.cd_mobile_spacing(run_cfg)
        particle_cell_row_length = self.itemcfg.particles_per_cell_row * particle_spacing
        if particle_cell_row_length > 1.0 + 1.0e-9:
            raise ValueError(
                "particles_per_cell_row does not fit in one cell for the "
                f"configured radius and spacing: {particle_cell_row_length:.4f}"
            )
        forward_speed = float(
            self.cfg_value(
                run_cfg,
                "reservoir_flow_speed",
                self.cfg_value(run_cfg, "reservoir_starting_vx", 0.02),
            )
        )
        collision_stiffness_q = float(
            self.cfg_value(run_cfg, "collision_stiffness_q", 0.0)
        )

        z = float(self.cfg_value(run_cfg, "nozzle_profile_z", self.nozzle_profile_z))
        if self.boundary_particle_function == "vertical_wall":
            inlet_x = self.nozzle_center_x
            inlet_y = float(
                self.cfg_value(run_cfg, "reservoir_inlet_y", self.nozzle_start_y)
            )
            x_min = self.nozzle_center_x - self.nozzle_inlet_radius + radius
            x_max = self.nozzle_center_x + self.nozzle_inlet_radius - radius
            particles_per_wave, x_start, max_particles_per_wave = (
                self.cd_particles_per_wave(x_min, x_max, particle_spacing)
            )
        else:
            inlet_x = float(
                self.cfg_value(run_cfg, "reservoir_inlet_x", self.nozzle_start_x)
            )
            inlet_y = self.nozzle_center_y
            y_min = self.nozzle_center_y - self.nozzle_inlet_radius + radius
            y_max = self.nozzle_center_y + self.nozzle_inlet_radius - radius
            particles_per_wave, y_start, max_particles_per_wave = (
                self.cd_particles_per_wave(y_min, y_max, particle_spacing)
            )

        for col in range(self.itemcfg.particle_columns):
            for row in range(particles_per_wave):
                if self.boundary_particle_function == "vertical_wall":
                    x = x_start + row * particle_spacing
                    y = inlet_y
                    vx = 0.0
                    vy = forward_speed
                else:
                    x = inlet_x
                    y = y_start + row * particle_spacing
                    vx = forward_speed
                    vy = 0.0
                self.addMobileParticle(
                    run_cfg,
                    rx=x,
                    ry=y,
                    rz=z,
                    vx=vx,
                    vy=vy,
                    vz=0.0,
                    radius=radius,
                    collision_stiffness_q=collision_stiffness_q,
                )

        print(
            f"BoundaryCDNozzleReservoir: generated {self.number_active_particles} "
            f"mobile particles, {particles_per_wave} per column "
            f"(max fit {max_particles_per_wave})"
        )

    def BoundaryParticlesCDNozzle(self, run_cfg):
        if self.dim == 3:
            self.BoundaryParticlesCDNozzle3D(run_cfg)
        else:
            self.BoundaryParticlesCDNozzle2D(run_cfg)

    def BoundaryParticlesCDNozzle2D(self, run_cfg):
        marker_locations = set()

        def add_marker(x, y, z, evaluator_id):
            key = (float(x), float(y), float(z))
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

        def marker_axis_positions(axis_min, axis_max):
            lower = float(axis_min)
            upper = float(axis_max)
            span = upper - lower
            whole_steps = int(math.floor(span))
            positions = [lower + float(step) for step in range(whole_steps + 1)]
            if upper - positions[-1] > 1.0e-12:
                positions.append(upper)
            else:
                positions[-1] = upper
            return positions

        z = float(round(self.nozzle_profile_z))
        if self.boundary_particle_function == "vertical_wall":
            inlet_min = self.nozzle_center_x - self.nozzle_inlet_radius
            inlet_max = self.nozzle_center_x + self.nozzle_inlet_radius
            for x in marker_axis_positions(inlet_min, inlet_max):
                add_marker(
                    x,
                    self.nozzle_start_y,
                    z,
                    BOUNDARY_EVALUATOR_HORIZONTAL,
                )
        else:
            inlet_min = self.nozzle_center_y - self.nozzle_inlet_radius
            inlet_max = self.nozzle_center_y + self.nozzle_inlet_radius
            for y in marker_axis_positions(inlet_min, inlet_max):
                add_marker(
                    self.nozzle_start_x,
                    y,
                    z,
                    BOUNDARY_EVALUATOR_VERTICAL,
                )

        for axial in range(1, self.nozzle_total_length + 1):
            radius = self.cd_nozzle_radius(axial)
            axial_offset = float(axial - 1)
            if self.boundary_particle_function == "vertical_wall":
                y = round(self.nozzle_start_y + axial_offset)
                locations = (
                    (round(self.nozzle_center_x + radius), y, z),
                    (round(self.nozzle_center_x - radius), y, z),
                )
            else:
                x = round(self.nozzle_start_x + axial_offset)
                locations = (
                    (x, round(self.nozzle_center_y + radius), z),
                    (x, round(self.nozzle_center_y - radius), z),
                )
            for x, y, z in locations:
                add_marker(
                    x,
                    y,
                    z,
                    BOUNDARY_EVALUATOR_CD_NOZZLE,
                )
        print(
            f"BoundaryCDNozzleReservoir: generated {self.number_boundary_particles} "
            "2D boundary particles, cell array "
            f"{self.cell_array_width}x{self.cell_array_height}x"
            f"{self.cell_array_depth}, axial length "
            f"{self.nozzle_total_length}"
        )

    def BoundaryParticlesCDNozzle3D(self, run_cfg):
        marker_locations = set()
        for axial in range(1, self.nozzle_total_length + 1):
            radius = self.cd_nozzle_radius(axial)
            theta = 0.0
            while theta < 2.0 * math.pi:
                x = round(radius * math.cos(theta) + self.nozzle_center_x)
                y = round(radius * math.sin(theta) + self.nozzle_center_y)
                z = round(float(axial))
                key = (x, y, z)
                if key not in marker_locations:
                    marker_locations.add(key)
                    self.addBoundaryParticle(
                        run_cfg,
                        float(x),
                        float(y),
                        float(z),
                        evaluator_id=BOUNDARY_EVALUATOR_CD_NOZZLE,
                    )
                theta += self.nozzle_theta_step
        print(
            f"BoundaryCDNozzleReservoir: generated {self.number_boundary_particles} "
            "3D boundary particles, cell array "
            f"{self.cell_array_width}x{self.cell_array_height}x"
            f"{self.cell_array_depth}, axial length "
            f"{self.nozzle_total_length}"
        )

    def write_cd_nozzle_obj(self, run_cfg):
        if self.dim != 2:
            print("BoundaryCDNozzleReservoir: OBJ generation is only implemented for dim=2")
            return

        obj_file = str(
            self.cfg_value(
                run_cfg,
                "cd_nozzle_obj_file",
                "C:/_DJ/gPCD/vulkan/sim/BoundaryCDNozzleReservoir/CDNozzleGenerated.obj",
            )
        )
        wall_thickness = float(
            self.cfg_value(run_cfg, "cd_nozzle_obj_wall_thickness", 0.25)
        )
        os.makedirs(os.path.dirname(obj_file), exist_ok=True)

        vertices = []
        faces = []

        def add_vertex(x, y, z):
            vertices.append((float(x), float(y), float(z)))
            return len(vertices)

        def add_double_sided_quad(a, b, c, d):
            faces.append((a, b, c, 1))
            faces.append((a, c, d, 1))
            faces.append((c, b, a, 2))
            faces.append((d, c, a, 2))

        upper_inner = []
        upper_outer = []
        lower_inner = []
        lower_outer = []
        z = self.nozzle_profile_z

        for axial in range(1, self.nozzle_total_length + 1):
            radius = self.cd_nozzle_radius(axial)
            axial_offset = float(axial - 1)
            if self.boundary_particle_function == "vertical_wall":
                y = self.nozzle_start_y + axial_offset
                upper_inner.append(add_vertex(self.nozzle_center_x + radius, y, z))
                upper_outer.append(
                    add_vertex(self.nozzle_center_x + radius + wall_thickness, y, z)
                )
                lower_inner.append(add_vertex(self.nozzle_center_x - radius, y, z))
                lower_outer.append(
                    add_vertex(self.nozzle_center_x - radius - wall_thickness, y, z)
                )
            else:
                x = self.nozzle_start_x + axial_offset
                upper_inner.append(add_vertex(x, self.nozzle_center_y + radius, z))
                upper_outer.append(
                    add_vertex(x, self.nozzle_center_y + radius + wall_thickness, z)
                )
                lower_inner.append(add_vertex(x, self.nozzle_center_y - radius, z))
                lower_outer.append(
                    add_vertex(x, self.nozzle_center_y - radius - wall_thickness, z)
                )

        for ii in range(self.nozzle_total_length - 1):
            add_double_sided_quad(
                upper_inner[ii],
                upper_inner[ii + 1],
                upper_outer[ii + 1],
                upper_outer[ii],
            )
            add_double_sided_quad(
                lower_outer[ii],
                lower_outer[ii + 1],
                lower_inner[ii + 1],
                lower_inner[ii],
            )

        with open(obj_file, "w", encoding="ascii") as obj:
            obj.write("# Generated by BoundaryCDNozzleReservoir.py\n")
            obj.write("# Visual nozzle wall mesh; dynamics use boundary particles.\n")
            obj.write("o CDNozzleGenerated\n")
            for x, y, z in vertices:
                obj.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
            for _ in vertices:
                obj.write("vt 0.000000 0.000000\n")
            obj.write("vn 0.000000 0.000000 1.000000\n")
            obj.write("vn 0.000000 0.000000 -1.000000\n")
            for a, b, c, normal_index in faces:
                obj.write(
                    f"f {a}/{a}/{normal_index} "
                    f"{b}/{b}/{normal_index} "
                    f"{c}/{c}/{normal_index}\n"
                )

        print(
            f"BoundaryCDNozzleReservoir: wrote triangle OBJ with "
            f"{len(vertices)} vertices and {len(faces)} faces to {obj_file}"
        )

    def addMobileParticle(
        self,
        run_cfg,
        rx,
        ry,
        rz,
        vx,
        vy,
        vz,
        radius,
        collision_stiffness_q,
    ):
        try:
            particle_struct = pdata()
            self.number_active_particles += 1
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
            particle_struct.state_flg = 0.0
            particle_struct.collision_stiffness_q = collision_stiffness_q
            self.p_list.append(particle_struct)
        except BaseException as e:
            print(f"Failed adding mobile particle:{e} ")
            return

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
            particle_struct.ptype = float(evaluator_id)
            particle_struct.molar_mass = 1.0
            particle_struct.radius = 0.25
            particle_struct.state_flg = 0.0
            particle_struct.collision_stiffness_q = 0.0
            self.p_list.append(particle_struct)
        except BaseException as e:
            print(f"Failed adding Particle:{e} ")   
            return

    
    def writeCFGData(self,run_cfg):
        cfg_data_name = self.itemcfg["output_file_prefix"]
        self.test_file_name = f"{self.itemcfg.data_dir}/{cfg_data_name}.tst"
        self.test_bin_name = f"{self.itemcfg.data_dir}/{cfg_data_name}.bin"
        self.report_file = f"{self.itemcfg.data_dir}/{cfg_data_name}.rpt"
        self.write_test_file(run_cfg)
        self.create_bin_file()
        self.write_bin_file(self.p_list)
        self.close_bin_file()
        self.report_generated_bounds()
        print(
            f"BoundaryCDNozzleReservoir: Wrote {self.number_particles} "
            f"particles to {self.test_bin_name}"
        )
