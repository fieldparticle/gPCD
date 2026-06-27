import sys
from contextlib import redirect_stdout
from io import StringIO
from sys import stderr, stdout
from PyQt6.QtCore import Qt,QObject
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QFileDialog, QLabel, QGroupBox,QMessageBox
from PyQt6.QtWidgets import QGridLayout, QTabWidget, QLineEdit,QListWidget
from PyQt6.QtWidgets import QPushButton, QGroupBox,QTextEdit
from PyQt6 import QtCore
from HSVWheel import *
from _thread import *
from gbase.ConfigUtility import *
import glob        
import subprocess
subprocess.__file__

class TabFormCDNOZ(QTabWidget):

    run_items = []
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

    def update_hsv_wheel(self):
       
        arrows = []

        for item in self.itemcfg.arrows:
            low = float(item.low)
            high = float(item.high)
            sat = float(item.sat)
            color = QColor(str(item.color))

            arrows.append([low, high, sat, color])

        self.hsv_wheel.set_arrows(arrows)
    #******************************************************************
    # Update the list widget
    #
    def update_list_widget(self):
        self.ListObj.clear()
        files_names = self.cfg.cdnoz_dir + "/*.cfg"
        files = glob.glob(files_names)
        for ii in files:
            self.ListObj.addItem(ii)

   #******************************************************************
    # Load the configuration data
    #
    def load_item_cfg(self,file):
        self.setFocus()
        self.CfgFile = file
        self.texFolder = os.path.dirname(self.CfgFile)
        self.texFileName = os.path.splitext(os.path.basename(self.CfgFile))[0]

        # Open the item configuration filke
        try :
            self.itemcfgFile = ConfigUtility(self.CfgFile)
            self.itemcfgFile.Create(self.bobj.log,self.CfgFile)
            self.itemcfg = self.itemcfgFile.config
        except BaseException as e:
            self.log.log(self,f"Unable to open item configurations file:{e}")
            self.hasConfig = False
            return False
        try:
            notepad_plus_plus_path = "C:\\Program Files\\Notepad++\\notepad++.exe" # Adjust as needed
            subprocess.Popen([notepad_plus_plus_path, self.CfgFile])
        except BaseException as e:
            self.log.log(self,f"Unable to import data generation file: error:{e}")
            return False
  
    def update(self):
        self.load_item_cfg(self.cur_cfg_file)
        self.image = QImage(self.itemcfg.image_file)
        self.pixmap = QPixmap.fromImage(self.image)
        aspect_ratio = self.pixmap.width() / self.pixmap.height()
         # Optional: scale images to a fixed size
        pixmap = self.pixmap.scaled(
            self.itemcfg.scale_x,self.itemcfg.scale_y,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        self.ImageBox.resize(pixmap.size())
        self.ImageBox.setPixmap(pixmap)
        self.update_hsv_wheel()
        self.filter_image()

    def ListObjChange(self,listObj):  
        selected_items = listObj.selectedItems()
        self.cur_cfg_file = selected_items[0].text() if selected_items else ""   
        self.load_item_cfg(self.cur_cfg_file)
        self.image = QImage(self.itemcfg.image_file)
        self.pixmap = QPixmap.fromImage(self.image)
        aspect_ratio = self.pixmap.width() / self.pixmap.height()
         # Optional: scale images to a fixed size
        pixmap = self.pixmap.scaled(
            self.itemcfg.scale_x,self.itemcfg.scale_y,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        self.ImageBox.resize(pixmap.size())
        self.ImageBox.setPixmap(pixmap)
        self.update_hsv_wheel()
        self.filter_image()

    def filter_image(self):
        filtered = self.isolate_hsv_ranges(self.image, self.hsv_wheel.arrows)

        filtered_pixmap = QPixmap.fromImage(filtered).scaled(
            self.itemcfg.scale_x,
            self.itemcfg.scale_y,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.pImageBox.resize(filtered_pixmap.size())
        self.pImageBox.setPixmap(filtered_pixmap)

    def hue_in_range(self, hue, low, high):
        low = low % 360
        high = high % 360

        if low <= high:
            return low <= hue <= high
        else:
            return hue >= low or hue <= high

    def isolate_hsv_ranges(self, image, arrows):
        out = QImage(image.size(), QImage.Format.Format_ARGB32)
        out.fill(QColor(255, 255, 255, 255))

        for y in range(image.height()):
            for x in range(image.width()):
                color = image.pixelColor(x, y)

                if color.valueF() < 0.05:
                    continue

                hue = color.hue()
                sat = color.saturationF()

                if hue < 0:
                    continue

                for low, high, sat_len, arrow_color in arrows:
                    if self.hue_in_range(hue, low, high) and sat <= sat_len:
                        out.setPixelColor(x, y, color)   # keep original image color
                        # out.setPixelColor(x, y, QColor(arrow_color))  # recolor selection
                        break

        return out

    
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
            LatexcfgFile = QGroupBox("Configuration")
            self.setSize(LatexcfgFile,300,300)
            self.tab_layout.addWidget(LatexcfgFile,0,0,2,2,alignment= Qt.AlignmentFlag.AlignLeft)
            dirgrid = QGridLayout()
            LatexcfgFile.setLayout(dirgrid)

            self.runButton = QPushButton("Update")
            self.setSize(self.runButton,30,100)
            self.runButton.setStyleSheet("background-color:  #dddddd")
            self.runButton.clicked.connect(self.update)
            dirgrid.addWidget(self.runButton,0,0)
            
           
            self.ListObj =  QListWidget()
            self.ListObj.setStyleSheet("background-color:  #FFFFFF")
            index = 0
            self.ListObj.itemSelectionChanged.connect(lambda: self.ListObjChange(self.ListObj))
            self.setSize(self.ListObj,200,280)
            dirgrid.addWidget(self.ListObj,3,0,1,2)
            self.ListObj.setCurrentRow(0)
            self.update_list_widget()

            self.ImageBox = QLabel("here")
            #self.setSize(self.ImageBox,200,650)
            self.ImageBox.setStyleSheet("background-color:  #FFFFFF")
            self.tab_layout.addWidget(self.ImageBox,0,3,1,2)
            self.ImageBox.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.ImageBox.setAlignment(Qt.AlignmentFlag.AlignTop)

            self.pImageBox = QLabel("here")
            #self.setSize(self.ImageBox,200,650)
            self.pImageBox.setStyleSheet("background-color:  #FFFFFF")
            self.tab_layout.addWidget(self.pImageBox,2,3,1,2)
            self.pImageBox.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.pImageBox.setAlignment(Qt.AlignmentFlag.AlignTop)


            self.hsv_wheel = HSVWheel(400)
            self.tab_layout.addWidget(self.hsv_wheel,3,0,1,2)
            self.hsv_wheel.repaint()
            
        except BaseException as e:
            self.log.log(self,e)
        
        self.bobj.connect_to_output(self.terminal)
    