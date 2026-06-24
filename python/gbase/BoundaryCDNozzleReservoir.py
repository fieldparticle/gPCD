import random

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
        cfg_data_name = self.itemcfg["STUDY_NAME"]
        suffix = f"{self.itemcfg.particle_columns}x{self.itemcfg.particles_per_row}x{self.itemcfg.particles_per_cell_row}"
        self.test_file_name = f"{self.itemcfg.data_dir}/{cfg_data_name}{suffix}.tst"
        try:
            os.remove(self.test_file_name)
        except BaseException as e:
            print(f"Delete bin file:{e}")
        self.test_bin_name = f"{self.itemcfg.data_dir}/{cfg_data_name}{suffix}.bin"
        try:
            os.remove(self.test_bin_name)
        except BaseException as e:
            print(f"Delete tst file:{e}")
        self.report_file = f"{self.itemcfg.data_dir}/{cfg_data_name}{suffix}.rpt"
        

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
        fstr = f"wallZMIN = {getattr(self, 'wallzmin', self.wallymin)};\n"
        f.write(fstr)
        fstr = f"wallZMAX = {getattr(self, 'wallzmax', self.wallymax)};\n"
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

    def runner(self):
        self.gen_nozzle_boundary_only()

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
            t = (x - inlet_end) / span
            return (
                self.nozzle_inlet_radius
                + t * (self.nozzle_throat_radius - self.nozzle_inlet_radius)
            )
        if converge_end <= x < throat_end:
            return self.nozzle_throat_radius
        if throat_end <= x < diverge_end:
            span = max(self.nozzle_diverge_length, 1.0e-12)
            t = (x - throat_end) / span
            return (
                self.nozzle_throat_radius
                + t * (self.nozzle_exit_radius - self.nozzle_throat_radius)
            )
        if x >= diverge_end:
            return self.nozzle_exit_radius
        return 0.0

    def configure_cd_nozzle_geometry(self, run_cfg):
        self.dim = int(self.cfg_value(run_cfg, "dim", 2))
        self.side_len = float(
            self.cfg_value(
                run_cfg,
                "over_ride_side_length",
                self.cfg_value(self.itemcfg, "over_ride_side_length", 64.0),
            )
        )
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
            self.cfg_value(run_cfg, "nozzle_center_x", 0.5 * self.side_len)
        )
        self.nozzle_center_y = float(
            self.cfg_value(run_cfg, "nozzle_center_y", 0.5 * self.side_len)
        )
        self.nozzle_center_z = float(
            self.cfg_value(run_cfg, "nozzle_center_z", 0.5 * self.side_len)
        )
        self.nozzle_profile_z = float(
            self.cfg_value(run_cfg, "nozzle_profile_z", self.nozzle_center_z)
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
        self.wallxmin = max(0.5, self.nozzle_center_x - max_radius)
        self.wallxmax = min(self.side_len - 1.0, self.nozzle_center_x + max_radius)
        self.wallymin = max(0.5, self.nozzle_center_y - max_radius)
        self.wallymax = min(self.side_len - 1.0, self.nozzle_center_y + max_radius)
        self.wallzmin = 0.5
        if self.dim == 3:
            self.wallzmax = min(self.side_len - 1.0, float(self.nozzle_total_length))
        else:
            self.wallzmin = self.nozzle_profile_z
            self.wallzmax = self.nozzle_profile_z

    def gen_nozzle_boundary_only(self):
        self.p_list = []
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0
        self.add_null_particle(self.p_list)
        self.index = 0
        run_cfg = self.itemcfg["RUN_CONFIGURATION"]
        self.configure_cd_nozzle_geometry(run_cfg)
        self.BoundaryParticlesCDNozzle(run_cfg)
        self.writeCFGData(run_cfg)

    def BoundaryParticlesCDNozzle(self, run_cfg):
        if self.dim == 3:
            self.BoundaryParticlesCDNozzle3D(run_cfg)
        else:
            self.BoundaryParticlesCDNozzle2D(run_cfg)

    def BoundaryParticlesCDNozzle2D(self, run_cfg):
        marker_locations = set()
        for axial in range(1, self.nozzle_total_length + 1):
            radius = self.cd_nozzle_radius(axial)
            x = round(float(axial))
            z = round(self.nozzle_profile_z)
            for y in (
                round(self.nozzle_center_y + radius),
                round(self.nozzle_center_y - radius),
            ):
                key = (x, y, z)
                if key not in marker_locations:
                    marker_locations.add(key)
                    self.addBoundaryParticle(run_cfg, float(x), float(y), float(z))
        print(
            f"BoundaryCDNozzleReservoir: generated {self.number_boundary_particles} "
            f"2D boundary particles, side length {self.side_len}, axial length "
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
                    self.addBoundaryParticle(run_cfg, float(x), float(y), float(z))
                theta += self.nozzle_theta_step
        print(
            f"BoundaryCDNozzleReservoir: generated {self.number_boundary_particles} "
            f"3D boundary particles, side length {self.side_len}, axial length "
            f"{self.nozzle_total_length}"
        )

    def addBoundaryParticle(self,RUN_CONFIGURATION,rx,ry,rz=2.0):
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
            particle_struct.molar_mass = 1.0
            particle_struct.radius = 0.25
            particle_struct.state_flg = 0.0
            particle_struct.collision_stiffness_q = 0.0
            self.p_list.append(particle_struct)
        except BaseException as e:
            print(f"Failed adding Particle:{e} ")   
            return

    
    def writeCFGData(self,RUN_CONFIGURATION):
        
        self.write_test_file(RUN_CONFIGURATION)
        self.create_bin_file()
        self.write_bin_file(self.p_list)
        self.close_bin_file()
        print(f"PipeReservoirEntry: Wrote {self.number_particles} reservoir particles to {self.test_bin_name}")
