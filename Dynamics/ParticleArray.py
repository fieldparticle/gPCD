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
from Utility import *

class ParticleArray():

    
    ##################################################################
    #
    # Main loop
    #
    ##################################################################
    def do_iteration(self):
        col_num = 0
        # For each particle
        for src in range(len(self.pary)):
            # Clear src particle collison array
            self.pary[src].collision_list.clear()
            # Run thorugh all other target particles 
            for trg in range(len(self.pary)):
                # If source not equal to target particle.    
                if src != trg:
                    # Check for a collsion between src and target
                    if (self.check_collision(src,trg) == True):
                        #------------------------------------
                        # If this is a NEW collsion
                        #------------------------------------
                        if(self.pary[src].col_flag == False):    
                            self.pary[src].col_flag = True
                            # Remember the incoming velocity magnitude
                            self.pary[src].cvmag = 0.75 
                            vo1,yo1 = self.predict_mom( self.pary[src].molar_mass,
                                                        self.pary[src].vx,
                                                        self.pary[src].vy,
                                                        self.pary[trg].molar_mass,
                                                        self.pary[trg].vx,
                                                        self.pary[trg].vy)
                            self.pary[src].pred_mom_xout = vo1
                            self.pary[src].pred_mom_yout = yo1
                        # If there is a collision create a new struct for
                        # each target particle
                        col_struct = collision()
                        # Get intersection, orient and prox vectors. And
                        # DOP (Depth of Penetration factor)
                        self.get_orient_prox_vec(self.pary[src],self.pary[trg],col_struct)
                        # Add the collision structure to the src particles container
                        self.pary[src].collision_list.append(col_struct)
                         # Iterate thorugh the collisions and calulate collision accelerations
                        self.calculate_collision_acceleration(src)
                    else:
                         if(self.pary[src].col_flag == True):
                             self.pary[src].col_flag = False
                             self.pary[src].vx = self.pary[src].pred_mom_xout
                             self.pary[src].vy = self.pary[src].pred_mom_yout
   
    ##################################################################
    #
    # Calulate the change in acceleration due to collisionm
    #
    ##################################################################
    def calculate_collision_acceleration(self,pnum):
        for cc in self.pary[pnum].collision_list:
            #print(f"v_comp:{v_comp}, temp_vel:{self.pary[pnum].temp_vel}")
            pf = cc.pen_factor
            v_coll =(pf*(self.pary[pnum].cvmag))
            self.pary[pnum].tot_collision_x_acc = -(v_coll)*math.cos(cc.orient_ang)
            self.pary[pnum].tot_collision_y_acc = -(v_coll)*math.sin(cc.orient_ang)
            


    ##################################################################
    #
    # Move particles
    #
    ##################################################################
    def move(self):

        for ii in self.pary:
            self.set_storage_variables(ii)
            # Add collision acceleration vectors to velcoity vectors
            ii.vx = ii.vx + ii.tot_collision_x_acc
            ii.vy = ii.vy + ii.tot_collision_y_acc

            #print( ii.tot_collision_x_acc)

            #ii.vx*(1-ii.cvx_rel)
                

            # Get the new angle
            ii.vel_ang = atan360(ii.vx,ii.vy,0.0)
            ii.vel_mag = np.linalg.norm([ii.vx,ii.vy])
                        
            # Move the particles
            ii.rx = ii.rx+ii.vx*self.itemcfg.dt
            ii.ry = ii.ry+ii.vy*self.itemcfg.dt

            # Clear everything
            ii.tot_collision_x_acc = 0.0
            ii.tot_collision_y_acc = 0.0
            if len(ii.collision_list) > 0:
                ii.collision_list.clear()

            # Make a velocity vector for plotting
            ii.vel_vec = [[ii.rx,ii.rx+ii.vx*ii.radius],[ii.ry,ii.ry+ii.vy*ii.radius]]   
   

    ##################################################################
    #
    # Do collsion test
    #
    ##################################################################
    def check_collision(self,ii,jj):
        col_flg = False
        dsq = ((self.pary[ii].rx-self.pary[jj].rx)**2+(self.pary[ii].ry-self.pary[jj].ry)**2+(self.pary[ii].rz-self.pary[jj].rz)**2)
        rsq = (self.pary[ii].radius + self.pary[jj].radius)**2
        #print(f"dsq:{dsq},rsq:{rsq}")
        if (dsq<rsq):
            return True
        return False
    ##################################################################
    #
    # Get orient, proximity vectors and depth of penetration
    #
    ##################################################################
    def get_orient_prox_vec(self,src,trg,col_struct):
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
            #col_struct.pen_factor = (src.prox_len/src.radius)
            return True
        except BaseException as e:
            print(e)
        return False

            
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
 ##################################################################
    #
    # Clear storage variables
    #
    ##################################################################
    def clear_storage_variables(self,src):
            self.iteration = 0
            self.current_time = 0.0
            src.stor_t.clear()
            src.stor_vx.clear()
            src.stor_vy.clear()
            src.stor_v_mag.clear()
            src.stor_v_ang.clear()
            src.stor_cvmag.clear()
            #src.stor_pen_factor.clear()
    def add(self,p):
        p.pnum = self.pnum
        self.pary.append(p)
        self.pnum += 1
 
    def print_p(self):
        for ii in self.pary:
            print(f"#:{ii.pnum},radius:{ii.radius},rx:{ii.rx},ry:{ii.ry},rz:{ii.rz},rx:{ii.rx},vx:{ii.rx},vy:{ii.rx},vz:{ii.rx}")
   
    def __init__(self,itemcfg):
        self.pary = []
        self.pnum = 0
        self.itemcfg = itemcfg
        self.wall_xmin = 0.0
        self.wall_xmax = 0.0
        self.wall_ymin = 0.0
        self.wall_ymax = 0.0
        self.current_time = 0.0
        self.iteration = 0

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

    def origin_vector(self,X,Y):
        outvec = [X[1]-X[0],Y[1]-Y[0]]
        return outvec
    
    def addWalls(self):
        if "walls" in self.itemcfg:
            if self.itemcfg.walls == True:
                walls = self.itemcfg.wall_dim
                self.wall_xmin = walls[0]
                self.wall_xmax = walls[1]
                self.wall_ymin = walls[2]
                self.wall_ymax = walls[3]

     ##################################################################
    #
    # Stor storge values
    #
    ##################################################################
    def save_data(self,data_file_name):
        for src in self.pary:
            file_name = data_file_name+f"{src.pnum}.csv"
            try:
                with open(file_name, 'w', newline='') as csvfile:
                    csvfile.write("P,t,vx,vy,pen_factor,v_mag,cvmag,v_ang,vrel,v_collx,vcolly\r\n")
                    for ii in range(len(src.stor_t)):
                        line = f"{src.stor_pnum[ii]},{src.stor_t[ii]:0.4f},{src.stor_vx[ii]:0.4f},{src.stor_vy[ii]:0.4f},"
                        line += f"{src.stor_pen_factor[ii]:0.4f},{src.stor_v_mag[ii]:0.4f},"
                        line += f"{src.stor_cvmag[ii]:0.4f},{src.stor_v_ang[ii]:0.4f},{src.stor_vx_rel[ii]:0.4f},"
                        line += f"{src.stor_tot_collision_x_acc[ii]:0.4f}\r\n"
                        csvfile.write(line)
            except BaseException as e:
                print(e)
    
 ##################################################################
    #
    # Stor storge values
    #
    ##################################################################
    def set_storage_variables(self,src):
        self.current_time  = self.current_time + self.itemcfg.dt
        #if self.iteration > 3:
        src.stor_t.append(self.current_time) 
        src.stor_vx.append(src.vx)
        src.stor_vy.append(src.vy)
        src.stor_v_mag.append(src.vel_mag)
        src.stor_v_ang.append(src.vel_ang)
        src.stor_cvmag.append(src.cvmag)
        src.stor_pnum.append(src.pnum)
        src.stor_pred_mom_xout.append(src.pred_mom_xout)
        src.stor_pred_mom_yout.append(src.pred_mom_xout)
        
        if len(src.collision_list) > 0:
            src.stor_pen_factor.append(src.collision_list[0].pen_factor)
            src.stor_vx_rel.append(src.cvx_rel)    
            src.stor_tot_collision_x_acc.append(src.tot_collision_x_acc)
            src.stor_tot_collision_y_acc.append(src.tot_collision_y_acc)
        else:
            src.stor_tot_collision_x_acc.append(0.0)
            src.stor_tot_collision_y_acc.append(0.0)
            src.stor_pen_factor.append(0.0)
            src.stor_vx_rel.append(0.0)
        self.iteration = self.iteration+1



    def predict_mom(self,m1,vx1in,v1yin,m2,vx2in,vy2in):
        t1 = ((m1-m2)/(m1+m2))
        t2 = (2*m2/(m1+m2))
        print(f"t1:{t1},t2:{t2}")
        vx1out = ((m1-m2)/(m1+m2))*vx1in + (2*m2/(m1+m2))*vx2in
        vy1out = ((m1-m2)/(m1+m2))*v1yin + (2*m2/(m1+m2))*vy2in
        
        vx2out = ((m1-m2)/(m1+m2))*vx2in + (2*m1/(m1+m2))*vx1in
        print(f"vx1out:{vx1out},vx2out{vx2out}")
        return vx1out,vy1out

