

import struct
import ctypes
class collision:
    def __init__(self):
        self.psource = 0
        self.ptarget = 0
        self.vdiff = 0.0
        self.col_flag = False
        self.col_phase = 0 # 0 no collsion, 1 in collsions, 2 out of collsion
        self.col_pointA = None
        self.col_pointB = None
        self.isec_vect = []
        self.orient_vec_print = []
        self.orient_vec = []
        self.orient_ang = 0.0
        self.prox_len = 0.0
        self.prox_vec = []
        self.pen_factor =0.0
        self.wall_x = 0
        self.wall_y = 0
        self.srcvx = 0.0
        self.srcvy = 0.0
        self.trgvx = 0.0
        self.trgvy = 0.0
        self.AComp = 0.0
        self.BComp = 0.0
        self.vel_ang = 0.0
        self.vx_rel = 0.0
        self.vy_rel = 0.0
        self.v_rel = 0.0
        
        


class particle():

    def __init__(self):
        pass        

   
    def make_copy(self,pobj):
        self.pnum = pobj.pnum
        self.rx = pobj.rx
        self.ry = pobj.ry
        self.rz = pobj.rz
        self.vx = pobj.vx
        self.cvx = 0.0
        self.vy = pobj.vy
        self.cvy = 0.0
        self.vz = pobj.vz
        self.cvz = 0.0
        self.vel_ang = 0.0
        self.radius  = pobj.radius
        self.vel_vec = [[self.rx,self.rx+self.vx*self.radius],[self.ry,self.ry+self.vy*self.radius]]   
        self.ptype = pobj.ptype
        self.molar_mass = pobj.molar_mass
        self.temp_vel = pobj.temp_vel
        self.vap_temp = pobj.vap_temp
        self.gas_const = pobj.gas_const
        self.attr_accel = pobj.attr_accel
        self.rpls_accel = pobj.rpls_accel
        self.cmprs = pobj.cmprs
        self.col_flag = False
        self.wcol_flag = False
        self.plot_vectors = False
        self.collision_list = []
        self.collision_count = 0
        self.tot_collision_y_acc = 0.0
        self.tot_collision_x_acc = 0.0    
        self.wall_list = []
        self.stor_vx_rel = []
   

        
    def set(self,pnum,rx,ry,rz,vx,vy,vz,radius,ptype,molar_mass,temp_vel,gas_const,vap_temp,attr_accel,rpls_accel,cmprs,plt_vec_flg):
        self.pnum = pnum
        self.rx = rx
        self.ry = ry
        self.rz = rz
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.vel_mag = 0.0
        self.vel_ang = 0.0
        self.post_coll_mag = 0.0
        self.radius  = radius
        self.vel_vec = [[self.rx,self.rx+self.vx*self.radius],[self.ry,self.ry+self.vy*self.radius]]   
        self.ptype = ptype
        self.molar_mass = molar_mass
        self.temp_vel = temp_vel
        self.vap_temp = vap_temp
        self.gas_const = gas_const
        self.attr_accel = attr_accel
        self.rpls_accel = rpls_accel
        self.cmprs = cmprs
        self.col_flag = False
        self.wcol_flag = [False,False,False,False]
        self.plot_vectors = plt_vec_flg
        self.collision_list = []
        self.collision_flags = []
        self.collision_count = 0
        self.tot_collision_y_acc = 0.0
        self.tot_collision_x_acc = 0.0    
        self.wall_list = []

        # A list of collsion
        self.col_flag = False
        self.cvmag = 0.0
        # Store the incoming velocity to a collsions
        self.cvx_rel = 0.0
        self.cvy = 0.0
        self.cvz = 0.0
        self.pred_mom_xout = 0.0
        self.pred_mom_yout = 0.0

        # Storage variables
        self.stor_t     = []
        self.stor_vx    = []
        self.stor_vy    = []
        self.stor_v_mag = []
        self.stor_v_ang = []
        self.stor_cvmag = []
        self.stor_pen_factor = []
        self.stor_vx_rel = []
        self.stor_tot_collision_x_acc = []
        self.stor_tot_collision_y_acc = []
        self.stor_pnum = []
        self.stor_pred_mom_xout = []
        self.stor_pred_mom_yout = []

        for ii in range(4):
            self.wall_list.append('Any')
        
   
        


