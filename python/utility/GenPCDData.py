
from BaseGenData import *
import math
class GenPCDData(BaseGenData):

    sel_file = None
    cell_items = []
    def __init__(self):
        super().__init__()


    def calc_side_len(self,part_per_cell,num_parts):
        ii = 0
        while True:
            ii = ii+1
            if(ii*ii*ii*part_per_cell>=num_parts):
                return ii

    
    def add_item(self,p_in_cell,side_len,radius,num_part):
        self.sel_file.write(f"1,1,1,{num_part+1},1,1,{num_part},s,{p_in_cell},{side_len},0.5,{radius:0.4f},0.0,0.0,0.0,0.0,0.0,0.0\n")
    
    def oldopen_selections_file(self):
        self.sel_file = open(self.itemcfg.selections_file_text,'w')
        self.sel_file.write("wx,wy,wz,dx,dy,dz,tot,sel,cols,sidelen,cdens,radius,vx,vy,vz,px,py,pz\n")
        cell_items = []
        start = 0.2
        num_part = 117649
        last_side_len = 0
        last_particles_in_row = 0
        for ii in range(450):
            rr =  start-ii*0.0005
            # If R is les then 0 we're done
            if rr <= 0:
                break
            # get diameter
            D = (2.0*rr)
            # how many particle fit in the 1.0 square cell
            subcell = 1.0/D
            # how long is this numebr of particles
            len_parts = subcell*D

            # if the len is greater than 1.0 then remove particles unit there is some space left
            while len_parts >= 1.0:
                len_parts -= D

            # What is the maximum number of particle that can fit
            particles_in_row = math.ceil(len_parts/(2.0*rr))
            # Will this number still fit - if not continue
            if particles_in_row*D > 1.0:
                continue

            # If the particles in row are not an even number then continue.
            # Odd number rows are hard to to collsions for.
            #if particles_in_row % 2 != 0:
             #   continue
            # If this number of particle in row equal the last calulation then
            # continue. If not record last number in row
            if last_particles_in_row == particles_in_row:
                continue
            else:
                last_particles_in_row = particles_in_row
                
            # Will this number still fit - if not continue
            len_space = 1.0-particles_in_row*D
            if len_space <= 0:
                continue

            # Calc number of particles per cell
            particles_in_cell = particles_in_row**3

            # cal number of cells
            number_cells = round(num_part/particles_in_cell)

            # Get total number of particle - if greater than number of particles
            # skip
            tot_particles = number_cells*particles_in_cell
            if tot_particles > num_part:
                continue

            # now get side_lenth
            side_len = round(number_cells**(1/3))
            
            # Cant have zero sidelenth
            if side_len <= 0:
                continue

            # if the last side length
            if last_side_len != side_len:
                self.add_item(particles_in_cell,side_len,rr,num_part)
                cell_items.append(f"particles_in_cell:{particles_in_cell},number of cells:{number_cells},particle in row:{ particles_in_row},side_len:{side_len},R:{rr:.4f},N:{int(tot_particles)}\n")
                last_side_len = side_len
            
        fl_name = self.itemcfg.data_dir+ "/cell_sizes.txt"
        with open(fl_name,'w') as ff:
            for ii in cell_items:
                ff.write(ii)

        self.sel_file.flush()
        self.sel_file.close()


        try:
            with open(self.itemcfg.selections_file_text,"r",newline='') as csvfl:
                reader = csv.DictReader(csvfl, delimiter=',',dialect='excel')
                for row in reader:
                    if row["sel"] == 's':
                        self.select_list.append(row)
        except BaseException as e:
            self.log.log(self,f"Error opening:{self.itemcfg.selections_file_text}, err:", e)
        return self.select_list        
    
    def get_radius(self,particles_in_row):
        start = 0.2
        for ii in range(600):
            rr =  start-ii*0.0005
            # If R is les then 0 we're done
            if rr <= 0:
                break
            # get diameter
            D = (2.0*rr)
            # how many particle fit in the 1.0 square cell
            subcell = 1.0/D
            # how long is this numebr of particles
            len_parts = subcell*D

            # if the len is greater than 1.0 then remove particles unit there is some space left
            while len_parts >= 1.0:
                len_parts -= D
            
            sep = 1.0-len_parts
            if sep < 0.1*rr:
                continue
            # What is the maximum number of particle that can fit
            in_row = round(len_parts/D)
            if in_row == particles_in_row:
                return rr
        return 0

    def open_selections_file(self):
        self.sel_file = open(self.itemcfg.selections_file_text,'w')
        self.sel_file.write("wx,wy,wz,dx,dy,dz,tot,sel,cols,sidelen,cdens,radius,vx,vy,vz,px,py,pz\n")
        
        number_particles = 117649
        particles_in_row = 2
        last_num_cells = 0
        old_side_len = 0
        rr = 0
        for cc in range(40):
            rr = self.get_radius(particles_in_row)
            if rr <= 0:
                break


            particles_in_cell = particles_in_row**3
            total_cells = round(number_particles/particles_in_cell)
            if last_num_cells == total_cells:
                particles_in_row += 2   
                continue
            else:
                last_num_cells = total_cells

            side_len = math.ceil(total_cells**(1/3))
            if old_side_len == side_len:
                particles_in_row += 2   
                continue
            else:
                old_side_len = side_len

            total_cells = side_len**3

        
            actual_num_particles = total_cells*particles_in_cell
            if actual_num_particles > number_particles:
                actual_num_particles = number_particles


            cell_dict = dict()
            cell_dict['particles_in_row'] = particles_in_row
            cell_dict['radius'] = rr
            cell_dict['particles_in_cell'] = particles_in_cell
            cell_dict['total_cells'] = total_cells
            cell_dict['side_len'] = side_len
            cell_dict['actual_num_particles'] = number_particles
            cell_dict['collision_density'] = 0.5
            tot_collisions = 0.5*number_particles
            cell_dict['tot_collisions'] = tot_collisions
            self.cell_items.append(cell_dict)
            self.add_item(particles_in_cell,side_len,rr,number_particles)
            particles_in_row += 2

        self.sel_file.flush()
        self.sel_file.close()


        try:
            with open(self.itemcfg.selections_file_text,"r",newline='') as csvfl:
                reader = csv.DictReader(csvfl, delimiter=',',dialect='excel')
                for row in reader:
                    if row["sel"] == 's':
                        self.select_list.append(row)
        except BaseException as e:
            self.log.log(self,f"Error opening:{self.itemcfg.selections_file_text}, err:", e)
        return self.select_list        
    
  
     
    def calulate_cell_properties(self,index,sel_dict=None):
        
        self.particles_in_cell = self.cell_items[index].get('particles_in_cell')
        self.particles_in_row = self.cell_items[index].get('particles_in_row')
        self.radius = self.cell_items[index].get('radius')
        self.tot_num_cells   = self.cell_items[index].get('total_cells')
        self.side_length = self.cell_items[index].get('side_len')
        self.number_particles = self.cell_items[index].get('actual_num_particles')
        self.collision_density = self.cell_items[index].get('collision_density')
        #self.tot_num_collsions = self.cell_items[index].get('tot_collisions')
        
        self.particles_in_row           = round(self.particles_in_cell**(1/3))
        self.particles_in_col           = self.particles_in_row
        self.particles_in_layers        = self.particles_in_row

        self.cell_occupancy_list_size   = int(self.particles_in_cell+10)
        self.num_collisions_per_cell    = int(self.particles_in_cell*self.collision_density)

        self.tot_num_collsions          = int(self.number_particles*self.collision_density)
        self.cell_x_len                 = self.side_length+1
        self.cell_y_len                 = self.side_length+1
        self.cell_z_len                 = self.side_length+1

        
        
        self.set_file_name = "{:03d}CollisionDataSet{:d}X{:d}X{:d}".format(index,self.number_particles,self.tot_num_collsions,self.side_length)
        self.test_file_name = self.cfg.data_dir + '/' + self.set_file_name + '.tst'
        self.test_bin_name = self.cfg.data_dir + '/' + self.set_file_name + '.bin'
        self.report_file = self.cfg.data_dir + '/' + self.set_file_name 

        self.log.log(self,f"Collsion Density: { self.collision_density},Number particles:{self.number_particles},Radius: {self.radius}")
        self.log.log(self,f"Particles in row: {self.particles_in_row}, Particles in Column: {self.particles_in_col}, Particles per cell: {self.particles_in_cell}")
        self.log.log(self,f"Cell array size: {self.cell_occupancy_list_size }")
        return 0
    
    def gen_data(self):
        self.gen_data_base()
        self.open_bin_file()
        
    def plot_particle_cell(self,file_name):
        self.plot_particle_cell_base(file_name)
    
   