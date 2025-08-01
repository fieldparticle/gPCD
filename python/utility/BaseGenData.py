import struct
import os
import csv
from mpl_interactions import ioff, panhandler, zoom_factory
import plotly.express as px
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import ctypes
import math
from ConfigClass import *
from abc import ABC, abstractmethod
import random
from shared.utilities import *


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
    def __init__(self):
        self. zlink = [0]*8
        
        
    _fields_ = [("pnum", ctypes.c_double),
                ("rx",  ctypes.c_double),
                ("ry",  ctypes.c_double),
                ("rz",  ctypes.c_double),
                ("radius",  ctypes.c_double),
                ("vx",  ctypes.c_double),
                ("vy",  ctypes.c_double),
                ("vz",  ctypes.c_double),
                ("ptype",  ctypes.c_double),
                ("rodnum",  ctypes.c_double),
                ("acc_r",  ctypes.c_double),
                ("Acc_a",  ctypes.c_double),
                ("molar_mass",  ctypes.c_double),
                ("temp_vel",  ctypes.c_double)]          


    
          

class BaseGenData:

    tst_file_cfg = ConfigClass("tstFIleCfg")
    particle_list = []
    particle_count = 0
    collision_count = 0
    collsions_in_cell_count = 0
    particles_in_cell_count = 0
    sepdist = 0.05
    select_list = []
    bin_file = None
    start_cell = 0
    end_cell = 0
    as_points = False
    test_bin_name = ""
    flg_plt_exists  = False
    toggle_flag = False
    cur_view_num = 0
    cur_file = ""
    flg_stop = False
    flg_plot_cell_faces = False
    flg_plot_cells = False
    rand_data = None
    max_cell_location = []
    side_length = 0
    side_length_count = 0
    cell_occupancy_list_size = 0
    last_max_scale = 0
    last_min_scale = 0
    old_rx = 0.0
    old_ry = 0.0
    old_rz = 0.0
    do_max_scale = True
    switch_col = True    
    collsion_count_check = 0
    particles_in_cell = 0
    num_collisions_per_cell = 0

    views = [('XY',   (90, -90, 0)),
        ('XZ',    (0, -90, 0)),
        ('YZ',    (0,   0, 0)),
        ('-XY', (-90,  90, 0)),
        ('-XZ',   (0,  90, 0)),
        ('-YZ',   (0, 180, 0))]   
    
    def __init__(self):
       pass

    def Create(self, FPIBGBase, ObjName,itemcfg,parent):
        self.parent = parent
        self.ObjName = ObjName
        self.bobj = FPIBGBase
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.log.log(self,"TabFormLatex finished init.")
        self.itemcfg = itemcfg
        self.cfg = self.itemcfg
        self.cur_view_num = int(self.cfg.default_view_text)
        self.toggle_flag = False
      

    def on_close(self,event):
        pass

        
    @abstractmethod
    def gen_data(self):
        pass
    @abstractmethod
    def plot_particle_cell(self):
        pass

 
    
    def add_null_particle(self,w_list):
        particle_struct = pdata()
        particle_struct.pnum = 0
        w_list.append(particle_struct)

    def open_bin_file(self):
        try:
            if self.bin_file:
                del self.bin_file
            self.bin_file = open(self.test_bin_name,"wb")
        except BaseException as e:
            self.log.log(self,e)
        self.count = 0

    def write_bin_file(self,w_lst):
        try:
            for ii in w_lst:
                self.bin_file.write(ii)
                self.count+=1
        except BaseException as e:
            self.log.log(self,e)
        
    def close_bin_file(self):
        if not self.bin_file.closed:
            self.bin_file.flush()
            self.bin_file.close()
        if(self.bin_file.closed != True):
            self.bobj.log.log("File:{self.test_bin_name} not closed")
        
    def write_test_file(self):
        if not os.path.exists(os.path.isdir(self.cfg.data_dir)):
            os.makedirs(os.path.isdir(self.cfg.data_dir))

    
    def open_selections_file(self):
        try:
            with open(self.itemcfg.selections_file_text,"r",newline='') as csvfl:
                reader = csv.DictReader(csvfl, delimiter=',',dialect='excel')
                for row in reader:
                    if row["sel"] == 's':
                        self.select_list.append(row)
        except BaseException as e:
            self.log.log(self,f"Error opening:{self.itemcfg.selections_file_text}, err:", e)
        return self.select_list

