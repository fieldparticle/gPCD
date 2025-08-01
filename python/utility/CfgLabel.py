import sys
import os
from PyQt6.QtCore import Qt,pyqtSignal, pyqtSlot,QObject
from PyQt6.QtWidgets import QGridLayout, QLineEdit,QListWidget,QComboBox,QInputDialog,QMessageBox,QWidget
from PyQt6.QtWidgets import QPushButton,QLabel, QGroupBox, QTextEdit, QRadioButton,QFileDialog,QDialog
from PyQt6.QtGui import QImage,QFontMetrics,QFont
from threading import Thread
import math
from AttrDictFields import *
from LatexDialogs import *
	
	

#############################################################################################
# 						class CfgDict():
#############################################################################################
class CfgDict():

	dict = {}
	currentListObj = None
	
	
	def __init__(self, key,value):
		self.key = key
		self.value = value
  	
	def setSize(self,control,H,W):
		control.setMinimumHeight(H)
		control.setMinimumWidth(W)
		control.setMaximumHeight(H)
		control.setMaximumWidth(W)

	def updateCFGData(self):
		for ii in range(len(self.ListObj)):
			items = [self.ListObj[ii].item(x).text() for x in range(self.ListObj[ii].count())]
			oob = self.cfg["command_dict"]
			oob[self.keyList[ii]] = items


	def moveItem(self):
		currentRow = self.self.currentListObj.currentRow()
		currentItem = self.self.currentListObj.takeItem(currentRow)
		self.self.currentListObj.insertItem(currentRow - 1, currentItem)
	
	def getListItemText(self):
		selected_items = self.self.currentListObj.selectedItems()
		if selected_items:
			#print(f"returning {selected_items[0].text()}\n")
			return selected_items[0].text()

	def RemoveItem(self):
		selected_items = self.self.currentListObj.currentRow()
		if selected_items < 0:
			return
		self.currentListObj.takeItem(selected_items)
	
	def Clicked(self):
		self.currentListObj = self.Parent.sender()
		self.currentIndex = self.currentListObj.currentRow()
		print("Clicked by:",self.currentListObj)
	
	def AddItem(self):
		dialog = KeyValDialog()
		dialog.data_submitted.connect(self.handle_data)
		dialog.exec()



	def EditItem(self):
		selected_items = self.currentListObj.selectedItems()
		if selected_items:
			if "=" in selected_items[0].text():
				cmd_lst = selected_items[0].text().split("=")
				dialog = KeyValDialog(cmd_lst[0],cmd_lst[1])
				dialog.exec()
				txt = f"{dialog.key_data}={dialog.val_data}"
				self.dict[dialog.key_data] = dialog.val_data
			
			selected_items = self.currentListObj.selectedItems()
			selected_items[0].setText(txt)

		else:
			QMessageBox.information(
									None,
									'Information',
									'You need to select an item.',
									QMessageBox.StandardButton.Ok
								)
	
	def changedFocus(self):
		print("Changed Focus")

	def Create(self,parent):
		self.Parent = parent
		self.cfg = self.Parent.bobj.cfg.config
			
		self.font = QFont("Times", 10)
		self.font.setBold(False)

		metrics = QFontMetrics(self.font)

		self.paramgrp = QGroupBox("")
		self.paramlo = QGridLayout()
		self.paramgrp.setLayout(self.paramlo)
		self.paramgrp.setStyleSheet('background-color: 111111;')
		text = self.key + ":"
		

		self.ListObj = []
		self.keyList = []
		self.vcnt = 0
		row = 0
		self.dict = AttrDictFields()
		for k,v in self.value.items():
			widget = CfgArray(k,v)
			self.paramlo.addWidget(widget.Create(self.Parent))    
			self.ListObj.append(widget) 
			H,W = widget.getHW()
		"""
		for k,v in self.value.items():
			self.dict[k] = v
			widget = None
			widget = CfgArray(k,v)
			widget.Create(cfg,self.itemcfg,self)
			self.ListObj.append(widget)
			keyval = f"{self.key}.{k}"
			self.keyList.append(k)
			widget.setFont(self.font)
			widget.setStyleSheet("background-color:  #FFFFFF")
			widget.clicked.connect(self.Clicked)
			for ii in range(len(v)):
				widget.insertItem(self.vcnt,v[ii])
			self.paramlo.addWidget(widget,row,1,alignment= Qt.AlignmentFlag.AlignLeft)
			self.vcnt+=1
			#print("Label:",k)
			LabelObj = QLabel(k)
			LabelObj.setFont(self.font)#all_lst = ii.split("=")
			self.paramlo.addWidget(LabelObj,row,0,alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)
			row +=1
		"""
		self.vcnt = 0
		
	

		self.dirButton = QPushButton("Add")
		self.setSize(self.dirButton,30,100)
		self.dirButton.setStyleSheet("background-color:  #dddddd")
		self.dirButton.clicked.connect(self.AddItem)
		self.paramlo.addWidget(self.dirButton)


		self.delButton = QPushButton("Remove")
		self.setSize(self.delButton,30,100)
		self.delButton.setStyleSheet("background-color:  #dddddd")
		self.delButton.clicked.connect(self.RemoveItem)
		self.paramlo.addWidget(self.delButton)
		

		self.editButton = QPushButton("Edit")
		self.setSize(self.editButton,30,100)
		self.editButton.setStyleSheet("background-color:  #dddddd")
		self.editButton.clicked.connect(self.EditItem)
		self.paramlo.addWidget(self.editButton)
		
		self.upButton = QPushButton("Up")
		self.setSize(self.upButton,30,100)
		self.upButton.setStyleSheet("background-color:  #dddddd")
		self.upButton.clicked.connect(self.moveItem)
		self.paramlo.addWidget(self.upButton)
		return self.paramgrp
		
	def getLayout(self):
		return self.paramlo
	
	def getListObj(self):
		return self.currentListObj 

	def valueChangeArray(self):
		selected_items = self.currentListObj.selectedItems()
		if selected_items:
			#print("Value Changed",selected_items[0].text())
			self.Parent.itemChanged(self.key,self.value)
			
			
	def getHW(self):
		H = self.vcnt*20
		W = 300
		return H,W

	def setHW(self,H,W):
		self.setSize(self.currentListObj,H,W)
		Hg = H+20
		Wg = W+20+self.lwidth
		self.setSize(self.paramgrp,Hg,Wg)
		return Hg,Wg

