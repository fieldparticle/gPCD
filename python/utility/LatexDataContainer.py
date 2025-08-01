
from LatexDataCSV import *
from LatexDataParticle import *
class LatexDataContainer():


    def __init__(self, FPIBGBase, itemcfg, ObjName, *args, **kwargs):
        self.ObjName = ObjName
        self.bobj = FPIBGBase
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.log.log(self,"LatexDataContainer finished init.")
        self.data_base = None
        self.itemcfg = itemcfg

    def Create(self,plot_num,data_type):

        matches = ["pqb","pcd","cfb","dup","pqbrandom"]
        #print(type(data_type))
        if isinstance(data_type,list):
            test = data_type[0].lower()
        elif isinstance(data_type,str):
            test = data_type.lower()
        else:
            print("LatexDataContainer.Create() bad data type")
        if "csv" in test:
            self.data_base = LatexDataCSV(self.bobj,self.itemcfg,"CSV Data")
            self.data_base.Create(0) 
        elif any(x in test for x in matches):
            self.data_base = LatexDataParticle(self.bobj,self.itemcfg,"Particle Data")
            self.data_base.Create(plot_num) 
        else:
            print("Invaid data type at line 26 in Create in LatexDataContainer()")  

    def getData(self):
        return self.data_base.getData()

        
