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
    collsion_count_check = 0
    
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


  
