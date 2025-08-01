from LogClass import *
from ConfigClass import *

import os
import inspect
import matplotlib.pyplot as plt
from ValHandler import *
#############################################################################################
# 						base class LatexClass
#############################################################################################
class LatexClass:

    ##  Constructor for the LatexClass object.
    # @param   ObjName --  (string) Saves the name of the object.
    def __init__(self,Parent):
        self.Parent = Parent
        self.bobj = self.Parent.bobj
        self.log = self.bobj.log
        self.cfg = Parent.itemcfg.config 
        self.itemcfg = Parent.itemcfg 
        self.cleanPRE = True
        self.valHandler = ValHandler()

    def setCleanPre(self, flg):
        self.cleanPRE = flg

    def WritePre(self,pre_name):
        cfg = self.Parent.itemcfg.config
        preoutname = cfg.tex_dir + "/" + pre_name +".tex"
        if self.cleanPRE == True:
            p = open(preoutname, "w")
        else:
            p = open(preoutname, "a")
        w = "%%============================================= Plot %s\r"%(cfg.name_text )
        p.write(w)
        w = "Fig. \\ref{fig:%s}\r"%(cfg.name_text)
        p.write(w)
        if len(cfg.tex_dir) == 0:
            loutname = cfg.name_text + ".tex"
        else:
            loutname =  cfg.tex_dir + "/" + cfg.name_text + ".tex"
        w = "\\input{%s}\r"%(loutname)
        p.write(w)
        p.close()    

    def get_tex_list(self):
        return [f"{self.itemcfg.config.tex_dir}/{self.itemcfg.config.name_text}.tex"]

class LatexEquationWriter(LatexClass):

    eq_lst = []
    tex_lst = []
    def __init__(self,Parent):
        super().__init__(Parent)

    def Create(self,eq_lst):
        self.eq_lst = eq_lst

    def Write(self):
        for ii in self.eq_lst:
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
# 						class LatexTableWriter
#############################################################################################
class LatexSplitTableWriter(LatexClass):
    
    def __init__(self,Parent):
        super().__init__(Parent)

    
    def Create(self,data):
        self.data = data
        self.cols = self.data.shape[0]
        self.rows = self.data.shape[1]
        self.table_array  = [[0 for x in range(self.cols)] for y in range(self.rows)] 
        self.setLatexData()
        
    header_arry = []
    
    def setLatexHeaderArray(self, header):
        self.header_arry = header

    def setTableItemArray(self, cellstr,col, row):
        self.table_array[row][col] = cellstr

    def setLatexData(self):
        for i in range(self.cols):
            for j in range(self.rows):
                self.loadItem(i,j)

    def loadItem(self,i,j):
        cellstr = ""
        val =  self.data[i][j]
        if i > len(self.cfg[f"format_array1"]):
            print("Mismatch between colums of data and the format of that data.")
            return
        fmt_txt = self.cfg[f"format_array1"][i]
        if 'd' in fmt_txt:
            pval = int(val)
        elif 'f' in fmt_txt:
            pval = float(val)
        elif 's' in fmt_txt:
            pval = str(val)
            ret = self.setTableItemArray(pval,i,j)
            return pval            
        out1 = f"{pval}"
        out_txt = "f\"%{fmt_txt}\"%(" + out1 + ")"
        #out_data = eval(out_txt)
        out_val = eval(out_txt)
        #out_val = eval(out_val)
        ret = self.setTableItemArray(out_val,i,j)
        return out_val
    
        if (i == 2):
            self.setTableItemArray(str("%.2f" % (1000*value)),i,j)
            return "%.2f" % (1000*value)
        
        if (i == 3):
            self.setTableItemArray(str("%.2f" % (1000*value)),i,j)
            return "%.2f" % (1000*value)

                    
    def MultiTable(self,f):
        
        num_tables = 0    
        split_at = 0
        end_row = 0
        if 'split_table_array' in self.cfg:
            num_tables = int(self.cfg.split_table_array[0])
            split_at = int(self.cfg.split_table_array[1])
            end_row = split_at-1
        else:
            num_tables = 1
            split_at = 0
        

        start_row = 0
        f.write("\\begin{table}[%s]\n" % self.cfg.placement_text)
        f.write("\\caption{\\textit{")
        f.write(self.cfg.caption_box)
        f.write("}}\n")
        f.write("\\label{tab:%s}\n"%self.cfg.name_text)
            
        for i in range(num_tables):
            if num_tables > 1:
                f.write("\\begin{minipage}{.5\\linewidth}\n")
            if i > 0:
                start_row = split_at
                end_row = self.rows
            f.write("\\fontsize{%s}{%s}\\selectfont\n" % (self.cfg.font_size,self.cfg.font_size))
            f.write("\\renewcommand{\\arraystretch}{%s}\n" % (self.cfg.arystretch_text))
            
            f.write("\\begin{center}\n")
            f.write("\\begin{tabular}\n{")
            for k in range(self.cols):
                f.write("l ")
            f.write("}\n")
            f.write("\\hline \\\\ \n")
            header_key = f"header_array1"
            lsz = len(self.cfg[header_key])
            headers = self.cfg[header_key]
            if (self.cols != lsz):
                f.close()
                print("In LatexTableWriter columns of data do not match column headings")   
                return 
            for k in range(lsz):
                if(k < lsz-1):
                    txt = ""
                    txt = "\\makecell{" + headers[k] + "}&"
                else:
                    txt = "\\makecell{" + headers[k] + "}"
                f.write(txt)
            
            f.write("\\\\ \\hline\n")

            for i in range(start_row,end_row): #,skip):
                for j in range(self.cols):
                    if(j < self.cols-1):
                        
                        #txt = self.format_cell(self.table_array[i][j],j,1) + "&"
                        txt = str(self.table_array[i][j]) + "&"
                        f.write(txt)
                    else:
                        txt = str(self.table_array[i][j]) + "\\\\ \n"
                        f.write(txt)
            f.write("\\hline\n\\end{tabular}\n\\end{center}\n")
            if num_tables > 1:
                f.write("\\end{minipage}\n")

        f.write("\\end{table}\n")
        f.close()
        self.WritePre("pre_tables")
      
    def Write(self):
        loutname = self.cfg.tex_dir + "/" + self.cfg.name_text + ".tex"
        try:
            f = open(loutname, "w")
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
            return
        self.MultiTable(f)

