import random

from gbase.utilities import *
from gbase.GenDataBase import *
from gbase.BinaryFileUtilities import *
import math
from gbase.pdata import *
from gbase.libconf import AttrDict
import io
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
        cfg_data_name = self.itemcfg["STUDY_NAME"]
        clear_files(self.itemcfg,cfg_data_name)

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
        # THIS is the only place you so this - The vulkan code nees to check this
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
        fstr = f"wallZMIN = {self.wallymin};\n"
        f.write(fstr)
        fstr = f"wallZMAX = {self.wallymax};\n"
        f.write(fstr)
        fstr = f"DT = {run_cfg.dt};\n"
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
        config = None
        
        self.p_list = []
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0
        self.add_null_particle(self.p_list)
        self.index = 0
        
        
        RUN_CONFIGURATION = self.itemcfg["RUN_CONFIGURATION"]
        
        radius = float(self.cfg_value(RUN_CONFIGURATION, "radius", 0.25))
        dt = float(self.cfg_value(RUN_CONFIGURATION, "dt", 1.0))
        collision_stiffness_q = float(self.cfg_value(RUN_CONFIGURATION, "collision_stiffness_q", 0.0))
        WallYMAX = float(self.cfg_value(RUN_CONFIGURATION, "WallYMAX", 10.0))
        WallYMIN = float(self.cfg_value(RUN_CONFIGURATION, "WallYMIN", 10.0))

        # Paticle length is twice the radius times the fraction of diameter separation.
        particle_length =2.0*radius+2.0*radius*self.itemcfg.fraction_of_diameter_separation
        # The particle row length is the number of particles per cell row times the particle length. 
        particle_cell_row_length = self.itemcfg.particles_per_cell_row*particle_length
        # if the length of the particles in a cell row is larger than one then there is overlap.
        if particle_cell_row_length > 1.0:
            print(f"Error: Particles per cell row is {particle_cell_row_length:.2f} which is greater than 1.0. ")
            return
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
        self.side_len = math.ceil(self.itemcfg.particles_per_row/self.itemcfg.particles_per_cell_row)+2.0
        print(f"Side length is {self.side_len} for particles per row of {particles_per_row} and particles per cell row of {self.itemcfg.particles_per_cell_row}")
        self.wallymax = self.side_len-1.0
        self.wallxmax = self.side_len-1.0
        self.wallxmin = 0.5
        self.wallymin = 0.5
       
        

        total_cell_row_length = self.itemcfg.particles_per_cell_row*particle_length
        empty_space = 1.0 - total_cell_row_length 
        empty_particle_count = math.floor(empty_space/particle_length)
        print(f"total_cell_row_length is {total_cell_row_length:.2f} empty space is {empty_space:.2f} which can fit {empty_particle_count:.2f} more particles in the row if we wanted to add more.")        


        tot_particles = self.itemcfg.particle_columns*self.itemcfg.particles_per_row
        total_colums = self.itemcfg.particle_columns
        particles_per_row = self.itemcfg.particles_per_row
        
        starting_vx = 0.02
        starting_vy = 0.0
        start_birth = 10.0
        halfway = math.ceil((particles_per_row-1)/2)
        try:
            for col in range(1,total_colums+1):    
                k = self.frames_between_waves(radius,starting_vx,dt,spacing_factor=1.05)
                birth_frame =  start_birth + k * (col-1.0)
                
                for row in range(1,particles_per_row+1):     
                    particle_struct = pdata()
                    self.number_active_particles +=1
                    self.number_particles += 1
                    particle_struct.pnum = self.number_particles
                    particle_struct.rx = 0.5
                    particle_struct.ry = 1.0+row*particle_length
                    particle_struct.rz = 2.0
                    particle_struct.vx = starting_vx
                    if row >= halfway:
                        particle_struct.vy = 0.05
                    else:
                        particle_struct.vy = -0.05
                    particle_struct.vz = 0.0
                    particle_struct.ptype = 0.0
                    particle_struct.molar_mass = 1.0
                    particle_struct.radius = radius
                    particle_struct.state_flg = birth_frame
                    particle_struct.collision_stiffness_q = collision_stiffness_q
                    self.p_list.append(particle_struct)
        except BaseException as e:
            print(f"Failed adding Particle:{e} ")   
            return
        self.BoundaryParticles(RUN_CONFIGURATION)
        self.writeCFGData(RUN_CONFIGURATION)

    def BoundaryParticles(self,RUN_CONFIGURATION):
        for wx in range(int(self.wallxmax)):
            self.addBoundaryParticle(RUN_CONFIGURATION,float(wx+1.0),self.wallymax-0.75)

        for wx in range(int(self.wallxmax)):
            self.addBoundaryParticle(RUN_CONFIGURATION,float(wx+1.0),self.wallymin+0.5)
        

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
        cfg_data_name = self.itemcfg["STUDY_NAME"]
        suffix = f"{self.itemcfg.particle_columns}x{self.itemcfg.particles_per_row}x{self.itemcfg.particles_per_cell_row}"
        self.test_file_name = f"{self.itemcfg.data_dir}/{cfg_data_name}{suffix}.tst"
        self.test_bin_name = f"{self.itemcfg.data_dir}/{cfg_data_name}{suffix}.bin"
        self.report_file = f"{self.itemcfg.data_dir}/{cfg_data_name}{suffix}.rpt"
        self.write_test_file(RUN_CONFIGURATION)
        self.create_bin_file()
        self.write_bin_file(self.p_list)
        self.close_bin_file()
        print(f"PipeReservoirEntry: Wrote {self.number_particles} reservoir particles to {self.test_bin_name}")
