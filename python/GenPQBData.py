from utilities import *
import random
from GenDataBase import *

class GenPQBData(GenDataBase):

    
    name = "GenPQBData"
    def __init__(self):
        super().__init__()

    def gen_random_numbers_in_range(self,low, high, n):
        return random.sample(range(low, high), n)
    
    def sort_write_random(self):
        plist = self.read_all_particle_data(self.test_bin_name)
        plist.sort(key=lambda x: x.pnum)
        self.create_bin_file()
        self.write_bin_file(plist)
        self.close_bin_file()


    def calculate_test_properties(self):
        try :
            print(self.index)
            self.collision_density      = float(self.select_list[self.index]["cdens"])
            self.number_particles       =  int(self.select_list[self.index]["tot"])
            self.radius                 = float(self.select_list[self.index]["radius"])
            self.sepdist                =  float(self.itemcfg.particle_separation)
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
        self.particles_in_row = round(len_parts/D)

        subcell = 1.0/self.particles_in_row
        dist =(subcell-2.0*self.radius) 
        self.sepdist = dist/2.0

        self.center_line_length     = 2.0*self.sepdist+2.0*self.radius

        self.particles_in_row       = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_col       = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_layers    = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_cell      = int(self.particles_in_row*self.particles_in_col*self.particles_in_layers)
        if self.itemcfg.cell_array_size == 0:
            self.cell_occupancy_list_size   = self.particles_in_cell+10
        else:
            self.cell_occupancy_list_size = self.itemcfg.cell_array_size
        self.tot_num_cells              = int(self.number_particles / self.particles_in_cell)
        self.num_collisions_per_cell    = int(self.particles_in_cell*self.collision_density)
        
        # Can't have odd number of particles in collsions 
        # Calculations here are based on particles in collsion not particle pairs
       # if self.num_collisions_per_cell % 2 != 0:
        #    self.num_collisions_per_cell+=1
       
        self.tot_num_collsions          = self.num_collisions_per_cell*self.tot_num_cells 
        self.side_length                = self.calc_side_length(self.number_particles,self.particles_in_cell)+1
        self.side_length_count          = self.side_length+1
        self.cell_x_len                 = self.side_length
        self.cell_y_len                 = self.side_length
        self.cell_z_len                 = self.side_length
      
        self.set_file_name = "{:03d}CollisionDataSet{:d}X{:d}X{:d}".format(self.index,self.number_particles,self.tot_num_collsions,self.side_length)
        self.test_file_name = self.itemcfg.data_dir + '/' + self.set_file_name + '.tst'
        self.test_bin_name = self.itemcfg.data_dir + '/' + self.set_file_name + '.bin'
        self.report_file = self.itemcfg.data_dir + '/' + self.set_file_name 

        self.log.log(self,f"Collsion Density: { self.collision_density},Number particles:{self.number_particles},Radius: {self.radius}, Separation Dist: {self.sepdist:.4f}, Center line length: {self.center_line_length:.2f}")
        self.log.log(self,f"Particles in row: {self.particles_in_row}, Particles in Column: {self.particles_in_col}, Particles per cell: {self.particles_in_cell}")
        self.log.log(self,f"Cell array size: {self.cell_occupancy_list_size }")
        return 0


    