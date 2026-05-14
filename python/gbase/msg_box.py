import sys
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from PyQt6.QtWidgets import QMessageBox, QWidget


def verify_dialog(
    parent: QWidget | None = None,
    title: str = "Verify",
    message: str = "Are you sure?",
    yes_text: str = "Yes",
    no_text: str = "No",
) -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(title)
    box.setText(message)

    yes_btn = box.addButton(yes_text, QMessageBox.ButtonRole.YesRole)
    no_btn = box.addButton(no_text, QMessageBox.ButtonRole.NoRole)

    box.setDefaultButton(no_btn)
    box.exec()

    return box.clickedButton() == yes_btn

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
