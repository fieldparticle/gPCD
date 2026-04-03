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
from particle import *
from Utility import *
from CollisionParticle import *
from vectors import *


class CollisionWall():

    
    def __init__(self,itemcfg):
        self.pnum = 0
        self.itemcfg = itemcfg
        self.wall_xmin = 0.0
        self.wall_xmax = 0.0
        self.wall_ymin = 0.0
        self.wall_ymax = 0.0

    #------------------------------------------------
    # Process Wall Collisions
    #------------------------------------------------
    def WallCollision(self,pary,src):
        self.pary = pary
        # Check for wall collisioins
        if(self.check_wall_collision(self.pary,src) == True):
            # Is this a new wall collision
            if(self.pary[src].wcol_flag == False):    
                    self.pary[src].wcol_flag = True
        else:
            if(self.pary[src].wcol_flag ==  True):
                self.pary[src].wcol_flag = False

    #------------------------------------------------
    # Add Walls
    #------------------------------------------------
    def addWalls(self):
        if "walls" in self.itemcfg:
            if self.itemcfg.walls == True:
                walls = self.itemcfg.wall_dim
                self.wall_xmin = walls[0]
                self.wall_xmax = walls[1]
                self.wall_ymin = walls[2]
                self.wall_ymax = walls[3]

     ##############################################################################################
    # Check for wall collsions
    #
    #
    #
    ##############################################################################################
    def check_wall_collision(self,pary,ii):
        self.pary = pary
        col_flg = -1
        col_ary = []
        
        # ---------------------West Wall ---------------------------------------------------------
        # East wall location
        if(abs(self.wall_xmin - self.pary[ii].rx) < self.pary[ii].radius):
                col_flg = 0
                # unit vector pointing in the direction of the wall
                v = (1, 0)
                # unit vector normal to the wall 
                d = (0, 1)
                pointY = self.wall_ymax
                pointX = self.wall_xmin
                col_ary.append({'wall': 0,'pointX': 0, 'pointY':0, d:[0,0],v:[0,0] })
                col_ary[-1]['wall'] = col_flg
                col_ary[-1]['d'] = d
                col_ary[-1]['v'] = v
                col_ary[-1]['pointY'] = pointY
                col_ary[-1]['pointX'] = pointX

        # West wall location
        if(abs(self.wall_xmax - self.pary[ii].rx) < self.pary[ii].radius):
            col_flg = 1
            # unit vector pointing in the direction of the wall
            v = (1, 0)
            # unit vector normal to the wall 
            d = (0, 1)
            pointY = self.wall_ymin
            pointX = self.wall_xmax
            col_ary.append({'wall': 0,'pointX': 0, 'pointY':0, d:[0,0],v:[0,0] })
            col_ary[-1]['wall'] = col_flg
            col_ary[-1]['d'] = d
            col_ary[-1]['v'] = v
            col_ary[-1]['pointY'] = pointY
            col_ary[-1]['pointX'] = pointX
        # North wall location
        if(abs(self.wall_ymax - self.pary[ii].ry) < self.pary[ii].radius):
            col_flg = 2
            # unit vector pointing in the direction of the wall
            v = (0, 1)
            # unit vector normal to the wall 
            d = (1, 0)
            pointY = self.wall_ymax
            pointX = self.wall_xmin
            col_ary.append({'wall': 0,'pointX': 0, 'pointY':0, d:[0,0],v:[0,0] })
            col_ary[-1]['wall'] = col_flg
            col_ary[-1]['d'] = d
            col_ary[-1]['v'] = v
            col_ary[-1]['pointY'] = pointY
            col_ary[-1]['pointX'] = pointX

        # South wall location
        if(abs(self.wall_ymin - self.pary[ii].ry) < self.pary[ii].radius):
            col_flg = 3
            # unit vector pointing in the direction of the wall
            v = (0, 1)
            # unit vector normal to the wall 
            d = (1, 0)
            pointY = self.wall_ymin
            pointX = self.wall_xmin
            col_ary.append({'wall': 0,'pointX': 0, 'pointY':0, d:[0,0],v:[0,0] })
            col_ary[-1]['wall'] = col_flg
            col_ary[-1]['d'] = d
            col_ary[-1]['v'] = v
            col_ary[-1]['pointY'] = pointY
            col_ary[-1]['pointX'] = pointX

        for jj in range(len(col_ary)):
            # If this is the start of a collsion 
            #if self.pary[ii].wcol_flag[col_ary[jj]['wall']]  == False:
             if self.pary[ii].wall_list[jj] == False:
                self.pary[ii].wall_list[jj] == True
                col_struct = collision()
                # Add the collision structure to the src particles container
                col_struct.col_num = self.pary[ii].num_cols
                self.pary[ii].collision_list.append(col_struct)
                self.pary[ii].num_cols += 1
                try :
                        # Center point of particle
                        P = (self.pary[ii].rx, self.pary[ii].ry)
                        # A point in the wall
                        A = (col_ary[jj]['pointX'], col_ary[jj]['pointY'])
                        d = col_ary[jj]['d']
                        v = col_ary[jj]['v']
                        # Ray is particle to  wall P+tv, and wall is A+sd
                        t,s,ipoint = intersect_ray_line_2d(P, v, A, d)
                        #print(f"t:{t},s:{s},ipoint:{ipoint}")
                        faux_center = P+2*t*np.array(v)
                        # Get a unity vector from the center of the particle to the wall intersection point
                        wall_vec = origin_vector([self.pary[ii].rx,ipoint[0]],[self.pary[ii].ry,ipoint[1]])
                        # Get the angle of the ray between the particle and the wall
                        col_struct.orient_ang = atan360(wall_vec[0],wall_vec[1],0)
                        # Don't need intersection points cause we can go directly to the orientation vector
                        col_struct.col_pointA = ipoint
                        col_struct.col_pointB = ipoint
                        col_struct.orient_vec_print=[[self.pary[ii].rx,ipoint[0]],[self.pary[ii].ry,ipoint[1]]]
                        col_struct.prox_vec = [0,0]
                        wall_vec_mag = np.linalg.norm([wall_vec[0],wall_vec[1]])
                        wall_vec = (self.pary[ii].rx, self.pary[ii].ry)
                        self.pary[ii].wcol_flag[col_flg] = True
                        col_struct.pen_factor = 1.0-wall_vec_mag/self.pary[ii].radius
                            

                except BaseException as e:
                    print(f"Wall Collision for particle {ii}, wall {jj}, {e}")
                return True
                
        return False