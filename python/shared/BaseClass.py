from shared.LogClass import LogClass
from shared.ConfigClass import ConfigClass
import inspect


class BaseObj:

    widget = None
    """
    This class is the global class for all other classes

    Attributes:
        log (FPIBGLog): FPIBGLog for loogin information and errors
    """
    
    def __init__ (self,ObjName):
        """
        Initializes the object with the application name.

        Args:
            Moniker (string): THe Name of the object.

        
        """
        print(f"Created " + ObjName)
        self.ObjName = ObjName
        
    def Create(self,CfgFileName,LogName):
        """
        Creates the base object and member objects log and config

        Args:
            self : this.
       
        """

        
        
        self.log = LogClass("GlobalLoggingObject")   
        self.log.Create(LogName)
        self.log.Open()
        self.cfg = ConfigClass("GlobalConfigObject")
        self.cfg.Create(self.log,CfgFileName)
        self.cfgname = CfgFileName

    def WriteConfig(self, dict):
        self.cfg.WriteConfig(dict)
        return
       
        
    def connect_to_output(self,widget):
        try:
            self.log.set_out_widget(widget)    
            self.log.log(self,"Linked ot output")
        except BaseException as e:
            self.log.log(self,e)
# @abstrctmethod
    def testObject(self,modNumber,dbglvl):
        if modNumber == 1 and dbglvl == 5:
            print(f"Running Mod" , modNumber , " Test")
            self.log.log(   inspect.currentframe().f_lineno,
                            __file__,
                            inspect.currentframe().f_code.co_name,
                            self.ObjName,
                            0,
                            "Test 1 Success")
            self.cfg.testObject(modNumber,dbglvl)
            return 0
        elif modNumber == 2 and dbglvl == 5:
            print(f"Running Mod" , modNumber , " Test")
            self.log.log(   inspect.currentframe().f_lineno,
                            __file__,
                            inspect.currentframe().f_code.co_name,
                            self.ObjName,
                            0,
                            "Test 2 Success")
            return 0
        
    
        self.log.log(   inspect.currentframe().f_lineno,
                            __file__,
                            inspect.currentframe().f_code.co_name,
                            self.Moniker,
                            1,
                            "Invalid test number")

    def Open(self):
        self.log.Open()
    def Close(self):
        self.log.Close()

    