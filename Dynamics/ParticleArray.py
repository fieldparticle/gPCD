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

class ParticleArray():

    def __init__(self,itemcfg):
        self.pary = []
        self.pnum = 0
        self.itemcfg = itemcfg
    
    def origin_vector(self,X,Y):
        outvec = [X[1]-X[0],Y[1]-Y[0]]
        return outvec
    
    def atan360(self,x,y,z):
        angle = math.atan2(y,x)%(2*math.pi)
        return (angle)
    
    def add(self,p):
        p.pnum = self.pnum
        self.pary.append(p)
        self.pnum += 1

    def print_p(self):
        for ii in self.pary:
            print(f"#:{ii.pnum},radius:{ii.radius},rx:{ii.rx},ry:{ii.ry},rz:{ii.rz},rx:{ii.rx},vx:{ii.rx},vy:{ii.rx},vz:{ii.rx}")

    def process_collision(self,src,trg):
        try:
            A = np.array((self.pary[src].rx, self.pary[src].ry))
            B = np.array((self.pary[trg].rx, self.pary[trg].ry))
            c =  np.linalg.norm(A-B)
            a = self.pary[src].radius
            b = self.pary[trg].radius
            cosAlpha = (b**2+c**2-a**2)/(2*b*c)
            # Unit vector pointing to centers
            u_AB = (B - A)/c
            # Normal vector
            pu_AB = np.array((u_AB[1], -u_AB[0])); 
            r = (b*(1-cosAlpha**2))
            # The intersection points.
            self.pary[src].col_pointA = A + u_AB * (b*cosAlpha) + pu_AB * (b*np.sqrt(1-cosAlpha**2))
            self.pary[src].col_pointB = A + u_AB * (b*cosAlpha) - pu_AB * (b*np.sqrt(1-cosAlpha**2))
            # Vector from center opf particle
            self.pary[src].isec_vect = [[self.pary[src].rx,self.pary[src].col_pointA[0]],
                                        [self.pary[src].ry,self.pary[src].col_pointA[0]]]
            # Bisector of line between intersection points
            O1 = (self.pary[src].col_pointA[0]+self.pary[src].col_pointB[0])/2.0
            O2 = (self.pary[src].col_pointA[1]+self.pary[src].col_pointB[1])/2.0

            # Print orientation vector from center of particle to bisector
            self.pary[src].orient_vec_print = [[self.pary[src].rx,O1],[self.pary[src].ry,O2]]
            # Orient vector
            self.orient_vec = np.array([[self.pary[src].rx,self.pary[src].ry],[O1,O2]])
             # Get length of orient vector.
            ol =  np.linalg.norm(self.pary[src].orient_vec) # this does not work
            ol1 = (self.pary[src].rx-O1)**2
            ol2 = (self.pary[src].ry-O2)**2
            ol = np.sqrt(ol1+ol2)
            # Find r1 
            r1 =abs(self.pary[src].radius - ol)
            # Subtract from ol
            self.pary[src].prox_len = self.pary[src].radius-2*r1
            # Convert to origin vector to get angle.
            ovec2 = self.origin_vector([self.pary[src].rx,O1],[self.pary[src].ry,O2])
            # Get orietn vector 360 degree angle.
            self.pary[src].orient_ang = self.atan360(ovec2[0],ovec2[1],0.0)
            proxvec = [[self.pary[src].rx,self.pary[src].prox_len*np.cos(self.pary[src].orient_ang)+self.pary[src].rx], [self.pary[src].ry,
                        self.pary[src].prox_len*np.sin(self.pary[src].orient_ang)+self.pary[src].ry]]
            self.pary[src].prox_vec = proxvec
            

        except BaseException as e:
            print(e)
        return

    def check_collision(self):
        col_flg = False
        for ii in range(len( self.pary)):
            for jj in range(len(self.pary)):
                if ii != jj:
                    dsq = ((self.pary[ii].rx-self.pary[jj].rx)**2+(self.pary[ii].ry-self.pary[jj].ry)**2+(self.pary[ii].rz-self.pary[jj].rz)**2)
                    rsq = (self.pary[ii].radius + self.pary[jj].radius)**2
                    #print(f"dsq:{dsq},rsq:{rsq}")
                    if (dsq<rsq):
                        self.pary[ii].col_flag = True
                        col_flg = True
                        self.process_collision(ii,jj)
        return col_flg


    def move(self):
        for ii in self.pary:
            ii.rx = ii.rx+ii.vx*self.itemcfg.dt
