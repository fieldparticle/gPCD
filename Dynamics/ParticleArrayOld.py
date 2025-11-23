from particle import *
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6 import QtCore, QtWidgets
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
import time
from particle import *
from WallRayIntersect import *

class ParticleArray():

    def __init__(self,itemcfg):
        self.pary = []
        self.pnum = 0
        self.itemcfg = itemcfg
        self.wall_xmin = 0.0
        self.wall_xmax = 0.0
        self.wall_ymin = 0.0
        self.wall_ymax = 0.0

    def start(self):
        pnum = 0
        # do everything relative to 1 instead of actual values
       
        ptxt = f"p{pnum}"
        pop = True
        plot_vectors = self.itemcfg.plot_vectors
        while pop == True:
            if ptxt in self.itemcfg:
                if self.itemcfg.rel_one == True:
                    self.itemcfg[ptxt].molar_mass = 1.0
                    self.itemcfg[ptxt].temp_vel = 1.0
                    self.itemcfg[ptxt].attr_accel = 0.0
                    self.itemcfg[ptxt].rpls_accel = 1.0
                p = particle()
                p.set(pnum,
                    self.itemcfg[ptxt].rx,
                    self.itemcfg[ptxt].ry,
                    self.itemcfg[ptxt].rz,
                    self.itemcfg[ptxt].vx,
                    self.itemcfg[ptxt].vy,
                    self.itemcfg[ptxt].vz,
                    self.itemcfg[ptxt].radius,
                    self.itemcfg[ptxt].ptype,
                    self.itemcfg[ptxt].molar_mass,
                    self.itemcfg[ptxt].temp_vel,
                    self.itemcfg[ptxt].gas_const,
                    self.itemcfg[ptxt].vap_temp,
                    self.itemcfg[ptxt].attr_accel,
                    self.itemcfg[ptxt].rpls_accel,
                    self.itemcfg[ptxt].cmprs,
                    plot_vectors[pnum])
                self.add(p)
                pnum+=1
                ptxt = f"p{pnum}"
            else:
                pop = False
        self.addWalls()

  
    
    def addWalls(self):
        if "walls" in self.itemcfg:
            if self.itemcfg.walls == True:
                walls = self.itemcfg.wall_dim
                self.wall_xmin = walls[0]
                self.wall_xmax = walls[1]
                self.wall_ymin = walls[2]
                self.wall_ymax = walls[3]

    def add(self,p):
        p.pnum = self.pnum
        self.pary.append(p)
        self.pnum += 1

    def print_p(self):
        for ii in self.pary:
            print(f"#:{ii.pnum},radius:{ii.radius},rx:{ii.rx},ry:{ii.ry},rz:{ii.rz},rx:{ii.rx},vx:{ii.rx},vy:{ii.rx},vz:{ii.rx}")

    def do_iteration(self):
        for src in range(len(self.pary)):
            self.pary[src].collision_list.clear()
            for trg in range(len(self.pary)):
                if src != trg:
                    # Is there a collsion between src and target
                    if (self.check_collision(src,trg) == True):
                        # Set the collision flag as true so the vectors will plot
                        self.pary[src].col_flag = True
                        # Create a new collision structure
                        new_col = collsion()
                        new_col.psource = src
                        new_col.ptarget = trg
                        new_col.col_flag = True
                        # Save off the current velocity magnitudes 
                        # to enuse the momentum is conserved in self.move(..)
                        self.pary[src].cvx = abs(self.pary[src].vx)
                        self.pary[src].cvy = abs(self.pary[src].vy)
                        self.process_collision(self.pary[src],self.pary[trg],new_col)
            self.check_wall_collision(src)
            self.calculate_collision_acceleration(src)

    def find_collsion_item(seld,col_struct,target):
        for cc in range(len(col_struct)):
            if col_struct[cc].ptarget == target:
                return cc
        return -1


    
    
    def check_collision(self,ii,jj):
        col_flg = False
        dsq = ((self.pary[ii].rx-self.pary[jj].rx)**2+(self.pary[ii].ry-self.pary[jj].ry)**2+(self.pary[ii].rz-self.pary[jj].rz)**2)
        rsq = (self.pary[ii].radius + self.pary[jj].radius)**2
        #print(f"dsq:{dsq},rsq:{rsq}")
        if (dsq<rsq):
            col_flg = True
        return col_flg

    def process_collision(self,src,trg,col_struct):
        
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
            # Vector from center opf particle
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
            r1 =abs(src.radius - ol)
            # Subtract from ol
            col_struct.prox_len = src.radius-2*r1
            # Convert to origin vector to get angle.
            ovec2 = self.origin_vector([src.rx,O1],[src.ry,O2])
            # Get orietn vector 360 degree angle.
            col_struct.orient_ang = atan360(ovec2[0],ovec2[1],0.0)
            proxvec = [[src.rx,col_struct.prox_len*np.cos(col_struct.orient_ang)+src.rx], 
                       [src.ry,col_struct.prox_len*np.sin(col_struct.orient_ang)+src.ry]]
            col_struct.prox_vec = proxvec
            col_struct.pen_factor = (1.0-col_struct.prox_len/src.radius)
            #self.pary[src].pen_factor = (self.pary[src].prox_len/self.pary[src].radius)
            src.collision_list.append(col_struct)
            return True
            

        except BaseException as e:
            print(e)
        return False

    def calculate_collision_acceleration(self,pnum):
        for ii in self.pary:
            ii.tot_collision_x_acc = 0.0
            ii.tot_collision_y_acc = 0.0
            #print(f"P{ii.pnum} Oritent angle {ii.or}")
            for cc in ii.collision_list:
                pf = ii.cmprs*cc.pen_factor
                vmag = pf*ii.temp_vel
                ii.tot_collision_x_acc = ii.tot_collision_x_acc-vmag*math.cos(cc.orient_ang)
                ii.tot_collision_y_acc = ii.tot_collision_y_acc-vmag*math.sin(cc.orient_ang)
    
    def move(self):
        for ii in self.pary:
            
            ii.vx = ii.vx + ii.tot_collision_x_acc
            ii.vy = ii.vy + ii.tot_collision_y_acc
            ii.vel_ang = atan360(ii.vx,ii.vy,0.0)
            
            if ii.col_flag == True:
                mag_cv = self.vmag(ii.cvx,ii.cvy)
                mag_v = self.vmag(ii.vx,ii.vy)
                #if mag_v != mag_cv:
                    #ii.vx = mag_cv*math.cos(ii.vel_ang)   
                    #ii.vy = mag_cv*math.sin(ii.vel_ang) 
                ii.col_flag = False  
                #print(f"mag.vx{self.vmag(ii.vx,ii.vy)}")
                #print(f"mag.cvx{self.vmag(ii.cvx,ii.cvy)}")
            
            ii.rx = ii.rx+ii.vx*self.itemcfg.dt
            ii.ry = ii.ry+ii.vy*self.itemcfg.dt
            ii.tot_collision_x_acc = 0.0
            ii.tot_collision_y_acc = 0.0
            
            if len(ii.collision_list) > 0:
                ii.collision_list.clear()
            ii.vel_vec = [[ii.rx,ii.rx+ii.vx*ii.radius],[ii.ry,ii.ry+ii.vy*ii.radius]]   
        
            
            