# 						class LatexTableWriter
#############################################################################################
class LatexMultiTableWriter(LatexClass):
    
    def __init__(self,Parent):
        super().__init__(Parent)

    
    def Create(self,data):
        self.data = data
        self.cols = self.data.shape[0]
        self.rows = self.data.shape[1]
        self.table_array  = [[0 for x in range(self.cols)] for y in range(self.rows)] 
        self.setLatexData()
        
    header_arry = []
    
    def setLatexHeaderArray(self, header):
        self.header_arry = header

    def setTableItemArray(self, cellstr,col, row):
        self.table_array[row][col] = cellstr

    def setLatexData(self):
        for i in range(self.cols):
            for j in range(self.rows):
                self.loadItem(i,j)

    def loadItem(self,i,j):
        cellstr = ""
        val =  self.data[i][j]
        if i > len(self.cfg[f"format_array1"]):
            print("Mismatch between colums of data and the format of that data.")
            return
        fmt_txt = self.cfg[f"format_array1"][i]
        if 'd' in fmt_txt:
            pval = int(val)
        elif 'f' in fmt_txt:
            pval = float(val)
        elif 's' in fmt_txt:
            pval = str(val)
            ret = self.setTableItemArray(pval,i,j)
            return pval            
        out1 = f"{pval}"
        out_txt = "f\"%{fmt_txt}\"%(" + out1 + ")"
        #out_data = eval(out_txt)
        out_val = eval(out_txt)
        #out_val = eval(out_val)
        ret = self.setTableItemArray(out_val,i,j)
        return out_val
    
        if (i == 2):
            self.setTableItemArray(str("%.2f" % (1000*value)),i,j)
            return "%.2f" % (1000*value)
        
        if (i == 3):
            self.setTableItemArray(str("%.2f" % (1000*value)),i,j)
            return "%.2f" % (1000*value)

                    
    def MultiTable(self,f):
        
        num_tables = 0    
        split_at = 0
        end_row = 0
        if 'split_table_array' in self.cfg:
            num_tables = int(self.cfg.split_table_array[0])
            split_at = int(self.cfg.split_table_array[1])
            end_row = split_at-1
        else:
            num_tables = 1
            split_at = 0
        

        start_row = 0
        end_row = self.rows
        f.write("\\begin{table}[%s]\n" % self.cfg.placement_text)
        f.write("\\caption{\\textit{")
        f.write(self.cfg.caption_box)
        f.write("}}\n")
        f.write("\\label{tab:%s}\n"%self.cfg.name_text)
            
        for i in range(num_tables):
            if num_tables > 1:
                f.write("\\begin{minipage}{.5\\linewidth}\n")
                if i > 0:
                    start_row = split_at
                    end_row = self.rows
            f.write("\\fontsize{%s}{%s}\\selectfont\n" % (self.cfg.font_size,self.cfg.font_size))
            f.write("\\renewcommand{\\arraystretch}{%s}\n" % (self.cfg.arystretch_text))
            
            f.write("\\begin{center}\n")
            f.write("\\begin{tabular}\n{")
            for k in range(self.cols):
                f.write("l ")
            f.write("}\n")
            f.write("\\hline \\\\ \n")
            header_key = f"header_array1"
            lsz = len(self.cfg[header_key])
            headers = self.cfg[header_key]
            if (self.cols != lsz):
                f.close()
                print("In LatexTableWriter columns of data do not match column headings")   
                return 
            for k in range(lsz):
                if(k < lsz-1):
                    txt = ""
                    txt = "\\makecell{" + headers[k] + "}&"
                else:
                    txt = "\\makecell{" + headers[k] + "}"
                f.write(txt)
            
            f.write("\\\\ \\hline\n")

            for i in range(start_row,end_row): #,skip):
                for j in range(self.cols):
                    if(j < self.cols-1):
                        
                        #txt = self.format_cell(self.table_array[i][j],j,1) + "&"
                        txt = str(self.table_array[i][j]) + "&"
                        f.write(txt)
                    else:
                        txt = str(self.table_array[i][j]) + "\\\\ \n"
                        f.write(txt)
            f.write("\\hline\n\\end{tabular}\n\\end{center}\n")
            if num_tables > 1:
                f.write("\\end{minipage}\n")

        f.write("\\end{table}\n")
        f.close()
        self.WritePre("pre_tables")
      
    def Write(self):
        loutname = self.cfg.tex_dir + "/" + self.cfg.name_text + ".tex"
        try:
            f = open(loutname, "w")
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
            return
        self.MultiTable(f)

        
        
