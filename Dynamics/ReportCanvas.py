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
        for ii in self.pa.pary:
            if ii.plot_vectors == True and len(ii.stor_t) > 0:
                self.ax.plot(ii.stor_t,ii.stor_v_mag,color='green', 
                             marker='o', linestyle='dashed', linewidth=0.5, markersize=2)
                self.ax.plot(ii.stor_t,ii.stor_cvmag,color='red', 
                             marker='o', linestyle='dashed', linewidth=0.5, markersize=2)

        self.ax.legend("Velocity Magnitude","Out og Collsion Mag",)

        self.ax.grid(True)
        self.draw()
  
  