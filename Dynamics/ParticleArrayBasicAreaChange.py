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
from store import *
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
        self.PC = CollisionParticle(itemcfg,self)
        self.WC = CollisionWall(itemcfg)
        self.total_momentum = 0.0
        self.remained_momentum = 0.0
        self.cur_momentum = 0.0
        self.store = Store()
    
    ##################################################################
    # Perform one iteration of time step. Called from ParticleCanvas.
    # 
    #
    ##################################################################
    def do_iteration(self):
        col_num = 0
        self.cur_momentum = 0
        self.current_time  = self.current_time + self.itemcfg.dt
        self.iteration = self.iteration+1
        # For each particle
        for src in range(len(self.pary)):
            self.pary[src].col_flag = False
            # Run thorugh all other target particles 
            for trg in range(len(self.pary)):
                # If source not equal to target particle.    
                if src != trg:
                    if  self.PC.ParticleCollision(self.pary,src,trg) == True or \
                        self.WC.WallCollision(self.pary,src) == True:
                        # Iterate thorugh the collisions and calulate collision accelerations
                        self.calculate_collision_acceleration(src)  
            '''
            if self.pary[src].col_flag == False:
                for cc in self.pary[src].collision_list:
                    cc.clear_collision()    
            '''
            #self.cur_momentum += np.linalg.norm([self.pary[src].vx,self.pary[src].vy])
            


   
    ##################################################################
    #
    # Calulate the change in acceleration due to collisionm
    #
    ##################################################################
    def calculate_collision_acceleration(self,pnum):
        # For each collision in the collision list ....
        for cc in self.pary[pnum].collision_list:
            
            if cc.col_flag == True:
                #if pnum == 0:
                    #print(f"Num Cols:{self.pary[pnum].num_colls},colnum:{cc.col_num}")
                # Get penetration factor

                cc.dpen_factor = cc.pen_factor-cc.prev_pf 
                #if pnum == 1:
                    #print(cc.dpen_factor)
                '''
                cc.prev_pf = cc.pen_factor
                if abs(cc.dpen_factor) < 1E3:
                    cc.area_diff = (cc.cur_area-cc.prev_area)
                else:
                '''
                cc.area_diff = cc.cur_area-cc.prev_area
                
                cc.tot_area += cc.cur_area
                
                
                #if pnum == 0:
                    #print(cc.area_diff)
                 #   print(f"tot:{self.pary[pnum].tot_area:0.5f},cur{area_diff:0.5f}")
                # Mulitply penetration factor by the particle velocity prior to the collision
                
                
                cc.v_coll = cc.cur_area*cc.vel_mag_per_area
                cc.v_coll_sum += get_sign(cc.area_diff)*cc.v_coll
                #print(get_sign(cc.area_diff)*cc.v_coll)
                # Calulate the accelration and add it to the total accelration (if there is more than one collsion) 
                #print(col_dir)
                cc.tot_collision_x_acc -= (cc.v_coll)*math.cos(cc.orient_ang)
                cc.tot_collision_y_acc -= (cc.v_coll)*math.sin(cc.orient_ang)
                #cc.tot_collision_acc = get_sign(cc.area_diff)*np.linalg.norm([cc.tot_collision_x_acc,cc.tot_collision_y_acc])
                #cc.tot_collision_acc = get_sign(cc.area_diff)*cc.pen_factor
                
                cc.internal_mom += np.linalg.norm([cc.tot_collision_x_acc,
                                                                 cc.tot_collision_y_acc])
                
                cc.internal_momx = cc.tot_collision_x_acc
                cc.internal_momy = cc.tot_collision_y_acc
                #print(self.pary[pnum].internal_momx)
                #if pnum == 1:
                 #   print(self.pary[pnum].internal_mom - self.pary[pnum].tot_collision_x_acc)
                
                

    ##################################################################
    #
    # Move particles
    #
    ##################################################################
    def move(self):
        #self.cur_momentum = 0.0
        for ii in self.pary:
            # Before moving save storage variables for this iteration
            self.store.set_storage_variables(ii,self.current_time,self.iteration)
            
            for cc in ii.collision_list:
            # Add collision acceleration vectors to velcoity vectors
                
                if cc.col_flag == False and cc.remain_mom != 0.0:
                    print(f"P:{ii.pnum} C:{cc.col_num} Remain:{cc.remain_mom}")
                    
                   #ii.vx += cc.remain_mom*math.cos(ii.vel_ang)
                   # ii.vy += cc.remain_mom*math.sin(ii.vel_ang)
                    cc.remain_mom = 0.0
                else:
                
                    ii.vx = ii.vx + cc.tot_collision_x_acc
                    ii.vy = ii.vy + cc.tot_collision_y_acc
                cc.tot_collision_x_acc = 0.0
                cc.tot_collision_y_acc = 0.0
            
                

            #if ii.pnum == 1:
            #    print(ii.vy)
            self.cur_momentum += np.linalg.norm([ii.vx,ii.vy])
            #ii.vx = round(ii.vx,5)
            #ii.vy = round(ii.vy,5)
            # Get the new angle
            ii.vel_ang = atan360(ii.vx,ii.vy,0.0)
            ii.vel_mag = np.linalg.norm([ii.vx,ii.vy])

            # This particle is out of collsions return momentum
                               
            # Move the particles
            ii.rx = ii.rx+ii.vx*self.itemcfg.dt
            ii.ry = ii.ry+ii.vy*self.itemcfg.dt
                     
            # Make a velocity vector for plotting
            ii.vel_vec = [[ii.rx,ii.rx+ii.vx*ii.radius],[ii.ry,ii.ry+ii.vy*ii.radius]]   
  
   

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