#############################################################################################
# 						class CfgImageArray():
#############################################################################################

class CfgImageArray():
	def __init__(self, key,value):
		self.key = key
		self.value = value
  	
	def setSize(self,control,H,W):
		control.setMinimumHeight(H)
		control.setMinimumWidth(W)
		control.setMaximumHeight(H)
		control.setMaximumWidth(W)

	def updateCFGData(self):
		items = [self.ListObj.item(x).text() for x in range(self.ListObj.count())]
		self.cfg[self.key] = items

	def getListItemText(self):
		selected_items = self.ListObj.selectedItems()
		if selected_items:
			#print(f"returning {selected_items[0].text()}\n")
			return selected_items[0].text()
			
	def moveItem(self):
		currentRow = self.ListObj.currentRow()
		currentItem = self.ListObj.takeItem(currentRow)
		self.ListObj.insertItem(currentRow - 1, currentItem)
	
	def RemoveItem(self):
		selected_items = self.ListObj.currentRow()
		if selected_items < 0:
			return
		self.ListObj.takeItem(selected_items)
		
	def AddImageItemFile(self):
		folder = QFileDialog.getOpenFileName(self.paramgrp, ("Open File"),
                                       "J:/FPIBGJournalStaticV2/rpt",
                                       ("Images (*.png)"))
		
		if folder[0]:
			self.ListObj.addItem(folder[0])
			if(self.ListObj.count() == 1):
				self.texFolder = os.path.dirname(folder[0])
				self.texFileName = os.path.splitext(os.path.basename(folder[0]))[0]
			self.Parent.filesChangedArray(folder[0])

	

	def Create(self,config,FPIBGConfig,parent):
		self.cfg = config
		self.base = FPIBGConfig
		self.Parent = parent
			
		self.font = QFont("Times", 10)
		self.font.setBold(False)

		metrics = QFontMetrics(self.font)

		self.paramgrp = QGroupBox("")
		self.paramlo = QGridLayout()
		self.paramgrp.setLayout(self.paramlo)
		self.paramgrp.setStyleSheet('background-color: 111111;')
		text = self.key + ":"
		self.LabelObj = QLabel(text)
		self.LabelObj.setFont(self.font)
		self.lwidth = metrics.horizontalAdvance(text)
		self.setSize(self.LabelObj,20,self.lwidth) 
		self.paramlo.addWidget(self.LabelObj,0,0,alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)

		self.ListObj =  QListWidget()
		self.ListObj.setFont(self.font)
		self.ListObj.setStyleSheet("background-color:  #FFFFFF")
		self.vcnt = 0

		for v in self.value:
			self.ListObj.insertItem(self.vcnt,self.value[self.vcnt])
			self.vcnt+=1

		self.paramlo.addWidget(self.ListObj,0,1,alignment= Qt.AlignmentFlag.AlignLeft)
		

		self.dirButton = QPushButton("Add")
		self.setSize(self.dirButton,30,100)
		self.dirButton.setStyleSheet("background-color:  #dddddd")
		self.dirButton.clicked.connect(self.AddImageItemFile)
		self.paramlo.addWidget(self.dirButton)


		self.delButton = QPushButton("Remove")
		self.setSize(self.delButton,30,100)
		self.delButton.setStyleSheet("background-color:  #dddddd")
		self.delButton.clicked.connect(self.RemoveItem)
		self.paramlo.addWidget(self.delButton)
		

		self.upButton = QPushButton("Up")
		self.setSize(self.upButton,30,100)
		self.upButton.setStyleSheet("background-color:  #dddddd")
		self.upButton.clicked.connect(self.moveItem)
		self.paramlo.addWidget(self.upButton)
		
		return self.paramgrp
		
	def getLayout(self):
		return self.paramlo
	
	def getListObj(self):
		return self.ListObj 

	def valueChangeArray(self):
		selected_items = self.ListObj.selectedItems()
		if selected_items:
			#print("Value Changed",selected_items[0].text())
			self.Parent.itemChanged(self.key,self.value)
			#self.cfg[self.key] = ("newitem","newiutem1")
			#self.cfg[self.key]=self.EditObj.text()
			#self.base.updateCfg()

	def getHW(self):
		H = self.vcnt*20
		W = 300
		return H,W

	def setHW(self,H,W):
		self.setSize(self.ListObj,H,W)
		Hg = H+20
		Wg = W+20+self.lwidth
		self.setSize(self.paramgrp,Hg,Wg)
		return Hg,Wg

