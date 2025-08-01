
class ValHandler:
    
    def __init__(self):
        pass
    file_name =""
    def appendValues(self,macro,val):
        valstr = "\\newcommand{\\" + macro + "}{" + val + "}\n"
        fl = open(self.file_name,'a')
        fl.write(valstr)
        fl.close()
    def Create(self,flname):
        self.file_name = flname
        fl = open(self.file_name,'w')
        fl.close()
        self.doValues()


    def doValues(self,fileName=None,fps=None,nump=None,qur=None):
        fl = open(self.file_name,'a')
        txt = "\\newcommand{\\bestTime}{" + "25" + " ms}\n"
        fl.write(txt)
        txt = "\\newcommand{\\bestFPS}{" + "40" + " fps}\n"
        fl.write(txt)
        txt = "\\newcommand{\\bestNumberParts}{" + "4,375,552" +"}\n"
        fl.write(txt)
        fl.write('\\newcommand{\\bestNumberQueries}{$9.5727x10^{12}$}\n')
        """
        txt = "\\newcommand{\\bestTime}{" + fps + " fps}\n"
        fl.write(txt)
        txt = "\\newcommand{\\bestNumberParts}{" + nump +"}\n"
        fl.write(txt)
        fl.write('\\newcommand{\\bestNumberQueries}{$9.5727x10^{12}$}\n')
        """
        fl.close()


