import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
from particle import *


class ParticleCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.xpos = 2.5
        self.ypos = 2.5
        self.pa = None
        self.itemcfg = None
        self.stor_time = []
        self.curr_time = 0.0
        self.iter = 0

        
    def initialize(self,itemcfg,particle_arry,):
        self.pa = particle_arry
        self.itemcfg = itemcfg
        self.xlim = self.itemcfg.xlim
        self.ylim = self.itemcfg.ylim
      
    def plot(self):
        pass


    #******************************************************************
    # Update data, and perform iteration calulations
    #
    def update_plot(self):
        # Set the current time
        self.curr_time = self.curr_time+self.itemcfg.dt
        if self.curr_time >= self.itemcfg.end_time:
            self.curr_time = 0.0
            return False
        #print(f"{self.curr_time:.4f}")

        #print("update")
        self.ax.clear()
        # Call the do_iteration of the selected ParticleArray <Basic,Springs,..>
        self.pa.do_iteration()
        
        # Plot particles
        for ii in self.pa.pary:
            color_list = ["green","red","blue"]
            # Draw the outer boundary circle
            cc = Circle((ii.rx,ii.ry),ii.radius,color=color_list[ii.pnum],alpha=0.8,fill=False)
            self.ax.add_patch(cc)
            # Draw the interna attraction circle
            cr = Circle((ii.rx,ii.ry),ii.bond_rad,color='black',alpha=0.8,fill=False)
            self.ax.add_patch(cr)
            # Print the number in the center
            self.ax.text(ii.rx,ii.ry,f"{ii.pnum}")
            # If there are walls draw them
            if self.itemcfg.walls == True:
                self.ax.plot([self.pa.wall_xmin,self.pa.wall_xmin ],[self.pa.wall_ymin,self.pa.wall_ymax],"k--")
                self.ax.plot([self.pa.wall_xmax,self.pa.wall_xmax ],[self.pa.wall_ymin,self.pa.wall_ymax],"k--")
                self.ax.plot([self.pa.wall_xmin,self.pa.wall_xmax ],[self.pa.wall_ymin,self.pa.wall_ymin],"k--")
                self.ax.plot([self.pa.wall_xmin,self.pa.wall_xmax ],[self.pa.wall_ymax,self.pa.wall_ymax],"k--")
                
            # If in collision plot vectors
        
            if ii.plot_vectors == True:
                # For every collision in the collision list plot vectors
                for cc in ii.collision_list:
                    if cc.col_flag == True:
                        if len(cc.col_pointA) != 2:
                            print("zero")
                        if len(cc.col_pointB) != 2:
                            print("zero")
                        # Plot the pair of intersection points
                        self.ax.plot(cc.col_pointA[0],cc.col_pointA[1],'ro')
                        self.ax.plot(cc.col_pointB[0],cc.col_pointB[1],'ro')
                        # Plot rays between center of the particle to the intesection points
                        self.ax.plot([ii.rx,cc.col_pointA[0]],[ii.ry,cc.col_pointA[1]],'r-')
                        self.ax.plot([ii.rx,cc.col_pointB[0]],[ii.ry,cc.col_pointB[1]],'r-')
                        # Plot the orientation vector
                        self.ax.plot(cc.orient_vec_print[0],cc.orient_vec_print[1],'k-')
                        # Plot the proximity vector
                        self.ax.plot(cc.prox_vec[0],cc.prox_vec[1],'k-')
                        
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
                self.ax.plot(ii.vel_vec[0],ii.vel_vec[1],'g-')     
            
        self.pa.move()
        self.ax.set_xlim(self.xlim)
        self.ax.set_ylim(self.ylim)
        self.ax.set_xlabel('X-axis')
        self.ax.set_ylabel('Y-axis')
        self.ax.set_aspect('equal', 'box')
        self.ax.grid(True)
        self.draw()
        return True
  