#############################################################################################
# 						class CfgArray():
#############################################################################################
class CfgArray():
	def __init__(self,key,value):
		self.key = key
		self.value = value
  	
	def setSize(self,control,H,W):
		control.setMinimumHeight(H)
		control.setMinimumWidth(W)
		control.setMaximumHeight(H)
		control.setMaximumWidth(W)

	def updateCFGData(self):
		items = [self.ListObj.item(x).text() for x in range(self.ListObj.count())]
		self.cfg[self.key] = items


	def moveItem(self):
		currentRow = self.ListObj.currentRow()
		currentItem = self.ListObj.takeItem(currentRow)
		self.ListObj.insertItem(currentRow - 1, currentItem)
	
	def getListItemText(self):
		selected_items = self.ListObj.selectedItems()
		if selected_items:
			#print(f"returning {selected_items[0].text()}\n")
			return selected_items[0].text()

	def RemoveItem(self):
		selected_items = self.ListObj.currentRow()
		if selected_items < 0:
			return
		self.ListObj.takeItem(selected_items)
		

	def AddItem(self):
		text, ok = QInputDialog.getText(
            None, 
            "Add SubPlot Caption", 
            "Enter caption:"
        )
		if ok and text:
			self.ListObj.addItem(text)

	def EditItem(self):
		selected_items = self.ListObj.selectedItems()
		if selected_items:
			inputd = QInputDialog()
			item_text = selected_items[0].text()
			text, ok = inputd.getText(
            	None, 
            	"Edit SubPlot Caption", 
            	"Edit caption:",
				QLineEdit.EchoMode.Normal,
				item_text
				
        	)
			if ok and text:
				selected_items[0].setText(text)
		else:
			QMessageBox.information(
									None,
									'Information',
									'You need to select an item.',
									QMessageBox.StandardButton.Ok
								)
	
	def Create(self,parent):
		self.Parent = parent
		self.cfg = self.Parent.bobj.cfg.config
		
			
		self.font = QFont("Times", 10)
		self.font.setBold(False)

		metrics = QFontMetrics(self.font)

		self.paramgrp = QGroupBox("")
		self.paramlo = QGridLayout()
		self.paramgrp.setLayout(self.paramlo)
		self.paramgrp.setStyleSheet('background-color: 111111;')
		text = self.key + ":"
		self.LabelObj = QLabel(text)
		self.LabelObj.setFont(self.font)
		self.lwidth = metrics.horizontalAdvance(text)
		self.setSize(self.LabelObj,20,self.lwidth) 
		self.paramlo.addWidget(self.LabelObj,0,0,alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)

		self.ListObj =  QListWidget()
		self.ListObj.setFont(self.font)
		self.ListObj.setStyleSheet("background-color:  #FFFFFF")
		self.vcnt = 0


		for v in self.value:
			self.ListObj.insertItem(self.vcnt,self.value[self.vcnt])
			self.vcnt+=1

		self.paramlo.addWidget(self.ListObj,0,1,alignment= Qt.AlignmentFlag.AlignLeft)
		self.ListObj.currentRowChanged.connect(self.valueChangeArray)

		self.dirButton = QPushButton("Add")
		self.setSize(self.dirButton,30,100)
		self.dirButton.setStyleSheet("background-color:  #dddddd")
		self.dirButton.clicked.connect(self.AddItem)
		self.paramlo.addWidget(self.dirButton)


		self.delButton = QPushButton("Remove")
		self.setSize(self.delButton,30,100)
		self.delButton.setStyleSheet("background-color:  #dddddd")
		self.delButton.clicked.connect(self.RemoveItem)
		self.paramlo.addWidget(self.delButton)
		

		self.editButton = QPushButton("Edit")
		self.setSize(self.editButton,30,100)
		self.editButton.setStyleSheet("background-color:  #dddddd")
		self.editButton.clicked.connect(self.EditItem)
		self.paramlo.addWidget(self.editButton)
		
		self.upButton = QPushButton("Up")
		self.setSize(self.upButton,30,100)
		self.upButton.setStyleSheet("background-color:  #dddddd")
		self.upButton.clicked.connect(self.moveItem)
		self.paramlo.addWidget(self.upButton)
		return self.paramgrp
		
	def getLayout(self):
		return self.paramlo
	
	def getListObj(self):
		return self.ListObj 

	def valueChangeArray(self):
		selected_items = self.ListObj.selectedItems()
		if selected_items:
			#print("Value Changed",selected_items[0].text())
			self.Parent.itemChanged(self.key,self.value,self.ListObj)
			#print(self.key,self.value)

			
			
	def getHW(self):
		H = self.vcnt*20
		W = 300
		return H,W

	def setHW(self,H,W):
		self.setSize(self.ListObj,H,W)
		Hg = H+20
		Wg = W+20+self.lwidth
		self.setSize(self.paramgrp,Hg,Wg)
		return Hg,Wg

