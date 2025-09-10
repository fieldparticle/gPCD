
from ReportClass import *
import os
import inspect
from TrendLine import *
import re
from AttrDictFields import *
from ConfigUtility import *


class LatexEquationWriter(ReportClass):

    eq_lst = []
    tex_lst = []
    def __init__(self,Parent):
        super().__init__(Parent)

    def Create(self,eq_lst):
        self.eq_lst = eq_lst

    def save_latex(self):
        texname = self.cfg.tex_dir + "/" + ii[0] + ".tex"
        self.tex_lst.append(texname)
        try:
            f = open(texname, "w")
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
            return    
        w = "\\begin{equation}\n"
        f.write(w)
        w = "\\begin{aligned}\n"
        f.write(w)
        
        f.write(ii[1])
        w ="\\label{eqn:" + ii[0] + "}\n"
        f.write(w)   
        w = "\\end{aligned}\n"
        f.write(w)   
        w = "\\end{equation}\n"
        f.write(w)   
        f.close()

    def get_tex_list(self):
        return self.tex_lst
        """
        loutname = self.cfg.tex_dir + "/" + self.cfg.name_text + ".tex"
        try:
            f = open(loutname, "w")
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
            return
        """
   
#############################################################################################