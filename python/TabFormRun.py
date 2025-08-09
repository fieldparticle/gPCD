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
from ConfigUtility import *
import subprocess
import threading
from subprocess import Popen, CREATE_NEW_CONSOLE
import asyncio
DETACHED_PROCESS = 0x00000008
class TabFormRun(QTabWidget):

    run_items = []
    run_obj = None
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
        selected_item = self.ListObj.selectedItems()
        self.selected_item = selected_item
        if self.selected_item:
            item = self.run_items[self.ListObj.currentRow()]
            wrk_dir = item[1]
            excuteable = item[2]
            cmd_line = item[3].split(' ')
            exe_line = wrk_dir + "/" + excuteable
            command= []
            command.append(exe_line)
            output = ""
            for ii in cmd_line:
                command.append(ii)
            try:
                process= subprocess.Popen(command, cwd=wrk_dir)
                self.log.log(self,f"Process Launched")
            except BaseException as e:
                self.log.log(self,f"Error running PCD:{e}")
        else:
            self.msg_box("Select an item to run in list box.")


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
            self.setSize(LatexcfgFile,200,650)
            self.tab_layout.addWidget(LatexcfgFile,0,0,2,2,alignment= Qt.AlignmentFlag.AlignLeft)
            
            dirgrid = QGridLayout()
            LatexcfgFile.setLayout(dirgrid)

            
            self.ListObj =  QListWidget()
            #self.ListObj.setFont(self.font)
            self.ListObj.setStyleSheet("background-color:  #FFFFFF")
            index = 0
            for k ,v in self.cfg.items():
                if"benching" in k:
                    for kk,vv in v.items():
                        self.run_items.append([vv[0],vv[1],vv[2],vv[3]])
                        self.ListObj.insertItem(index,vv[0]+vv[1])
                        index+=1
            #self.ListObj.itemSelectionChanged.connect(lambda: self.valueChangeArray(self.ListObj))
            dirgrid.addWidget(self.ListObj,3,0,1,2)
            self.ListObj.setCurrentRow(0)
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
        
        self.bobj.connect_to_output(self.terminal)
    