################################# GENERATE A SINGLE DATA ####################

    def stop_thread(self):
        self.flg_stop = True

    def gen_random_numbers_in_range(self,low, high, n):
        return random.sample(range(low, high), n)
    
    def sort_write_random(self):
        plist = self.read_all_particle_data(self.test_bin_name)
        plist.sort(key=lambda x: x.pnum)
        self.open_bin_file()
        self.write_bin_file(plist)
        self.close_bin_file()


    def gen_data_base(self,index,sel_dict,progress_callback):
        if(self.calulate_cell_properties(index,sel_dict) != 0):
            return
        self.open_bin_file()
        self.collsion_count_check = 0
        ret = self.do_cells(progress_callback)
        self.close_bin_file()
        self.write_test_file(index,sel_dict)
        col_ary_size = self.cell_occupancy_list_size
        if self.cfg.particle_enumeration_text == 'random':
            self.sort_write_random()
        pu = ParticleUtilities(self.side_length,col_ary_size)
        print("=========================================================\n")
        print(f"max_cell_location = <{self.max_cell_location[0]},{self.max_cell_location[0]},{self.max_cell_location[0]}>")
        index = pu.ArrayToIndex(self.max_cell_location)
        print(f"max_cell_index = <{index}> total particles ")
        print(f"Total Particles: {self.particle_count} Colliding Particles:{self.collision_count}. Collsion pairs:{self.collision_count/2}")
        print("=========================================================\n")
        return ret
       
        # Define the event handling function
    def calc_test_parms(self):
        pass

    def calc_side_length(self,num_parts,num_parts_per_cels):
        side_len = 0
        while True:
            side_len += 1
            if (side_len * side_len * side_len * num_parts_per_cels > num_parts):
                break
        ## Add on since particle locations are zero based
        return side_len+1


    def calulate_cell_properties(self,index,sel_dict):
        try :
            self.collision_density      = float(sel_dict['cdens'])
            self.number_particles       =  int(sel_dict['tot'])
            self.radius                 = float(sel_dict['radius'])
            self.sepdist                =  float(self.cfg.particle_separation_text)
        except BaseException as e:
            self.log.log(self,f"Key error in record:",e)
        
        # get diameter
        D = (2.0*self.radius)
        # how many particle fit in the 1.0 square cell
        subcell = math.floor(1.0/D)
        # how long is this numebr of particles
        len_parts = subcell*D

        # if the len is greater than 1.0 then remove particles unit there is some space left
        while len_parts >= 0.99:
            len_parts -= D

        # What is the maximum number of particle that can fit
        self.particles_in_row = round(len_parts/D)

        subcell = 1.0/self.particles_in_row
        dist =(subcell-2.0*self.radius) 
        self.sepdist = dist/2.0

        self.center_line_length     = 2.0*self.sepdist+2.0*self.radius

        self.particles_in_row       = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_col       = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_layers    = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_cell      = int(self.particles_in_row*self.particles_in_col*self.particles_in_layers)
        self.cell_occupancy_list_size   = self.particles_in_cell+10
        self.tot_num_cells              = int(self.number_particles / self.particles_in_cell)
        self.num_collisions_per_cell    = int(self.particles_in_cell*self.collision_density)
        
        # Can't have odd number of particles in collsions 
        # Calculations here are based on particles in collsion not particle pairs
        if self.num_collisions_per_cell % 2 != 0:
            self.num_collisions_per_cell+=1
       
        self.tot_num_collsions          = self.num_collisions_per_cell*self.tot_num_cells 
        self.side_length                = self.calc_side_length(self.number_particles,self.particles_in_cell)+1
        self.side_length_count          = self.side_length+1
        self.cell_x_len                 = self.side_length
        self.cell_y_len                 = self.side_length
        self.cell_z_len                 = self.side_length
      
        self.set_file_name = "{:03d}CollisionDataSet{:d}X{:d}X{:d}".format(index,self.number_particles,self.tot_num_collsions,self.side_length)
        self.test_file_name = self.cfg.data_dir + '/' + self.set_file_name + '.tst'
        self.test_bin_name = self.cfg.data_dir + '/' + self.set_file_name + '.bin'
        self.report_file = self.cfg.data_dir + '/' + self.set_file_name 

        self.log.log(self,f"Collsion Density: { self.collision_density},Number particles:{self.number_particles},Radius: {self.radius}, Separation Dist: {self.sepdist }, Center line length: {self.center_line_length:.2f}")
        self.log.log(self,f"Particles in row: {self.particles_in_row}, Particles in Column: {self.particles_in_col}, Particles per cell: {self.particles_in_cell}")
        self.log.log(self,f"Cell array size: {self.cell_occupancy_list_size }")
        return 0

 
    def do_cells(self,progress_callback):
        self.old_rx = 0.0
        self.old_ry = 0.0
        self.old_rz = 0.0
        if self.cfg.particle_enumeration_text == 'random':
            self.rand_data = self.gen_random_numbers_in_range(1, self.number_particles+1, self.number_particles)    
        if self.cfg.particle_enumeration_text == 'scale':
            self.last_max_scale = self.number_particles+1

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
            progress_callback.emit(zz)
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
                                        print(f"{self.collsion_count_check}")
                                    return 0
                                if len(self.w_list) >= int(self.cfg.write_block_len_text):
                                    self.write_bin_file(self.w_list)
                                    self.w_list.clear()
        self.write_bin_file(self.w_list)
        return 0
    
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
        if self.cfg.particle_enumeration_text == 'random':
            particle_struct.pnum = self.rand_data[self.particle_count]

        elif self.cfg.particle_enumeration_text == 'scale':
            if self.do_max_scale == True:
                self.last_max_scale-=1
                particle_struct.pnum = self.last_max_scale
            else:
                self.last_min_scale+=1
                particle_struct.pnum = self.last_min_scale
            
        elif self.cfg.particle_enumeration_text == 'sequential':    
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
    
    def write_test_file(self,index,sel_dict):
        
        with open(self.test_file_name,'w') as f:
            fstr = f"index = {index};\n"     
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
            fstr = f"particle_data_bin_file = \"{self.test_bin_name.replace('/','\\')}\";\n"
            f.write(fstr)
            fstr = f"report_file = \"{ self.report_file.replace('/','\\')}\";\n"
            f.write(fstr)
            fstr = f"collsion_density = {float(sel_dict['cdens'])};\n"
            f.write(fstr)
            fstr = f"pdensity = 0;\n"
            f.write(fstr)
            fstr = f"dispatchx = {sel_dict['dx']};\n"
            f.write(fstr)
            fstr = f"dispatchy = {sel_dict['dy']};\n"
            f.write(fstr)
            fstr = f"dispatchz = {sel_dict['dz']};\n"
            f.write(fstr)
            fstr = f"workGroupsx = {sel_dict['wx']};\n"
            f.write(fstr)
            fstr = f"workGroupsy = {sel_dict['wy']};\n"
            f.write(fstr)
            fstr = f"workGroupsz = {sel_dict['wz']};\n"
            f.write(fstr)
            fstr = f"cell_occupancy_list_size = {self.cell_occupancy_list_size};\n"
            f.write(fstr)
        f.close()


  
    
