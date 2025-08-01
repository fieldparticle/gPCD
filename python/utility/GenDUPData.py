
from BaseGenData import *

class GenDUPData(BaseGenData):

    def __init__(self):
        super().__init__()

    def gen_data(self):
        self.gen_data_base()
        
    def plot_particle_cell(self,file_name):
        self.plot_particle_cell_base(file_name)
    """
    def write_test_file(self,index,sel_dict):
        
        with open(self.test_file_name,'w') as f:
            fstr = f"index = {index};\n"     
            f.write(fstr)
            fstr = f"CellAryW = {self.cell_x_len+1};\n"     
            f.write(fstr)
            fstr = f"CellAryH = {self.cell_y_len+1};\n"     
            f.write(fstr)
            fstr = f"CellAryL = {self.cell_z_len+1};\n"     
            f.write(fstr)
            fstr = f"radius = {self.radius};\n"
            f.write(fstr)
            fstr = f"PartPerCell = {self.particles_in_space};\n"
            f.write(fstr)
            fstr = f"pcount = {self.number_particles};\n"
            f.write(fstr)
            fstr = f"colcount = {self.tot_num_collsions};\n"
            f.write(fstr)
            fstr = f"dataFile = \"{self.test_bin_name.replace('/','\\')}\";\n"
            f.write(fstr)
            fstr = f"aprFile = \"{ self.report_file.replace('/','\\')}\";\n"
            f.write(fstr)
            fstr = f"density = {float(sel_dict['cdens'])};\n"
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
            fstr = f"ColArySize = {64};\n"
            f.write(fstr)
        f.close()
    """

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
        if self.cfg.particle_enumeration_text == 'random':
            self.rand_data = self.gen_random_numbers_in_range(0, self.number_particles, self.number_particles)    
        
        ret = 0
        self.w_list = []
        self.particle_count = 0
        flg_col_rpt = False

        # If the collision_sel_text containes a file name then use it to generate 
        # collision_rpt_text,cell_ary_rpt_text,test_indexing_rpt_text to output diagnostics data
        # to compare with NSight
        if self.cfg.collision_sel_text in self.test_bin_name:
            flg_col_rpt = True
            fiel_name = f"{self.cfg.data_dir}/{self.cfg.collision_rpt_text}"
            col_file = open(fiel_name,'w')

        col_lst = []
        #self.add_null_particle(self.w_list)
        for zz in range(self.cell_z_len-1):
            progress_callback.emit(zz)
            for yy in range(self.cell_y_len-1):
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
        
        self.write_bin_file(self.w_list)
        if flg_col_rpt == True:
            for ii in col_lst:
                col_file.write(f"{ii[0]},{ii[1]}\n")
            col_file.close()
        
        return 0
        
        
                                    
        
    
