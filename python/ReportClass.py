import matplotlib.pyplot as plt
import matplotlib.ticker
import os
from matplotlib.ticker import (MultipleLocator,
                               FormatStrFormatter,
                               AutoMinorLocator,
                               FuncFormatter,
                               EngFormatter)

class ReportClass():
    
    fields_list = None
    itemcfg = None
    itemcfg_main = None
    tex_output_name = None
    cap_file = ""
    caption = ""
    
    def __init__(self, parent,fields_list,itemcfg):
        self.fields_list = fields_list
        self.itemcfg = itemcfg
        self.itemcfg_main = itemcfg
        self.bobj = parent
        self.log = self.bobj.log

    def do_report(self):
        pass

    def save_single_image(self):
        
        self.read_caption()
        self.tex_output_name = self.itemcfg.tex_dir + "/" + self.itemcfg.name + ".tex"
        try:
            f = open(self.tex_output_name , "w")
        except IOError as e:
            print(e)
            self.log.log(self,f"Couldn't write to file ({e})")
            raise IOError(f"Couldn't write to file ({e})")
        tex_output_name = self.tex_output_name 
        try:
            
            w ="\\begingroup\n"
            f.write(w)
            w = "\\centering\n"
            f.write(w)
            w = "\\begin{figure*}[" + self.itemcfg.placement + "]\n"
            f.write(w)
            previewTex = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}{ii}.png"
            gdir = "".join(previewTex.rsplit(self.itemcfg.tex_dir))
            sgdir = ''.join( c for c in gdir if  c not in '/' )
    #                print(sgdir)    
            w = "\t\t\\includegraphics[width=" +  str(self.itemcfg.plot_width) +  "in]{" + sgdir + "}\n"
            f.write(w)
            refname = os.path.splitext(os.path.basename(gdir))[0]
            w = "\t\t\\label{fig:" + refname + "}\n"
            f.write(w)
            w = "\\hspace{" + str(self.itemcfg.hspace) + "in}\n"
            f.write(w)
            w = "\\caption[TITLE:" + self.itemcfg.title + "]{\\textit{" + self.caption + "}}\n"
            f.write(w)
            w = "\t\t\\label{fig:" + self.itemcfg.name + "}\n"
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

    def save_multi_image(self):
        self.read_caption()
        cfg = self.itemcfg
        self.tex_output_name = self.itemcfg.tex_dir + "/" + self.itemcfg.name + ".tex"
        try:
            f = open(self.tex_output_name , "w")
        except IOError as e:
            print(e)
            self.log.log(self,f"Couldn't write to file ({e})")
            raise IOError(f"Couldn't write to file ({e})")
        tex_output_name = self.tex_output_name 
        w ="\\begingroup\n"
        f.write(w)
        
        w = "\\begin{figure*}[" + cfg.placement + "]\n"
        f.write(w)
        if cfg.centering == True:
            w = "\\centering\n"
            f.write(w)
        try:
            for ii in range(0,len(self.itemcfg.input_images)):
                #w = "\t\\begin{subfigure}[b]{" + cfg.plot_width_array[ii] + "in}\n"
                w = "\t\\begin{subfigure}[b]{" + str(cfg.plot_scale[ii]) + "\\textwidth}\n"
                f.write(w)
                previewTex = f"{cfg.plots_dir}/{cfg.input_images[ii]}"
                gdir = "".join(previewTex.rsplit(cfg.tex_dir))
                sgdir = ''.join( c for c in gdir if  c not in '/' )
                print(sgdir)    
                w = "\t\t\\includegraphics[width=\\textwidth]{" + sgdir + "}\n"
                f.write(w)
                w = "\t\t\\subcaption[" + "" +"]{" + cfg.sub_caption[ii] + "}\n"
                f.write(w)
                refname = os.path.splitext(os.path.basename(sgdir))[0]
                w = "\t\t\\label{fig:" + refname + "}\n"
                f.write(w)
                w = "\t\\end{subfigure}\n"
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
        except IOError as e:
            self.log.log(self,f"Couldn't write to file ({e})")
            f.close()
            return
        f.close()



    def save_latex(self):
        images = self.itemcfg.input_images
        if len(self.itemcfg.input_images) == 1:
            self.save_single_image()
        else:
            self.save_multi_image()
            print("multiimage")
        return
        


    def read_caption(self):
        self.cap_file = self.itemcfg.caption_file
        if os.path.exists(self.cap_file):
            with open(self.cap_file, 'r') as file:
                self.caption = file.read()
        else:
            file = open(self.cap_file, 'w') 
            file.close()
        pass

    def write_captions(self):
      pass