#############################################################################################
# 						class CfgString():
#############################################################################################
class CfgString():

	key = ""
	value = ""
	EditObj = None
	dirFlg = False
	fileFlg = False
	H = 0
	W = 0
	

	def __init__(self,key,value):
		self.key = key
		self.value = value
		

	def setAsDir(self):
		self.dirFlg = True

	def setAsFile(self):
		self.fileFlg = True

	def setSize(self,control,H,W):
		control.setMinimumHeight(H)
		control.setMinimumWidth(W)
		control.setMaximumHeight(H)
		control.setMaximumWidth(W)
	
	def updateCFGData(self):
		self.cfg[self.key] = self.EditObj.text()

	def Create(self,parent):
		self.Parent = parent
		self.cfg = self.Parent.bobj.cfg.config

	
		
		self.font = QFont("Times", 10)
		self.font.setBold(False)

		metrics = QFontMetrics(self.font)

		self.paramgrp = QGroupBox("")
		paramlo = QGridLayout()
		self.paramgrp.setLayout(paramlo)
		self.paramgrp.setStyleSheet('background-color: 111111;')
		
		text = self.key + ":"
		self.LabelObj = QLabel(text)
		self.LabelObj.setFont(self.font)
		self.lwidth = metrics.horizontalAdvance(text)
		self.setSize(self.LabelObj,20,self.lwidth) 
		paramlo.addWidget(self.LabelObj,0,0,alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)
		
		self.EditObj =  QLineEdit()
		self.EditObj.setFont(self.font)
		self.EditObj.setStyleSheet("background-color:  #FFFFFF")
		self.EditObj.setText(self.value)
		self.EditObj.editingFinished.connect(self.valueChange)
		
		ewidth =  math.floor(metrics.horizontalAdvance(self.value)*1.25)
		if len(self.value) == 0:
			ewidth = 100

		
		paramlo.addWidget(self.EditObj,0,1,alignment= Qt.AlignmentFlag.AlignLeft)
		
		if(self.fileFlg == True):
			self.dirButton = QPushButton("Select File")
			self.setSize(self.dirButton,30,100)
			self.dirButton.setStyleSheet("background-color:  #dddddd")
			self.dirButton.clicked.connect(self.AddImageItemFile)
			paramlo.addWidget(self.dirButton,1,0,alignment= Qt.AlignmentFlag.AlignLeft)
			self.H = 75
			self.W = 400
			self.setSize(self.EditObj,20,self.W-self.lwidth-20) 
			self.setSize(self.paramgrp,self.H,self.W)
		elif(self.dirFlg == True):
			self.dirButton = QPushButton("Select Dir")
			self.setSize(self.dirButton,30,100)
			self.dirButton.setStyleSheet("background-color:  #dddddd")
			self.dirButton.clicked.connect(self.AddImageItemDir)
			paramlo.addWidget(self.dirButton,1,0,alignment= Qt.AlignmentFlag.AlignLeft)
			self.H = 75
			self.W = 400
			self.setSize(self.EditObj,20,self.W-self.lwidth-20) 
			self.setSize(self.paramgrp,self.H,self.W)
		else:
			self.H = 50
			self.W = 400
			self.setSize(self.EditObj,20,self.W-self.lwidth-20) 
			self.setSize(self.paramgrp,self.H,self.W)
		return self.paramgrp
  	
	def RemoveImageItem(self):
		#print("remove")
		pass

	def AddImageItemDir(self):
		folder = QFileDialog.getOpenFileName(self.paramgrp, ("Open File"),
                                       "J:/MOD/FPIBGUtility/Latex",
                                       ("Images (*.png)"))
		
		if folder[0]:
			self.texFolder = os.path.dirname(folder[0])
			self.texFileName = os.path.splitext(os.path.basename(folder[0]))[0]
			self.EditObj.setText(self.texFolder)
			self.Parent.dirsChanged(folder[0])

	def AddImageItemFile(self):
		folder = QFileDialog.getOpenFileName(self.paramgrp, ("Open File"),
                                       "J:/FPIBGJournalStaticV2/rpt",
                                       ("Images (*.png)"))
		
		if folder[0]:
			self.texFolder = os.path.dirname(folder[0])
			self.texFileName = os.path.splitext(os.path.basename(folder[0]))[0]
			self.EditObj.setText(self.texFolder)
			self.Parent.filesChanged(folder[0])


	def AddImageItemDir(self):
		self.folder = QFileDialog.getExistingDirectory(self.paramgrp, ("Select Directory"),
                                       "J:/FPIBGJournalStaticV2/rpt")

		
		if self.folder:
			self.EditObj.setText(self.folder)
			
			


	def setText(self,text):
		self.EditObj.setText(text) 

	def setHW(self,H,W):
		#self.setSize(self.EditObj,H,W)
		#Hg = H+20
		#Wg = W+20+self.lwidth
		#self.setSize(self.paramgrp,Hg,Wg)
		return self.H,self.W
	
	def setTypeText(self,text):
		self.EditObj.setText(text)

	def valueChange(self):
		if(self.value!=self.EditObj.text()):
			#print("Value Changed",self.key)
			self.cfg[self.key]=self.EditObj.text()
			self.Parent.itemChanged(self.key,self.value)

