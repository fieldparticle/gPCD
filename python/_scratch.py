import numpy as np
import matplotlib.pyplot as plt
import csv
import math

def extract_fields(self.string):
    string = "np.log((fld.gms+fld.cms)/fld.loadedp)"
    str_len = len(string)
    nn = 0
    bld_fld = []
    while (nn > -1):
        nn = string.find('fld.',nn+1)
        bld_fld.clear()
        stop_len = str_len
        start_len = nn
        for ii in range(start_len,stop_len):
            if string[ii] not in "()/+-*":
                #print(string[ii])
                bld_fld.append(string[ii])
            else:
                break
        new_str = "".join(bld_fld)
        #print(new_str)                
            

        #print(nn)
