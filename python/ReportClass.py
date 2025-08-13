import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.ticker import (MultipleLocator,
                               FormatStrFormatter,
                               AutoMinorLocator,
                               FuncFormatter,
                               EngFormatter)

class ReportClass():
    
    fields_list = None
    itemcfg = None
    tex_output_name = None
    
    def __init__(self, fields_list,itemcfg):
        self.fields_list = fields_list
        self.itemcfg = itemcfg
    
      