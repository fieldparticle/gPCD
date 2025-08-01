import subprocess, os


class LatexPreview():
    fileName = ''
    def __init__(self,fileName,texlist,wkdir,valsFile):
        self.fileName = fileName
        self.texList = texlist
        self.wkdir = wkdir
        self.valsFile = valsFile
        pass

    def ProcessLatxCode(self):
        if not os.path.exists(self.valsFile):
            vl = open(self.valsFile,'w')            
            vl.write("% Values file.")
            vl.close()
        dirname = os.path.dirname(self.fileName)
        hdr_file = dirname + "/LatexUtilityBaseHeader.tex"
        hdr_lst = []
        with open(hdr_file,"r") as hfile:
            hdr_lst.append(hfile.readlines())

        fl = open(self.fileName,'w')
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

        fl.write('\\begin{document}\n')
        fl.write("\\input{"  +  self.valsFile  + "}\n")
        for ii in self.texList:
            texname = "\\input {" + ii + "}\n" 
            fl.write(texname)
        fl.write('\\end{document}\n')
        fl.flush()
        fl.close()
    
    def Run(self):
        with open("termPreview.log","w") as outFile:
            x = subprocess.call(f"pdflatex -halt-on-error -interaction=batchmode {self.fileName}",cwd= self.wkdir,stdout=outFile)
            if x != 0:
                print('Exit-code not 0, check result!')
                