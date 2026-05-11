from utilities import *
from GenDataBase import *
import math
from pdata import *
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

    def clear_files(self):
        pass
    def do_all_files_dbg(self):
        self.twoParticleHorizontal()
    
    def create_bin_file(self):
        try:
            self.bin_file = open(self.test_bin_name,"wb")
        except BaseException as e:
            self.log.log(self,e)
            return
        self.count = 0
    
    def twoParticleHorizontal(self):
        self.p_list = []
        self.add_null_particle(self.p_list)
        self.index = 0
        self.cell_x_len = self.cell_y_len = self.cell_z_len = 5
        self.particles_in_cell = 8
        self.number_particles = 2
        self.tot_num_collsions = self.num_collisions_per_cell =self.collsion_count_check = 0

        self.test_file_name = f"{self.itemcfg.data_dir}/TwoParticleHorizontal.tst"
        self.test_bin_name = f"{self.itemcfg.data_dir}/TwoParticleHorizontal.bin"
        self.report_file = f"{self.itemcfg.data_dir}/TwoParticleHorizontal.rpt"
        inverse_square_softening = 1.0
        momentum_per_area = 0.001

        particle_struct = pdata()
        particle_struct.pnum = 1
        particle_struct.rx = 2.0
        particle_struct.ry = 2.1
        particle_struct.rz = 2.0
        particle_struct.vx = 0.05
        particle_struct.vy = 0.0
        particle_struct.vz = 0.0
        particle_struct.molar_mass = 1.0
        particle_struct.radius = 0.25
        particle_struct.inverse_square_softening = inverse_square_softening
        particle_struct.momentum_per_area = momentum_per_area

        self.p_list.append(particle_struct)
    
        particle_struct = pdata()
        particle_struct.pnum = 2
        particle_struct.rx = 3.0
        particle_struct.ry = 2.1
        particle_struct.rz = 2.0
        particle_struct.vx = -0.05
        particle_struct.vy = 0.0
        particle_struct.vz = 0.0
        particle_struct.molar_mass = 1.0
        particle_struct.radius = 0.25
        particle_struct.inverse_square_softening = inverse_square_softening
        particle_struct.momentum_per_area = momentum_per_area
        self.p_list.append(particle_struct)
        self.write_test_file()
        self.create_bin_file()
        self.write_bin_file(self.p_list)
        self.close_bin_file()
        print(f"TwoParticleHorizontal: Wrote {self.count} particles to {self.test_bin_name}")

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
    def write_test_file(self):

        try:
            f = open(self.test_file_name,'w')
        except BaseException as e:
            raise BaseException(f"Can't open testfile {self.test_file_name} err{e}")
        fstr = f"index = {self.index};\n"     
        f.write(fstr)
        # size lengths must be plus 1 since the cell locations start as <0,0,0>
        # THIS is the only place you so this - The vulkan code nees to check this
        fstr = f"CellAryW = {self.cell_x_len};\n"     
        f.write(fstr)
        fstr = f"CellAryH = {self.cell_y_len};\n"     
        f.write(fstr)
        fstr = f"CellAryL = {self.cell_z_len};\n"     
        f.write(fstr)
        fstr = f"radius = 1.0;\n"
        f.write(fstr)
        fstr = f"particles_per_cell = {self.particles_in_cell+2};\n"
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
        fstr = f"collsion_density = 0;\n"
        f.write(fstr)
        fstr = f"pdensity = 0;\n"
        f.write(fstr)
        fstr = f"dispatchx = 3;\n"
        f.write(fstr)
        fstr = f"dispatchy = 1;\n"
        f.write(fstr)
        fstr = f"dispatchz = 1;\n"
        f.write(fstr)
        fstr = f"workGroupsx = 1\n"
        f.write(fstr)
        fstr = f"workGroupsy = 1;\n"
        f.write(fstr)
        fstr = f"workGroupsz = 1;\n"
        f.write(fstr)
        fstr = f"cell_occupancy_list_size = 4;\n"
        f.write(fstr)
        f.flush()
        f.close()
