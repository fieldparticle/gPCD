
from ReportClass import *
import os
import inspect
from TrendLine import *
import re
from AttrDictFields import *
from ConfigUtility import *
from ValuesDataBase import *


class ReportLatexEquation(ReportClass):

    eq_lst = []
    tex_lst = []
    def __init__(self,parent,itemcfg):
        super().__init__(parent,itemcfg)

   

    def Create(self,eq_lst):
        self.eq_lst = eq_lst

    def save_latex(self):
        vdb = ValuesDataBase(self.bobj)
        fld = vdb.get_vals()

        

        self.tex_output_name = self.itemcfg.tex_dir + "/" + self.itemcfg.name + ".tex"
        self.tex_lst.append(self.tex_output_name)
        try:
            f = open(self.tex_output_name, "w")
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
            return    
        w = "\\begin{equation}\n"
        f.write(w)
        w = "\\begin{aligned}\n"
        f.write(w)

        equat = "f\""
        eqtxt = ""
        for ii in self.itemcfg.equation:
            
            if 'fld' in ii:
                field,fmt = self.extract_field(ii)
                if field in fld:
                    val = fld[field]
                    try:
                        val_str = "f\"{" + val + fmt + "}\"" 
                        eval_str = eval(val_str)
                        eqtxt+=eval_str
                    except BaseException as e:
                        print(e)
                        raise ValueError
            
            else:
            
                eqtxt+= ii
       
        #f.write('$')
        f.write(eqtxt)
        #f.write('\n')
        w ="\\label{eqn:" + self.itemcfg.name + "}\n"
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