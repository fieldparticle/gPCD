import numpy as np

import struct
import ctypes
import math
from collision import *
COLL_IN = 1
COLL_OUT = 2
COLL_NONE = 3

class particle():

    def __init__(self):
        pass        
     
    def set(self,pnum,rx,ry,rz,vx,vy,vz,radius,ptype,molar_mass,temp_vel,gas_const,vap_temp,attr_accel,rpls_accel,in_col_fac,cmprs,plt_vec_flg):
        self.pnum = pnum
        self.rx = rx
        self.ry = ry
        self.rz = rz
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.vel_mag = 0.0
        self.vel_ang = 0.0
        self.m_vx = 0.0
        self.residue = 0.0
        self.radius  = radius
        self.bond_rad = radius/2.0
        self.vel_vec = [[self.rx,self.rx+self.vx*self.radius],[self.ry,self.ry+self.vy*self.radius]]   
        self.ptype = ptype
        self.molar_mass = 1.0 #molar_mass
        self.temp_vel = temp_vel
        self.vap_temp = vap_temp
        self.gas_const = gas_const
        self.internal_mom = 0.0
        self.initial_mag =  np.linalg.norm([vx,vy])
        self.cmprs = cmprs
        self.col_flag = COLL_NONE
        self.wcol_flag = [False,False,False,False]
        self.plot_vectors = plt_vec_flg
        self.wall_list = []
        self.pred_mom_mag = 0.0
        # A list of collsion
        self.num_colls = 0
        self.tot_colls = 0
        self.vel_mag_in = 0.0
        
        self.bond_ang = 0.0

        self.angle_acc_x = 0.0
        self.angle_acc_y = 0.0
        self.dTheta = 0.0
        self.ang_mom = 0.0
        self.ang_vel = 0.0
        self.prev_vel_ang = 0.0
        self.moment_inertia = 0.5*self.molar_mass*self.radius**2
        
        self.mom_per_u_area = 0.0
        self.time_in_collison_factor = in_col_fac
        # Add 4 collsions - we assume a particle can have no more tahn 4
        self.collision_list = []
        for ii in range(4):
            c = collision()
            c.col_flag == False
            c.col_num = ii
            self.collision_list.append(c)

        self.attr = attr_accel

        self.repl = []
        self.repl = rpls_accel
        
        
        self.stor_t     = []
        self.stor_vx    = []
        self.stor_vy    = []
        self.stor_v_mag = []
        self.stor_v_ang = []
        self.num_cols = 0
        self.stor_vel_mag_in = []
        self.stor_pnum = []
        self.stor_col_count = []
        self.stor_internal_mom = []
        self.stor_attr = []
        self.stor_v_rel = []
        self.stor_vx_rel = []
        self.stor_vy_rel = []
        self.stor_iter = []
        for ii in range(4):
            self.wall_list.append('Any')
        
   
        