class CfgCmd(CfgString):
	def __init__(self, key,value):
		super().__init__(key,value)
		

class CfgDataString():

	key = ""
	value = ""
	EditObj = None
	dirFlg = False
	fileFlg = False
	H = 0
	W = 0
	hasData = False
	startDir = "J:/MOD/FPIBGUtility/Latex"
	startDir = "J:/FPIBGJournalStaticV2/rpt"
	dataFile = ""

	def __init__(self, key,value):
		self.key = key
		self.value = value
		

	def setAsDir(self):
		self.dirFlg = True

	def setAsFile(self):
		self.fileFlg = True

	def setSize(self,control,H,W):
		control.setMinimumHeight(H)
		control.setMinimumWidth(W)
		control.setMaximumHeight(H)
		control.setMaximumWidth(W)
	
	def updateCFGData(self):
		self.cfg[self.key] = self.EditObj.text()

	def Create(self,parent):
		self.Parent = parent
		self.cfg = self.Parent.bobj.cfg.config

		self.font = QFont("Times", 10)
		self.font.setBold(False)

		metrics = QFontMetrics(self.font)

		self.paramgrp = QGroupBox("")
		paramlo = QGridLayout()
		self.paramgrp.setLayout(paramlo)
		self.paramgrp.setStyleSheet('background-color: 111111;')
		
		text = self.key + ":"
		self.LabelObj = QLabel(text)
		self.LabelObj.setFont(self.font)
		self.lwidth = metrics.horizontalAdvance(text)
		self.setSize(self.LabelObj,20,self.lwidth) 
		paramlo.addWidget(self.LabelObj,0,0,alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)
		
		self.EditObj =  QLineEdit()
		self.EditObj.setFont(self.font)
		self.EditObj.setStyleSheet("background-color:  #FFFFFF")
		self.EditObj.setText(self.value)
		self.EditObj.editingFinished.connect(self.valueChange)
		
		ewidth =  math.floor(metrics.horizontalAdvance(self.value)*1.25)
		if len(self.value) == 0:
			ewidth = 100

		
		paramlo.addWidget(self.EditObj,0,1,alignment= Qt.AlignmentFlag.AlignLeft)
		
		self.dirButton = QPushButton("Select File")
		self.setSize(self.dirButton,30,100)
		self.dirButton.setStyleSheet("background-color:  #dddddd")
		self.dirButton.clicked.connect(self.SelectDataFile)
		paramlo.addWidget(self.dirButton,1,0,alignment= Qt.AlignmentFlag.AlignLeft)
		self.H = 75
		self.W = 400
		self.setSize(self.EditObj,20,self.W-self.lwidth-20) 
		self.setSize(self.paramgrp,self.H,self.W)
		return self.paramgrp
  	
	def RemoveImageItem(self):
		#print("remove")
		pass

	def SelectDataFile(self):
		folder = QFileDialog.getOpenFileName(self.paramgrp, ("Open Data File"),
                                       self.startDir,
                                       ("Data (*.csv)"))
		
		if folder[0]:
			self.EditObj.setText(folder[0])


	def setText(self,text):
		self.EditObj.setText(text) 

	def setHW(self,H,W):
		#self.setSize(self.EditObj,H,W)
		#Hg = H+20
		#Wg = W+20+self.lwidth
		#self.setSize(self.paramgrp,Hg,Wg)
		return self.H,self.W
	
	def setTypeText(self,text):
		self.EditObj.setText(text)

	def valueChange(self):
		if(self.value!=self.EditObj.text()):
			#print("Value Changed",self.key)
			self.cfg[self.key]=self.EditObj.text()
			self.Parent.itemChanged(self.key,self.value)
			#self.base.updateCfg()


