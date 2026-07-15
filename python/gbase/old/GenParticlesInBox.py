import random

from gbase.utilities import *
from gbase.GenDataBase import *
import math
from gbase.pdata import *
from gbase.libconf import AttrDict
from gbase.MaterialProperties import (
    write_color_scheme_defines,
    write_material_properties,
)
import io
from gbase.BinaryFileUtilities import clear_files, read_all_particle_data
class GenParticlesInBox():

    
    
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
        particle_struct.ptype = PTYPE_NULL
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
        width, height, depth = get_cell_dimensions(run_cfg)
        fstr = f"CellAryW = {width};\n"     
        f.write(fstr)
        fstr = f"CellAryH = {height};\n"     
        f.write(fstr)
        fstr = f"CellAryL = {depth};\n"     
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
        if run_cfg.hsv_color == True:
            fstr = f"hsv_color = 1;\n"
        else:
            fstr = f"hsv_color = 0;\n"
        f.write(fstr)
        contact_force_measure = getattr(run_cfg, "contact_force_measure", "area")
        fstr = f"contact_force_measure = \"{contact_force_measure}\";\n"
        f.write(fstr)
        fstr = f"hsv_sat = {run_cfg.hsv_sat:0.4f};\n"
        f.write(fstr)
        fstr = f"hsv_val = {run_cfg.hsv_val:0.4f};\n"
        f.write(fstr)
        write_color_scheme_defines(f)
        write_material_properties(f, run_cfg)
        f.flush()
        f.close()
        
    def clear_files(self):
        cfg_data_name = self.itemcfg["STUDY_NAME"]
        clear_files(self.itemcfg,cfg_data_name)

    def runner(self):
        config = None
        
        self.p_list = []
        self.number_particles = 0
        self.add_null_particle(self.p_list)
        self.index = 0
        run_cfg = get_run_configuration(self.itemcfg)
        count = 0
        local_particles_in_row = self.itemcfg.num_particles_y
        local_particles_in_col = self.itemcfg.num_particles_x

        try:
            for row in range(1,local_particles_in_row+1):
                for col in range(1,local_particles_in_col+1):
                    particle_struct = pdata()
                    self.number_particles += 1
                    particle_struct.pnum = self.number_particles
                    particle_struct.rx = row+0.5
                    particle_struct.ry = col+0.5
                    particle_struct.rz = 2.0
                    particle_struct.vx = random.uniform(0.01, 0.02)
                    particle_struct.vy = random.uniform(0.01, 0.02)
                    particle_struct.vz = 0.0
                    particle_struct.molar_mass = 1.0
                    particle_struct.material_id = 0.0
                    particle_struct.radius = 0.25
                    particle_struct.state_flg = 1.0
                    particle_struct.collision_stiffness_q = 10
                    self.p_list.append(particle_struct)
                    
        except BaseException as e:
            print(f"Failed adding Particle:{e} ")   
            return
        cfg_data_name = self.itemcfg["STUDY_NAME"]
        self.test_file_name = f"{self.itemcfg.data_dir}/{cfg_data_name}.tst"
        self.test_bin_name = f"{self.itemcfg.data_dir}/{cfg_data_name}.bin"
        self.report_file = f"{self.itemcfg.data_dir}/{cfg_data_name}.rpt"
        self.write_test_file(run_cfg)
        self.create_bin_file()
        self.write_bin_file(self.p_list)
        self.close_bin_file()
        print(f"TwoParticleHorizontal: Wrote {self.number_particles} particles to {self.test_bin_name}")
