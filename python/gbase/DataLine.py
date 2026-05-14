from gbase.gPCDData import *
from gbase.AttrDictFields import *

class DataLine(AttrDictFields):

    def __init__(self):
        super().__init__()
        self.data = AttrDictFields()
        self.clear()
        self.data_lines = []
        self.data.clear()
        pass
     

