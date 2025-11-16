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
        self.pa.move()
        self.pa.check_collision()
            


        for ii in self.pa.pary:
            cc = Circle((ii.rx,ii.ry),ii.radius,color='blue',alpha=0.8,fill=False)
            self.ax.add_patch(cc)
            self.ax.text(ii.rx,ii.ry,f"{ii.pnum}")
            if ii.col_flag == True:
                if ii.plot_vectors == True:
                    self.ax.plot(ii.col_pointA[0],ii.col_pointA[1],'ro')
                    self.ax.plot(ii.col_pointB[0],ii.col_pointB[1],'ro')
                    self.ax.plot([ii.rx,ii.col_pointA[0]],[ii.ry,ii.col_pointA[1]],'r-')
                    self.ax.plot([ii.rx,ii.col_pointB[0]],[ii.ry,ii.col_pointB[1]],'r-')
                    self.ax.plot(ii.orient_vec_print[0],ii.orient_vec_print[1],'y-')
                    self.ax.plot(ii.prox_vec[0],ii.prox_vec[1],'k-')
                    self.ax.text(1.0,self.ylim[1]+0.02,f"P:{ii.pnum} orient angle:{ii.orient_ang:.4f}")        
            #self.ax.text(1.0,self.ylim[1]+0.02,"text")
        
        ratio = 1.0
        #x_left, x_right = self.ax.get_xlim()
        #y_low, y_high = self.ax.get_ylim()
        #self.ax.set_aspect(abs((x_right-x_left)/(y_low-y_high))*ratio)
        self.ax.set_xlim(self.xlim)
        self.ax.set_ylim(self.ylim)
        self.ax.set_xlabel('X-axis')
        self.ax.set_ylabel('Y-axis')
        self.ax.set_aspect('equal', 'box')
        self.ax.grid(True)
        self.draw()
  
  