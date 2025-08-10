
from GenDataBase import *
from utilities import *
import random

class GenDUPData(GenDataBase):

    def __init__(self):
        super().__init__()

    def gen_data(self):
        self.gen_data_base()
        
    def plot_particle_cell(self,file_name):
        self.plot_particle_cell_base(file_name)
    def calculate_test_properties(self):
        
        try :
           #print(self.index)
            self.collision_density      = float(self.select_list[self.index]["cdens"])
            self.number_particles       =  int(self.select_list[self.index]["tot"])
            self.radius                 = float(self.select_list[self.index]["radius"])
            self.sepdist                =  float(self.itemcfg.particle_separation)
            self.tot_num_cells          = int(self.select_list[self.index]["px"])
        except BaseException as e:
            raise BaseException(f"calculate_test_properties Key error in record:{e}")
       
        
        self.num_collisions_per_cell    = 16
        self.particles_in_cell          = 8
        self.number_particles           = self.tot_num_cells*self.particles_in_cell
        self.cell_occupancy_list_size   = self.particles_in_cell*4
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

        self.log.log(self,f"========================{self.test_file_name}=================================\n")
        self.log.log(self,f"Collsion Density: { self.collision_density},Number particles:{self.number_particles},Radius: {self.radius}")
        self.log.log(self,f"Particles per cell: {self.particles_in_cell}")
        self.log.log(self,f"Cell array size: {self.cell_occupancy_list_size }")
        return 0
    
    
    def gen_random_numbers_in_range(self,low, high, n):
        return random.sample(range(low, high), n)
    
    def place_particlePair(self,xx1,yy1,zz1,xx2,yy2,zz2,colliding,w_list):
        
        particle_struct1 = pdata()
        particle_struct1.ptype = 1
        self.collision_count+=1
        particle_struct1.pnum = self.particle_count + 1    
        particle_struct1.rx = xx1
        particle_struct1.ry = yy1
        particle_struct1.rz = zz1
        p0 =  np.array([xx1,yy1,zz1])
        particle_struct1.radius = self.radius
        w_list.append(particle_struct1)
        self.particle_count+=1
        self.particles_in_cell_count +=1

        if self.old_rx < particle_struct1.rx:
            self.old_rx = particle_struct1.rx
        if self.old_ry < particle_struct1.rx:
            self.old_ry = particle_struct1.rx
        if self.old_rz < particle_struct1.rx:
            self.old_rz = particle_struct1.rx

        particle_struct2 = pdata()
        particle_struct2.ptype = 1
        self.collision_count+=1
        particle_struct2.pnum = self.particle_count + 1    
        particle_struct2.rx = xx2
        particle_struct2.ry = yy2
        particle_struct2.rz = zz2
        p1 = np.array([xx2,yy2,zz2])
        particle_struct2.radius = self.radius
        w_list.append(particle_struct2)
        self.particle_count+=1
        self.particles_in_cell_count +=1
        dist = np.linalg.norm(p0 - p1)
        if dist >= (particle_struct2.radius + particle_struct1.radius):
            print(f"P:{particle_struct1.pnum} and P:{particle_struct2.pnum} are not colliding.")

        if self.old_rx < particle_struct2.rx:
            self.old_rx = particle_struct2.rx
        if self.old_ry < particle_struct2.rx:
            self.old_ry = particle_struct2.rx
        if self.old_rz < particle_struct2.rx:
            self.old_rz = particle_struct2.rx
        self.max_cell_location = [round(self.old_rx),round(self.old_ry),round(self.old_rz)]
        return [int(particle_struct1.pnum),int(particle_struct2.pnum)]

    def do_cells(self,progress_callback):

        if self.itemcfg.particle_enumeration == 'random':
            self.rand_data = self.gen_random_numbers_in_range(0, self.number_particles, self.number_particles)    
        
        ret = 0
        self.w_list = []
        self.particle_count = 0
        self.collision_count = 0
        self.number_particles = 0
        flg_col_rpt = False
        col_lst = []
        cell_count = 0
        cell_flag = False
        self.add_null_particle(self.w_list)
        for zz in range(self.cell_z_len-1):
            if cell_flag == True:
                    break
            ppc = float(self.particle_count)
            if progress_callback!= None:
                progress_callback.emit(ppc)
            else:
                print(f"{ppc:.2f}")
            for yy in range(self.cell_y_len-1):
                if cell_flag == True:
                    break
                for xx in range(self.cell_x_len-1):
                    # Top 4
                    p1ary = self.place_particlePair(xx+1.5,yy+1.5,zz+1.45,xx+1.5,yy+1.5,zz+1.55,1,self.w_list)  
                    #self.place_particles(xx+1.5,yy+1.5,zz+1.55,0,self.w_list)  
                    # Side 2 colide X plane
                    
                    p2ary = self.place_particlePair(xx+1.42,yy+1.0,zz+1.0,xx+1.57,yy+1.0,zz+1.0,1,self.w_list)  
                    #self.place_particles(xx+1.57,yy+1.0,zz+1.0,0,self.w_list)  

                    p3ary = self.place_particlePair(xx+1.0,yy+1.42,zz+1.0,xx+1.0,yy+1.57,zz+1.0,1,self.w_list)  
                    #self.place_particles(xx+1.0,yy+1.57,zz+1.0,0,self.w_list)  

                    p4ary = self.place_particlePair(xx+1.0,yy+1.0,zz+1.42,xx+1.0,yy+1.0, zz+1.57,1,self.w_list)  
                    #self.place_particles(xx+1.0,yy+1.0, zz+1.57,0,self.w_list)  

                    if flg_col_rpt == True:
                        col_lst.append(p1ary) 
                        col_lst.append(p2ary) 
                        col_lst.append(p3ary) 
                        col_lst.append(p4ary) 
                                     
                    cell_count += 1 
                    if cell_count == self.tot_num_cells:
                        cell_flag = True
                        break
        self.number_particles = self.particle_count
        self.write_bin_file(self.w_list)
       # if flg_col_rpt == True:
       #     for ii in col_lst:
       #         col_file.write(f"{ii[0]},{ii[1]}\n")
       #     col_file.close()
        
        return 0
        
        
                                    
        
    
