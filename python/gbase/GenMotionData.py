from gbase.BinaryFileUtilities import clear_files
from gbase.utilities import *
from gbase.GenDataBase import *
import math
from gbase.pdata import *
from gbase.libconf import AttrDict
import io
class GenMotionData():

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

    def clear_files(self):
        cfg_data_name = self.itemcfg["STUDY_NAME"]
        clear_files(self.itemcfg,cfg_data_name)

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
        fstr = f"dispatchx = {run_cfg.dispatchx};\n"
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
        f.flush()
        f.close()

    def runner(self):
        config = None
        '''
        cfg_study_name = self.itemcfg.simulation_file
        cfg_study_dir = self.itemcfg.simulation_dir
        cfg_file = f"{cfg_study_dir}/{cfg_study_name}"

        
        try:
            with io.open(cfg_file) as f:
                #self.log.log(self,"gPCD into Open config file.")
                config = libconf.load(f)
        except IOError as e:
            print("gPCD failed to open config file: " + cfg_file)
            return
        except libconf.ConfigParseError as e:
            print("gPCD failed to parse config file: " + cfg_file)
            print(e)
            return
        '''
        self.p_list = []
        self.add_null_particle(self.p_list)
        self.index = 0
        try:
            RUN_CONFIGURATION = self.itemcfg["RUN_CONFIGURATION"]
            PARTICLE_DATA = AttrDict()
            PP = self.itemcfg["PARTICLE_DATA"]
        
            for pp in range(len(PP)):
                src_str = f"p{pp+1}"
                part = AttrDict(PP[src_str])
                PARTICLE_DATA[pp] = part
                particle_struct = pdata()
                particle_struct.pnum = pp+1
                particle_struct.rx = part.location.x1
                particle_struct.ry = part.location.y1
                particle_struct.rz = part.location.z1
                particle_struct.vx = part.vx
                particle_struct.vy = part.vy
                particle_struct.vz = 0.0
                particle_struct.molar_mass = part.mass
                particle_struct.radius = part.radius
                particle_struct.inverse_square_softening = part.inverse_square_softening
                particle_struct.momentum_per_area = part.momentum_per_area
                self.p_list.append(particle_struct)
                self.number_particles = pp+1
        except BaseException as e:
            print("gPCD failed to read config file: ")   
            return
        cfg_data_name = self.itemcfg["STUDY_NAME"]
        self.test_file_name = f"{self.itemcfg.data_dir}/{cfg_data_name}.tst"
        self.test_bin_name = f"{self.itemcfg.data_dir}/{cfg_data_name}.bin"
        self.report_file = f"{self.itemcfg.data_dir}/{cfg_data_name}.rpt"
        self.write_test_file(RUN_CONFIGURATION)
        self.create_bin_file()
        self.write_bin_file(self.p_list)
        self.close_bin_file()
        print(f"TwoParticleHorizontal: Wrote {self.number_particles} particles to {self.test_bin_name}")
