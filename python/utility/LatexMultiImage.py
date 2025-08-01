from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget,QScrollArea,QVBoxLayout,QTabWidget,QFileDialog
from PyQt6.QtGui import QPixmap
from CfgLabel import *
from LatexClass import *
from LatexConfigurationClass import *

class LatexMultiImage(LatexConfigurationClass):

    def __init__(self,Parent):
        super().__init__(Parent)
        self.LatexFileImage = LatexMultiImageWriter(Parent)

    def setImgGroup(self):
        
        # -------------------------------------------------------------
        ## Image Interface
        for ii in self.itemcfg.config.images_name_array:
            self.imageList.append(ii)
            if self.name_text == "" : 
                self.name_text.setText(os.path.splitext(os.path.basename(ii))[0])
            self.images_dir.setText(os.path.dirname(ii))

        self.itemcfg.config.images_name_array
        self.imageGroupLayout = QGridLayout()
        self.Parent.imgmgrp.setLayout(self.imageGroupLayout)
        self.updateImageGroup()
        return self.Parent.imgmgrp
    

    def updateImageGroup(self):
        row = 0
        col = 0
        self.setSize(self.Parent.imgmgrp,500,500)
        self.clearLayout(self.imageGroupLayout)
        
        for ii in self.imageList:
            image = QLabel()
            image.setStyleSheet("background-color:  #ffffff")
            pixmap = QPixmap(ii)
            pix = pixmap.scaled(250,250)
            self.setSize(image,250,250) 
            image.setPixmap(pix)
            self.imageGroupLayout.addWidget(image,row,col,alignment= Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            col +=1
        

   