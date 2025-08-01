
from BaseGenData import *

class GenPQBRodsData(BaseGenData):

    num_rods = 0
    num_parts_per_rod = 0
    cur_rod = 0
    arrange_type = 0
    def __init__(self):
        super().__init__()

    def gen_data(self):
        self.gen_data_base()
        
    def plot_particle_cell(self,file_name):
        self.plot_particle_cell_base(file_name)
   
    def place_rod_round(self,xx,yy,zz,w_list):

        
        num_parts = int(self.px)
        num_layers = int(self.pz)
        dia = 2*self.radius
        min_C = num_parts * dia
        min_R = (min_C/(2.0*math.pi))*0.91
        del_theta = min_C/dia
        #print(f"sector:{S},circum:{C},R:{R},dS:{del_theta}")
        #theta = 0 + np.arange(0, 8) * del_theta
        theta = np.linspace(0, 2.0*math.pi,int(del_theta))
        
        x = min_R * np.cos(theta)
        y = min_R * np.sin(theta)
        
        for layer in range(num_layers):    
            for p in range(num_parts):
                particle_struct = pdata()
                particle_struct.ptype = 0
                particle_struct.radius = self.radius
                particle_struct.rnum = 1
                particle_struct.rx = 1.0 + x[p]
                particle_struct.ry = 1.0 + y[p]
                #print(f"{x[ang]:.2f}:{y[ang]:.2f}")
                particle_struct.rz = layer*2.0*self.radius
                w_list.append(particle_struct)


        return 0
    
    


    def place_rod_square(self,xx,yy,zz,w_list):
        for row in range(self.px):
            for col in range(self.py):
                for layer in range(self.pz):
                    particle_struct = pdata()
                    particle_struct.ptype = 0
                    particle_struct.radius = self.radius
                    particle_struct.rnum = 1
                    particle_struct.rx = 0.5 + xx + self.radius + row*2*self.radius
                    particle_struct.ry = 0.5 + yy + self.radius + col*2*self.radius
                    particle_struct.rz = 0.5 + zz + self.radius + layer*2*self.radius
                    w_list.append(particle_struct)

        return 0
    
    def do_cells(self,progress_callback):
          
        
        self.num_rods = int(self.cfg.number_rods_text)
        self.num_parts_per_rod = int(self.cfg.number_parts_per_rod_text)
        self.rows = self.cols = self.layers = math.ceil(self.num_parts_per_rod/2)
        self.max_cell_location = [0,0,0]

        # Put one rod in the center of each cell
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
                    if self.arrange_type == 1:
                        self.place_rod_square(xx,yy,zz,self.w_list)  
                    elif self.arrange_type == 2:
                        self.place_rod_round(xx,yy,zz,self.w_list)  
                    self.write_bin_file(self.w_list)
                    self.w_list.clear()
                    return


        return 0
        
        
    def calulate_cell_properties(self,index,sel_dict):
        try :
            self.collision_density      = float(sel_dict['cdens'])
            self.number_particles       =  int(sel_dict['tot'])
            self.radius                 = float(sel_dict['radius'])
            self.sepdist                =  float(self.cfg.particle_separation_text)
            self.px                     = int(sel_dict['px'])
            self.py                     = int(sel_dict['py'])
            self.pz                     = int(sel_dict['pz'])
        except BaseException as e:
            self.log.log(self,f"Key error in record:",e)

        self.arrange = self.cfg.arrangement_text
        if 'square' in self.arrange:
            self.arrange_type = 1
        elif 'round' in self.arrange:
            self.arrange_type = 2

        self.side_length = 5
        self.side_length_count          = self.side_length+1
        self.cell_x_len                 = self.side_length
        self.cell_y_len                 = self.side_length
        self.cell_z_len                 = self.side_length
        self.tot_num_collsions = 0
        self.set_file_name = "{:03d}CollisionDataSet{:d}X{:d}X{:d}".format(index,self.number_particles,self.tot_num_collsions,self.side_length)
        self.test_file_name = self.cfg.data_dir + '/' + self.set_file_name + '.tst'
        self.test_bin_name = self.cfg.data_dir + '/' + self.set_file_name + '.bin'
        self.report_file = self.cfg.data_dir + '/' + self.set_file_name 

        
        return 0
                                    
        
    
