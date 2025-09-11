from AttrDictFields import *
from ConfigUtility import *
import num2alpha as n2a
class ValuesDataBase():

    def __init__(self, Base):
        self.bobj = Base
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        
    

    def get_vals(self):
        self.vals_cfg_obj = ConfigUtility(self.cfg.values_data_base)
        self.vals_cfg_obj.Create(self.bobj.log,self.cfg.values_data_base)
        self.vals_cfg = self.vals_cfg_obj.config
        return self.vals_cfg

    def write_values(self,vals_list):
        self.vals_cfg_obj = ConfigUtility(self.cfg.values_data_base)
        self.vals_cfg_obj.Create(self.bobj.log,self.cfg.values_data_base)
        self.vals_cfg = self.vals_cfg_obj.config
        for k,v in self.vals_cfg.items():
            self.vals_cfg[k]=v
        for k,v in vals_list.items():
            self.vals_cfg[k]=v
        self.vals_cfg_obj.updateCfg()
        try:
            file_handle = open(self.cfg.export_latex_values, 'w')
        except BaseException as e:
            print("Values file does not exist:",e)
            return
        for k,v in self.vals_cfg.items():
            val_string = "\\newcommand{" + "\\" + k + "}{" + f"{v}" + "}\n"
            file_handle.write(val_string)
        file_handle.close()

        

    #******************************************************************
    # Write trendline data to the values file
    #       
    def write_latex_values(self):
        try:
            file_handle = open(self.itemcfg.values_file, 'w')
        except BaseException as e:
            print("Values file does not exist:",e)
            return
        if 'gpcd_table' not in self.itemcfg.type:
            for nm in self.lines_list:
                if 'CaptureVals' in nm:
                    name = self.itemcfg.name.replace('_','')
                    name = re.sub(r'\d+', '', name)
                    val_string = "\\newcommand{" + "\\" + name + "StartNum" + "}{" + f"{nm.start_val}" + "}\n"
                    file_handle.write(val_string)
                    start_val = int(nm.data[nm.data_lines[0].field][nm.start_val])
                    val_string = "\\newcommand{" + "\\" + name + "StartVal" + "}{" + f"{start_val}" + "}\n"
                    file_handle.write(val_string)
                    val_string = "\\newcommand{" + "\\" + name + "EndNum" + "}{" + f"{nm.end_val}" + "}\n"
                    file_handle.write(val_string)
                ltr = self.alph(nm.line_num)
            if nm.line_type == 'linear_trend':
                name = self.itemcfg.name.replace('_','')
                val_string = "\\newcommand{" + "\\" + name + "LinearTrendK" + f"{ltr}" + "}{" + f"{nm.K:.4E}" + "}\n"
                file_handle.write(val_string)
                val_string = "\\newcommand{" + "\\" + name + "LinearTrendIsec" + f"{ltr}" + "}{" + f"{nm.isec:.4E}" + "}\n"
                file_handle.write(val_string)
                #val_string = "\\newcommand{" + "\\" + name + "Covarance" + "}{" + f"${nm.covariance:.4E}$" + "}"
                val_string = "\\newcommand{" + "\\" + name + "LinearTrendRSquared" + f"{ltr}" + "}{" + f"{nm.r_squared:.4E}" + "}\n"
                file_handle.write(val_string)
            elif nm.line_type == 'quadratic_trend':
                name = self.itemcfg.name.replace('_','')
                val_string = "\\newcommand{" + "\\" + name + "QuadraticTrendK" + f"{ltr}" + "}{" + f"{nm.K:.4E}" + "}\n"
                file_handle.write(val_string)
                val_string = "\\newcommand{" + "\\" + name + "QuadraticTrendb"  + f"{ltr}" +"}{" + f"{nm.b:.4E}" + "}\n"
                file_handle.write(val_string)
                val_string = "\\newcommand{" + "\\" + name + "QuadraticTrendc" + f"{ltr}" +"}{" + f"{nm.c:.4E}" + "}\n"
                file_handle.write(val_string)
                #val_string = "\\newcommand{" + "\\" + name + "Covarance" + "}{" + f"${nm.covariance:.4E}$" + "}"
                val_string = "\\newcommand{" + "\\" + name + "QuadraticTrendRSquared" + f"{ltr}" + "}{" + f"{nm.r_squared:.4E}" + "}\n"
                file_handle.write(val_string)
        elif 'gpcd_table' in self.itemcfg.type:
            name = self.itemcfg.name.replace('_','')
            counter = 0
            for val in self.lines_list[0].export_vals:
                if val[1] == 0:
                    counter+=1
                val_string = "\\newcommand{" + "\\" + name + "row" + f"{self.alph(counter-1)}" + f"col{self.alph(val[1])}" + "}{" + f"{val[2]}" + "}\n"
                file_handle.write(val_string)
        file_handle.close()
        return

    def alph(self,num):
        return n2a.number_to_alpha(num)
        