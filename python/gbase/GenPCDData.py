from utilities import *
from GenDataBase import *
import math
class GenPCDData(GenDataBase):

    local_particles_in_row = 0
    local_particles_in_col = 0
    local_particles_in_layer = 0
    sel_file = None
    cell_items = []
    name = "genPCDData"
    def __init__(self):
        super().__init__()

    def calculate_test_properties(self):
        
        try :
           #print(self.index)
            self.collision_density      = float(self.select_list[self.index]["cdens"])
            self.number_particles       =  int(self.select_list[self.index]["tot"])
            self.radius                 = float(self.select_list[self.index]["radius"])
            self.sepdist                =  float(self.itemcfg.particle_separation)
            self.particles_in_row       = int(self.select_list[self.index]["px"])
        except BaseException as e:
            
            raise BaseException(f"calculate_test_properties Key error in record:{e}")
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
        particles_in_row = round(len_parts/D)

        subcell = 1.0/particles_in_row
        dist =(subcell-2.0*self.radius) 
        self.sepdist = dist/2.0

        self.center_line_length     = 2.0*self.sepdist+2.0*self.radius
        self.particles_in_col       = int(self.particles_in_row)
        self.particles_in_layers    = int(self.particles_in_row)
        self.particles_in_cell      = self.particles_in_col**3
        
    
        self.local_particles_in_row       = int(math.floor(1.00 /self.center_line_length))
        self.local_particles_in_col       = int(math.floor(1.00 /self.center_line_length))
        self.local_particles_in_layer    = int(math.floor(1.00 /self.center_line_length))
        #self.particles_in_cell      = int(self.particles_in_row*self.particles_in_col*self.particles_in_layers)
        if self.itemcfg.cell_array_size == 0:
            self.cell_occupancy_list_size   = self.particles_in_cell+10
        else:
            self.cell_occupancy_list_size = self.itemcfg.cell_array_size
        self.tot_num_cells              = int(self.number_particles / self.particles_in_cell)
        self.num_collisions_per_cell    = int(self.particles_in_cell*self.collision_density)
        
        # Can't have odd number of particles in collsions 
        # Calculations here are based on particles in collsion not particle pairs
        if self.num_collisions_per_cell % 2 != 0:
            self.num_collisions_per_cell+=1
       
        self.tot_num_collsions          = self.num_collisions_per_cell*self.tot_num_cells 
        self.tot_num_collsions          = int(self.collision_density*self.number_particles)
        self.side_length                = self.calc_side_length(self.number_particles,self.particles_in_cell)+1
        self.side_length_count          = self.side_length+1
        self.cell_x_len                 = self.side_length
        self.cell_y_len                 = self.side_length
        self.cell_z_len                 = self.side_length
      
        self.set_file_name = "{:03d}CollisionDataSet{:d}X{:d}X{:d}".format(self.index,self.number_particles,self.tot_num_collsions,self.side_length)
        self.test_file_name = self.itemcfg.data_dir + '/' + self.set_file_name + '.tst'
        self.test_bin_name = self.itemcfg.data_dir + '/' + self.set_file_name + '.bin'
        self.report_file = self.itemcfg.data_dir + '/' + self.set_file_name 

        self.log.log(self,f"========================{self.test_file_name}=================================\n")
        self.log.log(self,f"Collsion Density: { self.collision_density},Number particles:{self.number_particles},Radius: {self.radius}, Separation Dist: {self.sepdist:.4f}, Center line length: {self.center_line_length:.2f}")
        self.log.log(self,f"Particles in row: {self.particles_in_row}, Particles in Column: {self.particles_in_col}, Particles per cell: {self.particles_in_cell}")
        self.log.log(self,f"Cell array size: {self.cell_occupancy_list_size }")
        return 0
    
   
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
       
        subcell = 1.0/self.local_particles_in_row
        dist =(subcell-2.0*self.radius) 
        sep = dist/2.0

        self.center_line_length     = 2.0*sep+2.0*self.radius
        self.switch_col = False
        
       
        break_flag = False
        rx = 0
        num_left = self.number_particles - self.particle_count 
        if self.particles_in_cell_count == 0 :
            if (num_left <= self.particles_in_cell):
                break_flag = True

        
        if (break_flag == False):
            if (self.particles_in_row %2) != 0:
                rx = self.odd_columns(particle_struct,row,col,layer,xx,yy,zz,sep)
            else:
                rx = self.even_columns(particle_struct,row,col,layer,xx,yy,zz,sep)
        else:
            rx = 0.5 + sep + self.radius + self.center_line_length*col+xx

        ry = 0.5 + sep + self.radius + self.center_line_length*row+yy        
        rz = 0.5 + sep + self.radius + self.center_line_length*layer+zz
    
        if round(rx) == 1 and round(ry) == 1 and round(rz) == 1:
            self.collsion_count_check = self.collsions_in_cell_count
        


        particle_struct.pnum = self.particle_count + 1    

        particle_struct.rx = rx
        particle_struct.ry = ry
        particle_struct.rz = rz
        particle_struct.radius = self.radius
        w_list.append(particle_struct)
        self.particle_count+=1
        self.particles_in_cell_count +=1

        
        if self.last_cell != [round(rx),round(ry),round(rz)]:
            self.num_cells += 1
            self.last_cell = [round(rx),round(ry),round(rz)]

        if self.old_rx < rx:
            self.old_rx = rx
        if self.old_ry < ry:
            self.old_ry = ry
        if self.old_rz < rz:
            self.old_rz = rz
        self.max_cell_location = [round(self.old_rx),round(self.old_ry),round(self.old_rz)]
        return 0

    #******************************************************************
    # Place particles in even column layout
    # 
    #
    def even_columns(self,particle_struct,row,col,layer,xx,yy,zz,sep):
       
        rx = 0
        if col == 0:
            self.switch_col = False
        else:
            self.switch_col  = True
        if(self.collsions_in_cell_count < self.num_collisions_per_cell):
            if col%2:
                rx = 0.5 + sep + 0.25*self.radius + self.center_line_length*col+xx
                self.collsions_in_cell_count+=1
                self.collision_count += 1
                particle_struct.ptype = 1
                self.switch_col = False
            else:
                rx = 0.5 + sep + self.radius + self.center_line_length*col+xx
                self.collsions_in_cell_count += 1
                self.collision_count += 1
                particle_struct.ptype = 1
                self.switch_col = True

        else:
            particle_struct.ptype = 0
            rx = 0.5 + sep + self.radius + self.center_line_length*col+xx
        return rx
    #******************************************************************
    # Place particles in odd column layout
    # 
    #
    def odd_columns(self,particle_struct,row,col,layer,xx,yy,zz,sep):
        if col == 0:
            self.switch_col = False
        else:
            self.switch_col  = True
        pleft = self.particles_in_col - col
        rx = 0
        if self.collsions_in_cell_count < self.num_collisions_per_cell :
            if( (pleft % 2 == 0) or (pleft > 0 and self.switch_col == True)):
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
        else:
            particle_struct.ptype = 0
            rx = 0.5 + sep + self.radius + self.center_line_length*col+xx
        return rx
