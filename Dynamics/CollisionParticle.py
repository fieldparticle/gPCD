from particle import *
import math
from termcolor import colored
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6 import QtCore, QtWidgets
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
import time
from particle import *

from Utility import *
from CollisionParticle import *
from vectors import *

class CollisionParticle():
    def __init__(self,itemcfg,parent):
        self.pnum = 0
        self.itemcfg = itemcfg
        self.parent = parent


    def findTarget(self,pary,src,trg):
        for cc in self.pary[src].collision_list:
            if trg == cc.trg and cc.col_flag != False:
                return cc.col_num
           
        return -1

    def get_new(self,pary,src,trg):
        for cc in self.pary[src].collision_list:
            if trg != cc.trg and cc.col_flag == False:
                return cc.col_num
            
        return -1
    
    def ParticleCollision(self,pary,src,trg):
        new_flg = False
        next_slot = -1
        nextcc = None
        self.pary = pary
        
        # Check for a collsion between src and target
        if (self.check_collision(self.pary,src,trg) == True):
            cc = self.findTarget(self.pary,src,trg)
            if cc != -1:
                #print(self.pary[src].molar_mass)
                '''
                vo1,yo1 = predict_mom( self.pary[src].molar_mass,
                                        self.pary[src].vx,
                                        self.pary[src].vy,
                                        self.pary[trg].molar_mass,
                                        self.pary[trg].vx,
                                        self.pary[trg].vy)
                '''
                vo1,yo1 = predict_mom( self.pary[trg].molar_mass,
                                        self.pary[trg].vx,
                                        self.pary[trg].vy,
                                        self.pary[src].molar_mass,
                                        self.pary[src].vx,
                                        self.pary[src].vy)
                
                self.pary[src].collision_list[cc].pred_mom_xout = vo1
                self.pary[src].collision_list[cc].pred_mom_yout = yo1
                self.pary[src].collision_list[cc].pred_mom_mag= np.linalg.norm([vo1,yo1])
                self.get_orient_prox_vec(self.pary[src],self.pary[trg],self.pary[src].collision_list[cc])
                self.pary[src].col_flag = COLL_IN
                self.pary[src].collision_list[cc].col_iter+=1
                return True
            else:
                new_cc = self.get_new(pary,src,trg)
                print(f"SRC:{src} TRG:{trg} - New Coll:{new_cc}")
                self.new_coll(pary,src,trg,self.pary[src].collision_list[new_cc])
                self.pary[src].col_flag = COLL_IN
                
                return True
        # We are out of this collision    
        else:
            for cc in self.pary[src].collision_list:
                #cc.remain_mom = 0.0
                if cc.trg == trg and cc.col_flag == True:
                    self.pary[src].num_colls -= 1
                    cc.remain_mom = cc.vel_mag_in-self.pary[src].vel_mag
                    if src == 0:
                        print(colored(f"P:{self.pary[src].pnum} C: {cc.col_num} citr:{cc.col_iter} cc.tot_area:{cc.tot_area},remain:{cc.remain_mom}",'red'))
                    
                    #print(f"Out Coll P:{src} C:{cc.col_num} - ReaminMom:{cc.remain_mom}")
                    cc.col_flag = False        
                    cc.trg = -1

                    return False
        
        return False
    
    def new_coll(self,pary,src,trg,cc):
            cc.col_flag = True
            self.pary[src].num_colls+=1
            self.pary[src].tot_colls = self.pary[src].num_colls
            # Start a new collision - collision sturtures persist until they are out.
            cc.trg = trg
            #nextcc.col_num = 1
            # Remember the incoming velocity magnitude
            cc.vel_mag_in = np.linalg.norm([self.pary[src].vx,self.pary[src].vy])
            # Record vel_mag_in in the particle for storing and reporting
            #print(nextcc.vel_mag_in)
            self.pary[src].vel_mag_in = cc.vel_mag_in
            # Predict resulting momentum to ensure it all is returned after the collision
            vo1,yo1 = predict_mom( self.pary[src].molar_mass,
                                        self.pary[src].vx,
                                        self.pary[src].vy,
                                        self.pary[trg].molar_mass,
                                        self.pary[trg].vx,
                                        self.pary[trg].vy)
            self.pary[src].mom_per_u_area = cc.vel_mag_in/(math.pi*self.pary[src].radius**2)
            cc.vx_rel = self.pary[src].vx-self.pary[trg].vx
            cc.vy_rel = self.pary[src].vy-self.pary[trg].vy
            cc.v_rel = np.linalg.norm([cc.vx_rel,cc.vy_rel])
            cc.vel_mag_per_area = cc.v_rel/(math.pi*(self.pary[src].radius**2))
            cc.pred_mom_xout = vo1
            cc.pred_mom_yout = yo1
            self.pary[src].pred_mom_mag = np.linalg.norm([vo1,yo1])
            self.get_orient_prox_vec(self.pary[src],self.pary[trg],cc)
            cc.orient_ang_in = cc.orient_ang
            cc.col_iter = 0
            return True

    ##################################################################
    #
    # Do collsion test
    #
    ##################################################################
    def check_collision(self,pary,ii,jj):
        self.pary = pary
        col_flg = False
        dsq = ((self.pary[ii].rx-self.pary[jj].rx)**2+(self.pary[ii].ry-self.pary[jj].ry)**2+(self.pary[ii].rz-self.pary[jj].rz)**2)
        rsq = (self.pary[ii].radius + self.pary[jj].radius)**2
        #print(f"dsq:{dsq},rsq:{rsq}")
        if (dsq<rsq):

            return True
        return False
    
    import math

    def particle_contact(self,x1, y1, x2, y2, R,pnum):

        dx = x2 - x1
        dy = y2 - y1

        d2 = dx*dx + dy*dy
        d  = math.sqrt(d2)

        if d >= 2*R:
            return None   # no contact

        # contact normal
        nx = dx / d
        ny = dy / d

        # contact angle (line between particle centers)
        alpha = math.atan2(dy, dx)
        alpha = (math.atan2(dy, dx) + 2*math.pi) % (2*math.pi)


        # penetration
        delta = 2*R - d

        proxPercent = 1.0-(delta)/R
       # if pnum == 0:
       #     print(f"ProxPercent:{proxPercent}")
        # overlap area
        x = d/(2*R)
        x = max(-1.0, min(1.0, x))

        theta = 2*math.acos(x)

        area = R*R*(theta - math.sin(theta))
        tot_area = math.pi*R**2
        area_pcnt = (area/tot_area)
        #print(area_pcnt)
        return nx, ny, alpha, delta, area, area_pcnt


    ##################################################################
    #
    # Get orient, proximity vectors and depth of penetration
    #
    ##################################################################
    def get_orient_prox_vec(self,src,trg,col_struct):
        col_struct.prev_area = col_struct.cur_area
        
        nx, ny, alpha, delta, area, area_pcnt = self.particle_contact(src.rx, src.ry, trg.rx, trg.ry, src.radius,src.pnum)
        col_struct.cur_area = area
        try:
            A = np.array((src.rx, src.ry))
            B = np.array((trg.rx, trg.ry))
            c =  np.linalg.norm(A-B)
            a = src.radius
            b = trg.radius
            cosAlpha = (b**2+c**2-a**2)/(2*b*c)
            # Unit vector pointing to centers
            u_AB = (B - A)/c
            # Normal vector
            pu_AB = np.array((u_AB[1], -u_AB[0])); 
            r = ((1-cosAlpha**2))
            #print(r)
            if r < 0.0:
                return False
            # The intersection points.
            col_struct.col_pointA = A + u_AB * (b*cosAlpha) + pu_AB * (b*np.sqrt(1-cosAlpha**2))
            col_struct.col_pointB = A + u_AB * (b*cosAlpha) - pu_AB * (b*np.sqrt(1-cosAlpha**2))
            
            # Vector from center of particle
            col_struct.isec_vect = [[src.rx,col_struct.col_pointA[0]],
                                [src.ry,col_struct.col_pointA[0]]]
            # Bisector of line between intersection points
            O1 = (col_struct.col_pointA[0]+col_struct.col_pointB[0])/2.0
            O2 = (col_struct.col_pointA[1]+col_struct.col_pointB[1])/2.0
            
            # Print orientation vector from center of particle to bisector
            col_struct.orient_vec_print = [[src.rx,O1],[src.ry,O2]]
            
            # Orient vector
            col_struct.orient_vec = np.array([[src.rx,src.ry],[O1,O2]])
             # Get length of orient vector.
            ol =  np.linalg.norm(col_struct.orient_vec) # this does not work
            ol1 = (src.rx-O1)**2
            ol2 = (src.ry-O2)**2
            ol = np.sqrt(ol1+ol2)
            # Find r1 
            r1 = abs(src.radius - ol)
            # Subtract from ol
            col_struct.prox_len = src.radius-2*r1
            #if src.pnum == 0:
             #   print(f"prox_len:{col_struct.prox_len}")
            # Convert to origin vector to get angle.
            ovec2 = origin_vector([src.rx,O1],[src.ry,O2])
            # Get orietn vector 360 degree angle.
            col_struct.orient_ang = atan360(ovec2[0],ovec2[1],0.0)
            proxvec = [[src.rx,col_struct.prox_len*np.cos(col_struct.orient_ang)+src.rx], 
                       [src.ry,col_struct.prox_len*np.sin(col_struct.orient_ang)+src.ry]]
            col_struct.prox_vec = proxvec
            col_struct.pen_factor = (1.0-col_struct.prox_len/src.radius)
            col_struct.pen_factor = area_pcnt
            
            return True
        except BaseException as e:
            print(f"get_orient_prox_vec:{e}")
        return False
