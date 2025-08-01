import configparser
import os
import libconf
import io
import inspect
import shutil
from collections import OrderedDict


class ConfigClass:
    lvl = 100
    def Create(self,LogObj,CfgFileName):
        self.log = LogObj
        self.log.log(self,"FPIBG into Create.");
        self.CfgFileName = CfgFileName
        self.configPath = self.CfgFileName
        try:
            with io.open(self.configPath) as f:
                self.log.log(self,"FPIBG into Open config file.")
                self.config = libconf.load(f)
        except BaseException as e:
            print(e)
            self.log.log(self,f"Config File Open error {e}")
            

        self.log.log(self,"Successfully Loaded Config File.")       
            
            
    def get_repo_root(self):
        """Gets the absolute path of the project root directory."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print("Cuurent Dirgetreporoot:", current_dir)
        while not os.path.exists(os.path.join(current_dir, ".git")):
            current_dir = os.path.dirname(current_dir)
            if current_dir == "/":
                raise FileNotFoundError("Could not find .git directory")
        return current_dir
     
    def __init__(self,ObjName):
        """
        Constructor for the FPIBGConfig object.
        Saves the path of the config as a variable.
        Saves the configuration information as a dictionary.
        """
        self.ObjName = ObjName
        

    def Open():
        pass
    def Close():
        pass    
    
    ObjArray = []

    def testObject(self,modName):
            print(f"Running Mod" , modName , " Test")
            self.log.log( 1, inspect.currentframe().f_lineno,
                            __file__,
                            inspect.currentframe().f_code.co_name,
                            self.ObjName,
                            0,
                            f"Running:" + modName)
            
            
            return 0
            

   
    def GetConfig(self):
        """
        Function to retreive the config object.
        This object contains all of the data from the configuration file as a dictionary.
        """
        return self.config
    

    def updateCfg(self):
        self.WriteConfig(self.config)

    def WriteConfig(self, dict):
        if not os.path.exists(self.CfgFileName):
            print(f"Error: Source file '{self.CfgFileName}' does not exist.")
            return None

        name, ext = os.path.splitext(self.CfgFileName)
        destination_filename = f"{name}_bak{ext}"
        """
        try:
            shutil.copy2(self.CfgFileName, destination_filename)
            print(f"Successfully created a copy: '{destination_filename}'")
        except Exception as e:
            print(f"Error creating copy: {e}")
            return None
        """
        destination_filename = f"{name}{ext}"
        #Make the Changes
        dest_path = os.path.join(self.get_repo_root(), destination_filename)
        with io.open(dest_path, 'r+', encoding='utf-8') as f:
            conf_copy = {} #libconf.load(f)

            for key, value in dict.items():
                conf_copy[key] = value

            # Clear the file and save the new contents
            f.seek(0)
            f.truncate()
            libconf.dump(conf_copy, f)

        return


    