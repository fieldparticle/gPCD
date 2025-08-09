import struct
import os
import csv
#from mpl_interactions import ioff, panhandler, zoom_factory
#import plotly.express as px
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import ctypes
import math
from ConfigUtility import *
from utilities import *
from abc import ABC, abstractmethod


	#double rx;
	#double ry;
	#double rz;
	#double radius;
	#double vx;
	#double vy;
	#double vz;
	#double ptype;
	#double seq;
	#double acc_r;
	#double acc_a;
	#double molar_mass;
	#double temp_vel;
class pdata(ctypes.Structure):
    _fields_ = [("pnum", ctypes.c_double),
                ("rx",  ctypes.c_double),
                ("ry",  ctypes.c_double),
                ("rz",  ctypes.c_double),
                ("radius",  ctypes.c_double),
                ("vx",  ctypes.c_double),
                ("vy",  ctypes.c_double),
                ("vz",  ctypes.c_double),
                ("ptype",  ctypes.c_double),
                ("seq",  ctypes.c_double),
                ("acc_r",  ctypes.c_double),
                ("Acc_a",  ctypes.c_double),
                ("molar_mass",  ctypes.c_double),
                ("temp_vel",  ctypes.c_double)]          
          


class GenDataBase:

    #tst_file_cfg = ConfigUtility("tstFIleCfg")
    particle_list = []
    particle_count = 0
    collision_count = 0
    collsions_in_cell_count = 0
    particles_in_cell_count = 0
    select_list = []
    sepdist = 0.05
    bin_file = None
    particle_separation = 0.0
    flg_stop = False
    do_max_scale = False
    collsion_count_check = 0
    base_name = "GenDataBase"
    max_cell_location= []
    particles_in_row = 0
    last_cell = [0,0,0]
    num_cells = 0
    old_rx = 0
    old_ry = 0
    old_rz = 0


    views = [('XY',   (90, -90, 0)),
        ('XZ',    (0, -90, 0)),
        ('YZ',    (0,   0, 0)),
        ('-XY', (-90,  90, 0)),
        ('-XZ',   (0,  90, 0)),
        ('-YZ',   (0, 180, 0))]   
    
    def __init__(self):
       pass

    #******************************************************************
    # Standrd create
    #
    def create(self,parent,itemcfg):
        self.parent = parent
        self.bobj = parent.bobj
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.itemcfg = itemcfg

    ##############################################################################
    # Abstrict members
    # 
    ##############################################################################
    #******************************************************************
    # Abstrct place_particles
    #
    def place_particles(self,xx,yy,zz,row,col,layer,w_list):
        pass
    #******************************************************************
    # Abstrct do_cells
    #
    def do_cells(self):
        pass

    ##############################################################################
    # Partice calcualtions
    # 
    ##############################################################################    
    #******************************************************************
    # Caluate side length based on number of particles and particle per 
    # cell
    #
    def calc_side_length(self,num_parts,num_parts_per_cels):
        side_len = 0
        while True:
            side_len += 1
            if (side_len * side_len * side_len * num_parts_per_cels > num_parts):
                break
        ## Add on since particle locations are zero based
        return side_len+1

    ##############################################################################
    # File I/O
    # 
    ##############################################################################    
    #******************************************************************
    # Create the binary particles file
    # 
    #
    def create_bin_file(self):
        try:
            self.bin_file = open(self.test_bin_name,"wb")
        except BaseException as e:
            self.log.log(self,e)
            return
        self.count = 0
    
      
    def sort_write_random(self):
        plist = self.read_all_particle_data(self.test_bin_name)
        plist.sort(key=lambda x: x.pnum)
        self.create_bin_file()
        self.write_bin_file(plist)
        self.close_bin_file()


    #******************************************************************
    #  List the particles
    # 
    #
    
    def list_particles(self,file_name):
        p_count = 0
        p_list = self.read_particle_data(file_name)
        index = 0
        for ii in p_list:
            print(f"P:{ii.pnum} R:{ii.radius} I:{index}<{ii.rx:.2f},{ii.ry:.2f},{ii.rz:.2f}>[{round(ii.rx)},{round(ii.ry)},{round(ii.rz)}]")
            index +=1
    #******************************************************************
    # Caluate side length based on number of particles and particle per 
    # cell
    #
    def write_bin_file(self,w_lst):
        try:
            for ii in w_lst:
                self.bin_file.write(ii)
                self.count+=1
        except BaseException as e:
            self.log.log(self,e)

    #******************************************************************
    # Close the binary prticle file after its filled
    # cell
    #
    def close_bin_file(self):
        self.tot_num_collsions = self.collision_count
        self.bin_file.flush()
        self.bin_file.close()
        if(self.bin_file.closed != True):
            self.bobj.log.log("File:{self.test_bin_name} not closed")

    #******************************************************************
    # Read particle data in range
    # 
    #
    def read_particle_data(self,file_name):
        struct_fmt = 'dddddddddddddd'
        struct_len = struct.calcsize(struct_fmt)
        #print(struct_len)
        struct_unpack = struct.Struct(struct_fmt).unpack_from
        count = 0
        results = []
        counter = 0
        slist = self.itemcfg.particle_range
        start_it = int(slist[0])
        end_it = int(slist[1])
        with open(file_name, "rb") as f:
            
            while True:
                if counter >= start_it: 
                    record = pdata()
                    ret = f.readinto(record)
                    if ret == 0:
                        break
                    #print(record.pnum)
                    results.append(record)
                    if counter > end_it:
                        break
                counter += 1
                
        p_lst = []
        return results
        
    #******************************************************************
    # Reead all of the particle data
    # 
    #
    def read_all_particle_data(self,file_name):
        struct_fmt = 'dddddddddddddd'
        struct_len = struct.calcsize(struct_fmt)
        #print(struct_len)
        struct_unpack = struct.Struct(struct_fmt).unpack_from
        count = 0
        results = []
        with open(file_name, "rb") as f:
            while True:
                record = pdata()
                ret = f.readinto(record)
                if ret == 0:
                    break
                results.append(record)
        p_lst = []
        return results
    
    def calc_test_parms(self):
        pass

    #******************************************************************
    # Always add a null particle to the beginging of the particles
    # bnary file. The particle.exe code ignores 0 so that it can be used
    # to indeicvate an emply ellement of an array.
    #
    def add_null_particle(self,w_list):
        particle_struct = pdata()
        particle_struct.pnum = 0
        w_list.append(particle_struct)
    
    #******************************************************************
    # load all lines from the particle selections file into selections list
    # 
    #
    def open_selections_file(self):
        with open(self.itemcfg.selections_file,"r",newline='') as csvfl:
            reader = csv.DictReader(csvfl, delimiter=',',dialect='excel')
            for row in reader:
                if row["sel"] == 's':
                    self.select_list.append(row)
    
    #******************************************************************
    # Clear selections file list
    # 
    #
    def clear_selections(self):
        self.select_list.clear()
       
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
        fstr = f"radius = {self.radius};\n"
        f.write(fstr)
        fstr = f"particles_per_cell = {self.particles_in_cell};\n"
        f.write(fstr)
        fstr = f"num_particles = {self.number_particles};\n"
        f.write(fstr)
        fstr = f"num_particle_colliding = {self.tot_num_collsions};\n"
        f.write(fstr)
        fstr = f"exp_collisions_per_cell = {self.num_collisions_per_cell};\n"
        f.write(fstr)
        fstr = f"act_collisions_per_cell = {self.collsion_count_check};\n"
        f.write(fstr)
        fstr = f"particles_in_row = {self.particles_in_row};\n"
        f.write(fstr)
        fstr = f"particle_data_bin_file = \"{self.test_bin_name}\";\n"
        f.write(fstr)
        fstr = f"report_file = \"{ self.report_file}\";\n"
        f.write(fstr)
        fstr = f"collsion_density = {float(self.select_list[self.index]['cdens'])};\n"
        f.write(fstr)
        fstr = f"pdensity = 0;\n"
        f.write(fstr)
        fstr = f"dispatchx = {self.select_list[self.index]['dx']};\n"
        f.write(fstr)
        fstr = f"dispatchy = {self.select_list[self.index]['dy']};\n"
        f.write(fstr)
        fstr = f"dispatchz = {self.select_list[self.index]['dz']};\n"
        f.write(fstr)
        fstr = f"workGroupsx = {self.select_list[self.index]['wx']};\n"
        f.write(fstr)
        fstr = f"workGroupsy = {self.select_list[self.index]['wy']};\n"
        f.write(fstr)
        fstr = f"workGroupsz = {self.select_list[self.index]['wz']};\n"
        f.write(fstr)
        fstr = f"cell_occupancy_list_size = {self.cell_occupancy_list_size};\n"
        f.write(fstr)
        f.flush()
        f.close()


    #******************************************************************
    # Write the tst files taht are read by particle.exe for tests
    # 
    #
    def place_particles(self,xx,yy,zz,row,col,layer,w_list):

        
        # If particle cont is greater than the required numbe of particles return 3 to end the
        if (self.particle_count >= self.number_particles):
            return 3

        # IF number collsions met return 2
        if(self.particles_in_cell_count > self.particles_in_cell ):
            return 2
        
        # Switch for the range function
        if(self.do_max_scale == True):
            self.do_max_scale = False
        else:
            self.do_max_scale = True


        particle_struct = pdata()
        #print(f"particle: {self.particle_count}, xx={xx}, yy= {yy}, zz={zz}, layer= {layer}, row= {row} col= {col}")
        #                         |offset so no particle is in a cell with a zero in it|
       
        subcell = 1.0/self.particles_in_row
        dist =(subcell-2.0*self.radius) 
        sep = dist/2.0

        self.center_line_length     = 2.0*sep+2.0*self.radius
        self.switch_col = False
        odd_colum = 0
        if col == 0:
            odd_colum = 0
            self.switch_col = False
        else:
            odd_column = col%2
            self.switch_col  = True

        # If more colsions are needed
        if(self.collsions_in_cell_count < self.num_collisions_per_cell):
            if col%2:
                rx = 0.5 + sep + 0.25*self.radius + self.center_line_length*col+xx
                self.collsions_in_cell_count+=1
                self.collision_count+=1
                particle_struct.ptype = 1
                self.switch_col = False
            else:
                rx = 0.5 + sep + self.radius + self.center_line_length*col+xx
                self.collsions_in_cell_count+=1
                self.collision_count+=1
                particle_struct.ptype = 1
                self.switch_col = True
        else:
            particle_struct.ptype = 0
            rx = 0.5 + sep + self.radius + self.center_line_length*col+xx


        ry = 0.5 + sep + self.radius + self.center_line_length*row+yy        
        rz = 0.5 + sep + self.radius + self.center_line_length*layer+zz
    
        if round(rx) == 1 and round(ry) == 1 and round(rz) == 1:
            self.collsion_count_check = self.collsions_in_cell_count
        


        #print(f"row{row}:col{col} <{rx},{ry},{rz}> Cell:<{round(rx)},{round(ry)},{round(rz)}>")
        if self.itemcfg.particle_enumeration == 'random':
            particle_struct.pnum = self.rand_data[self.particle_count]

        elif self.itemcfg.particle_enumeration == 'scale':
            if self.do_max_scale == True:
                self.last_max_scale-=1
                particle_struct.pnum = self.last_max_scale
            else:
                self.last_min_scale+=1
                particle_struct.pnum = self.last_min_scale
            
        elif self.itemcfg.particle_enumeration == 'sequential':    
            particle_struct.pnum = self.particle_count + 1    

        particle_struct.rx = rx
        particle_struct.ry = ry
        particle_struct.rz = rz
        particle_struct.radius = self.radius
        w_list.append(particle_struct)
        self.particle_count+=1
        self.particles_in_cell_count +=1

        if self.old_rx < rx:
            self.old_rx = rx
        if self.old_ry < ry:
            self.old_ry = ry
        if self.old_rz < rz:
            self.old_rz = rz
        self.max_cell_location = [round(self.old_rx),round(self.old_ry),round(self.old_rz)]
        return 0
    #******************************************************************
    # Calulate the cell and particle propeties of the study
    #
    #     
    #******************************************************************
    def gen_data_base(self,index,progress_callback=None):
        self.index = index
        ret = 0
        if(self.calculate_test_properties() != 0):
            return
        if self.itemcfg.test_files_only == False:
            self.create_bin_file()  
            self.collsion_count_check = 0
            ret = self.do_cells(progress_callback)
            self.close_bin_file()
        
        self.write_test_file()
        col_ary_size = self.cell_occupancy_list_size
        
        if self.itemcfg.test_files_only == False:
            if self.itemcfg.particle_enumeration == 'random':
                self.sort_write_random()
            pu = ParticleUtilities(self.side_length,col_ary_size)

            self.log.log(self,f"num_cells={self.num_cells},max_cell_location = <{self.max_cell_location[0]},{self.max_cell_location[0]},{self.max_cell_location[0]}>")
            cell_index = pu.ArrayToIndex(self.max_cell_location)
            self.log.log(self,f"max_cell_index = <{cell_index}> total cells ")
        self.log.log(self,f"Collisions per cell:{self.num_collisions_per_cell}. Collsion pairs per cell:{self.num_collisions_per_cell/2}")
        
        
        self.log.log(self,f"Total Particles: {self.particle_count},Calculated Collisions:{self.tot_num_collsions}, Counted Collsions:{self.collision_count}")
        self.log.log(self,"=========================================================\n")
        return ret    
    
    #******************************************************************
    # Iterate though the cells and place partiucles 
    #
    #     
    #******************************************************************
    def do_cells(self,progress_callback):
        self.old_rx = 0.0
        self.old_ry = 0.0
        self.old_rz = 0.0
        self.num_cells = 0
        if self.itemcfg.particle_enumeration == 'random':
            self.rand_data = self.gen_random_numbers_in_range(1, self.number_particles+1, self.number_particles)    
        if self.itemcfg.particle_enumeration == 'scale':
            self.last_max_scale = self.number_particles+1
        self.collision_count = 0
        ret = 0
        self.w_list = []
        self.particle_count = 0
        self.add_null_particle(self.w_list)
        ########################################################
        # This only happens here. The side_length is n
        # but since cells start at zero they go from 0 to n-1
        z_range = self.cell_z_len-1
        y_range = self.cell_y_len-1
        z_range = self.cell_x_len-1
        
        ########################################################
        for zz in range(z_range):
            ppc = float(self.particle_count/self.number_particles)*100.0
            if progress_callback!= None:
                progress_callback.emit(ppc)
            else:
                print(f"{ppc:.2f}")
            for yy in range(y_range):
                for xx in range(z_range):
                    self.collsions_in_cell_count = 0
                    self.particles_in_cell_count = 0
                    # Inside a single cell. Process single cell
                    for layer in range(self.particles_in_layers):
                        for row in range(self.particles_in_row): 
                            for col in range(self.particles_in_col):        
                                if self.flg_stop == True:
                                    return 1
                                ret = self.place_particles(xx,yy,zz,row,col,layer,self.w_list)
                                if ret == 3:
                                    if len(self.w_list) > 0:
                                        self.write_bin_file(self.w_list)
                                        #print(f"{self.collsion_count_check}")
                                    return 0
                                if len(self.w_list) >= self.itemcfg.write_block_len:
                                    self.write_bin_file(self.w_list)
                                    self.w_list.clear()
        self.write_bin_file(self.w_list)
        return 0