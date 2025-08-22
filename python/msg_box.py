import sys
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

def showdialog(class_txt,err_txt):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText(err_txt)
    msg.setInformativeText("Error")
    msg.setWindowTitle("gPCD error box")
    msg.setDetailedText(err_txt)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.setStyleSheet("QLabel{min-width: 300px; font-size: 16px;}"
                            "QPushButton{width: 100px;}")
   #msg.buttonClicked.connect(err_txt)
    retval = msg.exec()
