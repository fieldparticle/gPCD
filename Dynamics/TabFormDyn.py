import sys
import importlib
import subprocess, os
from _thread import *
from contextlib import redirect_stdout
from io import StringIO
from sys import stderr, stdout
from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox,QLabel
from PyQt6.QtWidgets import QGridLayout, QTabWidget, QLineEdit,QListWidget
from PyQt6.QtWidgets import QPushButton, QGroupBox,QTextEdit
from PyQt6.QtGui import QFocusEvent
from PyQt6 import QtCore
from PyQt6.QtCore import Qt,QThread,QEvent, pyqtSignal,pyqtSlot,QObject,QRunnable,QThreadPool
from ConfigUtility import *
import tkinter as tk
from tkinter import * 
from tkinter import messagebox 
import glob
import traceback
import time
import struct
import ctypes


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
                ("Acc_a",  ctypes.c_double),
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
        folder = QFileDialog.getOpenFileName(self, ("Open File"),
                                       self.cfg.report_start_dir,
                                       ("Configuration File (*.cfg)"))
        
        if folder[0]:
           self.load_item_cfg(folder[0])
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
            self.setSize(LatexcfgFile,120,350)
            self.tab_layout.addWidget(LatexcfgFile,0,0,2,2,alignment= Qt.AlignmentFlag.AlignLeft)
            
            dirgrid = QGridLayout()
            LatexcfgFile.setLayout(dirgrid)

            #self.dirEdit =  QLineEdit()
            #self.dirEdit.setStyleSheet("background-color:  #ffffff")
            #self.dirEdit.setText("")
            #self.setSize(self.dirEdit,30,450)
            #dirgrid.addWidget(self.dirEdit,0,1)

            self.dirButton = QPushButton("Browse")
            self.setSize(self.dirButton,30,100)
            self.dirButton.setStyleSheet("background-color:  #dddddd")
            self.dirButton.clicked.connect(self.browseFolder)
            dirgrid.addWidget(self.dirButton,0,0)

            self.RefreshButton = QPushButton("Reload")
            self.setSize(self.RefreshButton,30,100)
            self.RefreshButton.setStyleSheet("background-color:  #dddddd")
            #self.RefreshButton.clicked.connect(self.refresh)
            dirgrid.addWidget(self.RefreshButton,0,1)

            self.StopButton = QPushButton("Stop Gen")
            self.setSize(self.StopButton,30,100)
            self.StopButton.setStyleSheet("background-color:  #dddddd")
            #self.StopButton.clicked.connect(self.gen_data)
            self.StopButton.setEnabled(False)
            dirgrid.addWidget(self.StopButton,0,2)

            ### COnfig File List
            self.cfg_files = [i for i in os.listdir(self.cfg.report_start_dir) if i.endswith("cfg")]
            self.CfgListObj =  QListWidget()
            self.CfgListObj.setStyleSheet("background-color:  #FFFFFF")
            self.vcnt = 0  
            self.setSize(self.CfgListObj,225,450)

            for ii in range(len(self.cfg_files)):
                self.CfgListObj.insertItem(ii,self.cfg_files[ii]) 
            self.CfgListObj.currentItemChanged.connect(self.cfg_on_current_item_changed)
            
            self.tab_layout.addWidget(self.CfgListObj,3,0,1,1)


            
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
    