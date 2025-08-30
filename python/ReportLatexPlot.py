
from ReportClass import *
import os
import inspect
from TrendLine import *
import re
from AttrDictFields import *
from ConfigUtility import *
class ReportLatexPlot(ReportClass):

    def __init__(self,parent,itemcfg):
        super().__init__(parent,itemcfg)

   

    def save_latex(self):
        if len(self.itemcfg.include) == 0:
            self.save_single_image()
        else:
            image_list = []
            for ii in self.itemcfg.include:
                self.itemcfg_obj = ConfigUtility(ii)
                self.itemcfg_obj.Create(self.bobj.log,ii)
                self.itemcfg_tmp = self.itemcfg_obj.config
                image_list.append(f"{self.itemcfg.plots_dir}/{self.itemcfg_tmp.name}.png")
            self.itemcfg['input_images'] = image_list
            self.save_multi_image()

      

        
    def replace_between_delimiters(self,text, start_delimiter, end_delimiter, replacement_string):
        """
        Replaces the substring between specified start and end delimiters with a new string.

        Args:
            text (str): The original string.
            start_delimiter (str): The starting delimiter.
            end_delimiter (str): The ending delimiter.
            replacement_string (str): The string to replace the content between delimiters.

        Returns:
            str: The modified string with the replaced content.
        """

        
        # Construct the regex pattern:
        # re.escape() handles special characters in delimiters
        # (.*?) matches any character non-greedily between delimiters
        pattern = re.escape(start_delimiter) + r"(.*?)" + re.escape(end_delimiter)


        # Use re.sub() to find and replace
        # The replacement string includes the delimiters themselves
        return re.sub(pattern, start_delimiter + replacement_string + end_delimiter, text)