#############################################################################################
# 						class CfgTextBox():
#############################################################################################
class CfgTextBox():

	key = ""
	value = ""
	def __init__(self, key,value,parent):
		self.key = key
		self.value = value
		
  	
	def setSize(self,control,H,W):
		control.setMinimumHeight(H)
		control.setMinimumWidth(W)
		control.setMaximumHeight(H)
		control.setMaximumWidth(W)
	
	def updateCFGData(self):
		self.cfg[self.key]=self.EditObj.toPlainText()

	def Create(self,parent):
		self.Parent = parent
		self.cfg = self.Parent.bobj.cfg.config

	
		
		self.font = QFont("Times", 10)
		self.font.setBold(False)

		metrics = QFontMetrics(self.font)

		self.paramgrp = QGroupBox("")
		self.paramlo = QGridLayout()
		self.paramgrp.setLayout(self.paramlo)
		self.paramgrp.setStyleSheet('background-color: 111111;')
		
		text = self.key + ":"
		self.LabelObj = QLabel(text)
		self.LabelObj.setFont(self.font)
		self.lwidth = metrics.horizontalAdvance(text)
		self.setSize(self.LabelObj,20,self.lwidth) 
		self.paramlo.addWidget(self.LabelObj,0,0,alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)
		
		self.EditObj =  QTextEdit()
		self.EditObj.setFont(self.font)
		self.EditObj.setStyleSheet("background-color:  #FFFFFF")
		self.EditObj.setText(self.value)
		self.EditObj.textChanged.connect(self.valueChange)
		#self.EditObj.textChanged.connect(self.valueChange)
		ewidth =  math.floor(metrics.horizontalAdvance(self.value)*1.25)
		if len(self.value) == 0:
			ewidth = 100
		self.setSize(self.EditObj,20,ewidth) 
		self.paramlo.addWidget(self.EditObj,0,1,alignment= Qt.AlignmentFlag.AlignLeft)
		#self.EditObj.   valueChange.connect(self.valueChanged)
		self.setSize(self.paramgrp,50,25+ewidth+self.lwidth)
		return self.paramgrp
	
	def getLayout(self):
		return self.paramlo

	def setHW(self,H,W):
		self.setSize(self.EditObj,H,W)
		Hg = H+20
		Wg = W+20+self.lwidth
		self.setSize(self.paramgrp,Hg,Wg)
		return Hg,Wg

	def valueChange(self):
		#if(self.value!=self.EditObj.toPlainText()):
		#	print("Value Changed",self.key)
		self.Parent.itemChanged(self.key,self.value)
		
		
		
