

import struct
import ctypes


class particle():

    def __init__(self):
        self.pnum = 0
        self.rx = 0.0
        self.ry = 0.0
        self.rz = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.r  = 0.0
        self.ptype = 0.0
        self.molar_mass = 0.0
        self.temp_vel = 0.0

   
    
    def set(self,rx,ry,rz,vx,vy,vz,radius,ptype,molar_mass,temp_vel,gas_const,vap_temp,attr_accel,rpls_accel,cmprs,plt_vec_flg):
        self.rx = rx
        self.ry = ry
        self.rz = rz
        self.vx = vx
        self.mvx = 0.0
        self.vy = vy
        self.vz = vz
        self.radius  = radius
        self.ptype = ptype
        self.molar_mass = molar_mass
        self.temp_vel = temp_vel
        self.vap_temp = vap_temp
        self.gas_const = gas_const
        self.attr_accel = attr_accel
        self.rpls_accel = rpls_accel
        self.cmprs = cmprs
        self.col_flag = False
        self.col_pointA = None
        self.col_pointB = None
        self.isec_vect = []
        self.orient_vec_print = []
        self.orient_vec = []
        self.orient_ang = 0.0
        self.prox_len = 0.0
        self.prox_vec = []
        self.plot_vectors = plt_vec_flg
        self.pen_factor =0.0
