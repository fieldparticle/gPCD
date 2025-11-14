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
    
    def origin_vector(vec4):
        outvec = [vec4[2]-vec4[0],vec4[3]-vec4[1]]
        return outvec
    
    def atan2piPt(vec2):
        angle = np.arctan(vec2[0],vec2[1])
        print(angle)
    
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
            self.pary[src].col_pointA = A + u_AB * (b*cosAlpha) + pu_AB * (b*np.sqrt(1-cosAlpha**2))
            self.pary[src].col_pointB = A + u_AB * (b*cosAlpha) - pu_AB * (b*np.sqrt(1-cosAlpha**2))
            self.pary[src].isec_vect = [[self.pary[src].rx,self.pary[src].col_pointA[0]],
                                        [self.pary[src].ry,self.pary[src].col_pointA[0]]]
            O1 = (self.pary[src].col_pointA[0]+self.pary[src].col_pointB[0])/2.0
            O2 = (self.pary[src].col_pointA[1]+self.pary[src].col_pointB[1])/2.0
            self.pary[src].orient_vec = [[self.pary[src].rx,O1],[self.pary[src].ry,O2]]
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
                    print(f"dsq:{dsq},rsq:{rsq}")
                    if (dsq<rsq):
                        self.pary[ii].col_flag = True
                        col_flg = True
                        self.process_collision(ii,jj)
        return col_flg


    def move(self):
        for ii in self.pary:
            ii.rx = ii.rx+ii.vx*self.itemcfg.dt