#############################################################################################
# 						class LatexPlotWriter
#############################################################################################
class LatexPlotWriter(LatexClass):

   ##  Constructor for the LatexClass object.
    # @param   ObjName --  (string) Saves the name of the object.
    def __init__(self,Parent):
        ## ObjName contains the name of this object.
        super().__init__(Parent)
 
    def Write(self):
        cfg = self.Parent.itemcfg.config
        outfile = cfg.tex_dir + "/" + cfg.name_text + ".tex"
        try:
            f = open(outfile, "w")
        except IOError as e:
            print(e)
            self.log.log(self,f"Couldn't write to file ({e})")
            return 
        
        try:
            
            w ="\\begingroup\n"
            f.write(w)
            w = "\\centering\n"
            f.write(w)
            w = "\\begin{figure*}[" + cfg.placement_text + "]\n"
            f.write(w)
            previewTex = f"{cfg.plots_dir}/{cfg.name_text}1.png"
            gdir = "".join(previewTex.rsplit(cfg.tex_dir))
            sgdir = ''.join( c for c in gdir if  c not in '/' )
    #                print(sgdir)    
            w = "\t\t\\includegraphics[width=" +  cfg.plot_width_text +  "in]{" + sgdir + "}\n"
            f.write(w)
            refname = os.path.splitext(os.path.basename(gdir))[0]
            w = "\t\t\\label{fig:" + refname + "}\n"
            f.write(w)
            w = "\\hspace{" + cfg.hspace_text + "in}\n"
            f.write(w)
            w = "\\caption[TITLE:" + cfg.title_text + "]{\\textit{" + cfg.caption_box + "}}\n"
            f.write(w)
            w = "\t\t\\label{fig:" + cfg.name_text + "}\n"
            f.write(w)
            w = "\\end{figure*}\n"
            f.write(w)
            w = "\\endgroup"
            f.write(w)
        except IOError as err:
            self.log.log(self,f"Couldn't write to file ({err})")
            f.close()
            return
        f.close()

        
     

