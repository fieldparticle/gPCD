from ReportClass import *
import os
import inspect
from TrendLine import *
import re
from AttrDictFields import *
from ConfigUtility import *
class ReportLatexTable(ReportClass):

    def __init__(self,parent,itemcfg,lines_list):
        super().__init__(parent,itemcfg)
        self.lines_list = lines_list
       
   

    def save_latex(self):
        self.tex_output_name = self.itemcfg.tex_dir + "/" + self.itemcfg.name + ".tex"
        self.Table = AttrDictFields()
        num_rows = 0
        for ii in range(len(self.lines_list)):
            print(self.lines_list[ii].data)
            print(self.lines_list[ii].data_lines[0]['field'])
            fld_str = self.lines_list[ii].data_lines[0]['field']
            l_itm = len(self.lines_list[ii].data[fld_str])
            if num_rows == 0:
                num_rows = l_itm
            elif l_itm != num_rows:
                print("number of rows do not match in save_latex()")
                return
            self.Table[fld_str]=self.lines_list[ii].data[fld_str]
            #self.table[self.lines_list[ii].field] = self.lines_list[ii].data_lines.field]            #self.cols = self.data.shape[0]
            #self.rows = self.data.shape[1]
            #self.table_array  = [[0 for x in range(self.cols)] for y in range(self.rows)] 
        self.rows = num_rows
        self.cols = len(self.Table)
        self.table_array = [[0 for x in range(self.rows)] for y in range(self.cols)] 
        self.setLatexData()
        self.Write()
      

        
    def replace_between_delimiters(self,text, start_delimiter, end_delimiter, replacement_string):
        """
        Replaces the substring between specified start and end delimiters with a new string.

        Args:
            text (str): The original string.
            start_delimiter (str): The starting delimiter.
            end_delimiter (str): The ending delimiter.
            replacement_string (str): The string to replace the content between delimiters.

        Returns:
            str: The modified string with the replaced content.
        """

        
        # Construct the regex pattern:
        # re.escape() handles special characters in delimiters
        # (.*?) matches any character non-greedily between delimiters
        pattern = re.escape(start_delimiter) + r"(.*?)" + re.escape(end_delimiter)


        # Use re.sub() to find and replace
        # The replacement string includes the delimiters themselves
        return re.sub(pattern, start_delimiter + replacement_string + end_delimiter, text)

    
        
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
        ii = 0
        for val in self.Table.values():
            if ii > len(self.itemcfg[f"format_array"]):
                print("Mismatch between colums of data and the format of that data.")
                return
            for jj in range(len(val)):
                fmt_txt = self.itemcfg[f"format_array"][ii]
                if 'd' in fmt_txt:
                    pval = int(val[jj])
                elif 'f' in fmt_txt:
                    pval = float(val[jj])
                elif 's' in fmt_txt:
                    pval = str(val[jj])
                    ret = self.setTableItemArray(pval,ii,jj)
                    return pval            
                out1 = f"{pval}"
                out_txt = "f\"%{fmt_txt}\"%(" + out1 + ")"
                #out_data = eval(out_txt)
                out_val = eval(out_txt)
                #out_val = eval(out_val)
                ret = self.setTableItemArray(out_val,ii,jj)
                return out_val
            
                '''
                if (ii == 2):
                    self.setTableItemArray(str("%.2f" % (1000*value)),i,j)
                    return "%.2f" % (1000*value)
                
                if (i == 3):
                    self.setTableItemArray(str("%.2f" % (1000*value)),i,j)
                    return "%.2f" % (1000*value)
                '''
                    
    def MultiTable(self,f):
        
        num_tables = 0    
        split_at = 0
        end_row = 0
        self.read_caption()
        if 'split_table_array' in self.itemcfg:
            num_tables = int(self.itemcfg.split_table_array[0])
            split_at = int(self.itemcfg.split_table_array[1])
            end_row = split_at-1
        else:
            num_tables = 1
            split_at = 0
        

        start_row = 0
        end_row = self.rows
        f.write("\\begin{table}[%s]\n" % self.itemcfg.placement)
        f.write("\\caption{\\textit{")
        f.write(self.caption)
        f.write("}}\n")
        f.write("\\label{tab:%s}\n"%self.itemcfg.name)
            
        for i in range(num_tables):
            if num_tables > 1:
                f.write("\\begin{minipage}{.5\\linewidth}\n")
                if i > 0:
                    start_row = split_at
                    end_row = self.rows
            f.write("\\fontsize{%s}{%s}\\selectfont\n" % (self.itemcfg.font_size,self.itemcfg.font_size))
            f.write("\\renewcommand{\\arraystretch}{%f}\n" % (self.itemcfg.array_stretch))
            
            f.write("\\begin{center}\n")
            f.write("\\begin{tabular}\n{")
            for k in range(self.cols):
                f.write("l ")
            f.write("}\n")
            f.write("\\hline \\\\ \n")
            header_key = f"header_array"
            lsz = len(self.itemcfg[header_key])
            headers = self.itemcfg[header_key]
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

            for rr in range(start_row,end_row): #,skip):
                for cc in range(self.cols):
                    #
                    if(cc < self.cols-1):
                        
                        #txt = self.format_cell(self.table_array[i][j],j,1) + "&"
                        txt = str(self.table_array[cc][rr]) + " & "
                        f.write(txt)
                    else:
                        txt = str(self.table_array[cc][rr]) + "\\\\ \n"
                        f.write(txt)
            f.write("\\hline\n\\end{tabular}\n\\end{center}\n")
            if num_tables > 1:
                f.write("\\end{minipage}\n")

        f.write("\\end{table}\n")
        f.close()
        #self.WritePre("pre_tables")
      
    def Write(self):
        try:
            f = open(self.tex_output_name, "w")
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
            return
        self.MultiTable(f)

        

    def SingleTable(self):
        cfg = self.itemcfg
        self.read_caption()
        outfile = cfg.tex_dir + "/" + cfg.name + ".tex"
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
            w = "\\begin{figure*}[" + cfg.placement + "]\n"
            f.write(w)
            previewTex = f"{cfg.plots_dir}"
            gdir = "".join(previewTex.rsplit(cfg.tex_dir))
            sgdir = ''.join( c for c in gdir if  c not in '/' )
    #                print(sgdir)    
            w = "\t\t\\includegraphics[width=" +  str(cfg.plot_width) +  "in]{" + sgdir + "}\n"
            f.write(w)
            refname = os.path.splitext(os.path.basename(gdir))[0]
            w = "\t\t\\label{fig:" + cfg.name + "}\n"
            f.write(w)
            w = "\\hspace{" + cfg.hspace + "in}\n"
            f.write(w)
            w = "\\caption[TITLE:" + cfg.title + "]{\\textit{" + self.caption + "}}\n"
            f.write(w)
            w = "\t\t\\label{fig:" + cfg.name + "}\n"
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
        return