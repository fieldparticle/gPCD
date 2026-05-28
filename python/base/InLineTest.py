class InLineTest:
    def __init__(self, *args, **kwargs):
        pass
    
    def Create(self,config_obj):
        self.item_cfg = config_obj
        # Open the item configuration file
        try:
            full_path = os.path.join(mod_path, mod_name)
            # Import the class named in generate_class
            self.gen_class = load_class_from_file(full_path)()
            #self.gen_class = self.load
        except BaseException as e:
            self.log.log(self,f"Unable to open item configurations file:{e}")
            self.hasConfig = False
            return 
    
    def StartRun(self, particles):
        return particles
