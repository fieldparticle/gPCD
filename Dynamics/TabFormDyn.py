import subprocess, os
from _thread import *
from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox,QLabel
from PyQt6.QtWidgets import QGridLayout, QTabWidget, QLineEdit,QListWidget
from PyQt6.QtWidgets import QPushButton, QGroupBox,QTextEdit
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from PyQt6.QtCore import Qt,QTimer
from ConfigUtility import *
import ctypes
from particle import *
from ParticleArray import *
from Sim import *
from Canvas import *

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

        # Open the item configuration filke
        try :
            self.itemcfgFile = ConfigUtility(self.CfgFile)
            self.itemcfgFile.Create(self.bobj.log,self.CfgFile)
            self.itemcfg = self.itemcfgFile.config
        except BaseException as e:
            self.msg_box(f"Config File syntax - line number of config file:{e}")
            self.log.log(self,f"Config File syntax - line number of config file:{e}")
            self.hasConfig = False
            return 
        self.StartButton.setEnabled(True) 
          
    def cfg_on_current_item_changed(self, current_item, previous_item):
        cfg_item = ""
        if current_item:
            cfg_item = f"{self.cfg.report_start_dir}/{current_item.text()}"
            self.CfgFile = cfg_item
            self.load_item_cfg(self.CfgFile)
            raw_name = os.path.basename(current_item.text())
            filename_without_ext = os.path.splitext(raw_name)[0]
            self.cap_file = f"{self.cfg.report_start_dir}/{filename_without_ext}.cap"
            self.des_file= f"{self.cfg.report_start_dir}/{filename_without_ext}.des"
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
        else:
            print("No item currently selected.")
            return
        
        
        notepad_plus_plus_path = "C:\\Program Files\\Notepad++\\notepad++.exe" # Adjust as needed

        subprocess.Popen([notepad_plus_plus_path, self.CfgFile])

    def stop(self):
        self.timer.stop()
        self.StopButton.setEnabled(False)

    def start(self):
        self.load_item_cfg(self.CfgFile)
        self.particle_array = ParticleArray(self.itemcfg)
        pnum = 0
        
        ptxt = f"p{pnum}"
        pop = True
        plot_vectors = self.itemcfg.plot_vectors
        while pop == True:
            if ptxt in self.itemcfg:
                p = particle()
                p.set(self.itemcfg[ptxt].rx,
                    self.itemcfg[ptxt].ry,
                    self.itemcfg[ptxt].rz,
                    self.itemcfg[ptxt].vx,
                    self.itemcfg[ptxt].vy,
                    self.itemcfg[ptxt].vz,
                    self.itemcfg[ptxt].radius,
                    self.itemcfg[ptxt].ptype,
                    self.itemcfg[ptxt].molar_mass,
                    self.itemcfg[ptxt].temp_vel,
                    plot_vectors[pnum])
                self.particle_array.add(p)
                pnum+=1
                ptxt = f"p{pnum}"
            else:
                pop = False
        self.canvas.initialize(self.itemcfg,self.particle_array)
        self.canvas.plot()
        self.StopButton.setEnabled(True)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # Set interval to 1 second
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()
        
    def update_plot(self):
        self.canvas.update_plot()
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
            self.tab_layout.addWidget(LatexcfgFile,0,0,2,2,alignment= Qt.AlignmentFlag.AlignLeft)
            
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

            ### COnfig File List
            self.cfg_files = [i for i in os.listdir(self.cfg.report_start_dir) if i.endswith("cfg")]
            self.CfgListObj =  QListWidget()
            self.CfgListObj.setStyleSheet("background-color:  #FFFFFF")
            self.vcnt = 0  
            self.setSize(self.CfgListObj,150,450)
            for ii in range(len(self.cfg_files)):
                self.CfgListObj.insertItem(ii,self.cfg_files[ii]) 
            self.CfgListObj.currentItemChanged.connect(self.cfg_on_current_item_changed)
            self.tab_layout.addWidget(self.CfgListObj,0,2,1,1)

            ## -------------------------------------------------------------
            ## Comunications Interface
            self.canvas = PlotCanvas()
            self.setSize(self.canvas,450,1000)
            self.tab_layout.addWidget(self.canvas)

            
            ## -------------------------------------------------------------
            ## Comunications Interface
            self.terminal =  QTextEdit(self)
            self.terminal.setStyleSheet("background-color:  #ffffff; color: green")
            self.setSize(self.terminal,225,900)
            self.tab_layout.addWidget(self.terminal,5,0,3,3,alignment= Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        except BaseException as e:
            self.log.log(self,f"Error in Create:{e}", LogOnly=True)
            return 
        
        self.bobj.connect_to_output(self.terminal)
    