# Connect the event handler to the source figure
####################################################################################################
    def toggle_cell_face(self):
        if self.flg_plot_cell_faces == True:
            self.flg_plot_cell_faces = False
        else:
            self.flg_plot_cell_faces = True
        if self.flg_plot_cells == True:
            self.update_plot()
        else:
            print("Plotting cells is off.")

    def toggle_cells(self):
        if(self.flg_plot_cells == True):
            self.flg_plot_cells = False
        else:
            self.flg_plot_cells = True
        self.update_plot()

    def set_view_num(self,viewnum):
        self.cur_view_num = viewnum

    def set_cell_toggle_flag(self, flag):
        self.toggle_flag = flag

    def close_plot(self):
        plt.close()

    def set_up_plot(self):
        self.fig = plt.figure(1,figsize=(12, 10))
        self.ax = self.fig.add_subplot(projection='3d')
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        

    def do_plot(self,view_num=None,cells_on=True,aspoints=True):
        self.plot_particles(self.plist,aspoints=self.as_points)
        if self.flg_plot_cells == True:
            for ii in range(self.side_length):
                for jj in range(self.side_length):
                    for kk in range(self.side_length):
                        self.plot_cells(ii,jj,kk)

        self.end_plot(sidelen=self.side_length)
        self.flg_plt_exists  = True

    def update_plot(self): 
        plt.cla()
        self.do_plot()
        plt.show(block=False)
        plt.pause(0.01)
        
    def plot_base(self,file_name,view_num=None,cells_on=True,as_points=True):
        if '1' in self.cfg.plot_as_points_text:
            self.as_points = True
        else:
            self.as_points = False
        self.cur_file = file_name        
        self.set_up_plot()
        file_prefix = os.path.splitext(file_name)[0]
        self.test_file_name = file_prefix + ".tst"
        self.tst_file_cfg.Create(self.bobj.log,self.test_file_name)
        self.tst_side_length = int(self.cfg.start_sidelen_text)
        self.side_length = self.tst_file_cfg.config.CellAryW
        self.plist = self.read_particle_data(file_name)
        self.do_plot(aspoints=self.as_points )
        plt.show(block=False)

    def plot_particles(self,plist,aspoints=True,scolor=None):
        
        p_count = 0
        sphere_facets = int(self.cfg.sphere_facets_text)
        p_start = int(self.cfg.particle_range_array[0])
        p_end = int(self.cfg.particle_range_array[1])
        theta = np.linspace(0, 2 * np.pi, sphere_facets)
        phi = np.linspace(0, np.pi, sphere_facets)
        theta, phi = np.meshgrid(theta, phi)
        pcolor = self.cfg.particle_color_text
        
        if aspoints == True:    
            xx = []
            yy = []
            zz = []
            for ii in plist:
                if (p_count >= p_start):
                    if ii.ptype == 1:
                        col_clr ='blue'
                    else:
                        col_clr = pcolor
                    self.ax.scatter(ii.rx,ii.ry,ii.rz,color=col_clr)
                p_count +=1
                if(p_count > p_end):
                    break
        else:
            for ii in plist:
                if (p_count >= p_start):
                    # Convert to Cartesian coordinates
                    x = ii.rx + ii.radius * np.sin(phi) * np.cos(theta)
                    y = ii.ry + ii.radius * np.sin(phi) * np.sin(theta)
                    z = ii.rz + ii.radius * np.cos(phi)
                    #self.ax.plot_surface(x, y, z, alpha=0.8)
                    #print(f"Particle {p_count} Loc: <{ii.rx:2f},{ii.ry:2f},{ii.rz:2f})>")
                    
                    if 'none' in pcolor:
                        self.ax.plot_surface(x, y, z, alpha=0.8)
                    elif ii.ptype == 1:
                        self.ax.plot_surface(x, y, z, color='blue',alpha=0.8)
                    else:
                        self.ax.plot_surface(x, y, z, color=pcolor,alpha=0.8)
                    #print(f"Particle {p_count} Loc: <{ii.rx:2f},{ii.ry:2f},{ii.rz:2f})>")
                    
                p_count +=1
                if(p_count > p_end):
                    break
                    
        
    def side_value_changed(self,side_txt):
        if len(side_txt) < 2:
            return None
        self.start_cell = int(side_txt[0])
        self.end_cell = int(side_txt[1])
        
    def plot_view_changed(self,view):
        self.fig.canvas.draw()

    def end_plot(self,sidelen = None):
        lims = [float(self.cfg.limits_array[0]),float(self.cfg.limits_array[1])]
        view_num=self.cur_view_num
        self.ax.view_init(elev=self.views[view_num][1][0], azim=self.views[view_num][1][1], roll=self.views[view_num][1][2])
        self.ax.set_title('3D Line Plot')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')

        self.ax.set_xlim(lims)
        self.ax.set_ylim(lims)
        self.ax.set_zlim(lims)
        """
        #else:
            mxlims =[0,4]
           #ylims = max(npplist[:,2])
            #mzlims = max(npplist[:,3])
            lims = [0,5]
            self.ax.set_xlim(lims)
            self.ax.set_ylim(lims)
            self.ax.set_zlim(lims)
        """
        self.ax.set_title('3D Sphere')
        plt.gca().set_aspect('equal')
        #plt.get_current_fig_manager().full_screen_toggle()
        


    def get_side_length_txt(self):
        side_txt = f"{self.tst_side_length}:{self.tst_side_length}"
        
    def plot_cells(self,cx,cy,cz):
