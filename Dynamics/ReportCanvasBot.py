import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
from particle import *


class ReportCanvasBot(FigureCanvas):

    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.xpos = 2.5
        self.ypos = 2.5
        self.pa = None
        self.itemcfg = None

    # Initialize ReportCanavs
    # need config file, particle array, and a pointer to the 
    # form so that it can update parameter widgets    
    def initialize(self,itemcfg,particle_arry,parent):
        self.p = parent
        self.pa = particle_arry
        self.itemcfg = itemcfg
        self.xlim = self.itemcfg.xlim
        self.ylim = self.itemcfg.ylim
   
    # Udpate the 
    def update_plot(self):
        self.ax.cla()
        color_list = ["green","red","blue"]
        # Set the parameter widgets in TabFormDyn
        line_text = []
        for ii in self.pa.pary:
            if self.itemcfg.plot_list[ii.pnum] ==True:
                # Plot predicted resulting momentum
                for cc in ii.collision_list:
                    if cc.col_flag == True or (cc.col_flag == False and cc.stor_area_diff[-1]!= 0):
                        if self.itemcfg.plot_accel[ii.pnum] == True:
                            self.ax.plot(ii.stor_t,cc.stor_area_diff,color=color_list[ii.pnum], 
                                    linestyle='dotted', linewidth=1.0, markersize=2)
                        if self.itemcfg.plot_tot_area[ii.pnum] == True:
                            self.ax.plot(ii.stor_t,cc.stor_tot_area,color='black', 
                                    linestyle='dotted', linewidth=1.0, markersize=2)
                    
                    #self.ax.legend("Velocity Magnitude","Out og Collsion Mag")
                    line_text.append(f"P{ii.pnum} cc:{cc.col_num} stor_area_diff")
                    line_text.append(f"P{ii.pnum} cc:{cc.col_num} stor_tot_area")
        self.ax.legend(line_text,loc='upper left')    
        self.ax.grid(True)
        self.draw()
    
    