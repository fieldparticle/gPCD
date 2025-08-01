from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from CfgLabel import *
from LatexClass import *
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_qtagg import FigureCanvasAgg as FigureCanvas
from matplotlib.backends.qt_compat import QtWidgets
import numpy as np
from LatexConfigurationClass import *
from LatexConfigurationClass import *
from LatexPlotBase import * 
from ConfigClass import *
from AttrDictFields import *
from LatexPreview import *
from LatexDialogs import *
from TrendLine import *
from ValHandler import *
from LatexDataContainer import *
import matplotlib.ticker
from matplotlib.ticker import (MultipleLocator,
                               FormatStrFormatter,
                               AutoMinorLocator,
                               FuncFormatter,
                               EngFormatter)

from mpl_toolkits.axisartist.axislines import AxesZero
import matplotlib.ticker as ticker

class LatexPlotBase(LatexConfigurationClass):
    fignum = 0
    
    data = None
    hasPlot = False
    npdata = None
    fig = None
    ax = None
    pixmap = None
    has_legend = False

    def __init__(self,Parent,itemCFG=None):
        super().__init__(Parent)
        self.LatexFileImage = LatexMultiImageWriter(self.Parent)


    def getClassMajor(self,ClasStr):
        match(ClasStr):
            case "ax":
                return self.ax
            case "plt":
                return plt
            case "fig":
                return self.fig

    def __exit__(self):
        plt.close("all")
   
    def updateCfgData(self):
        for oob in self.objArry:
            oob.updateCFGData()
        self.itemcfg.updateCfg()
        self.updatePlotData()
        self.LatexFileImage.Write() 
    
    def splitCommandLinks(self,stringIn):
        parmString = ""
        parmsList = []
        cmdsList = []
        cmdsOnlyString = ""
        endFlg = False
        multicmd = []
        stringIn = stringIn.strip()
        if ':' in stringIn:
            multicmd = stringIn.split(':')
        else:
            multicmd.append(stringIn)
        for jj in range(len(multicmd)):
            parmString = ""
            cmdsOnlyString = ""
            for i in range(0, len(multicmd[jj])): 
                if  multicmd[jj][i] != '=' and endFlg == False: 
                    cmdsOnlyString = cmdsOnlyString + multicmd[jj][i] 
                elif endFlg == False:
                    endFlg = True
                else:
                    parmString  = parmString + multicmd[jj][i]
            parmsList.append(parmString.strip())   
            cmdsList.append(cmdsOnlyString.strip())
        return cmdsList,parmsList
        
        
    def OpenLatxCFG(self):
        #print(self.itemcfg)
        self.doItems(self.itemcfg.config)
        self.updatePlotData()

    def updatePlotData(self):
        if(self.fignum != 0):
            plt.close("all")
        for ii in range(0,int(self.cfg.num_plots_text)):
            previewTex = f"{self.itemcfg.config.plots_dir}/{self.itemcfg.config.name_text}{ii+1}.png"
            if os.path.exists(previewTex):
                os.remove(previewTex)
        self.fignum += 1
        self.valHandler.Create(f"{self.itemcfg.config.tex_dir}/_vals_{self.itemcfg.config.name_text}.tex")          
        # for each plot line
        for plotNum in range(1,int(self.cfg.num_plots_text)+1):
            self.fig = plt.figure(plotNum)
            self.ax = self.fig.gca()
        
            
            start,stop  = self.doLineSlice(plotNum)
            trendlines  =  self.doTrendLine(plotNum)
            plot_cmds   = self.doPlotCommands(plotNum)
            plotNames   = self.doPlotNames(plotNum)
            data_fields = self.doDataFields(plotNum)
            temp_ary = []
            # allocate a attribute dictionary for fields
            fld = AttrDictFields()
            # Create a data container object
            dataObj = LatexDataContainer(self.bobj,self.itemcfg,"LatexDataContainer")
            try :
                dataObj.Create(plotNum,data_fields)
            except BaseException as e:
                print(e)
                print("There is not data or there is an error with the path.")
                print(f"Current path is:{self.cfg.data_dir}")
                return
            # Get the data
            data = dataObj.getData()
            # Create a eval table
            for name, df in data.items():
                fld[name] = data[name]

            # Fill the data performaing any math on the columns
            for ii in range(len(data_fields)):
                fld_name = data_fields[ii].replace(':','_')
                if any(map(lambda char: char in data_fields[ii], "+-/*")):
                    field = eval(fld_name)
                    temp_ary.append(field)
                else:
                    # Else strip the fld. from the field and get the array at that column name
                    fldtxt = fld_name.split('.')
                    temp_ary.append(data[fldtxt[1]])
                self.onpdata = np.array(temp_ary)   
            self.hasPlot = True
            temp_ary = []

             # Convert text plot command to function
            plot_list = plot_cmds[plotNum-1].split(".")
            class_major = self.getClassMajor(plot_list[0])
            funct = getattr(class_major,(plot_list[1]))
            self.doGeneralCommands(plotNum)            
            try :
            # Do the plot
                for pp in range(len(plot_cmds)):
                    ret_dict = self.DoPlotFormat(plotNum,pp+1) # Do the Legend
                    self.line = funct(self.onpdata[0,start:],self.onpdata[pp+1,start:],**ret_dict)
            except BaseException as e:
                print(f"Plot num:{plotNum} error:{e}")
                return
                    
            # Do trendline
            try :
                if not "none" in trendlines[plotNum-1]:
                    for zz in range(len(plot_cmds)):
                        ret_dict = self.DoTrendFormat(plotNum,zz+1) # Do the Legend
                        trend  = TrendLine(self.onpdata[0,start:],self.onpdata[zz+1,start:],trendlines[zz-1],plotNames[zz-1],self.valHandler,self.itemcfg.config.tex_dir)
                        trend.doTrendLine(plt,ret_dict)
            except BaseException as e:
                print(f"Trend num:{plotNum} error:{e}")
                return
            
            dataObj.data_base.get_verify()

            if self.has_legend == True:
                leg_items = self.ax.legend()
            # Save temp image 
            pltTempImg = f"{self.itemcfg.config.plots_dir}/{self.itemcfg.config.name_text}{plotNum}.png"
            plt.savefig(pltTempImg, bbox_inches='tight')
            plt.close("all")        

    def DoTrendFormat(self,plotNum,line_num):
        ret_dict = {}
        plotGrouptxt = "trendFormat" + str(plotNum)+str(line_num)
        oob = self.itemcfg.config[plotGrouptxt]
        if len(oob) > 0:
            for ii in range(len(oob)):
                all_item = oob[ii].split("=")
                cmd_item = all_item[0]
                val_item = all_item[1]
                try :
                    if self.isfloat(val_item) == True:
                        ret_dict[cmd_item]= float(val_item)
                    elif self.isInt(val_item) == True:
                        ret_dict[cmd_item] = int(val_item)
                    else:
                        ret_dict[cmd_item] = str(val_item)
                except BaseException as e:
                    self.log.log(self,e)
                    print(e)
                    continue
        return ret_dict
    
    def DoPlotFormat(self,plotNum,line_num):
        ret_dict = {}
        plotGrouptxt = "plotFormat" + str(plotNum)+str(line_num)
        oob = self.itemcfg.config[plotGrouptxt]
        if len(oob) > 0:
            for ii in range(len(oob)):
                all_item = oob[ii].split("=")
                cmd_item = all_item[0]
                if 'label' in cmd_item:
                    self.has_legend = True
                val_item = all_item[1]
                try :
                    if self.isfloat(val_item) == True:
                        ret_dict[cmd_item]= float(val_item)
                    elif self.isInt(val_item) == True:
                        ret_dict[cmd_item] = int(val_item)
                    else:
                        ret_dict[cmd_item] = str(val_item)
                except BaseException as e:
                    self.log.log(self,e)
                    print(e)
                    continue
        return ret_dict

    def doGeneralCommands(self,plotNum):
        fig = plt.figure(plotNum)
        ax = self.fig.gca()
        plotGrouptxt = f"commands{plotNum}"
        oob = self.itemcfg.config[plotGrouptxt]
        for func_str in oob:
             
           # print(func_str)
            try:
                eval(func_str)     
            except BaseException as e:
                self.log.log(self,f"Command {func_str} is invalid or ill formed")
        

                           
            
    def doAxesLabel(self,plotNum):
        plotGrouptxt = f"AxesLabel{plotNum}"
        oob = self.itemcfg.config[plotGrouptxt]
        return oob

    def doAxisFormat(self,plotNum):

        # Get color. Its special becasue it has no rcParams
        plotGrouptxt = f"AxesFormat{plotNum}"
        oob = self.itemcfg.config[plotGrouptxt]
        return oob

    def doGrid(self,plotNum):
        pass
        
    def doDataFields(self,plotNum):
        # Get color. Its special becasue it has no rcParams
        plotGrouptxt = f"DataFields{plotNum}"
        oob = self.itemcfg.config[plotGrouptxt]
        return oob
    
    def doPlotCommands(self,plotNum):
        # Get color. Its special becasue it has no rcParams
        plotGrouptxt = f"PlotCommands{plotNum}"
        oob = self.itemcfg.config[plotGrouptxt]
        return oob
    
    def doPlotNames(self,plotNum):
        # Get color. Its special becasue it has no rcParams
        plotGrouptxt = f"PlotNames{plotNum}"
        oob = self.itemcfg.config[plotGrouptxt]
        return oob

    def doLineSlice(self,plotNum):
        plotGrouptxt = "LineSlice" + str(plotNum)
        slice = self.itemcfg.config[plotGrouptxt][0].split(':')
        sslice = slice[0]
        eslice = slice[1]
        if self.isInt(sslice) == True:
            sslice = int(sslice)
        else:
            sslice = ""
        if self.isInt(eslice) == True:
            eslice = int(eslice)
        else:
            eslice = ""
        return sslice,eslice

    def doLineColors(self,plotNum):
         # Get color. Its special becasue it has no rcParams
        plotGrouptxt = f"LineColors{plotNum}"
        oob = self.itemcfg.config[plotGrouptxt]
        return oob

    def doTrendLine(self,plotNum):
         # Get color. Its special becasue it has no rcParams
        plotGrouptxt = f"Trendline{plotNum}"
        oob = self.itemcfg.config[plotGrouptxt]
        return oob

    def doLegend(self,plotNum):
        # Get color. Its special becasue it has no rcParams
        plotGrouptxt = f"Legend{plotNum}"
        oob = self.itemcfg.config[plotGrouptxt]
        return oob
       



    def setImgGroup(self,layout):
        pass
          
   