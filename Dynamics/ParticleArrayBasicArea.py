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


                if cc.col_iter > 0:
                    cc.orient_ang_diff = cc.orient_ang-cc.prev_orient_ang
                    cc.orient_ang_area = get_angle_area(cc.orient_ang_diff,self.pary[pnum].radius)
                    cc.area_diff = cc.cur_area-cc.prev_area
                    if get_sign(cc.area_diff) < 0:
                        cc.tot_area_diff_in += abs(cc.area_diff)
                    else:
                        cc.tot_area_diff_out += abs(cc.area_diff)

                    cc.tot_area_diff = cc.tot_area_diff_in-cc.tot_area_diff_out
                # Get penetration factor
                    if pnum == 0 :
                        
                        '''
                        print(  f"P:{pnum} C:{cc.col_num}, citr:{cc.col_iter}", 
                                f"o_ang_in:{cc.orient_ang_in:0.8f}",
                                f"o_ang_out:{cc.orient_ang:0.8f}",
                                f"o_ang_diff:{cc.orient_ang_diff:0.8f}",
                                f"o_ang_area:{cc.orient_ang_area:0.8f}",
                                f"cur_area:{cc.cur_area:0.8f}"
                                )
                        
                        print(  f"tot_pf_in:{cc.tot_pf_in:0.8f}",
                                f"tot_pf_out:{cc.tot_pf_out:0.8f}",
                                f"pf_diff:{cc.tot_pf_diff:0.8f}",
                                f"pf_vel_diff:{cc.tot_pf_diff*self.pary[pnum].vel_mag :0.8f}"
                                )
                        
                        print(  f"P:{pnum} C:{cc.col_num}, citr:{cc.col_iter}", 
                                f"tot_area_diff_in:{cc.tot_area_diff_in:0.8f}",
                                f"tot_area_diff_out:{cc.tot_area_diff_out:0.8f}",
                                f"tot_area_diff:{cc.tot_area_diff:0.8f}",
                                f"area_diff:{cc.area_diff:0.8f}"
                                )
                        '''
                        
                cc.prev_orient_ang = cc.orient_ang
                cc.prev_area = cc.cur_area
                
                #cc.left_over_mag = 0.0
                # Calulate collision acceleration magnitude by multiplyinig
                # the current intersection area by the relative velocity
                # and then subtract attraction by attraction acceleration.
                #cc.v_coll = (cc.cur_area+cc.orient_ang_area)*cc.v_rel #-get_sign(cc.area_diff)*self.pary[pnum].attr
                cc.v_coll = (cc.cur_area)*cc.v_rel #-get_sign(cc.area_diff)*self.pary[pnum].attr
                '''
                if cc.orient_ang_diff > 0.0:
                    self.pary[pnum].initial_mag+=get_sign(cc.orient_ang_diff)*cc.orient_ang_diff*cc.v_rel
                
                if pnum == 0:
                    print(f"citr{cc.col_iter} imag:{self.pary[pnum].initial_mag}")
                '''
                #cc.v_coll = round(cc.pen_factor,2)*cc.v_rel #-get_sign(cc.area_diff)*self.pary[pnum].attr
                cc.v_coll=cc.v_coll/(self.pary[pnum].num_colls)
                # Calulate the accelration and add it to the total accelration (if there is more than one collsion) 
                cc.tot_collision_x_acc -=(cc.v_coll)*math.cos(cc.orient_ang)
                cc.tot_collision_y_acc -=(cc.v_coll)*math.sin(cc.orient_ang)
            else:
                if cc.remain_mom != 0.0:
                    cc.left_over_mag = cc.remain_mom
                    print(colored(f"{cc.left_over_mag}",'blue'))
               
               

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
                if cc.col_flag == True:
                    ii.vx = ii.vx + cc.tot_collision_x_acc
                    ii.vy = ii.vy + cc.tot_collision_y_acc
                    cc.tot_collision_x_acc = 0.0
                    cc.tot_collision_y_acc = 0.0
                
                elif cc.col_flag == False and cc.left_over_mag != 0.0:
                    cc.tot_collision_x_acc = -(cc.left_over_mag/ii.num_colls)*math.cos(cc.orient_ang)
                    cc.tot_collision_y_acc = -(cc.left_over_mag/ii.num_colls)*math.sin(cc.orient_ang)
                    
                    ii.vx = ii.vx + cc.tot_collision_x_acc
                    ii.vy = ii.vy + cc.tot_collision_y_acc
                    cc.left_over_mag = 0.0
                
            self.cur_momentum += np.linalg.norm([ii.vx,ii.vy])
            
            
            # Get the new angle
            ii.vel_ang = atan360(ii.vx,ii.vy,0.0)
            # Account for rotational 
            ii.dTheta = ii.prev_vel_ang - ii.vel_ang
            ii.ang_vel = ii.dTheta/self.itemcfg.dt
            ii.ang_mom = ii.ang_vel*ii.moment_inertia
           
            ii.prev_vel_ang = ii.vel_ang
 
        
            ii.angle_acc_x = (ii.ang_mom)*math.cos(ii.vel_ang)
            ii.angle_acc_y = (ii.ang_mom)*math.sin(ii.vel_ang)
            

            if ii.pnum == 0:
                print(f"ang_mom:{ii.ang_mom:0.6f},raccx:{ii.angle_acc_x :0.6f},raccy:{ii.angle_acc_y:0.6f}")
            
            ii.vel_mag = np.linalg.norm([ii.vx,ii.vy])
            

            #print(f"mag before{ii.vel_mag},mag after{ii.vel_mag}")
            ii.internal_mom = ii.initial_mag-(ii.vel_mag-ii.ang_mom)
            #print(f"{ii.num_colls},{ii.col_flag}")
            if ii.num_colls == 0 and ii.col_flag == COLL_IN and self.itemcfg.restore_momentum == True:

                ii.vx += ii.internal_mom*math.cos(ii.vel_ang)
                ii.vy += ii.internal_mom*math.sin(ii.vel_ang)
                #if ii.internal_mom == 0.0:
                ii.col_flag = COLL_OUT
                
                ii.internal_mom = 0.0
                
            #print(f"{ii.initial_mag},{ii.internal_mom},{ii.vel_mag}")
                              
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

   