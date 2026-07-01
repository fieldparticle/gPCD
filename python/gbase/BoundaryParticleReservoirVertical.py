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
        pass        

    #******************************************************************
    # Write the tst files taht are read by particle.exe for tests
    # 
    #
    def write_test_file(self):
        ##JMB use self.itemcfg
        try:
            f = open(self.test_file_name,'w')
        except BaseException as e:
            raise BaseException(f"Can't open testfile {self.test_file_name} err{e}")
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
        fstr = f"boundary_x_min = {self.wallxmin:0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_x_max = {self.wallxmax:0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_y_min = {self.wallymin:0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_y_max = {self.wallymax:0.6f};\n"
        f.write(fstr)
        boundary_z = float(self.cfg_value(run_cfg, "reservoir_z", 2.0))
        fstr = f"boundary_z_min = {boundary_z:0.6f};\n"
        f.write(fstr)
        fstr = f"boundary_z_max = {boundary_z:0.6f};\n"
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
        f.flush()
        f.close()
        

    def runner(self):
        run_cfg = get_run_configuration(self.itemcfg)
        
    # ------------------------------------------------------------------
    # Simulation configuration checks
    # ------------------------------------------------------------------
    def validate_simulation_configuration(self):
        pass

    def addMobileParticle(self):
        try:
            for col in range(1,self.itemcfg.particle_columns+1):    
                for row in range(1,particles_per_row+1):     
                    rx, ry, rz, vx, vy, vz = self.release_state_for_particle_vert(
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
                    particle_struct.state_flg = 0.0
                    particle_struct.collision_stiffness_q = collision_stiffness_q
                    self.p_list.append(particle_struct)
        except BaseException as e:
            print(f"Failed adding Particle:{e} ")   
            return
        self.writeCFGData(self)

   
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
        self.write_test_file(run_cfg)
        self.create_bin_file()
        self.write_bin_file(self.p_list)
        self.close_bin_file()
        self.report_generated_bounds()
        print(f"PipeReservoirEntry: Wrote {self.number_particles} reservoir particles to {self.test_bin_name}")
