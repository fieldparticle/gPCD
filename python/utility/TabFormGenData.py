import sys
import importlib
from contextlib import redirect_stdout
from io import StringIO
from sys import stderr, stdout
from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox
from PyQt6.QtWidgets import QGridLayout, QTabWidget, QLineEdit,QListWidget
from PyQt6.QtWidgets import QPushButton, QGroupBox
from PyQt6 import QtCore
from ConfigClass import *
from LatexClass import *
from CfgLabel import *
from GenSig import *
from PyQt6.QtCore import (
    QObject,
    QRunnable,
    QThreadPool,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)
from PanelGenDataConfig import *
import glob


class TabGenData(QTabWidget,QRunnable):
    
    texFolder = ""
    CfgFile = ""
    texFileName = ""
    hasConfig = False
    itemcfg = ConfigClass("Latex Class")
    startDir = "J:/MOD/FPIBGUtility/Latex"
    startDir = "J:/FPIBGJournalStaticV2/rpt"
    startDir = "J:/FPIBGDATAT/cfg"
    selected_item = -1
    ObjName = ""
    ltxObj = None
    select_list = []
    gen_obj = None
    sel_dict = None

    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs )
        self.threadpool = QThreadPool()
        thread_count = self.threadpool.maxThreadCount()
        print(f"Multithreading with maximum {thread_count} threads")
       
        
    
    def setSize(self,control,H,W):
        control.setMinimumHeight(H)
        control.setMinimumWidth(W)
        control.setMaximumHeight(H)
        control.setMaximumWidth(W)

    def update_cfg_section(self):
        self.ltxObj.clearConfigGrp()
        self.ltxObj.OpenLatxCFG()
        files_names = self.itemcfg.config.data_dir + "/*.bin"
        files = glob.glob(files_names)
        for ii in files:
            self.ListObj.addItem(ii)
        self.SaveButton.setEnabled(True)
        self.GenDataButton.setEnabled(True)
    
    def SaveConfigurationFile(self):
        self.ltxObj.updateCfgData()
        
        #self.ltxObj.clearConfigGrp()

  
    def browseFolder(self):
        """ Opens a dialog window for the user to select a folder in the file system. """
        #folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        
        folder = QFileDialog.getOpenFileName(self, ("Open File"),
                                       self.startDir,
                                       ("Configuration File (*.cfg)"))
        try:
            # Remove the intro image
            if self.intro_image != None:
                self.tab_layout.removeWidget(self.intro_image)
                #layout.removeWidget(self.widget_name)
                self.intro_image.deleteLater()
                self.intro_image = None
        except BaseException as e:
            txt = "At TabFormData" + e
            print(txt)

        # if a valid folder
        if folder[0]:
            # Set the config file member
            self.CfgFile = folder[0]
            self.texFolder = os.path.dirname(self.CfgFile)
            self.texFileName = os.path.splitext(os.path.basename(self.CfgFile))[0]
            self.dirEdit.setText(self.CfgFile)

            try :
                # Create a configuration class from this config file
                self.itemcfg = ConfigClass(self.CfgFile)
                self.itemcfg.Create(self.bobj.log,self.CfgFile)
                
            except BaseException as e:
                self.log.log(self,f"TabFormGenData Unable to open item configurations file:{e}")
                self.hasConfig = False
                return 
            # If config reads ok
            if self.hasConfig == True:
                # Clear the last config group
                self.ltxObj.clearConfigGrp()

            # Get bin files already in the data directory - and list them
            files_names = self.itemcfg.config.data_dir + "/*.bin"
            files = glob.glob(files_names)
            self.ListObj.clear()
            for ii in files:
                 self.ListObj.addItem(ii)

            # can now use save,gendata,and fill cell array     
            self.SaveButton.setEnabled(True)
            self.GenDataButton.setEnabled(True)
            self.CAButton.setEnabled(True)
            self.TstButton.setEnabled(True)
            self.ColButton.setEnabled(True)

            # Here specify as a string the gendata class
            gen_class_txt = f"{self.itemcfg.config.import_text}.{self.itemcfg.config.import_text}"

            # Create the 
            self.ltxObj = GenDataConfigPanel()
            self.ltxObj.Create(self.bobj,self,gen_class_txt)
            self.ltxObj.setConfigGroup(self.tab_layout)
            self.ltxObj.OpenLatxCFG()
            self.hasConfig = True
            #i = self.tab_layout.indexOf(self.intro_image)
            #layout.itemAt(i)
           

   

    def browseNewItem(self):
        """ Opens a dialog window for the user to select a folder in the file system. """
        #folder = QFileDialog.getExistingDirectory(self, "Select Folder")

        if(self.ListObj.currentRow() < 0):
            print("Must select type first.")
            return
        else:
            print(f"Opening Row {self.ListObj.currentRow()}")

        folder = QFileDialog.getSaveFileName(self, ("Open File"),
                                       "J:/FPIBGJournalStaticV2/rpt",
                                       ("Images (*.cfg)"))
        cfg_cnt = ""
        if folder[0]:
            self.CfgFile = folder[0]
            with open(self.cfg.single_template, 'r') as file:
                cfg_cnt = file.read()
            #print(cfg_cnt)
            file.close()
            with open(folder[0], 'w') as file:
                file.write(cfg_cnt)
                file.close()
            self.texFolder = os.path.dirname(self.CfgFile)
            self.texFileName = os.path.splitext(os.path.basename(self.CfgFile))[0]
            self.dirEdit.setText(self.CfgFile)
            self.OpenLatxCFG(self.CfgFile)
            self.log.log(self,f"Opened {self.CfgFile}")
            self.tab_layout.removeWidget(self.intro_image)

    def plot_closed(self):
        self.ltxObj.clearConfigGrp()
        self.ltxObj.setConfigGroup(self.tab_layout)
        self.ltxObj.OpenLatxCFG()