##############################################################################################
    # Check for wall collsions
    #
    #
    #
    ##############################################################################################
    def check_wall_collision(self,ii):
        # ---------------------East Wall ---------------------------------------------------------
        if self.pary[ii].rx > self.wall_xmax-self.pary[ii].radius:

            # If this is the start of a collsion 
            if self.pary[ii].wcol_flag[0]  == False:
                self.pary[ii].cvx = abs(self.pary[ii].vx)
                self.pary[ii].cvy = abs(self.pary[ii].vy)
                # Center point of particle
                P = (self.pary[ii].rx, self.pary[ii].ry)
                # unit vector pointing in the direction of the wall
                v = (1, 0)
                # A point in the wall
                A = (self.itemcfg.wall_dim[1], self.itemcfg.wall_dim[3])
                # Direction of wall
                d = (0, 1)
                t,s,ipoint = intersect_ray_line_2d(P, v, A, d)
                #print(f"t:{t},s:{s},ipoint:{ipoint}")
                faux_center = P+2*t*np.array(v)
                # Create a pseudo particle
                wp = particle()
                wp.make_copy(self.pary[ii])
                wp.rx = faux_center[0]
                wp.ry = faux_center[1]
                wp.vx = 0.0
                wp.vy = 0.0
                self.pary[ii].wall_list[0]= wp
                self.pary[ii].wcol_flag[0] = True
                return True
            # If already in collsion
            else:
                wall_col = collsion()
                self.process_collision(self.pary[ii],self.pary[ii].wall_list[0],wall_col)
                return True
        # If out of collision clear collsion flag
        elif self.pary[ii].wcol_flag[0]  == True:
            self.pary[ii].wcol_flag[0] = False
            return False
                
        # West Wall ###############################################
        if self.pary[ii].rx < self.wall_xmin+self.pary[ii].radius:
            if self.pary[ii].wcol_flag[1]  == False:
                self.pary[ii].cvx = abs(self.pary[ii].vx)
                self.pary[ii].cvy = abs(self.pary[ii].vy)
                # Center point of particle
                P = (self.pary[ii].rx, self.pary[ii].ry)
                # unit vector pointing in the direction of the wall
                v = (-1, 0)
                # A point in the wall
                A = (self.itemcfg.wall_dim[0], self.itemcfg.wall_dim[3])
                # Direction of wall
                d = (0, 1)
                t,s,ipoint = intersect_ray_line_2d(P, v, A, d)
                #print(f"t:{t},s:{s},ipoint:{ipoint}")
                faux_center = P+2*t*np.array(v)
                # Create a pseudo particle
                wp = particle()
                wp.make_copy(self.pary[ii])
                wp.rx = faux_center[0]
                wp.ry = faux_center[1]
                wp.vx = 0.0
                wp.vy = 0.0
                self.pary[ii].wall_list[1] = wp
                self.pary[ii].wcol_flag[1] = True
                return True
            else:
                wall_col = collsion()
                self.process_collision(self.pary[ii],self.pary[ii].wall_list[1],wall_col)
                return True
        elif self.pary[ii].wcol_flag[1]  == True:
            self.pary[ii].wcol_flag[1] = False
            return False
    
        # Top Wall ###############################################
        if self.pary[ii].ry > self.wall_ymax-self.pary[ii].radius:
            if self.pary[ii].wcol_flag[2]  == False:

                self.pary[ii].cvx = abs(self.pary[ii].vx)
                self.pary[ii].cvy = abs(self.pary[ii].vy)
                P = (self.pary[ii].rx, self.pary[ii].ry)
                v = (0, 1)
                A = (self.itemcfg.wall_dim[1], self.itemcfg.wall_dim[3])
                d = (1, 0)
                t,s,ipoint = intersect_ray_line_2d(P, v, A, d)
                #print(f"t:{t},s:{s},ipoint:{ipoint}")
                faux_center = P+2*t*np.array(v)
                # Create a pseudo particle
                wp = particle()
                wp.make_copy(self.pary[ii])
                wp.rx = faux_center[0]
                wp.ry = faux_center[1]
                wp.vx = 0.0
                wp.vy = 0.0
                self.pary[ii].wall_list[2] = wp
                self.pary[ii].wcol_flag[2] = True
            else:
                wall_col = collsion()
                self.process_collision(self.pary[ii],self.pary[ii].wall_list[2],wall_col)
                return True
        elif self.pary[ii].wcol_flag[2]  == True:
            self.pary[ii].wcol_flag[2] = False
            return False
      
        # Bottom Wall ###############################################
        if self.pary[ii].ry < self.wall_ymin+self.pary[ii].radius:
            if self.pary[ii].wcol_flag[3]  == False:
                self.pary[ii].cvx = abs(self.pary[ii].vx)
                self.pary[ii].cvy = abs(self.pary[ii].vy)
                  # Center point of particle
                P = (self.pary[ii].rx, self.pary[ii].ry)
                # unit vector pointing in the direction of the wall
                v = (0, -1)
                # A point in the wall
                A = (self.itemcfg.wall_dim[1], self.itemcfg.wall_dim[2])
                # Direction of wall
                d = (1, 0)
                t,s,ipoint = intersect_ray_line_2d(P, v, A, d)
                #print(f"t:{t},s:{s},ipoint:{ipoint}")
                faux_center = P+2*t*np.array(v)
                # Create a pseudo particle
                wp = particle()
                wp.make_copy(self.pary[ii])
                wp.rx = faux_center[0]
                wp.ry = faux_center[1]
                wp.vx = 0.0
                wp.vy = 0.0
                self.pary[ii].wall_list[3] = wp
                self.pary[ii].wcol_flag[3] = True
            else:
                wall_col = collsion()
                self.process_collision(self.pary[ii],self.pary[ii].wall_list[3],wall_col)
                return True
        elif self.pary[ii].wcol_flag[3]  == True:
            self.pary[ii].wcol_flag[3] = False
            return False
        
        return False
