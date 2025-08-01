
import sys                                                    
from PyQt6.QtWidgets import QApplication
from utility.LatexWin import *
from shared.BaseClass import *
import matplotlib

######################### PYTHON PATH NEEDS TO BE SET TO FIND THE CLASSES###############
## Create a base class.
bc = BaseObj("FrontEnd")
#print("Hello World\n", file=sys.stdout)
bc.Create("Particle.cfg",'FPIBGJB.log')

if __name__ == '__main__':
    f = matplotlib.matplotlib_fname()
    #print(f)
    app = QApplication(sys.argv)
    screens = app.screens()
    window = LatexWin(bc,"LatexMainWin")
    screen = screens[3]
    qr = screen.geometry()
    window.move(qr.left(), qr.top())
    window.Create(bc)
    sys.exit(app.exec())
    
