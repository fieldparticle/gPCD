from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox
from PyQt6.QtWidgets import QGridLayout, QTabWidget, QLineEdit,QListWidget,QTextEdit
from PyQt6.QtWidgets import QPushButton, QGroupBox
from PyQt6 import QtCore
from _thread import *
from ConfigClass import *
from LatexClass import *
from CfgLabel import *
from LatexSingleImage import *
from LatexMultiImage import *
from LatexPlotBase import *
from LatexPlotParticle import *
from LatexPlot import *
from LatexSingleTable import *
from LatexEquation import *
from LatexMultiPlot import *
class TabFormLatex(QTabWidget):
    
    texFolder = ""
    prv = None
    CfgFile = ""
    texFileName = ""
    hasConfig = False
    itemcfg = ConfigClass("Latex Class")
    startDir = "J:/MOD/FPIBGUtility/Latex"
    startDir = "J:/FPIBGJournalStaticV2/rpt"
    startDir = "J:/FPIBGDATAT/cfg_paper"

    ObjName = ""
    ltxObj = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
       
    def setSize(self,control,H,W):
        return
        control.setMinimumHeight(H)
        control.setMinimumWidth(W)
        control.setMaximumHeight(H)
        control.setMaximumWidth(W)

    def refresh_config(self):
        self.OpenConfigFile()

    def SaveConfigurationFile(self):
        self.ltxObj.updateCfgData()
        
        #self.ltxObj.clearConfigGrp()

    def OpenConfigFile(self,file_name=None):
            if file_name != None:
                self.CfgFile = file_name
            
            self.texFolder = os.path.dirname(self.CfgFile)
            self.texFileName = os.path.splitext(os.path.basename(self.CfgFile))[0]
            self.dirEdit.setText(self.CfgFile)
            try :
                self.itemcfg = ConfigClass(self.CfgFile)
                self.itemcfg.Create(self.bobj.log,self.CfgFile)
                
            except BaseException as e:
                self.log.log(self,f"Unable to open item configurations file:{e}")
                print(f"Unable to open item configurations file:{e}")
                self.hasConfig = False
                return 
            self.type = self.itemcfg.config.type_text 
            if self.hasConfig == True:
                self.ltxObj.clearConfigGrp()
            if "multiimage" in self.type:
                self.ltxObj = LatexMultiImage(self)
                self.ltxObj.setConfigGroup(self.tab_layout)
                self.ltxObj.OpenLatxCFG()
                self.ListObj.setEnabled(False)
                self.hasConfig = True
            elif "image" in self.type:
                self.ltxObj = LatexSingleImage(self)
                self.ltxObj.setConfigGroup(self.tab_layout)
                self.ltxObj.OpenLatxCFG()
                self.hasConfig = True
            elif "splittable" in self.type:
                self.ltxObj = LatexSplitTable(self)
                self.ltxObj.setConfigGroup(self.tab_layout)
                self.ltxObj.OpenLatxCFG()
                self.hasConfig = True
            elif "multitable" in self.type:
                self.ltxObj = LatexMultiTable(self)
                self.ltxObj.setConfigGroup(self.tab_layout)
                self.ltxObj.OpenLatxCFG()
                self.hasConfig = True
            elif "singletable" in self.type:
                self.ltxObj = LatexSingleTable(self)
                self.ltxObj.setConfigGroup(self.tab_layout)
                self.ltxObj.OpenLatxCFG()
                self.hasConfig = True
            elif "plotparticle" in self.type:
                self.ltxObj = LatexPlotParicle(self)
                self.ltxObj.setConfigGroup(self.tab_layout)
                self.ltxObj.OpenLatxCFG()
                self.hasConfig = True
            elif "multiplot" in self.type:
                self.ltxObj = LatexMultiPlot(self)
                self.ltxObj.setConfigGroup(self.tab_layout)
                self.ltxObj.OpenLatxCFG()
                self.hasConfig = True
            elif "singleplot" in self.type:
                self.ltxObj = LatexPlot(self)
                self.ltxObj.setConfigGroup(self.tab_layout)
                self.ltxObj.OpenLatxCFG()
                self.hasConfig = True
            elif "equation" in self.type:
                self.ltxObj = LatexEquation(self)
                self.ltxObj.setConfigGroup(self.tab_layout)
                self.ltxObj.OpenLatxCFG()
                self.hasConfig = True
            elif "type" in self.type:
                self.ltxObj = LatexSingleImage(self)
                self.ltxObj.setConfigGroup(self.tab_layout)
                self.ltxObj.setImgGroup(self.tab_layout)
                self.ltxObj.OpenLatxCFG()
                self.hasConfig = True
            else:
                print("InvalidType")
                return
            
           
            self.SaveButton.setEnabled(True)
            self.PreviewButton.setEnabled(True)



    def browseFolder(self):
        """ Opens a dialog window for the user to select a folder in the file system. """
        #folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        folder = QFileDialog.getOpenFileName(self, ("Open File"),
                                       self.startDir,
                                       ("Configuration File (*.cfg)"))
        
        if folder[0]:
            self.OpenConfigFile(folder[0])
            

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
   
    def preview(self):
        if self.prv != None:
            if (self.prv.flg_isopen):
                self.prv.close()
        self.SaveConfigurationFile()
        previewFile = f"{self.itemcfg.config.tex_dir}/preview.tex"
        previewPdf =  f"{self.itemcfg.config.tex_dir}/preview.pdf"
        texlist = self.ltxObj.getTexList()
        
        prviewWorkingDir = self.itemcfg.config.tex_dir
        valFile = f"{self.itemcfg.config.tex_dir}/_vals_{self.itemcfg.config.name_text}.tex"
        prvCls = LatexPreview(previewFile,texlist,prviewWorkingDir,valFile)
        prvCls.ProcessLatxCode()
        prvCls.Run()
        with open('termPreview.log', "r") as infile:  
            txt_line = infile.readline().strip("\n")
            self.terminal.append(txt_line)
            while txt_line:
                txt_line = infile.readline().strip("\n")
                self.terminal.append(txt_line)
        self.prv = PreviewDialog(previewPdf)
        self.prv.exec()
        

        

    def Create(self,FPIBGBase):
        
        self.bobj = FPIBGBase
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.log.log(self,"TabFormLatex finished init.")
        self.log.log(self,"TabFormLatex started Create.")
        try:
            self.setStyleSheet("background-color:  #eeeeee")
            self.tab_layout = QGridLayout()
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.setSize(self,1000,1000)
            self.setFixedWidth(1000)
            self.setLayout(self.tab_layout)

            ## -------------------------------------------------------------
            ## Set parent directory
            LatexcfgFile = QGroupBox("Latex File Configuration")
            #self.setSize(LatexcfgFile,450,500)
            self.tab_layout.addWidget(LatexcfgFile,0,0,2,2,alignment= Qt.AlignmentFlag.AlignLeft)
            
            dirgrid = QGridLayout()
            LatexcfgFile.setLayout(dirgrid)

            self.dirEdit =  QLineEdit()
            self.dirEdit.setStyleSheet("background-color:  #ffffff")
            self.dirEdit.setText("")

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

            self.newButton = QPushButton("New")
            self.setSize(self.newButton,30,100)
            self.newButton.setStyleSheet("background-color:  #dddddd")
            self.newButton.clicked.connect(self.browseNewItem)
            dirgrid.addWidget(self.newButton,2,1)

            self.refsButton = QPushButton("Refresh")
            self.setSize(self.refsButton,30,100)
            self.refsButton.setStyleSheet("background-color:  #dddddd")
            self.refsButton.clicked.connect(self.refresh_config)
            dirgrid.addWidget(self.refsButton,2,2)

            self.PreviewButton = QPushButton("Preview")
            self.setSize(self.PreviewButton,30,100)
            self.PreviewButton.setStyleSheet("background-color:  #dddddd")
            self.PreviewButton.clicked.connect(self.preview)
            self.PreviewButton.setEnabled(False)
            dirgrid.addWidget(self.PreviewButton,2,3)
            
            self.ListObj =  QListWidget()
            #self.ListObj.setFont(self.font)
            self.ListObj.setStyleSheet("background-color:  #FFFFFF")
            self.vcnt = 0            
            self.ListObj.insertItem(0, "image")
            self.ListObj.insertItem(1, "plot")
            self.ListObj.insertItem(2, "multiplot")
            self.ListObj.insertItem(3, "multiimage")
            self.ListObj.itemSelectionChanged.connect(lambda: self.valueChangeArray(self.ListObj))
            dirgrid.addWidget(self.ListObj,3,0,2,2)
            
            self.intro_image = QLabel(self)
            self.pixmap = QPixmap('Logo.png')
            self.pixmap = self.pixmap.scaled(600, 400)
            self.intro_image.setPixmap(self.pixmap)
            #self.setSize(self.intro_image,350,450)
            ##Add items to the layout
            
            self.tab_layout.addWidget(self.intro_image,0,2,2,2,alignment= Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

            ## -------------------------------------------------------------
            ## Comunications Interface
            self.terminal =  QTextEdit(self)
            self.terminal.setStyleSheet("background-color:  #ffffff; color: green")
            self.setSize(self.terminal,225,900)
            self.terminal.setFixedWidth(950)
            self.tab_layout.addWidget(self.terminal,5,0,2,4,alignment= Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        except BaseException as e:
            self.log.log(self,e)
   
    def valueChangeArray(self,listObj):  
        selected_items = listObj.selectedItems()
        if selected_items:
            #print("List object Value Changed",selected_items[0].text())
            self.ltxObj.setTypeText(selected_items[0].text())         
    