#############################################################################################
# 						class CfgBool():
#############################################################################################
class CfgBool():
	
	key = ""
	value = ""
	def __init__(self, key,value):
		self.key = key
		self.value = value
		
	def Create(self,parent):
		pass
  	
	def setSize(self,control,H,W):
		control.setMinimumHeight(H)
		control.setMinimumWidth(W)
		control.setMaximumHeight(H)
		control.setMaximumWidth(W)

	def updateCFGData(self):
		if(self.Combo.currentIndex() == 0):
			self.cfg[self.key]=True	
		else:
			self.cfg[self.key]=False
		

	def Create(self,parent):
		self.Parent = parent
		self.cfg = self.Parent.itemcfg.config

	
		self.font = QFont("Times", 10)
		self.font.setBold(False)

		metrics = QFontMetrics(self.font)

		paramgrp = QGroupBox("")
		paramlo = QGridLayout()
		paramgrp.setLayout(paramlo)
		paramgrp.setStyleSheet('background-color: 111111;')
		
		text = self.key + ":"
		self.LabelObj = QLabel(text)
		self.LabelObj.setFont(self.font)
		lwidth = metrics.horizontalAdvance(text)
		self.setSize(self.LabelObj,20,lwidth) 
		paramlo.addWidget(self.LabelObj,0,0,alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)
		
		self.Combo =  QComboBox()
		self.Combo.setFont(self.font)
		self.Combo.setStyleSheet("background-color:  #FFFFFF")
		
		self.Combo.addItem("True")
		self.Combo.addItem("False")
		self.Combo.currentIndexChanged.connect(self.valueChange)
		paramlo.addWidget(self.Combo,0,1,alignment= Qt.AlignmentFlag.AlignLeft)
		
		if(self.cfg[self.key] == True):
			self.Combo.setCurrentIndex(0)
			self.value = True
		else:
			self.Combo.setCurrentIndex(1)
			self.value = False
		return paramgrp
		
	def valueChange(self,index):
		
		if(self.Combo.currentIndex() == 0):
			self.cfg[self.key]=True	
			self.value = True
		else:
			self.cfg[self.key]=False
			self.value = False
		self.Parent.itemChanged(self.key,self.value)
		#print("Index Changed",index)
		
			
		
		
