import os

class CheckCfg():

    def __init__(self,cfg):
        self.cfg = cfg
        
        
        
        

    def check_rpt_files(self):
        if 'type' not in self.cfg:
            return "Config file missing 'type'"
        if 'batch' in self.cfg.type:
            return 'ok'
        else:
            my_list = ["plot", "csvtable", "image", "csvplot", "gpcd_table"]
            if self.cfg.type not in my_list:
                return "Invalid type. Valid types are plot or table, or image or csvplot'"
        if self.cfg.type == 'plot':
            if 'name' not in self.cfg:
                return "Config file missing 'name'"
            if 'plots_dir' not in self.cfg:
                return "Config file missing 'plots_dir'"
            else:
                if not os.path.isdir(self.cfg.plots_dir):
                    return f"Invalid direcoty plots_dir = {self.cfg.plot_dir}"
            if 'tex_dir' not in self.cfg:
                return "Config file missing 'tex_dir'"
            else:
                if not os.path.isdir(self.cfg.tex_dir):
                    return f"Invalid direcoty tex_dir = {self.cfg.tex_dir}"
                
            if 'tex_image_dir' not in self.cfg:
                    return "Config file missing 'tex_image_dir'"

            if 'input_data_dir' not in self.cfg:
                    return "Config file missing 'input_data_dir'"
            else:
                if not os.path.isdir(self.cfg.input_data_dir):
                    return f"Invalid direcoty input_data_dir = {self.cfg.input_data_dir}"
            #caption_file
            #mode
            #compute_type
            #hspace
            #font_size
            #floating
            #placement
            #title
            #plot_width
            #include
            #data_fields
            dfl_list = ["true", "false"]
            if 'data_fields' not in self.cfg:
                return "Config file missing 'data_fields'"
            elif len(self.cfg.data_fields) < 2:
                return f"Not enough fields in data_fields. Length is {len(self.cfg.data_fields)}."
            if 'plot_switch' not in self.cfg:
                    return "Config file missing 'plot_switch'"
            else:
                for ii in self.cfg.plot_switch:
                    if ii not in dfl_list:
                        return f"plot_switch  {ii} is not true or false." 

        
        if 'centering' not in self.cfg:
            return "Config file missing 'centering'"

        return 'ok'            
        #return "fail ok"






    def check_gen_files(self):

        if 'type' not in self.cfg:
            self.log.log(self,"Config file missing 'type'")
            return 1
        if 'selections_file' not in self.cfg:
            self.log.log(self,"Config file missing 'selections_file'")
            return 1
        if 'generate_class' not in self.cfg:
            self.log.log(self,"Config file missing 'generate_class'")
            return 1
        
        if 'particle_separation' not in self.cfg:
            self.log.log(self,"Config file missing 'particle_separation'")
            return 1
        if 'write_block_len' not in self.cfg:
            self.log.log(self,"Config file missing 'write_block_len'")
            return 1
        if 'particle_enumeration' not in self.cfg:
            self.log.log(self,"Config file missing 'particle_enumeration'")
            return 1
        if 'test_files_only' not in self.cfg:
            self.log.log(self,"Config file missing 'test_files_only'")
            return 1
        if 'replace_all' not in self.cfg:
            self.log.log(self,"Config file missing 'replace_all'")
            return 1
        if 'cell_array_size' not in self.cfg:
            self.log.log(self,"Config file missing 'cell_array_size'")
            return 1
        if 'cell_range' not in self.cfg:
            self.log.log(self,"Config file missing 'cell_range'")
            return 1
        if 'sphere_facets' not in self.cfg:
            self.log.log(self,"Config file missing 'sphere_facets'")
            return 1
        if 'particle_range' not in self.cfg:
            self.log.log(self,"Config file missing 'particle_range'")
            return 1
        if 'particle_color' not in self.cfg:
            self.log.log(self,"Config file missing 'particle_color'")
            return 1
        if 'test_indexing_log' not in self.cfg:
            self.log.log(self,"Config file missing 'test_indexing_log'")
            return 1
        return 0