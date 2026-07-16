from asyncio import subprocess
import sys
import importlib
from contextlib import redirect_stdout
from io import StringIO
from sys import stderr, stdout
from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox,QLabel
from PyQt6.QtWidgets import QGridLayout, QTabWidget, QLineEdit,QListWidget
from PyQt6.QtWidgets import QPushButton, QGroupBox,QTextEdit
from PyQt6.QtGui import QFocusEvent
from PyQt6 import QtCore
from PyQt6.QtCore import Qt,QThread,QEvent, pyqtSignal,pyqtSlot,QObject,QRunnable,QThreadPool
from gbase.ConfigUtility import *
import tkinter as tk
from tkinter import * 
from tkinter import messagebox 
import glob
import traceback
import time
from gbase.PlotParticles import *
import struct
import ctypes
from gbase.BinaryFileUtilities import *
from gbase.import_module import load_class_from_file
from gbase.pdata import *
from gbase.GenPQBData import *
from SimulationRunner_HSVPanel import run_analysis as simulation_run_analysis_2d
from SimulationRunner3D_HSVPanel import run_analysis as simulation_run_analysis_3d
from base.ForcePlots import run_force_plots
from gbase.ReadCaptureFile import *
import subprocess
subprocess.__file__




class TabGenData(QTabWidget):
    
    texFolder = ""
    CfgFile = ""
    texFileName = ""
    hasConfig = False
    itemcfg = None
    selected_item = -1
    #ObjName = ""
    gen_class = None
    thread = None
    current_test_file = 0
    particle_data = None
    terminal = None
    batch_mode = False
    #******************************************************************
    # Init
    #
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs )
        self.diagnostics_cfg_file = None
        self.threadpool = QThreadPool()
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        thread_count = self.threadpool.maxThreadCount()
        #print(f"Multithreading with maximum {thread_count} threads")
        #self.installEventFilter(self)


    def focusInEvent(self, event):
        super().event(event)
        print("MyTabWidget gained focus via focusInEvent!")

    def no_selection(self):
        msgBox = QMessageBox()
        msgBox.setText("You have not selected a data file in the list box.")
        msgBox.exec()
    def msg_box(self,text):
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.exec()
    
    def read_capture(self):
        read_obj = ReadCaptureFile()
        selected_item = self.DataList.selectedItems()
        self.selected_item = selected_item
        if not self.selected_item:
            self.no_selection()
            return
        try:
            bin_file = selected_item[0].text()
            capture_files = read_obj.FindCaptureFiles(bin_file)
            if not capture_files:
                self.log.log(
                    self,
                    f"No capture files match {Path(bin_file).stem}_<frame>.cap",
                )
                return

            read_obj.ReadBinFile(bin_file)
            for capture_file in capture_files:
                read_obj.ReadCapFile(capture_file)
                read_obj.Report()
        except BaseException as e:
            self.log.log(self, f"Could not create capture report: {e}")

    ##############################################################################
    # Configuration file stuff
    # 
    ##############################################################################
    def run_study(self):
        count = 0
        for ii in range(0,self.itemcfg.num_studies):
            if self.selected_run_analysis(self.CfgFile, study=True, study_number=ii) == True:
                break
        self.batch_mode = False

    def do_batch(self):
        count = 0
        for ii in self.itemcfg.batch_items:
            print(f"Batch item:{ii}")
            self.CfgFile=f"{self.itemcfg.data_dir}/{ii[0]}"
            if self.selected_run_analysis(self.CfgFile, batch_mode=True, end_frame=ii[1]) == True:
                break
        self.batch_mode = False

    def load_include(self):
        include_items = self.itemcfgFile.open_log(self.itemcfg.include_file)
        for key, value in include_items.items():
            self.itemcfg[key] = value
           #print(f'{key}')

        pass
    #******************************************************************
    # Load the configuration data
    #
    def load_item_cfg(self,file):
        self.batch_mode = False
        self.setFocus()
        self.CfgFile = file
        self.texFolder = os.path.dirname(self.CfgFile)
        self.texFileName = os.path.splitext(os.path.basename(self.CfgFile))[0]
        self.dirEdit.setText(self.CfgFile)

        # Open the item configuration filke
        try :
            self.itemcfgFile = ConfigUtility(self.CfgFile)
            self.itemcfgFile.Create(self.bobj.log,self.CfgFile)
            self.itemcfg = self.itemcfgFile.config
            if 'include_file' in self.itemcfg:
                self.load_include()
            if self.itemcfg.get("type") == "batch":
                self.diagnostics_cfg_file = file
        except BaseException as e:
            self.log.log(self,f"Unable to open item configurations file:{e}")
            self.hasConfig = False
            return False
        if self.itemcfg.type != "verfperf":
            self.study_mode = False
            self.batch_mode = False
            if self.itemcfg.type == "batch":
                self.batch_mode = True
                return True
            if self.itemcfg.study == True:
                self.study_mode = True
                return True
        try:
            notepad_plus_plus_path = "C:\\Program Files\\Notepad++\\notepad++.exe" # Adjust as needed
            subprocess.Popen([notepad_plus_plus_path, self.CfgFile])
            mod_path = self.itemcfg.module_dir
            mod_name = self.itemcfg.module_class
            full_path = os.path.join(mod_path, mod_name)
            # Import the class named in generate_class
            self.gen_class = load_class_from_file(full_path)()
            #self.gen_class = self.load_class(self.itemcfg.generate_class)()
            self.gen_class.create(self,self.itemcfg) 
        except BaseException as e:
            self.log.log(self,f"Unable to import data generation file: error:{e}")
            return False
        self.update_data_list_widget()
        self.plot_obj.create(self.itemcfg,self)
        
        # Enable to generate data
        self.GenDataButton.setEnabled(True)
            


    #******************************************************************
    # reload the configuration file
    #
    def refresh(self):
        try:
            self.itemcfgFile = ConfigUtility(self.CfgFile)
            self.itemcfgFile.Create(self.bobj.log, self.CfgFile)
            self.itemcfg = self.itemcfgFile.config
        except BaseException as e:
            self.log.log(self,f"Could not read particle data:{e}")
            return False
        if 'include_file' in self.itemcfg:
            self.load_include()
        try:
            if self.itemcfg.get("type") not in ("batch", "verfperf"):
                mod_path = self.itemcfg.module_dir
                mod_name = self.itemcfg.module_class
                full_path = os.path.join(mod_path, mod_name)
                self.gen_class = load_class_from_file(full_path)()
                self.gen_class.create(self, self.itemcfg)
                self.plot_obj.create(self.itemcfg, self)
        except BaseException as e:
            self.log.log(self,f"Unable to refresh data generation file: error:{e}")
            return False
        return True
        
    #******************************************************************
    # Browse to an existing cfg file
    #
    def browseFolder(self):
        """ Opens a dialog window for the user to select a folder in the file system. """
        self.startDir = self.cfg.gen_start_dir
        folder = QFileDialog.getOpenFileName(self, ("Open File"),
                                       self.startDir,
                                       ("Configuration File (*.cfg)"))
        # If a valid configuation file name is returned
        if folder[0]:
            self.load_item_cfg(folder[0])
 
    def run_analysis(self):
        self.refresh()
        if self.batch_mode==True:
            self.do_batch()
        elif self.study_mode==True:
            self.run_study()
        else:
            return self.selected_run_analysis(self.CfgFile)

    def selected_run_analysis(self, cfg_file, batch_mode=False, study=False, study_number=None, end_frame=None):
        return self.selected_simulation_runner(cfg_file)(
            cfg_file,
            batch_mode=batch_mode,
            study=study,
            study_number=study_number,
            end_frame=end_frame,
        )

    def selected_simulation_runner(self, cfg_file):
        dimensions = self.simulation_dimensions(cfg_file)
        if dimensions == 3:
            return simulation_run_analysis_3d
        return simulation_run_analysis_2d

    def simulation_dimensions(self, cfg_file):
        if cfg_file == self.CfgFile and self.itemcfg is not None:
            cfg = self.itemcfg
        else:
            cfg_file_obj = ConfigUtility(cfg_file)
            cfg_file_obj.Create(self.bobj.log, cfg_file)
            cfg = cfg_file_obj.config
            if "include_file" in cfg:
                include_items = cfg_file_obj.open_log(cfg.include_file)
                for key, value in include_items.items():
                    cfg[key] = value

        raw_dimensions = cfg.get("dimensions", 2)
        try:
            dimensions = int(raw_dimensions)
        except (TypeError, ValueError):
            raise ValueError(
                f"{cfg_file} dimensions must be 2 or 3, got {raw_dimensions!r}"
            )
        if dimensions not in (2, 3):
            raise ValueError(
                f"{cfg_file} dimensions must be 2 or 3, got {dimensions}"
            )
        return dimensions

    #******************************************************************
    # Generate the data
    #
    def gen_data(self):
         # Pass the function to execute
        if self.refresh() == False:
            print("Config file error")
            return
        index = 0
        os.system('cls' if os.name == 'nt' else 'clear')
        self.current_test_file = 0
        self.gen_class.openSelectionsFile()
        self.gen_class.clear_files()
        self.gen_class.do_all_files_dbg()
        self.update_data_list_widget()
    
    def refresh_dir(self,cfg_file):
        pass
        ## -------------------------------------------------------------
        ## CFg Files Select Interface
        
        self.CfgFile = cfg_file
        notepad_plus_plus_path = "C:\\Program Files\\Notepad++\\notepad++.exe" # Adjust as needed
        subprocess.Popen([notepad_plus_plus_path, cfg_file])
    #******************************************************************
    # Update the list widget
    #
    def update_list_widget(self):
        self.ListObj.clear()
        files_names = self.cfg.analysis_script_dir + "/*.cfg"
        files = glob.glob(files_names)
        for ii in files:
                self.ListObj.addItem(ii)

    def update_data_list_widget(self):    
        self.DataList.clear()
        files_names = self.itemcfg.data_dir + "/*.bin"
        files = glob.glob(files_names)
        for ii in files:
                self.DataList.addItem(ii)
        
    def print_output(self, s):
        print(s)

    #******************************************************************
    # Update the terminal window
    #
    def update_terminal(self,n):
        print(f"{n:.3f}% done")
        self.terminal.append(f"{n:.3f}% done")
  
    #******************************************************************
    # List a subset of particles to chgeck location and numers
    #
    def list_particles(self):
        selected_item = self.DataList.selectedItems()
        self.selected_item = selected_item
        if self.selected_item:
           #print(selected_item[0].text())
           count_all_particle_data(selected_item[0].text())
           

        else:
            self.no_selection()
    ##############################################################################
    # Testing
    # 
    ##############################################################################
    def test_index_array(self):
        selected_item = self.DataList.selectedItems()
        self.selected_item = selected_item
        if self.selected_item:
           #print(selected_item[0].text())
           self.test_array_to_index(selected_item[0].text())
        else:
            self.no_selection()

    #******************************************************************
    # Count collisions
    #
    def count_collisions(self):
        selected_item = self.ListObj.selectedItems()
        self.selected_item = selected_item
        if self.selected_item:
           #print(selected_item[0].text())
           test_file_name = selected_item[0].text()
        else:
            self.no_selection()
            return 
        try :
            self.particle_data = self.read_all_particle_data(self.selected_item[0].text())
            tst_prefix = os.path.splitext(test_file_name)[0]
            tst_file = tst_prefix + '.tst'
            tst_file_obj = ConfigUtility(tst_file)
            tst_file_obj.Create(self.bobj.log,tst_file)
            tst_file_cfg = tst_file_obj.config
            pu = ParticleUtilities(
                tst_file_cfg.CellAryW,
                tst_file_cfg.cell_occupancy_list_size,
                tst_file_cfg.CellAryH,
                tst_file_cfg.CellAryL,
            )
        except BaseException as e:
            print(f"Verify indexing error:{e}")
            return
        file_name = f"{self.itemcfg.data_dir}/{self.itemcfg.test_collisions_log}"

        [pcount,ccount] = pu.detect_collsions(self.particle_data,file_name)
        
        totcol = int(
            tst_file_cfg.particles_per_cell
            * tst_file_cfg.CellAryW
            * tst_file_cfg.CellAryH
            * tst_file_cfg.CellAryL
        )
        totcells = int(tst_file_cfg.num_particles/tst_file_cfg.particles_per_cell)
        totcol = int(totcells*ccount)
        self.log.log(self,f"Number collsions per cell counted:{ccount}. Processed during generation {tst_file_cfg.num_particle_colliding}")
        self.log.log(self,f"Number particles per cell:{pcount}. Paricles in row :{tst_file_cfg.particles_in_row}")
   
        

    #******************************************************************
    # Test that the array indexing is consecutive addresses
    #
    def test_array_to_index(self,test_file_name):
        try :
            file_name = f"{self.itemcfg.data_dir}/{self.itemcfg.test_indexing_log}"
            col_file = open(file_name,'w')
            tst_prefix = os.path.splitext(test_file_name)[0]
            tst_file = tst_prefix + '.tst'
            tst_file_obj = ConfigUtility(tst_file)
            tst_file_obj.Create(self.bobj.log,tst_file)
            tst_file_cfg = tst_file_obj.config
            width = int(tst_file_cfg.CellAryW)
            height = int(tst_file_cfg.CellAryH)
            depth = int(tst_file_cfg.CellAryL)
            col_file.write(f"Width:{width},Height:{height},Depth:{depth}\n")
            col_ary_size = tst_file_cfg.cell_occupancy_list_size
            pu = ParticleUtilities(width, col_ary_size, height, depth)
        except BaseException as e:
            print(f"Verify indexing error:{e}")
            return
        for zz in range(depth):
            for yy in range(height):
                for xx in range(width):
                    ary = [round(xx),round(yy),round(zz)]
                    index = pu.ArrayToIndex(ary)
                    col_file.write(f"Index:{index} at <{xx},{yy},{zz}>\n")

        col_file.close()
    
    ##############################################################################
    # Plot stuff
    # 
    ##############################################################################
    #******************************************************************
    # Thread is complete start a new thread for the next file if there is any
    #
    def plot_particles(self):
        if self.refresh() == False:
            print("Config file error")
            return
        selected_item = self.DataList.selectedItems()
        if selected_item ==self.selected_item:
            self.plot_obj.close_plot()
        else:
            self.selected_item = selected_item

        if self.selected_item:
            try:
                plot_particle_list = self.itemcfg.particle_range
                tst_file = self.selected_item[0].text()
                #file_name = os.path.basename(path_name) 
                #tst_prefix = os.path.splitext(file_name)[0]
                #tst_file = self.itemcfg.data_dir + '/' + tst_prefix + '.bin'

                self.particle_data = read_particle_data(tst_file, plot_particle_list)
            except BaseException as e:
                self.log.log(self,f"Could not read particle data:{e}")
                return
            try:
                self.plot_obj.plot(self.itemcfg,self.particle_data,tst_file)
            except BaseException as e1:
                self.log.log(self,f"Ploting error:{e1}")
        else:
            self.no_selection()

    #******************************************************************
    # Have plot obj toggle cells
    #
    def toggle_cells(self):
        self.plot_obj.toggle_cells()
    #******************************************************************
    # Have plot obj toggle cell faces
    #    
    def toggle_cell_faces(self):
        self.plot_obj.toggle_cell_face()
    ##############################################################################
    # Setup stuff 
    # 
    ##############################################################################
    
    #******************************************************************
    # Set the size of a widget
    #
    def setSize(self,control,H,W):
        control.setMinimumHeight(H)
        control.setMinimumWidth(W)
        control.setMaximumHeight(H)
        control.setMaximumWidth(W)

    def run_diagnostics_plots(self):
        diagnostics_cfg = self.diagnostics_cfg_file or self.CfgFile
        self.diagnostics_figure = run_force_plots([diagnostics_cfg])

    def test_config(self):
        selected_item = self.DataList.selectedItems()
        self.selected_item = selected_item

        if self.selected_item:
            tst_file_full = self.selected_item[0].text()
            tst_file_pre = os.path.splitext(tst_file_full)
            tst_file = f"{tst_file_pre[0]}.tst"
            try:
                with open(tst_file, "r", encoding="utf-8") as cfg_file:
                    include_config = libconf.load(cfg_file)
            except BaseException as e:
                self.log.log(self,f"Could not read particle data:{e}")
                return
            print("Config file passed")
        else:
            self.no_selection()

        

    #******************************************************************
    # Creatwe the tab
    #
    def Create(self,ParticleBase):
        self.bobj = ParticleBase
        self.cfg = self.bobj.cfg.config
        self.diagnostics_cfg_file = os.path.join(
            self.cfg.analysis_script_dir,
            "batch_test_001.cfg",
        )
        self.log = self.bobj.log
        self.log.log(self,"TabFormGenData finished init.")
        try:
            self.setStyleSheet("background-color:  #eeeeee")
            self.tab_layout = QGridLayout()
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.setLayout(self.tab_layout)

            ## -------------------------------------------------------------
            ## Set parent directory
            LatexcfgFile = QGroupBox("Generate/Test Particle Data")
            self.setSize(LatexcfgFile,650,1000)
            self.tab_layout.addWidget(LatexcfgFile,0,0,4,2,alignment= Qt.AlignmentFlag.AlignLeft)
            
            dirgrid = QGridLayout()
            LatexcfgFile.setLayout(dirgrid)

            self.dirEdit =  QLineEdit()
            self.dirEdit.setStyleSheet("background-color:  #ffffff")
            self.dirEdit.setText("")
            self.setSize(self.dirEdit,30,450)

            self.dirButton = QPushButton("Browse")
            self.setSize(self.dirButton,30,100)
            self.dirButton.setStyleSheet("background-color:  #dddddd")
            self.dirButton.clicked.connect(self.browseFolder)
            dirgrid.addWidget(self.dirButton,0,0)
            dirgrid.addWidget(self.dirEdit,0,1)

            self.AnalyseButton = QPushButton("Simulate")
            self.setSize(self.AnalyseButton,30,100)
            self.AnalyseButton.setStyleSheet("background-color:  #dddddd")
            self.AnalyseButton.clicked.connect(self.run_analysis)
            self.AnalyseButton.setEnabled(True)
            dirgrid.addWidget(self.AnalyseButton,2,0)

            self.DiagnosticsButton = QPushButton("Force Plots")
            self.setSize(self.DiagnosticsButton,30,100)
            self.DiagnosticsButton.setStyleSheet("background-color:  #dddddd")
            self.DiagnosticsButton.clicked.connect(self.run_diagnostics_plots)
            self.DiagnosticsButton.setEnabled(True)
            dirgrid.addWidget(self.DiagnosticsButton,2,1)

            self.RefreshButton = QPushButton("Reload")
            self.setSize(self.RefreshButton,30,100)
            self.RefreshButton.setStyleSheet("background-color:  #dddddd")
            self.RefreshButton.clicked.connect(self.update_list_widget)
            dirgrid.addWidget(self.RefreshButton,2,2)

            self.newButton = QPushButton("Plot")
            self.setSize(self.newButton,30,100)
            self.newButton.setStyleSheet("background-color:  #dddddd")
            self.newButton.clicked.connect(self.plot_particles)
            dirgrid.addWidget(self.newButton,2,3)

            self.GenDataButton = QPushButton("GenData")
            self.setSize(self.GenDataButton,30,100)
            self.GenDataButton.setStyleSheet("background-color:  #dddddd")
            self.GenDataButton.clicked.connect(self.gen_data)
            self.GenDataButton.setEnabled(False)
            dirgrid.addWidget(self.GenDataButton,2,4)

            self.StopButton = QPushButton("Test Config")
            self.setSize(self.StopButton,30,100)
            self.StopButton.setStyleSheet("background-color:  #dddddd")
            self.StopButton.clicked.connect(self.test_config)
            #self.StopButton.setEnabled(False)
            dirgrid.addWidget(self.StopButton,2,5)

            self.ToggleCellsBtn = QPushButton("Toggle Cells")
            self.setSize(self.ToggleCellsBtn,30,100)
            self.ToggleCellsBtn.setStyleSheet("background-color:  #dddddd")
            self.ToggleCellsBtn.clicked.connect(self.toggle_cells)
            dirgrid.addWidget(self.ToggleCellsBtn,3,0)

            self.ToggleCellFacesBtn = QPushButton("Toggle Cell Faces")
            self.setSize(self.ToggleCellFacesBtn,30,110)
            self.ToggleCellFacesBtn.setStyleSheet("background-color:  #dddddd")
            self.ToggleCellFacesBtn.clicked.connect(self.toggle_cell_faces)
            dirgrid.addWidget(self.ToggleCellFacesBtn,3,1)

            self.TestArrayBtn = QPushButton("Test Array Indexing")
            self.setSize(self.TestArrayBtn,30,120)
            self.TestArrayBtn.setStyleSheet("background-color:  #dddddd")
            self.TestArrayBtn.clicked.connect(self.test_index_array)
            dirgrid.addWidget(self.TestArrayBtn,3,2)

            self.VerfPCountBtn = QPushButton("Test Particle Count")
            self.setSize(self.VerfPCountBtn,30,120)
            self.VerfPCountBtn.setStyleSheet("background-color:  #dddddd")
            #self.VerfPCountBtn.clicked.connect(self.toggle_cell_faces)
            dirgrid.addWidget(self.VerfPCountBtn,3,3)

            self.ListParticleBtn = QPushButton("List Particcles")
            self.setSize(self.ListParticleBtn,30,120)
            self.ListParticleBtn.setStyleSheet("background-color:  #dddddd")
            self.ListParticleBtn.clicked.connect(self.list_particles)
            dirgrid.addWidget(self.ListParticleBtn,3,3)

            self.CountCollBtn = QPushButton("Count Collisions")
            self.setSize(self.CountCollBtn,30,120)
            self.CountCollBtn.setStyleSheet("background-color:  #dddddd")
            self.CountCollBtn.clicked.connect(self.count_collisions)
            dirgrid.addWidget(self.CountCollBtn,3,4)

            self.ReadCapBtn = QPushButton("Read Capture File")
            self.setSize(self.ReadCapBtn,30,120)
            self.ReadCapBtn.setStyleSheet("background-color:  #dddddd")
            self.ReadCapBtn.clicked.connect(self.read_capture)
            dirgrid.addWidget(self.ReadCapBtn,3,5)

            list_label = QLabel("Data Set")
            dirgrid.addWidget(list_label,4,0,1,2)
            ### COnfig Files List
            self.ListObj =  QListWidget()
            self.ListObj.setStyleSheet("background-color:  #FFFFFF")
            self.setSize(self.ListObj,350,450)
            dirgrid.addWidget(self.ListObj,5,0,2,2)
            self.ListObj.itemSelectionChanged.connect(lambda: self.valueChange(self.ListObj))   
            ### Data Files List
            self.DataList =  QListWidget()
            self.DataList.setStyleSheet("background-color:  #FFFFFF")
            self.setSize(self.DataList,350,450)
            dirgrid.addWidget(self.DataList,5,3,2,2)
            self.DataList.itemSelectionChanged.connect(lambda: self.DataFileChange(self.DataList))   


            view_label = QLabel("Views")
            dirgrid.addWidget(view_label,7,0,1,2)

            self.ViewList =  QListWidget()
            self.ViewList.setStyleSheet("background-color:  #FFFFFF")
            self.setSize(self.ViewList,120,450)
            #self.ViewList.setSpacing(1)
            dirgrid.addWidget(self.ViewList,7,0,1,2)
            
            ## -------------------------------------------------------------
            ## Comunications Interface
            self.terminal =  QTextEdit(self)
            self.terminal.setStyleSheet("background-color:  #ffffff; color: green")
            self.setSize(self.terminal,225,900)
            self.tab_layout.addWidget(self.terminal,9,0,3,3,alignment= Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        except BaseException as e:
            self.log.log(self,f"Error in Create:{e}")
            return 
        
        self.bobj.connect_to_output(self.terminal)
        self.plot_obj = PlotParticles()
        # update the list
        
        for ii in self.plot_obj.views:
            self.ViewList.addItem(str(ii))
        self.log.log(self,"TabFormLatex finished Create.")        
        #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/GenDUP.cfg")
        #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/GenPQBSequential.cfg")
        #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/GenPQBRandom.cfg")
        #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/TwoParticleHorizontal.cfg")
        #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/TwoParticleAngled.cfg")
        #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/TestCompressor.cfg")
        #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/TestReservoir.cfg")
        #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/CDNozzle.cfg")
        #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/FreeStream.cfg")
        #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/FreeStreamHeteroPy.cfg")
        #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/lumens.cfg")
        self.load_item_cfg("C:/_DJ/gPCD/python/cfg_gendata/Cathedral.cfg")
        self.update_list_widget()
        self.update_data_list_widget()
        
    def valueChange(self,listObj):  
        selected_items = listObj.selectedItems()
        Text = selected_items[0].text() if selected_items else ""   
        self.dirEdit.setText(Text)
        self.refresh_dir(Text)   
        self.load_item_cfg(Text)
    
    def DataFileChange(self,dataList):
        selected_items = dataList.selectedItems()
        self.DataFileText = selected_items[0].text() if selected_items else ""
        print(f"Selected data file:{self.DataFileText}")   