#############################################################################################
# 						class CfgInt():
#############################################################################################
class CfgInt():

	key = ""
	value = ""
	def __init__(self, key,value):
		self.key = key
		self.value = value
  	
	def setSize(self,control,H,W):
		control.setMinimumHeight(H)
		control.setMinimumWidth(W)
		control.setMaximumHeight(H)
		control.setMaximumWidth(W)

	def updateCFGData(self):
		if(str(self.value)!=self.EditObj.text()):
			self.cfg[self.key]=self.EditObj.text()
		

	def Create(self,parent):
		self.Parent = parent
		self.cfg = self.Parent.bobj.cfg.config

	
		
		self.font = QFont("Times", 12)
		self.font.setBold(False)

		metrics = QFontMetrics(self.font)

		paramgrp = QGroupBox("")
		paramlo = QGridLayout()
		paramgrp.setLayout(paramlo)
		paramgrp.setStyleSheet('background-color: 111111;')
		
		text = self.key + ":"
		self.LabelObj = QLabel(text)
		self.LabelObj.setFont(self.font)
		lwidth = metrics.horizontalAdvance(text)
		self.setSize(self.LabelObj,20,lwidth) 
		paramlo.addWidget(self.LabelObj,0,0,alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)
		
		self.EditObj =  QLineEdit()
		self.EditObj.setFont(self.font)
		#self.EditObj.setStyleSheet('background-color: 222222;')
		self.EditObj.setText(str(self.value))
		self.EditObj.editingFinished.connect(self.valueChange)
		#self.EditObj.textChanged.connect(self.valueChange)
		ewidth =  math.floor(metrics.horizontalAdvance(str(self.value))*1.25)
		self.setSize(self.EditObj,20,ewidth) 
		paramlo.addWidget(self.EditObj,0,1,alignment= Qt.AlignmentFlag.AlignLeft)
		#self.EditObj.   valueChange.connect(self.valueChanged)
		self.setSize(paramgrp,50,25+ewidth+lwidth)
		return paramgrp
		
	def valueChange(self):
		self.Parent.itemChanged(self.key,self.value)
		pass
		
			
		
		

class CfgButton():
	def __init__(self,key,value):
		self.key = key
		self.value = value
  	
	def setSize(self,control,H,W):
		control.setMinimumHeight(H)
		control.setMinimumWidth(W)
		control.setMaximumHeight(H)
		control.setMaximumWidth(W)

	def updateCFGData(self):
		pass

	
	
	def Create(self,parent):
		self.Parent = parent
		self.cfg = self.Parent.bobj.cfg.config
		
		
		self.font = QFont("Times", 10)
		self.font.setBold(False)

		metrics = QFontMetrics(self.font)

		self.paramgrp = QGroupBox("")
		self.paramlo = QGridLayout()
		self.paramgrp.setLayout(self.paramlo)
		self.paramgrp.setStyleSheet('background-color: 111111;')
		text = self.key + ":"
		self.LabelObj = QLabel(text)
		self.LabelObj.setFont(self.font)
		self.lwidth = metrics.horizontalAdvance(text)
		self.setSize(self.LabelObj,20,self.lwidth) 
		self.paramlo.addWidget(self.LabelObj,0,0,alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)

		self.Button = QPushButton(self.key)
		self.setSize(self.Button,30,100)
		self.Button.setStyleSheet("background-color:  #dddddd")
		self.Button.clicked.connect(self.valueChange)
		self.paramlo.addWidget(self.Button)
		return self.paramgrp
	
	def getLayout(self):
		return self.paramlo

	def valueChange(self):
		self.Parent.itemChanged(self.key,self.value)
		#print(self.key,self.value)

			
			
	def getHW(self):
		H = self.vcnt*20
		W = 300
		return H,W

	def setHW(self,H,W):
		self.setSize(self.ListObj,H,W)
		Hg = H+20
		Wg = W+20+self.lwidth
		self.setSize(self.paramgrp,Hg,Wg)
		return Hg,Wg
