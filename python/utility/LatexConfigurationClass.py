
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget,QScrollArea,QVBoxLayout,QTabWidget,QFileDialog
from PyQt6.QtGui import QPixmap
from CfgLabel import *
from LatexClass import *
from ConfigClass import *
import csv
class LatexConfigurationClass():
    objArry = []
    dictTab = []
    tabCount = 0
    layouts = []
    lyCount = 0
    imageList = []
    hasRawData = False
    hasSummaryData = False
    topdir = ""
    sumFile = ""
    data_files = []
    average_list = []
       

    #LatexFileImage = None
    imagelo = None

    def __init__(self,Parent):
        self.Parent = Parent
        self.bobj = self.Parent.bobj
        self.gcfg = self.bobj.cfg.config
        self.log = self.bobj.log
        # So we can pass a diffenrent item conf when parent does not own just one
        self.itemcfg = Parent.itemcfg 
        self.cfg = Parent.itemcfg .config
        

    def setTypeText(self,Text):
        self.type_text.setTypeText(Text)
        
    def updateCfgData(self):
        for oob in self.objArry:
            oob.updateCFGData()
        self.itemcfg.updateCfg()
        self.LatexFileImage.Write() 

    def getTexList(self):
        return self.LatexFileImage.get_tex_list()

    def setSize(self,control,H,W):
        control.setMinimumHeight(H)
        control.setMinimumWidth(W)
        control.setMaximumHeight(H)
        control.setMaximumWidth(W)

    def itemChanged(self,key,val):
        return   
 
    def SaveConfigurationFile(self):
        self.itemcfg.updateCfg()
        self.LatexFileImage.Create(self.bobj,self.itemcfg.config.name_text)
        self.LatexFileImage.cleanPRE = True
        self.LatexFileImage.width = 0
        self.LatexFileImage.height = 0
        self.LatexFileImage.Write(self.itemcfg.config,plt) 
    
    def OpenLatxCFG(self):
        #print(self.itemcfg)
        #self.LatexFileImage.outDirectory = self.itemcfg.config.tex_dir
        #self.LatexFileImage.ltxDirectory = self.itemcfg.config.tex_image_dir
        self.doItems(self.itemcfg.config)
    
    def clearLayout(self,layout):
     #   print("-- -- input layout: "+str(layout))
        for i in reversed(range(layout.count())):
            layoutItem = layout.itemAt(i)
            if layoutItem.widget() is not None:
                widgetToRemove = layoutItem.widget()
      #          print("found widget: " + str(widgetToRemove))
                widgetToRemove.setParent(None)
                layout.removeWidget(widgetToRemove)
            elif layoutItem.spacerItem() is not None:
                continue
       #         print("found spacer: " + str(layoutItem.spacerItem()))
            else:
                layoutToRemove = layout.itemAt(i)
                #        print("-- found Layout: "+str(layoutToRemove))
                self.clearLayout(layoutToRemove)

    def clearConfigGrp(self):
        del self.objArry [:]
        del self.dictTab[:]
        self.tabCount = 0
        del self.layouts[:]
        self.lyCount = 0
        self.clearLayout(self.cfglayout)
        

    def setConfigGroup(self,layout):
        self.ConfigGroup = QGroupBox("Latex File Configuration")
        layout.addWidget(self.ConfigGroup,0,2,1,1,alignment= Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.cfglayout = QVBoxLayout()
        self.setSize(self.ConfigGroup,400,700) 
        self.ConfigGroup.setLayout(self.cfglayout)
        self.tabs = QTabWidget()
        self.cfglayout.addWidget(self.tabs)
        self.scrollArea = QScrollArea()
        self.dictTab.append(self.scrollArea)
        content_widget = QWidget()
        content_widget.setStyleSheet('background-color: 111111;')
        self.dictTab[self.tabCount].setWidget(content_widget)
        self.layouts.append(QVBoxLayout(content_widget))
        self.dictTab[self.tabCount].setWidgetResizable(True)
        
        #tab_layout.addWidget(self.ConfigGroup)
   
            

    
    def doItems(self,cfg):
        self.tabCount+=1
        self.lyCount +=1
        self.dictTab.append(QScrollArea())
        self.tabs.addTab(self.dictTab[self.tabCount],"Config Items")
        content_widget = QWidget()
        content_widget.setStyleSheet('background-color: 111111;')
        self.dictTab[self.tabCount].setWidget(content_widget)
        self.layouts.append(QVBoxLayout(content_widget))
        self.dictTab[self.tabCount].setWidgetResizable(True)
        self.cfgHeight = 0
        for k ,v in cfg.items():
            if type(v) == list :
                H,W =self.doList(cfg,k,v)
                #print("List",k,len(v))
            elif type(v) == libconf.AttrDict:
                widget = CfgDict(k,v)
                self.layouts[self.lyCount].addWidget(widget.Create(self))
                self.objArry.append(widget)    
                self.cfgHeight += 70
            elif type(v) == str:
                H,W = self.doString(cfg,k,v)
                self.cfgHeight += H
            elif type(v) == bool:
                #print("Str",k,v)
                widget = CfgBool(k,v)
                self.layouts[self.lyCount].addWidget(widget.Create(self))
                self.objArry.append(widget)
                self.cfgHeight += 70
            elif type(v) == int:
                #print("int",k,v)
                widget = CfgInt(k,v)
                self.layouts[self.lyCount].addWidget(widget.Create(self))
                self.objArry.append(widget)    
                self.cfgHeight += 70
            elif type(v) == tuple   :
               H,W = self.doArray(cfg,k,v)
               self.cfgHeight += H
        #self.setSize(self.ConfigGroup,self.cfgHeight,450)

    def DoImageList(self,cfg,k,v):
        self.ImagesList = CfgImageArray(k,v)
        self.layouts[self.lyCount].addWidget(self.ImagesList.Create(cfg,self.itemcfg,self))    
        self.objArry.append(self.ImagesList) 
        return self.ImagesList.getHW()         

    def DoArray(self):
        pass

    def doList(self,cfg,k,v):
        #print("tuple",k,len(v))
        if "images_name_array" in k:
            H,W = self.DoImageList(cfg,k,v)
        elif "caption_array" in k:
            widget = CfgArray(k,v)
            self.layouts[self.lyCount].addWidget(widget.Create(self))    
            self.objArry.append(widget) 
            H,W = widget.getHW()
        elif "command_dict" in k:
            widget = CfgDict(k,v)
            self.layouts[self.lyCount].addWidget(widget.Create(self))
            self.objArry.append(widget)                 
            H,W = widget.getHW()
        else:
            widget = CfgArray(k,v)
            self.layouts[self.lyCount].addWidget(widget.Create(self))    
            self.objArry.append(widget) 
            H,W = widget.getHW()
        return H,W
        
    
    def doString(self,cfg,k,v):
        #print("Str",k,len(v))
        H = 0
        W = 0
        if "caption_box" == k:
            widget = CfgTextBox(k,v,self)
            self.layouts[self.lyCount].addWidget(widget.Create(self))
            H,W = widget.setHW(100,250)
            self.objArry.append(widget)
        elif "type_text" in k:
            self.type_text = CfgString(k,v)
            self.layouts[self.lyCount].addWidget(self.type_text.Create(self))
            H,W = self.type_text.setHW(30,250)     
            self.objArry.append(self.type_text)
        elif "data_file" in k:
            self.name_text = CfgDataString(k,v)
            self.layouts[self.lyCount].addWidget(self.name_text.Create(self))
            H,W = self.name_text.setHW(30,250)     
            self.objArry.append(self.name_text)
        elif "images_name_text" in k:
            self.images_name_text = CfgString(k,v)
            self.layouts[self.lyCount].addWidget(self.images_name_text.Create(self))
            H,W = self.images_name_text.setHW(30,250)     
            self.objArry.append(self.images_name_text)
        elif "name_text" in k:
            self.name_text = CfgString(k,v)
            self.layouts[self.lyCount].addWidget(self.name_text.Create(self))
            H,W = self.name_text.setHW(30,250)     
            self.objArry.append(self.name_text)
        elif "tex_dir" in k:
            self.tex_dir = CfgString(k,v)
            self.tex_dir.setAsDir()
            self.layouts[self.lyCount].addWidget(self.tex_dir.Create(self))
            H,W = self.tex_dir.setHW(100,250)
            self.objArry.append(self.tex_dir)  
        elif "images_dir" in k:
            self.images_dir = CfgString(k,v)
            self.images_dir.setAsDir()
            self.layouts[self.lyCount].addWidget(self.images_dir.Create(self))
            H,W = self.images_dir.setHW(100,250)
            self.objArry.append(self.images_dir)
        elif "cmd" in k:
            widget = CfgCmd(k,v)
            self.layouts[self.lyCount].addWidget(widget.Create(self))
            H,W = 0,0
            self.objArry.append(widget)
        elif "dir" in k:
            widget = CfgString(k,v)
            widget.setAsDir()
            self.layouts[self.lyCount].addWidget(widget.Create(self))
            H,W = widget.setHW(100,250)
            self.objArry.append(widget)
        elif "file" in k:
            widget = CfgString(k,v)
            widget.setAsFile()
            self.layouts[self.lyCount].addWidget(widget.Create(self))
            H,W = widget.setHW(100,250)
            self.objArry.append(widget)
        else:
            widget = CfgString(k,v)
            self.layouts[self.lyCount].addWidget(widget.Create(self))
            H,W = widget.setHW(30,250)
            self.objArry.append(widget)
        
        return H,W
    
    
  
   

   