#############################################################################################
# 						class LatexImageWriter
#############################################################################################
class LatexImageWriter(LatexClass):

  ##  Constructor for the LatexClass object.
    # @param   ObjName --  (string) Saves the name of the object.
    def __init__(self,Parent):
        ## ObjName contains the name of this object.
        super().__init__(Parent)
       
    
 
    def Write(self):
        cfg = self.Parent.itemcfg.config
        loutname = cfg.tex_dir + "/" + cfg.name_text + ".tex"
        previewTex = f"{cfg.tex_dir}/{cfg.images_name_text}"
        gdir = "".join(previewTex.rsplit(cfg.tex_dir))
        sgdir = ''.join( c for c in gdir if  c not in '/' )
        print(sgdir)    
        f = open(loutname, "w")
        w = "\\begin{figure*}[" + cfg.placement_text + "]\r"
        f.write(w)
        w = "\\centering\r"
        f.write(w)
        if len(cfg.tex_dir) == 0:
            loutname = cfg.name_text 
        else:
            loutname = cfg.tex_dir + "/" + cfg.name_text
        w = "\\includegraphics[width=%0.2fin]{%s}\r"%(8.5*float(cfg.scale_text),sgdir)
        f.write(w)
        w = "\\caption[%s]{\\textit{%s}}\r"%(cfg.title_text,cfg.caption_box)
        f.write(w)
        w = "\\label{fig:%s}\r"%(cfg.name_text)
        f.write(w)
        w = "\\end{figure*}\r"
        f.write(w)
        f.close()
        self.WritePre("pre_plots")
     
      
        pass


#############################################################################################
# 						class LatexMultiImageWriter
#############################################################################################
class LatexMultiImageWriter(LatexClass):


    
   ##  Constructor for the LatexClass object.
    # @param   ObjName --  (string) Saves the name of the object.
    def __init__(self,Parent):
        ## ObjName contains the name of this object.
        super().__init__(Parent)
        self.images = []
 
    def Write(self):
        cfg = self.Parent.itemcfg.config
        outfile = cfg.tex_dir + "/" + cfg.name_text + ".tex"
        try:
            f = open(outfile, "w")
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
        w ="\\begingroup\n"
        f.write(w)
        
        w = "\\begin{figure*}[" + cfg.placement_text + "]\n"
        f.write(w)
        if cfg.centering_bool == True:
            w = "\\centering\n"
            f.write(w)
        try:
            for ii in range(0,int(self.cfg.num_plots_text)):
                #w = "\t\\begin{subfigure}[b]{" + cfg.plot_width_array[ii] + "in}\n"
                w = "\t\\begin{subfigure}[b]{" + cfg.plot_scale_array[ii] + "\\textwidth}\n"
                f.write(w)
                previewTex = f"{cfg.plots_dir}/{cfg.images_name_array[ii]}"
                gdir = "".join(previewTex.rsplit(cfg.tex_dir))
                sgdir = ''.join( c for c in gdir if  c not in '/' )
                print(sgdir)    
                w = "\t\t\\includegraphics[width=\\textwidth]{" + sgdir + "}\n"
                f.write(w)
                w = "\t\t\\subcaption[" + "" +"]{" + cfg.caption_array[ii] + "}\n"
                f.write(w)
                refname = os.path.splitext(os.path.basename(sgdir))[0]
                w = "\t\t\\label{fig:" + refname + "}\n"
                f.write(w)
                w = "\t\\end{subfigure}\n"
                f.write(w)
                w = "\\hspace{" + cfg.hspace_text + "in}\n"
                f.write(w)
            w = "\\caption[TITLE:" + cfg.title_text + "]{\\textit{" + cfg.caption_box + "}}\n"
            f.write(w)
            w = "\t\t\\label{fig:" + cfg.name_text + "}\n"
            f.write(w)
            w = "\\end{figure*}\n"
            f.write(w)
            w = "\\endgroup"
            f.write(w)
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
            f.close()
            return
        f.close()

     
     #############################################################################################
# 						class LatexMultiImageWriter
#############################################################################################
class LatexMultiPlotWriter(LatexClass):


    
   ##  Constructor for the LatexClass object.
    # @param   ObjName --  (string) Saves the name of the object.
    def __init__(self,Parent):
        ## ObjName contains the name of this object.
        super().__init__(Parent)
        self.images = []
 
    def Write(self):
        cfg = self.Parent.itemcfg.config
        outfile = cfg.tex_dir + "/" + cfg.name_text + ".tex"
        try:
            f = open(outfile, "w")
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
        w ="\\begingroup\n"
        f.write(w)
        w = "\\centering\n"
        f.write(w)
        w = "\\begin{figure*}[" + cfg.placement_text + "]\n"
        f.write(w)
        
        try:
            for ii in range(0,int(self.cfg.num_plots_text)):
                w = "\t\\begin{subfigure}[b]{" + cfg.plot_width_text + "in}\n"
                f.write(w)
                previewTex = f"{cfg.plots_dir}/{cfg.name_text}{ii+1}.png"
                gdir = "".join(previewTex.rsplit(cfg.tex_dir))
                sgdir = ''.join( c for c in gdir if  c not in '/' )
