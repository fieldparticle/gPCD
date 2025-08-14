from gPCDData import *
from AttrDictFields import *

class DataContainer():

    raw_fields_list = []
    fields_list = []
    #******************************************************************
    # init
    #
    def __init__(self, Base, itemcfg):
        self.bobj = Base
        self.cfg = self.bobj.cfg
        self.log = self.bobj.log
        self.data_base = None
        self.itemcfg = itemcfg
    
    
    #******************************************************************
    # Save the DataFields<data_num> configuraton item in a list
    #
    def clear(self):
        self.fields_list = []

    #******************************************************************
    # Save the DataFields<data_num> configuraton item in a list
    #
    def get_particle_data_fields(self):
        more_fields = True
        plot_num = 1
        self.raw_fields_list.clear()
        while more_fields == True:
            cfg_DataFields = f"DataFields{plot_num}"
            if cfg_DataFields in self.itemcfg:
                data_fields = self.itemcfg[cfg_DataFields]
                for jj in data_fields:
                    self.raw_fields_list.append([jj,plot_num])
            else:
                break
            plot_num += 1    
        self.parse_fields_list()
        self.resolve_data_files()
        return 
    
    #******************************************************************
    # parse the fields from the list and add to a dictionary 
    #
    def parse_fields_list(self):
        count = 0
        for data_lines in self.raw_fields_list:
            #print(data_lines)
            sep_semi_colon = data_lines[0].split(':')
            comma_split = sep_semi_colon[1].split(',')
            sep_period = sep_semi_colon[0].split('.')
            fields_dict = AttrDictFields()
            fields_dict["field"] = comma_split[0]
            fields_dict["data_base"] = sep_period[1]
            fields_dict["line_type"] = comma_split[1]
            fields_dict["plot_num"] = data_lines[1]
            fields_dict["test_type"] = self.itemcfg.mode
            self.fields_list.append(fields_dict)

        return
    
    #******************************************************************
    # Get the field list
    #
    def get_feilds_list(self):
        return self.fields_list

    def do_report(self):
        field_dict= self.fields_list[0]
        data_obj = field_dict.data_object
        return data_obj.do_report(self.fields_list)
    
    #******************************************************************
    # Call the first data base and verify
    #
    def do_verify(self):
        field_dict= self.fields_list[0]
        data_obj = field_dict.data_object
        return data_obj.do_verify(field_dict)

    
    #******************************************************************
    # Call the first data base and verify
    #
    def build_fields_list(self):
        for ii in self.fields_list:
            data_obj = ii.data_object
            data_obj.check_data_files(ii)
            data_obj.do_performance(ii)
            data_obj.read_summary_file(ii)
        
        return self.fields_list
        

    #******************************************************************
    # Call the first data base and verify
    #
    def do_performance(self):
        for ii in self.fields_list:
            data_obj = ii.data_object
            data_obj.check_data_files(ii)
            data_obj.do_performance(ii)
            data_obj.read_summary_file(ii)

    #******************************************************************
    # load the data into the fields
    #
    def resolve_data_files(self):
        matches = ["pqb","pcd","cfb","dup","pqbrandom"]    
        for ii in self.fields_list:
            test_fld = ii["data_base"].upper()
            ii["source_dir"] = self.itemcfg.input_data_dir
            self.out_folder = os.path.dirname(self.itemcfg.input_data_dir)
            target = self.out_folder + '/' + "perfData" + ii.data_base
            ii["target_dir"] = target
            ii["data_object"] = gPCDData(self,self.itemcfg)
            ii["mode"] = self.itemcfg.mode
            ii["compute_type"] = self.itemcfg.compute_type
        return 


        
