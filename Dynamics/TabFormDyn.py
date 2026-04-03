import subprocess, os
import csv
from _thread import *
from tkinter import *
from tkinter import messagebox 

from PyQt6.QtWidgets import (QFileDialog, 
                             QGroupBox,
                             QLabel,
                             QGridLayout, 
                             QTabWidget, 
                             QCheckBox,
                             QListWidget,
                             QPushButton, 
                             QGroupBox,
                             QComboBox,
                             QTextEdit,
                             QRadioButton)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from PyQt6.QtCore import Qt,QTimer
from QToggle import *
from python.ConfigUtility import *
import ctypes
from particle import *
#from ParticleArrayBasicAreaChange import *
from ParticleArrayBasicArea import *
#from ParticleArrayBasic import *
#from Sim import *
from ParticleCanvas import *
from ReportCanvas import *
from ReportCanvasBot import *

class pdata(ctypes.Structure):
    _fields_ = [("pnum", ctypes.c_double),
                ("rx",  ctypes.c_double),
                ("ry",  ctypes.c_double),
                ("rz",  ctypes.c_double),
                ("radius",  ctypes.c_double),
                ("vx",  ctypes.c_double),
                ("vy",  ctypes.c_double),
                ("vz",  ctypes.c_double),
                ("ptype",  ctypes.c_double),
                ("seq",  ctypes.c_double),
                ("acc_r",  ctypes.c_double),
                ("acc_a",  ctypes.c_double),
                ("molar_mass",  ctypes.c_double),
                ("temp_vel",  ctypes.c_double)]          

