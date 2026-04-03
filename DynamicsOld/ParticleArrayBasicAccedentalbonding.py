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

from Utility import *
from CollisionParticle import *
from CollisionWall import *
class ParticleArrayBasic():
    def __init__(self,itemcfg):
        self.pary = []
        self.pnum = 0
        self.itemcfg = itemcfg
        self.current_time = 0.0
        self.iteration = 0
        self.PC = CollisionParticle(itemcfg)
        self.WC = CollisionWall(itemcfg)
        self.total_momentum = 0.0
        self.cur_momentum = 0.0
    
    ##################################################################
    # Perform one iteration of time step. Called from ParticleCanvas.
    # 
    #
    ##################################################################
    def do_iteration(self):
        col_num = 0
        self.cur_momentum = 0
        # For each particle
        for src in range(len(self.pary)):
            
            # Run thorugh all other target particles 
            for trg in range(len(self.pary)):
                # If source not equal to target particle.    
                if src != trg:
                    if  self.PC.ParticleCollision(self.pary,src,trg) == True or \
                        self.WC.WallCollision(self.pary,src) == True:
                        # Iterate thorugh the collisions and calulate collision accelerations
                        self.calculate_collision_acceleration(src)  
            self.cur_momentum += np.linalg.norm([self.pary[src].vx,self.pary[src].vy])


   
    ##################################################################
    #
    # Calulate the change in acceleration due to collisionm
    #
    ##################################################################
    def calculate_collision_acceleration(self,pnum):
        # For each collision in the collision list ....
        for cc in self.pary[pnum].collision_list:
            if cc.col_flag == True:
                # Get penetration factor
                pf = cc.pen_factor
                co_diff = abs(cc.orient_ang_in-cc.orient_ang)
                #if pnum == 1:
                 #   print(f"in:{cc.orient_ang_in},out:{cc.orient_ang},diff:{co_diff}")
                
                # Calculate the dot product of the new and original orienbtation vector
                #if cc.step == 0:
                #    cc.prev_pf = pf
                    
                pf_diff = pf-cc.prev_pf
                #if pnum == 1:
                #    print(pf_diff)
                
                if pf_diff > 0:
                    cc.step += 1
                else:
                    cc.step -= 1
                if pnum == 1:
                    print(f"{cc.step},{pf:.4f},{cc.prev_pf:.4f},{pf_diff:.4f}")
                # Mulitply penetration factor by the particle velocity prior to the collision
                pfs = cc.step*0.1
                v_coll = (pfs*(cc.vel_mag_in))
                '''
                if co_diff > 0.0:
                    v_coll = (pf*(cc.vel_mag_in))
                    v_coll -= co_diff*pf
                else:
                    v_coll = (pf*(cc.vel_mag_in))
                '''
                if pf_diff > 0:
                    self.pary[pnum].internal_mom += v_coll    
                if pf_diff < 0:
                    self.pary[pnum].internal_mom -= v_coll    
                #if pnum == 1:
                #    print(self.pary[pnum].internal_mom)
                
                # Calulate the accelration and add it to the total accelration (if there is more than one collsion) 
                self.pary[pnum].tot_collision_x_acc = -(v_coll)*math.cos(cc.orient_ang)
                self.pary[pnum].tot_collision_y_acc = -(v_coll)*math.sin(cc.orient_ang)
                cc.prev_pf = pf

    ##################################################################
    #
    # Move particles
    #
    ##################################################################
    def move(self):

        for ii in self.pary:
            # Before moving save storage variables for this iteration
            self.set_storage_variables(ii)
            
            # Add collision acceleration vectors to velcoity vectors
            ii.vx = ii.vx + ii.tot_collision_x_acc 
            ii.vy = ii.vy + ii.tot_collision_y_acc

            # Get the new angle
            ii.vel_ang = atan360(ii.vx,ii.vy,0.0)
            ii.vel_mag = np.linalg.norm([ii.vx,ii.vy])

                        
            # Move the particles
            ii.rx = ii.rx+ii.vx*self.itemcfg.dt
            ii.ry = ii.ry+ii.vy*self.itemcfg.dt

            # Clear everything
            ii.tot_collision_x_acc = 0.0
            ii.tot_collision_y_acc = 0.0
            
            # Make a velocity vector for plotting
            ii.vel_vec = [[ii.rx,ii.rx+ii.vx*ii.radius],[ii.ry,ii.ry+ii.vy*ii.radius]]   
  
   
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
            src.stor_vel_mag_in.clear()

            #src.stor_pen_factor.clear()

    def add(self,p):
        p.pnum = self.pnum
        self.pary.append(p)
        self.pnum += 1
 
    def print_p(self):
        for ii in self.pary:
            print(f"#:{ii.pnum},radius:{ii.radius},rx:{ii.rx},ry:{ii.ry},rz:{ii.rz},rx:{ii.rx},vx:{ii.rx},vy:{ii.rx},vz:{ii.rx}")
   
    
    def start(self):
        pnum = 0
        self.total_momentum = 0.0
        # Apply acceleration from particle array (p<n>) in config file. Otherwie
        # Do everything relative to 1.0.
        if "use_accel" in self.itemcfg:
            self.use_accel = self.itemcfg.use_accel
        else:
            self.use_accel = False
        
        # Build the parameters for the particle creation call.
        ptxt = f"p{pnum}"
        pop = True
        # Do we plot vectors? - cfg.plot_vectors
        plot_vectors = self.itemcfg.plot_vectors
        # While we can read particles from the cfg.p<n> arrays...
        while pop == True:
            # If particle n is in the configuration file...
            if ptxt in self.itemcfg:
                # get parameters
                if self.itemcfg.rel_one == True:
                    self.itemcfg[ptxt].molar_mass = 1.0
                    self.itemcfg[ptxt].temp_vel = 1.0
                    self.itemcfg[ptxt].attr_accel = 0.0
                    self.itemcfg[ptxt].rpls_accel = 1.0
                # Create a new Particle
                p = particle()
                # Set the particle with given data
                p.set(pnum,
                    self.itemcfg[ptxt].rx,          # Positions x
                    self.itemcfg[ptxt].ry,          #           y
                    self.itemcfg[ptxt].rz,          #           z
                    self.itemcfg[ptxt].vx,          # Velocities u
                    self.itemcfg[ptxt].vy,          #            v
                    self.itemcfg[ptxt].vz,          #            w
                    self.itemcfg[ptxt].radius,      # Particle Radius
                    self.itemcfg[ptxt].ptype,       # Ptype 1 for particle. Rest reserved for boundary particles.
                    self.itemcfg[ptxt].molar_mass,  # Molar mass for caluating temp veloivity and acceleration.
                    self.itemcfg[ptxt].temp_vel,    # Tempertature veloity ##! Needs to be calualted not from cfg.
                    self.itemcfg[ptxt].gas_const,   # Gas constat for calulating acceleration
                    self.itemcfg[ptxt].vap_temp,    # Vapor Temp
                    self.itemcfg[ptxt].attr_accel,  # Attraction Acceleration cfg.attr_accel
                    self.itemcfg[ptxt].rpls_accel,  # Repulsion Accelration cfg.rpls_accel
                    0.0,
                    self.itemcfg[ptxt].cmprs,       # Don't know ##! DELETE
                    self.itemcfg.plot_vectors[pnum])# Will we plot the vectors for this particle pnum
                self.total_momentum += np.linalg.norm([self.itemcfg[ptxt].vx,self.itemcfg[ptxt].vy])
                # Add the particle
                self.add(p)
                # Advace the counter
                pnum+=1
                # Fixup the search string
                ptxt = f"p{pnum}"
            else:
                pop = False
        # Add the walls
        self.addWalls()

   
    def addWalls(self):
        if "walls" in self.itemcfg:
            if self.itemcfg.walls == True:
                # Add walls for plotting in ParticleCanvas
                walls = self.itemcfg.wall_dim
                self.wall_xmin = walls[0]
                self.wall_xmax = walls[1]
                self.wall_ymin = walls[2]
                self.wall_ymax = walls[3]
                # Add walls for collision detection in CollisionWall
                self.WC.addWalls()

     ##################################################################
    #
    # Save storge values
    #
    ##################################################################
    def save_data(self,data_file_name):
        for src in self.pary:
            file_name = data_file_name+f"{src.pnum}.csv"
            try:
                with open(file_name, 'w', newline='') as csvfile:
                    csvfile.write("P,t,vx,vy,pen_factor,v_mag,vel_mag_in,imom,v_ang,v_collx,vcolly\r\n")
                    for ii in range(len(src.stor_t)):
                        line = f"{src.stor_pnum[ii]},{src.stor_t[ii]:0.4f},{src.stor_vx[ii]:0.4f},{src.stor_vy[ii]:0.4f},"
                        line += f"{src.stor_pen_factor[ii]:0.4f},{src.stor_v_mag[ii]:0.4f},"
                        line += f"{src.stor_vel_mag_in[ii]:0.4f},{src.stor_internal_mom[ii]:0.4f},{src.stor_v_ang[ii]:0.4f},"
                        line += f"{src.stor_tot_collision_x_acc[ii]:0.4f}\r\n"
                        csvfile.write(line)
            except BaseException as e:
                print("save_data error {e}")
    
    ##################################################################
    #
    # Stor storge values
    #
    ##################################################################
    def set_storage_variables(self,src):
        self.current_time  = self.current_time + self.itemcfg.dt
        #if self.iteration > 3:
        # Store 
        src.stor_t.append(self.current_time) 
        src.stor_vx.append(src.vx)
        src.stor_vy.append(src.vy)
        src.stor_internal_mom.append(src.internal_mom)
        src.stor_v_mag.append(src.vel_mag)
        src.stor_v_ang.append(src.vel_ang)
        src.stor_vel_mag_in.append(src.vel_mag_in)
        src.stor_pnum.append(src.pnum)
        src.stor_pred_mom_xout.append(src.pred_mom_xout)
        src.stor_pred_mom_yout.append(src.pred_mom_xout)
        
        if len(src.collision_list) > 0:
            src.stor_pen_factor.append(src.collision_list[0].pen_factor)
            src.stor_tot_collision_x_acc.append(src.tot_collision_x_acc)
            src.stor_tot_collision_y_acc.append(src.tot_collision_y_acc)
        else:
            src.stor_tot_collision_x_acc.append(0.0)
            src.stor_tot_collision_y_acc.append(0.0)
            src.stor_pen_factor.append(0.0)
            src.stor_vx_rel.append(0.0)
        self.iteration = self.iteration+1



    

