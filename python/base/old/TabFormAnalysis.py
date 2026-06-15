import sys
from contextlib import redirect_stdout
from io import StringIO
from sys import stderr, stdout
from PyQt6.QtCore import Qt,QObject
from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox
from PyQt6.QtWidgets import QGridLayout, QTabWidget, QLineEdit,QListWidget
from PyQt6.QtWidgets import QPushButton, QGroupBox,QTextEdit
from PyQt6 import QtCore
from _thread import *
from gbase.ConfigUtility import *
import subprocess
import threading
from subprocess import Popen, CREATE_NEW_CONSOLE
import asyncio
from runner import run_analysis
DETACHED_PROCESS = 0x00000008
        

class TabFormAnalysis(QTabWidget):

    
    run_obj = None
    terminal = None
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
    
    
    def setSize(self,control,H,W):
        control.setMinimumHeight(H)
        control.setMinimumWidth(W)
        control.setMaximumHeight(H)
        control.setMaximumWidth(W)

    def msg_box(self,text):
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.exec()

    async def run_command(self, cmd,wdir):
        proc = await asyncio.create_subprocess_shell(cmd, cwd=wdir)
        
  
    def run(self):
        self.selected_item = self.ListObj.currentRow()
        if self.selected_item:
            self.ListObj.setCurrentRow(self.selected_item)  
            item = self.ListObj.currentItem().text()
            run_analysis(self.cfg.analysis_script_dir + "/" + item)
        else:
            self.msg_box("Select an item to run in list box.")
    
    def refresh_dir(self):
        ## -------------------------------------------------------------
        ## CFg Files Select Interface
        self.selected_item = self.ListObj.currentRow()
        item = self.ListObj.currentItem().text()
        self.CfgFile = self.cfg.analysis_script_dir + "/" + item
        notepad_plus_plus_path = "C:\\Program Files\\Notepad++\\notepad++.exe" # Adjust as needed
        subprocess.Popen([notepad_plus_plus_path, self.CfgFile])

    def Create(self,Base):
        
        self.bobj = Base
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.log.log(self,"TabFormLatex finished init.")
        self.log.log(self,"TabFormLatex started Create.")
        try:
            self.setStyleSheet("background-color:  #eeeeee")
            self.tab_layout = QGridLayout()
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.setLayout(self.tab_layout)
            ## -------------------------------------------------------------
            ## Set parent directory
            LatexcfgFile = QGroupBox("Run Configuraiton")
            self.setSize(LatexcfgFile,600,650)
            self.tab_layout.addWidget(LatexcfgFile,0,0,2,2,alignment= Qt.AlignmentFlag.AlignLeft)
            
            dirgrid = QGridLayout()
            LatexcfgFile.setLayout(dirgrid)

            
            self.ListObj =  QListWidget()
            #self.ListObj.setFont(self.font)
            self.ListObj.setStyleSheet("background-color:  #FFFFFF")
            index = 0
            self.cfg_files = [i for i in os.listdir(self.cfg.analysis_script_dir) if i.endswith("cfg")]
            for ii in range(len(self.cfg_files)):
                self.ListObj.insertItem(ii,self.cfg_files[ii])
            self.ListObj.currentItemChanged.connect(self.refresh_dir)
            dirgrid.addWidget(self.ListObj,3,0,1,2)
            self.runButton = QPushButton("Run")
            self.setSize(self.runButton,30,100)
            self.runButton.setStyleSheet("background-color:  #dddddd")
            self.runButton.clicked.connect(self.run)
            dirgrid.addWidget(self.runButton,0,0)
            

        
            ## -------------------------------------------------------------
            ## Comunications Interface
            self.terminal =  QTextEdit(self)
            self.terminal.setStyleSheet("background-color:  #ffffff; color: green")
            self.setSize(self.terminal,225,650)
            self.tab_layout.addWidget(self.terminal,4,0,1,3,alignment= Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        except BaseException as e:
            self.log.log(self,e)
        
    def valueChange(self,listObj):  
        selected_items = listObj.selectedItems()
        if selected_items:
            pass

        self.bobj.connect_to_output(self.terminal)
    