class TabFormDyn(QTabWidget):
    
   
    
    #******************************************************************
    # Init
    #
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs )
        self.CheckOn = False
        self.CheckOff = True
        self.PauseFlag = False
        
   
    def setSize(self,control,H,W):
        control.setMinimumHeight(H)
        control.setMinimumWidth(W)
        control.setMaximumHeight(H)
        control.setMaximumWidth(W)

    def browseFolder(self):
        """ Opens a dialog window for the user to select a folder in the file system. """
        #folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        self.folder = QFileDialog.getOpenFileName(self, ("Open File"),
                                       self.cfg.report_start_dir,
                                       ("Configuration File (*.cfg)"))
        
        if self.folder[0]:
           self.load_item_cfg(self.folder[0])

    #******************************************************************
    # Reload the current cfg file after its been updates outside app
    #   
    def reload(self):
        self.load_item_cfg(self.CfgFile)
    
    #******************************************************************
    # Load the confiruation file
    #
    def load_item_cfg(self,file):
            
        self.CfgFile = file
        self.texFolder = os.path.dirname(self.CfgFile)
        self.texFileName = os.path.splitext(os.path.basename(self.CfgFile))[0]
        #self.dirEdit.setText(self.CfgFile)
        self.pselect.clear()
        # Open the item configuration filke
        try :
            self.itemcfgFile = ConfigUtility(self.CfgFile)
            self.itemcfgFile.Create(self.bobj.log,self.CfgFile)
            self.itemcfg = self.itemcfgFile.config
            self.pselect.addItem("none")

            # Load the plot velocity magnitude flags
            for pp in range(len(self.itemcfg.plt_vel_mag)):
                self.pselect.addItem(f"{pp}")
            # Set the current index in the Plot selection drop down
            # to show which particle will show vetors
            self.pselect.setCurrentIndex(self.itemcfg.select_particle+1)
            # Turn off plot velocity magnitude 
            ##! This should be read from the configuraton
            self.vel_mag_chk.setChecked(self.CheckOff)
            # Add description to description box
            self.desc_edit.setText(self.itemcfg.description)

        except BaseException as e:
            messagebox.showinfo("Intialization Error",f"Config File syntax - line number of config file:{e}")
            self.log.log(self,f"Config File syntax - line number of config file:{e}")
            self.hasConfig = False
            return 
        # A configuration exists so endable the Start and Stop buttons
        self.StartButton.setEnabled(True) 
        self.SaveButton.setEnabled(True)
          
    def cfg_on_current_item_changed(self, current_item, previous_item):
        cfg_item = ""
        if current_item:
            cfg_item = f"{self.cfg.report_start_dir}/{current_item.text()}"
            self.CfgFile = cfg_item
            self.load_item_cfg(self.CfgFile)
            raw_name = os.path.basename(current_item.text())
            filename_without_ext = os.path.splitext(raw_name)[0]
            self.data_file_name = f"{self.cfg.data_dir}/{filename_without_ext}"
        else:
            print("No item currently selected.")
            return

        
        notepad_plus_plus_path = "C:\\Program Files\\Notepad++\\notepad++.exe" # Adjust as needed

        subprocess.Popen([notepad_plus_plus_path, self.CfgFile])
    # Save the data collected by the report canvas.
    def save_data(self):
            self.particle_array.store.save_data(self.data_file_name,self.particle_array.pary)

    def stop(self):
        self.timer.stop()
        self.StopButton.setEnabled(False)
        self.PauseButton.setEnabled(False)

    def pause(self):
        if self.PauseFlag == False :
            self.PauseFlag = True 
            self.timer.stop()
        else:
            self.PauseFlag = False 
            self.timer.start()
        
    def start(self):
        self.load_item_cfg(self.CfgFile)
        self.particle_array = ParticleArrayBasic(self.itemcfg)
        
        # Call start for the selected ParticleArray Object
        self.particle_array.start()
        self.tot_mom_label.setText(f"{self.particle_array.total_momentum:.8f}")
        # Set the parameters of the Particle Canvas which is where 
        # particles a plotted
        self.ParticleCanvas.initialize(self.itemcfg,self.particle_array)
        # Set the parameters of the TOP Report Canvas which is where 
        # particle data over time are stored
        # Needs config file, particle array, and a pointer ti itself
        self.ReportCanvas.initialize(self.itemcfg,self.particle_array,self)
        self.ReportCanvasBot.initialize(self.itemcfg,self.particle_array,self)

        # Enable the stop and pause buttons while we are running
        self.StopButton.setEnabled(True)
        self.PauseButton.setEnabled(True)
        # Creae a timer
        self.timer = QTimer(self)
        # Set the timer interval
        self.timer.setInterval(self.itemcfg.timer_interval)  # Set interval to 1 second
        # Connect to this update_plot() function
        self.timer.timeout.connect(self.update_plot)
        # Call update plot every timer_interval
        self.timer.start()

    #******************************************************************
    # Timer call back for updating the plot and reports
    #     
    def update_plot(self):
        # Call the particle canvas update_plot
        if (self.ParticleCanvas.update_plot() == False):
            self.timer.stop()
            self.StopButton.setEnabled(False)
            for ii in self.particle_array.pary:
                self.particle_array.store.clear_storage_variables(ii)
        self.ReportCanvas.update_plot()
        self.ReportCanvasBot.update_plot()
        self.cur_mom_label.setText(f"{self.particle_array.cur_momentum:.8f}")
        dmomdiff = self.particle_array.total_momentum-self.particle_array.cur_momentum
        self.diff_mom_label.setText(f"{dmomdiff:.8f}")
        #print(f"tot:{self.particle_array.total_momentum:0.6f},c:{self.particle_array.cur_momentum:0.6f}, \
        #      diff:{dmomdiff:0.6f}, \
       #             rmain:{self.particle_array.remained_momentum:0.6f}")

    #******************************************************************
    # Create the tab
    #
    def Create(self,ParticleBase):
        self.bobj = ParticleBase
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.log.log(self,"TabFormGenData finished init.",LogOnly=True)
    
        try:
            
            self.setStyleSheet("background-color:  #eeeeee")
            self.tab_layout = QGridLayout()
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.setLayout(self.tab_layout)

           
            ## -------------------------------------------------------------
            ## Set parent directory
            LatexcfgFile = QGroupBox("Start Dynamics")
            self.setSize(LatexcfgFile,120,450)
            self.tab_layout.addWidget(LatexcfgFile,0,0,alignment=Qt.AlignmentFlag.AlignLeft)
            
            dirgrid = QGridLayout()
            LatexcfgFile.setLayout(dirgrid)

            self.dirButton = QPushButton("Browse")
            self.setSize(self.dirButton,30,100)
            self.dirButton.setStyleSheet("background-color:  #dddddd")
            self.dirButton.clicked.connect(self.browseFolder)
            dirgrid.addWidget(self.dirButton,0,0)

            self.RefreshButton = QPushButton("Reload")
            self.setSize(self.RefreshButton,30,100)
            self.RefreshButton.setStyleSheet("background-color:  #dddddd")
            self.RefreshButton.clicked.connect(self.load_item_cfg)
            dirgrid.addWidget(self.RefreshButton,0,1)

            self.StartButton = QPushButton("Start")
            self.setSize(self.StartButton,30,100)
            self.StartButton.setStyleSheet("background-color:  #dddddd")
            self.StartButton.clicked.connect(self.start)
            self.StartButton.setEnabled(False)
            dirgrid.addWidget(self.StartButton,0,2)

            self.PauseButton = QPushButton("Pause")
            self.setSize(self.PauseButton,30,100)
            self.PauseButton.setStyleSheet("background-color:  #dddddd")
            self.PauseButton.clicked.connect(self.pause)
            self.PauseButton.setEnabled(False)
            dirgrid.addWidget(self.PauseButton,0,3)

            self.StopButton = QPushButton("Stop")
            self.setSize(self.StopButton,30,100)
            self.StopButton.setStyleSheet("background-color:  #dddddd")
            self.StopButton.clicked.connect(self.stop)
            self.StopButton.setEnabled(False)
            dirgrid.addWidget(self.StopButton,1,3)

            self.SaveButton = QPushButton("Save Data")
            self.setSize(self.SaveButton,30,100)
            self.SaveButton.setStyleSheet("background-color:  #dddddd")
            self.SaveButton.clicked.connect(self.save_data)
            self.SaveButton.setEnabled(False)
            dirgrid.addWidget(self.SaveButton,1,0)
            

            ### COnfig File List
            self.cfg_files = [i for i in os.listdir(self.cfg.report_start_dir) if i.endswith("cfg")]
            self.CfgListObj =  QListWidget()
            self.CfgListObj.setStyleSheet("background-color:  #FFFFFF")
            self.vcnt = 0  
            self.setSize(self.CfgListObj,150,450)
            for ii in range(len(self.cfg_files)):
                self.CfgListObj.insertItem(ii,self.cfg_files[ii]) 
            self.CfgListObj.currentItemChanged.connect(self.cfg_on_current_item_changed)
            self.tab_layout.addWidget(self.CfgListObj,0,1,1,1)

            self.desc_edit = QTextEdit()
            self.setSize(self.desc_edit,150,450)
            self.desc_edit.setStyleSheet("background-color:  #FFFFFF")
            self.desc_edit.setText("hello")
            self.tab_layout.addWidget(self.desc_edit,0,3,1,1)

            ## -------------------------------------------------------------
            ## Particle plot canvas
            self.ParticleCanvas = ParticleCanvas()
            self.setSize(self.ParticleCanvas,300,1000)
            self.tab_layout.addWidget(self.ParticleCanvas,1,0,3,3)

             ## -------------------------------------------------------------
            ## Report plot canvas TOP
            self.ReportCanvas = ReportCanvas()
            self.setSize(self.ReportCanvas,275,1000)
            self.tab_layout.addWidget(self.ReportCanvas,4,0,2,3)
            
             ## Report plot canvas BOT
            self.ReportCanvasBot = ReportCanvasBot()
            self.setSize(self.ReportCanvasBot,275,1000)
            self.tab_layout.addWidget(self.ReportCanvasBot,8,0,2,3)
            ## -------------------------------------------------------------
            ## Set parent directory
            SelectionGroup = QGroupBox("Plot Selection")
            self.setSize(SelectionGroup,150,450)
            
            #--------------------------------------
            # Selection pane
            SelGrid = QGridLayout()
            SelectionGroup.setLayout(SelGrid)

            # Particle combo            
            self.psel_lbl = QLabel("Select particle to plot")
            SelGrid.addWidget(self.psel_lbl,0,0)
            self.pselect = QComboBox()
            self.pselect.setStyleSheet("background-color:  #FFFFFF")
            SelGrid.addWidget(self.pselect,1,0)

            '''
            # Plot Type 
            self.ptype_lbl = QLabel("Select particle to plot")
            SelGrid.addWidget(self.ptype_lbl,0,0)
            self.ptype_list = QComboBox()
            self.ptype_list.setStyleSheet("background-color:  #FFFFFF")
            SelGrid.addWidget(self.ptype_list,1,0)
            self.ptype_list.addItem("Velocity Magnitude")
            '''



            # Plot velmag
            self.vel_mag_chk = QToggle("Plot Velocity Magnitude")
            #self.vel_mag_chk.toggled.connect(self.plot_vel_mag)
            self.vel_mag_chk.setStyleSheet("QCheckBox::indicator { background-color: lightgreen; }")
            self.vel_mag_chk.setChecked(False)
            SelGrid.addWidget(self.vel_mag_chk)

            # ?
            self.vel_pmag_chk =  QToggle("Plot Post Collsion Velocity Magnitude")
            self.vel_pmag_chk.setChecked(False)
            SelGrid.addWidget(self.vel_pmag_chk,5,0)
            self.tab_layout.addWidget(SelectionGroup,1,3,alignment=Qt.AlignmentFlag.AlignLeft)

            ## Totals Group
            self.totalsGroup = QGroupBox(f"Totals")
            self.setSize(self.totalsGroup,60,450)
            self.totalsGrid = QGridLayout()
            self.totalsGroup.setLayout(self.totalsGrid)
            ##### Starting total momentum
            lbl = QLabel("Start Momentum:")
            lbl.setStyleSheet("font: 9pt Comic Sans MS")
            self.totalsGrid.addWidget(lbl,1,0)
            self.tot_mom_label = QLabel("0.0")
            self.tot_mom_label.setStyleSheet("font: 9pt Comic Sans MS")
            self.totalsGrid.addWidget(self.tot_mom_label,1,2)
            ##### Current total momentum
            lbl2 = QLabel("Current Momentum:")
            lbl2.setStyleSheet("font: 9pt Comic Sans MS")
            self.totalsGrid.addWidget(lbl2,1,3)
            self.cur_mom_label = QLabel("0.0")
            self.cur_mom_label.setStyleSheet("font: 9pt Comic Sans MS")
            self.totalsGrid.addWidget(self.cur_mom_label,1,4)

            ##### Current total momentum
            lbl3 = QLabel("Diff:")
            lbl3.setStyleSheet("font: 9pt Comic Sans MS")
            self.totalsGrid.addWidget(lbl3,1,5)
            self.diff_mom_label = QLabel("0.0")
            self.diff_mom_label.setStyleSheet("font: 9pt Comic Sans MS")
            self.totalsGrid.addWidget(self.diff_mom_label,1,6)

            # Add totals group    
            self.tab_layout.addWidget(self.totalsGroup,2,3)

            self.rl = []
            for ii in range(3):
                rp = {"RptGroup":self,
                                  "RptGrid":self,
                                  "vx_label":self,
                                  "vx_rpt":self,
                                  "vy_label":self,
                                  "vy_rpt":self,
                                  "v_label":self,
                                  "v_rpt":self,
                                  "v_ang_label":self,
                                  "v_ang_rpt":self,
                                  "v_imom_label":self,
                                  "v_imom_rpt":self}
                
                
                ###################################################
                ## Report Group 1
                rp["RptGroup"] = QGroupBox(f"Particle Report {ii}")
                self.setSize(rp["RptGroup"],100,450)

                rp["RptGrid"] = QGridLayout()
                rp["RptGroup"].setLayout(rp["RptGrid"] )
                
                rp["vx_label"] = QLabel("vx:")
                rp["vx_label"].setStyleSheet("font: 10pt Comic Sans MS")
                rp["RptGrid"].addWidget(rp["vx_label"],0,0,alignment=Qt.AlignmentFlag.AlignLeft)

                rp["vx_rpt"] = QLabel("0.0")
                rp["vx_rpt"].setStyleSheet("background-color:#FFFFFF; font:10pt Comic Sans MS")
                self.setSize(rp["vx_rpt"],20,80)
                rp["RptGrid"].addWidget(rp["vx_rpt"],0,1,alignment=Qt.AlignmentFlag.AlignLeft)

                rp["vy_label"] = QLabel("vy:")
                rp["vy_label"].setStyleSheet("font: 10pt Comic Sans MS")
                rp["RptGrid"].addWidget(rp["vy_label"],0,2,alignment=Qt.AlignmentFlag.AlignLeft)

                rp["vy_rpt"] = QLabel("0.0")
                rp["vy_rpt"].setStyleSheet("background-color:#FFFFFF; font:10pt Comic Sans MS")
                self.setSize(rp["vy_rpt"],20,80)
                rp["RptGrid"].addWidget(rp["vy_rpt"],0,3,alignment=Qt.AlignmentFlag.AlignLeft)    

                rp["v_label"] = QLabel("v:")
                rp["v_label"].setStyleSheet("font: 10pt Comic Sans MS")
                rp["RptGrid"].addWidget(rp["v_label"],0,4,alignment=Qt.AlignmentFlag.AlignLeft)

                rp["v_rpt"] = QLabel("0.0")
                rp["v_rpt"].setStyleSheet("background-color:#FFFFFF; font:10pt Comic Sans MS")
                self.setSize(rp["v_rpt"],20,80)
                rp["RptGrid"].addWidget(rp["v_rpt"],0,5)    

                rp["v_ang_label"] = QLabel("\u0398")
                rp["v_ang_label"].setStyleSheet("font: 10pt Comic Sans MS")
                rp["RptGrid"].addWidget(rp["v_ang_label"],1,1)
                
                rp["v_ang_rpt"] = QLabel("0.0")
                rp["v_ang_rpt"].setStyleSheet("background-color:#FFFFFF; font:10pt Comic Sans MS")
                self.setSize(rp["v_ang_rpt"],20,80)
                rp["RptGrid"].addWidget(rp["v_ang_rpt"],1,2)    

                rp["v_imom_label"] = QLabel("imom")
                rp["v_imom_label"].setStyleSheet("font: 10pt Comic Sans MS")
                rp["RptGrid"].addWidget(rp["v_imom_label"],1,3)
                

                rp["v_imom_rpt"] = QLabel("0.0")
                rp["v_imom_rpt"].setStyleSheet("background-color:#FFFFFF; font:10pt Comic Sans MS")
                self.setSize(rp["v_imom_rpt"],20,80)
                rp["RptGrid"].addWidget(rp["v_imom_rpt"],1,4)    

                self.tab_layout.addWidget(rp["RptGroup"],3+ii,3,alignment=Qt.AlignmentFlag.AlignLeft)
                            
                self.rl.append(rp)
           

            self.CheckOn = False
            self.CheckOff = True
        except BaseException as e:
            self.log.log(self,f"Error in Create:{e}", LogOnly=True)
            return 
        
    
    