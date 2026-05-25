import random

from gbase.utilities import *
from gbase.GenDataBase import *
from gbase.BinaryFileUtilities import *
import math
from gbase.pdata import *
from gbase.libconf import AttrDict
import io
class GenPipeReservoirEntry():

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
        fstr = f"CellAryW = {run_cfg.side_len};\n"     
        f.write(fstr)
        fstr = f"CellAryH = {run_cfg.side_len};\n"     
        f.write(fstr)
        fstr = f"CellAryL = {run_cfg.side_len};\n"     
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
        fstr = f"dispatchx = {self.number_particles+1};\n"
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
        fstr = f"wallXMIN = {run_cfg.WallXMIN};\n"
        f.write(fstr)
        fstr = f"wallXMAX = {run_cfg.WallXMAX};\n"
        f.write(fstr)
        fstr = f"wallYMIN = {run_cfg.WallYMIN};\n"
        f.write(fstr)
        fstr = f"wallYMAX = {run_cfg.WallYMAX};\n"
        f.write(fstr)
        fstr = f"wallZMIN = {run_cfg.WallZMIN};\n"
        f.write(fstr)
        fstr = f"wallZMAX = {run_cfg.WallZMAX};\n"
        f.write(fstr)
        fstr = f"flow_type = \"{self.cfg_value(run_cfg, 'flow_type', 'pipe_reservoir_entry')}\";\n"
        f.write(fstr)
        fstr = f"particle_rate = {self.cfg_value(run_cfg, 'particle_rate', 0.0)};\n"
        f.write(fstr)
        fstr = f"inlet_velocity = {self.cfg_value(run_cfg, 'inlet_velocity', 0.0)};\n"
        f.write(fstr)
        fstr = f"inlet_x = {self.cfg_value(run_cfg, 'inlet_x', run_cfg.WallXMIN)};\n"
        f.write(fstr)
        fstr = f"outlet_x = {self.cfg_value(run_cfg, 'outlet_x', run_cfg.WallXMAX)};\n"
        f.write(fstr)
        fstr = f"pipe_y_min = {self.cfg_value(run_cfg, 'pipe_y_min', run_cfg.WallYMIN)};\n"
        f.write(fstr)
        fstr = f"pipe_y_max = {self.cfg_value(run_cfg, 'pipe_y_max', run_cfg.WallYMAX)};\n"
        f.write(fstr)
        fstr = f"escape_mode = {int(self.cfg_value(run_cfg, 'escape_mode', 1))};\n"
        f.write(fstr)
        f.flush()
        f.close()

    def runner(self):
        config = None
        
        self.p_list = []
        self.number_particles = 0
        self.add_null_particle(self.p_list)
        self.index = 0
        
        
        RUN_CONFIGURATION = self.itemcfg["RUN_CONFIGURATION"]
        reservoir_count = int(self.cfg_value(RUN_CONFIGURATION, "reservoir_particle_count", 32))
        radius = float(self.cfg_value(RUN_CONFIGURATION, "radius", 0.25))
        mass = float(self.cfg_value(RUN_CONFIGURATION, "particle_mass", 1.0))
        local_particles_in_row = self.itemcfg.num_particles_y
        local_particles_in_col = self.itemcfg.num_particles_x
        try:
           for row in range(1,local_particles_in_row+1):
                for col in range(1,local_particles_in_col+1):
                    particle_struct = pdata()
                    self.number_particles += 1
                    particle_struct.pnum = self.number_particles
                    particle_struct.rx = 1.5
                    particle_struct.ry = row+0.5
                    particle_struct.rz = 2.0
                    particle_struct.vx = random.uniform(0.01, 0.02)
                    particle_struct.vy = random.uniform(0.01, 0.02)
                    particle_struct.vz = 0.0
                    particle_struct.molar_mass = 1.0
                    particle_struct.radius = 0.25
                    particle_struct.state_flg = 1.0
                    self.p_list.append(particle_struct)
                    
                
                
                    
        except BaseException as e:
            print(f"Failed adding Particle:{e} ")   
            return
        cfg_data_name = self.itemcfg["STUDY_NAME"]
        self.test_file_name = f"{self.itemcfg.data_dir}/{cfg_data_name}.tst"
        self.test_bin_name = f"{self.itemcfg.data_dir}/{cfg_data_name}.bin"
        self.report_file = f"{self.itemcfg.data_dir}/{cfg_data_name}.rpt"
        self.write_test_file(RUN_CONFIGURATION)
        self.create_bin_file()
        self.write_bin_file(self.p_list)
        self.close_bin_file()
        print(f"PipeReservoirEntry: Wrote {self.number_particles} reservoir particles to {self.test_bin_name}")
