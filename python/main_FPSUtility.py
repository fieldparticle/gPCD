###############################################################
## Preamble to every script. Will append the shared directory #
import sys                                                    #  
import os                                                     #
syspth = sys.path                                             #
cwd = os.path.dirname(os.path.abspath(__file__))
os.chdir(cwd)
print(cwd)                          #
#shrddir = cwd + "\\python\\shared"                            #
#sys.path.append(shrddir)           
#shrddir = cwd + "\\python\\test"                            #
#sys.path.append(shrddir)           
import getpass                                                #
#print(getpass.getuser())                                      #
guser = getpass.getuser()                            #
# Now do imports                                              #
###############################################################
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton
from PyQt6.QtCore import Qt
from UtilityMainWin import *
from gbase.ParticleBase import *
from gbase.MonitorSelection import load_preferred_monitor
import matplotlib
## Create a base class.
bc = ParticleBase("FrontEnd")
#print("Hello World\n", file=sys.stdout)
bc.Create("ParticleUtil.cfg",'ParicleUtil.log')

if __name__ == '__main__':
    #f = matplotlib.matplotclslib_fname()
    #print(f)
    app = QApplication(sys.argv)
    screens = app.screens()
    window = UtilityMainWin(bc,"UtilMainWin")
    preferred_monitor = load_preferred_monitor(0)
    if preferred_monitor < 0:
        preferred_monitor = 0
    if preferred_monitor >= len(screens):
        preferred_monitor = len(screens) - 1
    screen = screens[preferred_monitor] if screens else app.primaryScreen()
    qr = screen.geometry()
    window.move(qr.left(), qr.top())
    window.Create(bc)
    sys.exit(app.exec())
    

