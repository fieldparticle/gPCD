import subprocess, os

from PyQt6.QtWidgets import QGridLayout, QLineEdit,QDialog,QLabel,QPushButton,QWidget
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtCore import QPoint
import time
class LatexPreview():
    fileName = ''
    def __init__(self,fileName,texname,wkdir,valsFile):
        self.fileName = fileName
        self.texname = texname
        self.wkdir = wkdir
        self.valsFile = valsFile
        pass

    def ProcessLatxCode(self):
        self.hdr_file = self.wkdir + "/LatexUtilityBaseHeader.tex"
        self.prev_file = self.wkdir + "/preview.tex"
        hdr_lst = []
        with open(self.hdr_file,"r") as hfile:
            hdr_lst.append(hfile.readlines())

        fl = open(self.prev_file,'w')
        for ii in range(len(hdr_lst)):
            res = ' '.join(hdr_lst[ii])
            fl.write(res)    
        fl.write('\\usepackage{graphicx}\n')
        fl.write('\\usepackage{subcaption}\n')
        fl.write('\\usepackage{makecell}\n')
        fl.write('\\newcommand{\\mmrr}{\\textit{\\textbf{$mmrr$}}}\n')
        fl.write('\\newcommand{\\arr}{\\textit{\\textbf{$arr$}}}\n')
        fl.write('\\newcommand{\\arrg}{\\textit{\\textbf{$arr_G$}}}\n')
        fl.write('\\newcommand{\\arrc}{\\textit{\\textbf{$arr_C$}}}\n')
        fl.write('\\newcommand{\\arrt}{\\textit{\\textbf{$arr_T$}}}\n')
        if self.valsFile != None:
            fl.write("\\include{"  +  self.valsFile  + "}\n")
        fl.write('\\begin{document}\n')
        texname = "\\input {" + self.texname + "}\n" 
        fl.write(texname)
        fl.write('\\end{document}\n')
        fl.flush()
        fl.close()
    
    def Run(self):
        with open("termPreview.log","w") as outFile:
            x = subprocess.call(f"pdflatex -halt-on-error -interaction=batchmode {self.prev_file}",cwd=self.wkdir,stdout=outFile)
            if x != 0:
                print('Exit-code not 0, check result!')

class PreviewDialog(QDialog):
	
    flg_isopen = False
    def __init__(self,pdfName):
        super().__init__()
        self.pdfName = pdfName
        self.setWindowTitle('Data Passing Dialog')
        self.setGeometry(100, 100, 1000, 800)
        layout = QGridLayout()
        self.document = QPdfDocument(self)
        try:
            self.document.load(pdfName)
        except BaseException as e:
            self.log.log(self,e)

        view = QPdfView(self)
        view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        #view.setPageMode(QPdfView.PageMode.MultiPage)
        view.setDocument(self.document)
        layout.addWidget(view)
        self.submit_button = QPushButton('Done')
        self.submit_button.clicked.connect(self.submit_data)
        layout.addWidget(self.submit_button)
        widget = QWidget()
        widget.setLayout(layout)
        self.setLayout(layout)
        self.flg_isopen = True
        self.show()
    
    def closeEvent(self,event):
        flg_isopen = False
        event.accept()

    def submit_data(self):
        self.accept()

    def new_doc(self):
      pass