#                print(sgdir)    
                w = "\t\t\\includegraphics[width=" +  cfg.plot_width_text +  "in]{" + sgdir + "}\n"
                f.write(w)
                w = "\t\t\\subcaption[" + "" +"]{" + cfg.caption_array[ii] + "}\n"
                f.write(w)
                refname = os.path.splitext(os.path.basename(gdir))[0]
                w = "\t\t\\label{fig:" + refname + "}\n"
                f.write(w)
                w = "\t\\end{subfigure}\n"
                f.write(w)
                w = "\\hspace{" + cfg.hspace_text + "in}\n"
                f.write(w)
            w = "\\caption[TITLE:" + cfg.title_text + "]{\\textit{" + cfg.caption_box + "}}\n"
            f.write(w)
            w = "\t\t\\label{fig:" + cfg.name_text + "}\n"
            f.write(w)
            w = "\\end{figure*}\n"
            f.write(w)
            w = "\\endgroup"
            f.write(w)
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
            f.close()
            return
        f.close()

      
        



   
#############################################################################################
# 						class LatexTableWriter
#############################################################################################
class LatexTableWriter(LatexClass):
    
    def __init__(self,Parent):
        super().__init__(Parent)

    
    def Create(self,data):
        self.data = data
        self.cols = self.data.shape[0]
        self.rows = self.data.shape[1]
        self.table_array  = [[0 for x in range(self.cols)] for y in range(self.rows)] 
        self.setLatexData()
        
    header_arry = []
    
    def setLatexHeaderArray(self, header):
        self.header_arry = header

    def setTableItemArray(self, cellstr,col, row):
        self.table_array[row][col] = cellstr

    def setLatexData(self):
        for i in range(self.cols):
            for j in range(self.rows):
                self.loadItem(i,j)

    def loadItem(self,i,j):
        cellstr = ""
        try:
            if i == 11:
                print(f"{i} {j}")       
            val =  self.data[i][j]
            if i > len(self.cfg[f"format_array1"]):
                print("Mismatch between colums of data and the format of that data.")
                return
            
            fmt_txt = self.cfg[f"format_array1"][i]
            if 'd' in fmt_txt:
                pval = int(val)
            elif 'f' in fmt_txt:
                pval = float(val)
            elif 's' in fmt_txt:
                pval = str(val)
                ret = self.setTableItemArray(pval,i,j)
                return pval            
        except BaseException as e:
            print(e)
        out1 = f"{pval}"
        out_txt = "f\"%{fmt_txt}\"%(" + out1 + ")"
        #out_data = eval(out_txt)
        out_val = eval(out_txt)
        #out_val = eval(out_val)
        ret = self.setTableItemArray(out_val,i,j)
        return out_val
    
      
    def Table(self,f):
        
        f.write("\\begin{table}[%s]\n" % self.cfg.placement_text)
        
        f.write("\\fontsize{%s}{%s}\\selectfont\n" % (self.cfg.font_size,self.cfg.font_size))
        f.write("\\renewcommand{\\arraystretch}{%s}\n" % (self.cfg.arystretch_text))
        
        f.write("\\caption{\\textit{")
        f.write(self.cfg.caption_box)
        f.write("}}\n")
        f.write("\\label{tab:%s}\n"%self.cfg.name_text)
        f.write("\\begin{center}\n")
        f.write("\\begin{tabular}\n{")
        for k in range(self.cols):
            f.write("l ")
        f.write("}\n")
        f.write("\\hline \\\\ \n")
        header_key = f"header_array1"
        lsz = len(self.cfg[header_key])
        headers = self.cfg[header_key]
        if (self.cols != lsz):
            f.close()
            print("In LatexTableWriter columns of data do not match column headings")   
            return 
        for k in range(lsz):
            if(k < lsz-1):
                txt = ""
                txt = "\\makecell{" + headers[k] + "}&"
            else:
                txt = "\\makecell{" + headers[k] + "}"
            f.write(txt)
        
        f.write("\\\\ \\hline\n")

        for i in range(0,self.rows): #,skip):
            for j in range(self.cols):
                if(j < self.cols-1):
                    
                    #txt = self.format_cell(self.table_array[i][j],j,1) + "&"
                    txt = str(self.table_array[i][j]) + "&"
                    f.write(txt)
                else:
                    txt = str(self.table_array[i][j]) + "\\\\ \n"
                    f.write(txt)
        f.write("\\hline\n\\end{tabular}\n\\end{center}\n")
            
        f.write("\\end{table}\n")
        f.close()
        self.WritePre("pre_tables")
      
    def Write(self):
        loutname = self.cfg.tex_dir + "/" + self.cfg.name_text + ".tex"
        try:
            f = open(loutname, "w")
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
            return
        self.Table(f)
