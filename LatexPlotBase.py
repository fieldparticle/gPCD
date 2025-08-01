from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from CfgLabel import *
from LatexClass import *
import pandas as pd
import matplotlib.pyplot as plt
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
                               FuncFormatter)

class LatexPlotBase(LatexConfigurationClass):
    fignum = 0
    
    data = None
    hasPlot = False
    npdata = None
    fig = None
    ax = None
    pixmap = None

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
        self.fignum += 1
        self.valHandler.doValues(f"{self.itemcfg.config.tex_dir}/_vals_{self.itemcfg.config.name_text}.tex")          
        # for each plot line
        for plotNum in range(1,int(self.cfg.num_plots_text)+1):
            self.fig = plt.figure(plotNum)
            self.ax = self.fig.gca()
        
            self.DoPlotFormat(plotNum)
            start,stop  = self.doLineSlice(plotNum)
            lineColors  = self.doLineColors(plotNum)
            trendlines  =  self.doTrendLine(plotNum)
            legends     = self.doLegend(plotNum)
            plot_cmds   = self.doPlotCommands(plotNum)
            plotNames   = self.doPlotNames(plotNum)
            data_fields = self.doDataFields(plotNum)
            data_src    = self.doDataSource(plotNum)
            data_file   = self.doDataFile(plotNum)
            #grid        = self.doGrid(plotNum)
            #axisFormat   = self.doAxisFormat(plotNum)
            self.doGeneralCommands(plotNum)
           # axex        = self.doAxesLabel(plotNum)
            temp_ary = []
            # allocate a attribute dictionary for fields
            fld = AttrDictFields()
            # Create a data container object
            dataObj = LatexDataContainer(self.bobj,self.itemcfg,"LatexDataContainer")
            try :
                # Create the data objecy
                if(data_file == None):
                    dataObj.Create(data_src,self.cfg.data_dir)
                else:
                    dataObj.Create(data_src,self.cfg.data_dir,data_file)
            except BaseException as e:
                return
            # Get the data
            data = dataObj.getData()
            #print(data_src)
            #print(data)
            # Create a eval table
            for name, df in data.items():
                fld[name] = data[name]

            # Fill the data performaing any math on the columns
            for ii in range(len(data_fields)):
                if any(map(lambda char: char in data_fields[ii], "+-/*")):
                    field = eval(data_fields[ii])
                    temp_ary.append(field)
                else:
                    # Else strip the fld. from the field and get the array at that column name
                    fldtxt = data_fields[ii].split('.')
                    temp_ary.append(data[fldtxt[1]])
                self.onpdata = np.array(temp_ary)   
            self.hasPlot = True
            #self.updatePlot(plotNum)
            temp_ary = []

             # Convert text plot command to function
            plot_list = plot_cmds[plotNum-1].split(".")
            class_major = self.getClassMajor(plot_list[0])
            funct = getattr(class_major,(plot_list[1]))
            # Do the plot
            for pp in range(len(plot_cmds)):
               # self.ax.xaxis.set_major_formatter(FormatStrFormatter(axisFormat[0]))
               # self.ax.xaxis.set_major_formatter(FormatStrFormatter(axisFormat[pp+1]))
                self.line = funct(self.onpdata[0,start:],self.onpdata[pp+1,start:],color=lineColors[pp],label=legends[pp])
                 # Do the Legend
                
           

            # Do trendline
            if not "none" in trendlines[plotNum-1]:
                
                for zz in range(len(plot_cmds)):
                    trendtxt = f"{legends[zz]} {trendlines[plotNum]} trendline" 
                    trend  = TrendLine(self.onpdata[0,start:],self.onpdata[zz+1,start:],trendlines[zz-1],plotNames[zz-1],self.valHandler,self.itemcfg.config.tex_dir)
                    trend.doTrendLine(plt,lineColors[zz],trendtxt)
            
            self.ax.legend()
            #self.ax.grid(grid)
            # Save temp image 
            pltTempImg = f"{self.itemcfg.config.plots_dir}/{self.itemcfg.config.name_text}{plotNum}.png"
            plt.savefig(pltTempImg, bbox_inches='tight')
            plt.close("all")        
                            
    def doGeneralCommands(self,plotNum):
        fig = plt.figure(plotNum)
        ax = self.fig.gca()
        plotGrouptxt = f"commands{plotNum}"
        oob = self.itemcfg.config[plotGrouptxt]
        for func_str in oob:
             
            print(func_str)
            try:
                exec(func_str)     
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
       

    def DoPlotFormat(self,plotNum):
        plotGrouptxt = "plotFormat" + str(plotNum)
        oob = self.itemcfg.config[plotGrouptxt]
        if len(oob) > 0:
            for ii in range(len(oob)):
                all_item = oob[ii].split("=")
                cmd_item = all_item[0]
                val_item = all_item[1]
                try :
                    if self.isfloat(val_item) == True:
                        plt.rcParams[cmd_item]= float(val_item)
                    elif self.isInt(val_item) == True:
                        plt.rcParams[cmd_item] = int(val_item)
                    else:
                        plt.rcParams[cmd_item] = str(val_item)
                except BaseException as e:
                    self.log.log(self,e)
                    continue


    def setImgGroup(self,layout):
        pass
          