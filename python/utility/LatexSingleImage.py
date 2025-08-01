from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget,QScrollArea,QVBoxLayout,QTabWidget,QFileDialog
from PyQt6.QtGui import QPixmap
from CfgLabel import *
from LatexClass import *
from LatexConfigurationClass import *
class LatexSingleImage(LatexConfigurationClass):
    objArry = []
    dictTab = []
    tabCount = 0
    layouts = []
    lyCount = 0
  


    def __init__(self,Parent):
        super().__init__(Parent)
        self.LatexFileImage = LatexImageWriter(self.Parent)

   
    def updateCfgData(self):
        for oob in self.objArry:
            oob.updateCFGData()
        self.itemcfg.updateCfg()
        self.LatexFileImage.Write() 

    def OpenLatxCFG(self):
        print(self.itemcfg)
        self.doItems(self.itemcfg.config)
   
    def setImgGroup(self,layout):
        ## Image Interface
        self.imageGroupLayout = QGridLayout()
        self.Parent.imgmgrp.setLayout(self.imageGroupLayout)
        self.image = QLabel()
        self.image.setStyleSheet("background-color:  #ffffff")
        self.setSize(self.image,15,15)
        self.imageGroupLayout.addWidget(self.image,1,0,alignment= Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.ImageName = self.itemcfg.config.images_name_text
        self.ImagePath = self.itemcfg.config.tex_dir + "/" + self.ImageName
        self.pixmap = QPixmap(self.ImagePath)
        self.setSize(self.Parent.imgmgrp,self.pixmap.height()+20,self.pixmap.width()) 
        self.setSize(self.image,self.pixmap.height()+20,self.pixmap.width()) 
        self.image.setPixmap(self.pixmap)
        return self.Parent.imgmgrp
    
        

   
    
 

   