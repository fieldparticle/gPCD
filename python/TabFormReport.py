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
from DataContainer import *
from ReportClass import *
from ReportLatexPlot import *
from LatexPreview import *
from PdfViewer import *
from CheckCfg import *
class TabFormReport(QTabWidget):
    
    texFolder = ""
    CfgFile = ""
    texFileName = ""
    hasConfig = False
    itemcfg = ConfigUtility("Latex Class")
    data_container = None
    latex_container = None
    interpeter = None
    report_class = None
    prv = None
    ObjName = ""
    ltxObj = None
    terminal  = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        
    
    def setSize(self,control,H,W):
        control.setMinimumHeight(H)
        control.setMinimumWidth(W)
        control.setMaximumHeight(H)
        control.setMaximumWidth(W)

    
    #******************************************************************
    # Load the confiruation file
    #
    def load_item_cfg(self,file):
            
            self.CfgFile = file
            self.texFolder = os.path.dirname(self.CfgFile)
            self.texFileName = os.path.splitext(os.path.basename(self.CfgFile))[0]
            self.dirEdit.setText(self.CfgFile)

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
            chk = CheckCfg(self.itemcfg,)
            msg = chk.check_rpt_files()
            if (msg) != 'ok':
                self.msg_box(msg)
                self.log.log(self,msg)
                return
            self.data_container = None 
            self.data_container = DataContainer(self,self.itemcfg)
            self.VerifyButton.setEnabled(True)
            self.PreviewButton.setEnabled(True)



    def browseFolder(self):
        """ Opens a dialog window for the user to select a folder in the file system. """
        #folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        folder = QFileDialog.getOpenFileName(self, ("Open File"),
                                       self.cfg.report_start_dir,
                                       ("Configuration File (*.cfg)"))
        
        if folder[0]:
           self.load_item_cfg(folder[0])

    #******************************************************************
    # GP message box
    #
    def msg_box(self,text):
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.exec()


    def do_image(self):
        try :
            self.data_container.clear()
            self.data_container.get_particle_data_fields()
            lines_list = None
            lines_list = self.data_container.do_preview()
            self.report_obj = ReportClass(self,lines_list,self.itemcfg)
            
        except BaseException as e:
            print(f"preview failed:{e}")

    
    def do_plots(self):
        for ii in self.itemcfg.include:
            self.itemcfg_obj = ConfigUtility(ii)
            self.itemcfg_obj.Create(self.bobj.log,ii)
            self.itemcfg_main = self.itemcfg_obj.config
            self.do_plot()
    
    def do_plot(self):
        try :
            self.data_container = None 
            self.data_container = DataContainer(self,self.itemcfg_main)
            self.data_container.clear()
            self.data_container.get_particle_data_fields()
            lines_list = None
            self.data_container.apply_data_to_fields()
            self.data_container.do_report()
        except BaseException as e:
            print(f"preview failed:{e}")

    #******************************************************************
    # Preview the latex genberated pdf
    #
    def preview(self):
        self.reload()
        match self.itemcfg.type:
            case "plot":
                if len(self.itemcfg.include) == 0:
                    self.itemcfg_main = self.itemcfg
                    self.do_plot()
                else:
                    self.do_plots()

            case "image":
                self.do_image()
            case _:
                print(f"Report type : {self.itemcfg.type} not found.")

        self.report_obj = ReportLatexPlot(self,self.itemcfg)
        self.report_obj.save_latex()
        self.preview_dialog(self.report_obj.tex_output_name)
    
    #******************************************************************
    # Open a preview dialog
    #
    def preview_dialog(self,text_file_name):
        previewFile = f"{self.itemcfg.tex_dir}/preview.tex"
        previewPdf =  f"{self.itemcfg.tex_dir}/preview.pdf"
        
        prviewWorkingDir = self.itemcfg.tex_dir
        valFile = f"{self.itemcfg.tex_dir}/_vals_{self.itemcfg.name}.tex"
        prvCls = LatexPreview(previewFile,text_file_name,prviewWorkingDir,valFile)
        prvCls.ProcessLatxCode()
        prvCls.Run()
        with open('termPreview.log', "r") as infile:  
            txt_line = infile.readline().strip("\n")
            self.terminal.append(txt_line)
            while txt_line:
                txt_line = infile.readline().strip("\n")
                self.terminal.append(txt_line)
        self.prv = PdfViewer(previewPdf)
        self.prv.show()
        
    #******************************************************************
    # Reload the current cfg file after its been updates outside app
    #   
    def reload(self):
        self.load_item_cfg(self.CfgFile)
    #******************************************************************
    # Build the data by analysing and saving summery files
    #   
    def build_data(self):
        if "V" in self.itemcfg.mode:
            self.verify()
        elif "P" in self.itemcfg.mode:
            self.performance()
    #******************************************************************
    # Build the data by performance
    #   
    def performance(self):
        try :
            self.data_container.get_particle_data_fields()
            self.data_container.do_performance()
        except BaseException as e:
            print(f"Performance Failed:{e}")
    
    #******************************************************************
    # Test all of the files to verify counts
    #   
    def verify(self):
        try :
            self.data_container.get_particle_data_fields()
            self.data_container.get_data()
            ret = self.data_container.do_verify()
            if ret > 0:
                self.msg_box(f"Verify failed: Number of errors:{ret}. See ")
            else:
                self.msg_box(f"Verify Passed!")
        except BaseException as e:
            print(f"Verify Failed:{e}")

        pass
    #******************************************************************
    # Greate the GUI
    #   
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
            LatexcfgFile = QGroupBox("Report Configuraiton")
            self.setSize(LatexcfgFile,150,600)
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
            #self.SaveButton.clicked.connect(self.SaveConfigurationFile)
            self.SaveButton.setEnabled(False)
            dirgrid.addWidget(self.SaveButton,2,0)

            self.newButton = QPushButton("New")
            self.setSize(self.newButton,30,100)
            self.newButton.setStyleSheet("background-color:  #dddddd")
           # self.newButton.clicked.connect(self.browseNewItem)
            dirgrid.addWidget(self.newButton,2,1)

            self.VerifyButton = QPushButton("Build Data")
            self.setSize(self.VerifyButton,30,100)
            self.VerifyButton.setStyleSheet("background-color:  #dddddd")
            self.VerifyButton.clicked.connect(self.build_data)
            self.VerifyButton.setEnabled(False)
            dirgrid.addWidget(self.VerifyButton,2,3)


            self.PreviewButton = QPushButton("Preview")
            self.setSize(self.PreviewButton,30,100)
            self.PreviewButton.setStyleSheet("background-color:  #dddddd")
            self.PreviewButton.clicked.connect(self.preview)
            self.PreviewButton.setEnabled(False)
            dirgrid.addWidget(self.PreviewButton,2,2)


            self.ReloadButton = QPushButton("Reload")
            self.setSize(self.ReloadButton,30,100)
            self.ReloadButton.setStyleSheet("background-color:  #dddddd")
            self.ReloadButton.clicked.connect(self.reload)
            self.ReloadButton.setEnabled(True)
            dirgrid.addWidget(self.ReloadButton,2,3)

            '''
            self.ListObj =  QListWidget()
            #self.ListObj.setFont(self.font)
            self.ListObj.setStyleSheet("background-color:  #FFFFFF")
            self.vcnt = 0            
            self.ListObj.insertItem(0, "image")
            self.ListObj.insertItem(1, "plot")
            self.ListObj.insertItem(2, "multiplot")
            self.ListObj.insertItem(3, "multiimage")
            self.ListObj.itemSelectionChanged.connect(lambda: self.valueChangeArray(self.ListObj))
            dirgrid.addWidget(self.ListObj,3,0,1,2)
            '''

            ## -------------------------------------------------------------
            ## Comunications Interface
            self.terminal =  QTextEdit(self)
            self.terminal.setStyleSheet("background-color:  #ffffff; color: green")
            self.setSize(self.terminal,225,900)
            self.tab_layout.addWidget(self.terminal,4,0,1,3,alignment= Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        except BaseException as e:
            self.log.log(self,e)
        try:

                        # PQBR
            self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBR_ALL.cfg")
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBR_COMP_SPF.cfg")
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBR_GRPH_SPF.cfg")
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBR_GRPH_SPF_LIN_RESIDUAL.cfg") 
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBR_GRPH_SPF_LOG10.cfg")
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBR_GRPH_SPF_LOG10_RESIDUAL.cfg")
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBR_GRPH_SPF_QUAD_RESIDUAL.cfg")       
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBR_TOTAL_FPS.cfg")   
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBR_TOTAL_SPF.cfg")    
            
            # PQBS
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBS_ALL.cfg")
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBS_COMP_SPF.cfg")
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBS_GRPH_SPF.cfg")
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBS_GRPH_SPF_LIN_RESIDUAL.cfg")
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/PQBS_SPF.cfg") 
            
            # Other
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/TriangleJoins.cfg
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/
            #self.load_item_cfg("C:/_DJ/gPCD/python/cfg_reports/

            
            
        except BaseException as e1:
            print(f"Cannot open cfg file:{e1}")
   
    def valueChangeArray(self,listObj):  
        selected_items = listObj.selectedItems()
        if selected_items:
            #print("List object Value Changed",selected_items[0].text())
            self.ltxObj.setTypeText(selected_items[0].text())         
    