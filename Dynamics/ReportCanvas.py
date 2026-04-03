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
        line_text = []
        # Set the parameter widgets in TabFormDyn
        for ii in self.pa.pary:
            try:
                self.p.rl[ii.pnum]["vx_rpt"].setText(f"{ii.stor_vx[-1]:0.8f}")
            except BaseException as e:
                print("stor expecvtion")
                
            self.p.rl[ii.pnum]["vy_rpt"].setText(f"{ii.stor_vy[-1]:0.8f}")
            self.p.rl[ii.pnum]["v_rpt"].setText(f"{ii.stor_v_mag[-1]:0.8f}")
            self.p.rl[ii.pnum]["v_ang_rpt"].setText(f"{ii.stor_v_ang[-1]:0.8f}")
            self.p.rl[ii.pnum]["v_imom_rpt"].setText(f"{ii.stor_internal_mom[-1]:0.8f}")
            if self.itemcfg.plot_list[ii.pnum] == True:
                # Plot veocity magnitude
                if self.itemcfg.plt_vel_mag[ii.pnum] == True:
                    self.ax.plot(ii.stor_t,ii.stor_v_mag,color=color_list[ii.pnum], 
                                marker='o', linewidth=1.0, markersize=2)
                
                    self.ax.plot(ii.stor_t,ii.stor_internal_mom,color=color_list[ii.pnum], 
                                alpha=0.3, linewidth=1.0, markersize=2)
                    line_text.append(f"P{ii.pnum} velocity magnitude")
                    line_text.append(f"P{ii.pnum} internal mom")
                # Plot internal momentum
                '''
                if self.itemcfg.plt_vel_mag[ii.pnum] == True:
                    self.ax.plot(ii.stor_t,ii.stor_internal_mom,color=color_list[ii.pnum], 
                                marker='*', linewidth=1.0, markersize=2)
                ''' 
                
                # Plot predicted resulting momentum
                
                for cc in ii.collision_list:
                    if cc.col_flag == True:
                        #print([0.0,ii.stor_t[-1]])
                        #print([ii.pred_mom_out,ii.pred_mom_out])
                        if self.itemcfg.plot_pred_mom[ii.pnum] == True:
                            self.ax.plot([0.0,ii.stor_t[-1]],[abs(cc.pred_mom_mag),abs(cc.pred_mom_mag)],color=color_list[ii.pnum], 
                                    linestyle='dashed', linewidth=1.0, markersize=2)
                        if self.itemcfg.plot_accel[ii.pnum] == True:
                            self.ax.plot(ii.stor_t,cc.stor_area_diff,color=color_list[ii.pnum], 
                                    linestyle='dotted', linewidth=1.0, markersize=2)
                        
                        line_text.append(f"P{ii.pnum} predicted magnitude")
                        line_text.append(f"P{ii.pnum} area difference")

            self.ax.legend(line_text,loc='upper left')    


            #self.ax.legend("Velocity Magnitude","Out og Collsion Mag")
            
        self.ax.grid(True)
        self.draw()

  