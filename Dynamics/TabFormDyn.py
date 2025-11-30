import subprocess, os
import csv
from _thread import *
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
from ConfigUtility import *
import ctypes
from particle import *
from ParticleArray import *
#from Sim import *
from ParticleCanvas import *
from ReportCanvas import *

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
            for pp in range(len(self.itemcfg.plt_vel_mag)):
                self.pselect.addItem(f"{pp}")
            self.pselect.setCurrentIndex(self.itemcfg.select_particle+1)
            #self.vel_mag_chk.setChecked(self.itemcfg.plt_vel_mag[self.itemcfg.select_particle])  
            self.vel_mag_chk.setChecked(self.CheckOff)
            self.desc_edit.setText(self.itemcfg.description)

        except BaseException as e:
            self.msg_box(f"Config File syntax - line number of config file:{e}")
            self.log.log(self,f"Config File syntax - line number of config file:{e}")
            self.hasConfig = False
            return 
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
            self.data_file_name = f"{self.cfg.report_start_dir}/{filename_without_ext}"
            '''
            #self.cap_file = f"{self.cfg.report_start_dir}/{filename_without_ext}.cap"
            #self.des_file= f"{self.cfg.report_start_dir}/{filename_without_ext}.des"
            caption = ""
            des = ""
            if os.path.exists(self.cap_file):
                with open(self.cap_file, 'r') as file:
                    caption = file.read()
            else:
                file = open(self.cap_file, 'w') 
                file.close()

            if os.path.exists(self.des_file):
                with open(self.des_file, 'r') as file:
                    des = file.read()
            else:
                file = open(self.des_file, 'w') 
                file.close()
            print(f"Current item selected: {current_item.text()}")
            '''
        else:
            print("No item currently selected.")
            return

        
        notepad_plus_plus_path = "C:\\Program Files\\Notepad++\\notepad++.exe" # Adjust as needed

        subprocess.Popen([notepad_plus_plus_path, self.CfgFile])

    def save_data(self):
            self.particle_array.save_data(self.data_file_name)

    def stop(self):
        self.timer.stop()
        self.StopButton.setEnabled(False)

    def start(self):
        self.load_item_cfg(self.CfgFile)
        self.particle_array = ParticleArray(self.itemcfg)
        self.particle_array.start()
        self.ParticleCanvas.initialize(self.itemcfg,self.particle_array)
        self.ReportCanvas.initialize(self.itemcfg,self.particle_array)
        self.StopButton.setEnabled(True)
        self.timer = QTimer(self)
        self.timer.setInterval(self.itemcfg.timer_interval)  # Set interval to 1 second
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()
        
    def update_plot(self):
        if (self.ParticleCanvas.update_plot() == False):
            self.timer.stop()
            self.StopButton.setEnabled(False)
            for ii in self.particle_array.pary:
                self.particle_array.clear_storage_variables(ii)
        self.ReportCanvas.update_plot()

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

            self.StopButton = QPushButton("Stop")
            self.setSize(self.StopButton,30,100)
            self.StopButton.setStyleSheet("background-color:  #dddddd")
            self.StopButton.clicked.connect(self.stop)
            self.StopButton.setEnabled(False)
            dirgrid.addWidget(self.StopButton,0,3)

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
            self.setSize(self.ParticleCanvas,400,1000)
            self.tab_layout.addWidget(self.ParticleCanvas,1,0,2,3)

             ## -------------------------------------------------------------
            ## Report plot canvas
            self.ReportCanvas = ReportCanvas()
            self.setSize(self.ReportCanvas,400,1000)
            self.tab_layout.addWidget(self.ReportCanvas,3,0,2,3)
            
            ## -------------------------------------------------------------
            ## Set parent directory
            SelectionGroup = QGroupBox("Plot Selection")
            self.setSize(SelectionGroup,150,450)
            
            
            SelGrid = QGridLayout()
            SelectionGroup.setLayout(SelGrid)

            self.psel_lbl = QLabel("Select particle to plot")
            SelGrid.addWidget(self.psel_lbl,0,0)
            
            self.pselect = QComboBox()
            self.pselect.setStyleSheet("background-color:  #FFFFFF")
            SelGrid.addWidget(self.pselect,1,0)

            self.vel_mag_chk = QToggle("Plot Velocity Magnitude")
            self.vel_mag_chk.toggled.connect(self.plot_vel_mag)
            self.vel_mag_chk.setStyleSheet("QCheckBox::indicator { background-color: lightgreen; }")
            self.vel_mag_chk.setChecked(False)
            SelGrid.addWidget(self.vel_mag_chk)

            self.vel_pmag_chk =  QToggle("Plot Post Collsion Velocity Magnitude")
            self.vel_pmag_chk.setChecked(False)
            SelGrid.addWidget(self.vel_pmag_chk,5,0)

            self.tab_layout.addWidget(SelectionGroup,1,3,alignment=Qt.AlignmentFlag.AlignLeft)

            
            self.CheckOn = False
            self.CheckOff = True
        except BaseException as e:
            self.log.log(self,f"Error in Create:{e}", LogOnly=True)
            return 
        
    def plot_vel_mag(self):
        pass
        '''
        if self.vel_mag_chk.isChecked():
            self.vel_mag_chk.setChecked(False)
        else:
            self.vel_mag_chk.setChecked(True)
        '''        

    def plot_vel_pmag(self):
        pass
        '''
        if self.vel_pmag_chk.isChecked():
            self.vel_pmag_chk.setChecked(False)
        else:
            self.vel_pmag_chk.setChecked(True)
        '''    
    