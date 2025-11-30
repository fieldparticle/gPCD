import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
from particle import *


class ReportCanvas(FigureCanvas):
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
   
    def update_plot(self):
        self.ax.cla()
        color_list = ["green","red"]
        for ii in self.pa.pary:
            
            if self.itemcfg.plt_vel_mag[ii.pnum] == True:
                self.ax.plot(ii.stor_t,ii.stor_v_mag,color=color_list[ii.pnum], 
                             marker='o', linewidth=1.0, markersize=2)
                
            if self.itemcfg.plot_pred_mom[ii.pnum] == True:
                print([0.0,ii.stor_t[-1]])
                print([ii.pred_mom_out,ii.pred_mom_out])
                self.ax.plot([0.0,ii.stor_t[-1]],[ii.pred_mom_out,ii.pred_mom_out],color=color_list[ii.pnum], 
                             linestyle='dashed', linewidth=1.0, markersize=2)

        #self.ax.legend("Velocity Magnitude","Out og Collsion Mag")

        self.ax.grid(True)
        self.draw()
  
  