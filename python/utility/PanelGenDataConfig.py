import importlib
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget,QScrollArea,QVBoxLayout,QTabWidget,QFileDialog
from PyQt6.QtGui import QPixmap
from CfgLabel import *
from LatexClass import *
from ConfigClass import *
import csv
class GenDataConfigPanel():
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
    
    cur_file_name = ""
  

    #LatexFileImage = None
    imagelo = None

    def __init__(self):
        pass
    
        
    def Create(self,FPIBGBase,gui_parent,gen_class_txt):
        self.gui_parent = gui_parent
        self.bobj = FPIBGBase
        self.gcfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.cfg = self.gui_parent.itemcfg.config

        try :
            gen_class = self.load_class(gen_class_txt)
        except BaseException as e:
            print("LatexDataConfigurationClass.Create():",e)
            return
        self.gen_obj = None
        self.gen_obj = gen_class()
        self.gen_obj.Create(self.bobj,"BaseGenClass",self.cfg,self)
        

    def side_value_change(self):
        side_txt = self.side_len_edit.text().split(':')
        self.gen_obj.side_value_changed(side_txt)
        
    def toggle_cell_face(self):
        self.gen_obj.toggle_cell_face()
        
    def close_plot(self):
        self.gen_obj.close_plot()

    def toggle_cells(self):
        self.gen_obj.toggle_cells()

    def plot(self,file_name):
        self.cur_file_name = file_name
        self.gen_obj.plot_base(file_name,as_points=True)
        self.do_plot_group()

    def plot_view_changed(self,obj):
        view = obj.currentRow()
        self.gen_obj.set_view_num(view)
        self.gen_obj.update_plot()
        return
    
    def out_put_cell_ary(self):
        self.gen_obj.out_put_cell_ary()

    def getGenObj(self):
        return self.gen_obj
    
    def gen_data(self):
        self.gen_obj.gen_data()

    def DoArray(self):
        pass

    def load_class(self,class_name):
        module_name, class_name = class_name.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    def setTypeText(self,Text):
        self.type_text.setTypeText(Text)
        
    def updateCfgData(self):
        for oob in self.objArry:
            oob.updateCFGData()
        self.cfg.updateCfg()
        self.LatexFileImage.Write() 

    def setSize(self,control,H,W):
        control.setMinimumHeight(H)
        control.setMinimumWidth(W)
        control.setMaximumHeight(H)
        control.setMaximumWidth(W)

    def itemChanged(self,key,val,obj=None):
        print("Items Changed in Parent:",key,val)
        if key == "Toggle Cells":
            self.toggle_cells()
        elif(key == "Toggle Cell Face"):
            self.toggle_cell_face()
        elif (key == "view_list"):
            self.plot_view_changed(obj)
        
 
    def SaveConfigurationFile(self):
        self.cfg.updateCfg()
        self.LatexFileImage.Create(self.bobj,self.cfg.config.name_text)
        self.LatexFileImage.cleanPRE = True
        self.LatexFileImage.width = 0
        self.LatexFileImage.height = 0
        self.LatexFileImage.Write(self.cfg.config,plt) 
    
    def OpenLatxCFG(self):
        self.doItems(self.cfg)
    
    def clearLayout(self,layout):
     
        for i in reversed(range(layout.count())):
            layoutItem = layout.itemAt(i)
            if layoutItem.widget() is not None:
                widgetToRemove = layoutItem.widget()
                widgetToRemove.setParent(None)
                layout.removeWidget(widgetToRemove)
            elif layoutItem.spacerItem() is not None:
                continue
            else:
                layoutToRemove = layout.itemAt(i)
                self.clearLayout(layoutToRemove)

    def clearConfigGrp(self):
        del self.objArry [:]
        del self.dictTab[:]
        self.tabCount = 0
        del self.layouts[:]
        self.lyCount = 0
        self.clearLayout(self.cfglayout)
        

    def setConfigGroup(self,layout):
        self.parent_lay_out = layout
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
               if 'cell_select_list' in k:
                   return
               H,W = self.doArray(cfg,k,v)
               self.cfgHeight += H
        #self.setSize(self.ConfigGroup,self.cfgHeight,450)

    
        


    def do_plot_group(self):
        self.clearConfigGrp()
        #------------------------- header 
        self.ConfigGroup = QGroupBox("Latex File Configuration")
        self.parent_lay_out.addWidget(self.ConfigGroup,0,2,1,1,alignment= Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
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
        #--------------------------------------------
        #Items
     
        widget = CfgString("start_sidelen_text",self.cfg.start_sidelen_text) 
        self.layouts[self.lyCount].addWidget(widget.Create(self))   
        self.objArry.append(widget)  

        self.widget = CfgButton("Toggle Cells",None) 
        self.layouts[self.lyCount].addWidget(self.widget.Create(self))   
        self.objArry.append(widget)  

        widget = CfgButton("Toggle Cell Face",None) 
        self.layouts[self.lyCount].addWidget(widget.Create(self))   
        self.objArry.append(widget)  

        start_end_array = CfgArray("particle_range_array",self.cfg.particle_range_array)
        self.layouts[self.lyCount].addWidget(start_end_array.Create(self))
        self.objArry.append(start_end_array)  

        side_edit_lable = CfgString("start_sidelen_text",self.cfg.start_sidelen_text) 
        self.layouts[self.lyCount].addWidget(side_edit_lable.Create(self))   
        self.objArry.append(side_edit_lable)  
        
        view_list = CfgArray("view_list",self.cfg.view_list)
        self.layouts[self.lyCount].addWidget(view_list.Create(self))
        self.objArry.append(view_list)  
        

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
            widget = CfgTextBox(k,v)
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
            self.tex_dir = CfgString(k,v,self)
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
    
    
  
   

   