

import struct
import ctypes
class collsion:
    def __init__(self):
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
   

        
    def set(self,pnum,rx,ry,rz,vx,vy,vz,radius,ptype,molar_mass,temp_vel,gas_const,vap_temp,attr_accel,rpls_accel,cmprs,plt_vec_flg):
        self.pnum = pnum
        self.rx = rx
        self.ry = ry
        self.rz = rz
        self.vx = vx
        self.cvx = 0.0
        self.vy = vy
        self.cvy = 0.0
        self.vz = vz
        self.cvz = 0.0
        self.vel_ang = 0.0
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
        self.collision_count = 0
        self.tot_collision_y_acc = 0.0
        self.tot_collision_x_acc = 0.0    
        self.wall_list = []
        
        for ii in range(4):
            self.wall_list.append('Any')
        
   
        


