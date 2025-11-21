import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
from particle import *


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.xpos = 2.5
        self.ypos = 2.5
        self.pa = None
        self.itemcfg = None

        
    def initialize(self,itemcfg,particle_arry):
        self.pa = particle_arry
        self.itemcfg = itemcfg
        self.xlim = self.itemcfg.xlim
        self.ylim = self.itemcfg.ylim
      
    def plot(self):
        pass

    def update_plot(self):
        #print("update")
        self.ax.clear()
        self.pa.do_iteration()
        
        for ii in self.pa.pary:
            cc = Circle((ii.rx,ii.ry),ii.radius,color='blue',alpha=0.8,fill=False)
            self.ax.add_patch(cc)
            self.ax.text(ii.rx,ii.ry,f"{ii.pnum}")
            if self.itemcfg.walls == True:
                self.ax.plot([self.pa.wall_xmin,self.pa.wall_xmin ],[self.pa.wall_ymin,self.pa.wall_ymax],"k--")
                self.ax.plot([self.pa.wall_xmax,self.pa.wall_xmax ],[self.pa.wall_ymin,self.pa.wall_ymax],"k--")
                self.ax.plot([self.pa.wall_xmin,self.pa.wall_xmax ],[self.pa.wall_ymin,self.pa.wall_ymin],"k--")
                self.ax.plot([self.pa.wall_xmin,self.pa.wall_xmax ],[self.pa.wall_ymax,self.pa.wall_ymax],"k--")
                

            if ii.col_flag == True or any(ii.wcol_flag):
                if ii.plot_vectors == True:
                    for cc in range(len(ii.collision_list)):
                        self.ax.plot(ii.collision_list[cc].col_pointA[0],ii.collision_list[cc].col_pointA[1],'ro')
                        self.ax.plot(ii.collision_list[cc].col_pointB[0],ii.collision_list[cc].col_pointB[1],'ro')
                        self.ax.plot([ii.rx,ii.collision_list[cc].col_pointA[0]],[ii.ry,ii.collision_list[cc].col_pointA[1]],'r-')
                        self.ax.plot([ii.rx,ii.collision_list[cc].col_pointB[0]],[ii.ry,ii.collision_list[cc].col_pointB[1]],'r-')
                        self.ax.plot(ii.collision_list[cc].orient_vec_print[0],ii.collision_list[cc].orient_vec_print[1],'y-')
                        self.ax.plot(ii.collision_list[cc].prox_vec[0],ii.collision_list[cc].prox_vec[1],'k-')
                        self.ax.text(ii.pnum+self.xlim[0],self.ylim[1]+0.10,f"P:{ii.pnum} orient angle:{ii.collision_list[cc].orient_ang:.4f}")   
                        self.ax.text(ii.pnum+self.xlim[0],self.ylim[1]+0.04,f"P:{ii.pnum} penetration factor :{ii.collision_list[cc].pen_factor:.4f}")  
                        
            else:
                ii.col_pointA = None
                ii.col_pointB = None
                ii.isec_vect = []
                ii.orient_vec_print = []
                ii.orient_vec = []
                ii.orient_ang = 0.0
                ii.prox_len = 0.0
                ii.prox_vec = []
                ii.pen_factor =0.0
            if ii.plot_vectors == True:
                self.ax.text(ii.pnum+self.xlim[0],self.ylim[1]+0.00,f"P:{ii.pnum} velocity x:{ii.vx:.4f},y:{ii.vy:.4f}")
                self.ax.plot(ii.vel_vec[0],ii.vel_vec[1],'g-')     
            
        self.pa.move()
        self.ax.set_xlim(self.xlim)
        self.ax.set_ylim(self.ylim)
        self.ax.set_xlabel('X-axis')
        self.ax.set_ylabel('Y-axis')
        self.ax.set_aspect('equal', 'box')
        self.ax.grid(True)
        self.draw()
  
  