#################################################### GEN DATA

# load all lines from the particle selections file into selections list
    
    def gen_one_data(self,progress_callback):
        return self.gen_obj.gen_data_base(self.index,self.sel_dict,progress_callback)
            

    def result(self, s):
        pass


    def thread_complete(self):
        print("Thread Complete")
        self.bobj.log.log(self,f"Wrote {self.gen_obj.count} particles to {self.gen_obj.test_bin_name}")
        self.gen_obj.verify_particle_count(self.gen_obj.test_bin_name)
        self.index += 1
        if (self.index >= len(self.select_list)) or (self.gen_obj.flg_stop == True):
            self.GenDataButton.setStyleSheet("background-color:  #dddddd")
            self.GenDataButton.clicked.connect(self.gen_data)
            self.GenDataButton.setText("GenData")
            files_names = self.itemcfg.config.data_dir + "/*.bin"
            files = glob.glob(files_names)
            self.ListObj.clear()
            for ii in files:
                 self.ListObj.addItem(ii)

            return
        
        else:
            self.launch_thread()

    def progress_fn(self, n):
        print(f"{n:.1f}% done")

    def launch_thread(self):
        self.sel_dict = self.select_list[self.index]
        worker = Worker( self.gen_one_data) 
        worker.signals.result.connect(self.result)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)
    
    def stop_data(self):
        self.gen_obj.stop_thread()
        self.GenDataButton.setStyleSheet("background-color:  #dddddd")
        self.GenDataButton.clicked.connect(self.gen_data)
        self.GenDataButton.setText("GenData")

    def gen_data(self):
        self.gen_obj = self.ltxObj.getGenObj()
        self.GenDataButton.setStyleSheet("background-color:  #ff0000")
        self.GenDataButton.setText("Stop")
        self.GenDataButton.clicked.connect(self.stop_data)
        
        if not os.path.exists(self.itemcfg.config.data_dir):
            os.makedirs(self.itemcfg.config.data_dir)
        self.select_list = self.gen_obj.open_selections_file()
        self.index = 0
        self.launch_thread()
           
     
    def list_particles(self):
        selected_item = self.ListObj.selectedItems()
        self.selected_item = selected_item
        if self.selected_item:
            self.gen_obj = self.ltxObj.getGenObj()
            p_list = self.gen_obj.read_all_particle_data(self.selected_item[0].text())
            self.gen_obj.list_particles(p_list,self.terminal)
        else:
            print("no item selected")
        
    def test_index_array(self):
        selected_item = self.ListObj.selectedItems()
        self.selected_item = selected_item
        if self.selected_item:
           self.gen_obj = self.ltxObj.getGenObj()
           self.gen_obj.test_array_to_index()
        else:
            print("no item selected")

    def count_collsions(self):
        selected_item = self.ListObj.selectedItems()
        self.selected_item = selected_item
           
        if self.selected_item:
           self.gen_obj = self.ltxObj.getGenObj()
           self.gen_obj.count_collions()

    def out_put_cell_ary(self):
        selected_item = self.ListObj.selectedItems()
        self.selected_item = selected_item
           
        if self.selected_item:
            self.ltxObj.gen_obj.out_put_cell_ary()
        else:
            print("no item selected")

    
       
    def plot_particles(self):
        selected_item = self.ListObj.selectedItems()
        self.selected_item = selected_item
        self.ltxObj.close_plot()
        if self.selected_item:
            self.ltxObj.plot(self.selected_item[0].text())
        else:
            print("no item selected")
       

    def Create(self,FPIBGBase):
        self.bobj = FPIBGBase
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.log.log(self,"TabFormLatex finished init.")
        try:
            self.setStyleSheet("background-color:  #eeeeee")
            self.tab_layout = QGridLayout()
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.setLayout(self.tab_layout)

            ## -------------------------------------------------------------
            ## Set parent directory
            LatexcfgFile = QGroupBox("Generate/Test Particle Data")
            self.setSize(LatexcfgFile,450,500)
            self.tab_layout.addWidget(LatexcfgFile,0,0,2,2,alignment= Qt.AlignmentFlag.AlignLeft)
            
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

            self.SaveButton = QPushButton("Save")
            self.setSize(self.SaveButton,30,100)
            self.SaveButton.setStyleSheet("background-color:  #dddddd")
            self.SaveButton.clicked.connect(self.SaveConfigurationFile)
            self.SaveButton.setEnabled(False)
            dirgrid.addWidget(self.SaveButton,2,0)

            self.newButton = QPushButton("Plot")
            self.setSize(self.newButton,30,100)
            self.newButton.setStyleSheet("background-color:  #dddddd")
            self.newButton.clicked.connect(self.plot_particles)
            dirgrid.addWidget(self.newButton,2,1)

            self.listButton = QPushButton("List Partcles")
            self.setSize(self.listButton,30,100)
            self.listButton.setStyleSheet("background-color:  #dddddd")
            self.listButton.clicked.connect(self.list_particles)
            dirgrid.addWidget(self.listButton,2,2)


            self.GenDataButton = QPushButton("GenData")
            self.setSize(self.GenDataButton,30,100)
            self.GenDataButton.setStyleSheet("background-color:  #dddddd")
            self.GenDataButton.clicked.connect(self.gen_data)
            self.GenDataButton.setEnabled(False)
            dirgrid.addWidget(self.GenDataButton,2,3)
            
            self.CAButton = QPushButton("Fill Cell Array")
            self.setSize(self.CAButton,30,100)
            self.CAButton.setStyleSheet("background-color:  #dddddd")
            self.CAButton.clicked.connect(self.out_put_cell_ary)
            self.CAButton.setEnabled(False)
            dirgrid.addWidget(self.CAButton,3,0)
            
            self.TstButton = QPushButton("Test Array Indexing")
            self.setSize(self.TstButton,30,100)
            self.TstButton.setStyleSheet("background-color:  #dddddd")
            self.TstButton.clicked.connect(self.test_index_array)
            self.TstButton.setEnabled(False)
            dirgrid.addWidget(self.TstButton,3,1)
            
            self.ColButton = QPushButton("Count Collisions")
            self.setSize(self.ColButton,30,100)
            self.ColButton.setStyleSheet("background-color:  #dddddd")
            self.ColButton.clicked.connect(self.count_collsions)
            self.ColButton.setEnabled(False)
            dirgrid.addWidget(self.ColButton,3,2)

            self.ListObj =  QListWidget()
            #self.ListObj.setFont(self.font)
            self.ListObj.setStyleSheet("background-color:  #FFFFFF")
            self.setSize(self.ListObj,350,450)
            self.vcnt = 0            
            self.ListObj.itemSelectionChanged.connect(lambda: self.valueChange(self.ListObj))
            dirgrid.addWidget(self.ListObj,4,0,1,2)
            self.log.log(self,"TabFormLatex finished Create.")

            self.intro_image = QLabel(self)
            self.pixmap = QPixmap('TestingProcess.png')
            self.intro_image.setPixmap(self.pixmap)
            #self.setSize(self.intro_image,350,450)
            ##Add items to the layout
            self.tab_layout.addWidget(self.intro_image,0,2,2,2)
            
            ## -------------------------------------------------------------
            ## Comunications Interface
            self.terminal =  QTextEdit(self)
            self.terminal.setStyleSheet("background-color:  #ffffff; color: green")
            self.setSize(self.terminal,225,900)
            self.tab_layout.addWidget(self.terminal,5,0,3,3,alignment= Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        except BaseException as e:
            self.log.log(self,f"Error in Create:{e}")
            self.bobj.connect_to_output(self.terminal)
   
    def valueChange(self,listObj):  
        selected_items = listObj.selectedItems()
        if selected_items:
            #print("List object Value Changed",selected_items[0].text())
            self.gen_obj = self.ltxObj.getGenObj()
            self.gen_obj.update_selection(selected_items[0].text())         
    