
class LatexDataBaseClass():

    hasData = False
    data = None
    def __init__(self, FPIBGBase,itemcfg, ObjName):
        self.ObjName = ObjName
        self.bobj = FPIBGBase
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.data_base = None
        self.itemcfg = itemcfg


    def Create(self, data_type,data_dir,data_file=None):
        self.data_type = data_type
     
    
    def hasData(self):
        return self.hasData
    
    def getData(self):
        pass