#        print(f"<{cx},{cy},{cz}>")
        ret = False
        for ii in self.itemcfg.cell_select_list:
            if ii == [cx,cy,cz]:
                ret = True
                break
        if ret == True:
            R = 0.5
            pt_lst = np.zeros((8,3))
            pt_lst[0]= [cx-R,cy-R,cz-R]
            pt_lst[1]= [cx+R,cy-R,cz-R]
            pt_lst[2]= [cx+R,cy+R,cz-R]
            pt_lst[3]= [cx-R,cy+R,cz-R]
            pt_lst[4]= [cx-R,cy-R,cz+R]
            pt_lst[5]= [cx+R,cy-R,cz+R]
            pt_lst[6]= [cx+R,cy+R,cz+R]
            pt_lst[7]= [cx-R,cy+R,cz+R]
            x = pt_lst[:,0]
            y = pt_lst[:,1]
            z = pt_lst[:,2]
            # Face IDs
            vertices = [[0,1,2,3],[1,5,6,2],[3,2,6,7],[4,0,3,7],[5,4,7,6],[4,5,1,0]]
            
            tupleList = list(zip(x, y, z))
            poly3d = [[tupleList[vertices[ix][iy]] for iy in range(len(vertices[0]))] for ix in range(len(vertices))]
            face_color = 'y'
            if self.flg_plot_cell_faces == True:
                alpha_val = 0.1
            else:
                alpha_val = 0.0
            self.ax.add_collection3d(Poly3DCollection(poly3d, edgecolors= 'k',facecolors=face_color, linewidths=1, alpha=alpha_val))
        
    def update_selection(self,file_name):
        self.cur_file = file_name     
        file_prefix = os.path.splitext(file_name)[0]
        self.test_file_name = file_prefix + ".tst"
        self.tst_file_cfg.Create(self.bobj.log,self.test_file_name)

    def out_put_cell_ary(self):
        self.side_length = self.tst_file_cfg.config.CellAryW
        col_ary_size = self.tst_file_cfg.config.cell_occupancy_list_size
        plist = self.read_all_particle_data(self.cur_file)
        pu = ParticleUtilities(self.side_length,col_ary_size)
        file_prefix = os.path.splitext(self.cur_file)[0]
        out_file_name = f"{file_prefix}.CellArray.csv"
        pu.gen_cell_ary(plist,out_file_name)

    def count_collions(self):
        self.side_length = self.tst_file_cfg.config.CellAryW
        col_ary_size = self.tst_file_cfg.config.cell_occupancy_list_size
        plist = self.read_all_particle_data(self.cur_file)
        pu = ParticleUtilities(self.side_length,col_ary_size)
        file_prefix = os.path.splitext(self.cur_file)[0]
        out_file_name = f"{file_prefix}.CellArray.csv"
        pu.detect_collsions(plist,out_file_name)
        
    def list_particles(self,p_list,list_obj):
        p_count = 0
        list_obj.clear()
        self.side_length = self.tst_file_cfg.config.CellAryW
        col_ary_size = self.tst_file_cfg.config.cell_occupancy_list_size
        pu = ParticleUtilities(self.side_length,col_ary_size)
        for ii in p_list:
            index = pu.ArrayToIndex([round(ii.rx),round(ii.ry),round(ii.rz)])
            list_obj.append(f"P:{ii.pnum} R:{ii.radius} I:{index}<{ii.rx:.2f},{ii.ry:.2f},{ii.rz:.2f}>[{round(ii.rx)},{round(ii.ry)},{round(ii.rz)}]")
        


    def test_array_to_index(self):
        file_name = f"{self.itemcfg.data_dir}/{self.itemcfg.test_indexing_rpt_text}"
        col_file = open(file_name,'w')
        file_prefix = os.path.splitext(self.test_file_name)[0]
        tst_side_length =  self.tst_file_cfg.config.CellAryW
        col_file.write(f"Height:{ tst_side_length},Width{tst_side_length}\n")
        col_ary_size = self.tst_file_cfg.config.cell_occupancy_list_size
        pu = ParticleUtilities(tst_side_length,col_ary_size)
        for zz in range(tst_side_length):
            for yy in range(tst_side_length):
                for xx in range(tst_side_length):
                    ary = [round(xx),round(yy),round(zz)]
                    index = pu.ArrayToIndex(ary)
                    col_file.write(f"Index:{index} at <{xx},{yy},{zz}>\n")

        col_file.close()

    def verify_particle_count(self,file_name):
        counter = 0
        with open(file_name, "rb") as f:
            while True:
                record = pdata()
                ret = f.readinto(record)
                if ret == 0:
                    break
                counter += 1
            
        print(f"Verify counted :{counter} against {self.number_particles}")
        


    def read_particle_data(self,file_name):
        struct_fmt = 'dddddddddddddd'
        struct_len = struct.calcsize(struct_fmt)
        #print(struct_len)
        struct_unpack = struct.Struct(struct_fmt).unpack_from
        count = 0
        results = []
        counter = 0
        slist = self.cfg.particle_range_array
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
        
    def read_all_particle_data(self,file_name):
        struct_fmt = 'dddddddddddddd'
        struct_len = struct.calcsize(struct_fmt)
        struct_unpack = struct.Struct(struct_fmt).unpack_from
        results = []
        counter = 0
        try:
            with open(file_name, "rb") as f:
                while True:
                    record = pdata()
                    ret = f.readinto(record)
                    if ret == 0:
                        break
                    results.append(record)    
        except BaseException as e:
            print(e)
        p_lst = []
        return results
    
  

    def on_scroll(self, event):
        #print(event.button, event.step)
        
        # Check if the event is a scroll event
        if event.button == 'down':
            scale_factor = 1.1  # Increase the scale factor to zoom in more
        elif event.button == 'up':
            scale_factor = 0.9  # Decrease the scale factor to zoom out more
        else:
            scale_factor = 1.0

        # Get the current x and y limits of the axes
        x_limits = self.ax.get_xlim()
        y_limits = self.ax.get_ylim()
        z_limits = self.ax.get_xlim()

        # Calculate the new limits based on the scroll event
        x_range = (event.xdata - x_limits[0]) / (x_limits[1] - x_limits[0])
        y_range = (event.ydata - y_limits[0]) / (y_limits[1] - y_limits[0])
        z_Range = y_range
        new_x_limits = (
            event.xdata - (x_limits[1] - x_limits[0]) * scale_factor * x_range,
            event.xdata + (x_limits[1] - x_limits[0]) * scale_factor * (1 - x_range)
        )
        new_y_limits = (
            event.ydata - (y_limits[1] - y_limits[0]) * scale_factor * y_range,
            event.ydata + (y_limits[1] - y_limits[0]) * scale_factor * (1 - y_range)
        )
        

        # Update the x and y limits of the axes
        self.ax.set_xlim(new_x_limits)
        self.ax.set_ylim(new_y_limits)
        self.ax.set_zlim(new_y_limits)
        plt.pause(0.01)
