from BaseGenData import *

class GenCFBData(BaseGenData):

    last_max_scale = 0
    last_min_scale = 0
    old_rx = 0.0
    old_ry = 0.0
    old_rz = 0.0
    do_max_scale = True
    switch_col = True
    def __init__(self):
        super().__init__()



    def gen_data(self):
        self.gen_data_base()
        
    def plot_particle_cell(self,file_name):
        self.plot_particle_cell_base(file_name)
    
    
   
        