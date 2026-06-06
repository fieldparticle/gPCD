    
import struct
import glob
import os
from gbase.msg_box import verify_dialog
from gbase.pdata import pdata
##############################################################################    
#******************************************************************
# Clear the files in the data directory
#
def clear_files(itemcfg,FileName=None):
    

    res = verify_dialog(None, "Delete Verification", 
                        "Are you sure you want to delete all of the files in the data directory?", 
                        "Yes", "No")

    if res == False:
        return
    if FileName == None:
        if itemcfg.test_files_only == False and itemcfg.replace_all == True:
            clr_path = itemcfg.data_dir + "/*.csv"
            files = glob.glob(clr_path)
            for f in files:
                os.remove(f)

            clr_path = itemcfg.data_dir + "/*.bin"
            files = glob.glob(clr_path)
            for f in files:
                os.remove(f)
            
            clr_path = itemcfg.data_dir + "/*.tst"
            files = glob.glob(clr_path)
            for f in files:
                os.remove(f)
    else:
    
        clr_path = itemcfg.data_dir + "/" + FileName + ".bin"
        if os.path.exists(clr_path):
            os.remove(clr_path)

        clr_path = itemcfg.data_dir + "/" + FileName + ".tst"
        if os.path.exists(clr_path):
            os.remove(clr_path)
    return
#******************************************************************
# Reead all of the particle data
# 
#
def count_all_particle_data(file_name):
    struct_fmt = 'dddddddddddddd'
    struct_len = struct.calcsize(struct_fmt)
    #print(struct_len)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    count = 0
    results = []
    with open(file_name, "rb") as f:
        while True:
            record = pdata()
            ret = f.readinto(record)
            count += 1
            if ret == 0:
                break
            
    p_lst = []
    return count
#******************************************************************
# Reead all of the particle data
# 
#
def read_all_particle_data(file_name):
    struct_fmt = 'dddddddddddddd'
    struct_len = struct.calcsize(struct_fmt)
    #print(struct_len)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    count = 0
    results = []
    with open(file_name, "rb") as f:
        while True:
            record = pdata()
            ret = f.readinto(record)
            if ret == 0:
                break
            results.append(record)
    p_lst = []
    return results
 #******************************************************************
# Read particle data in range
#
#
def read_particle_data(file_name,particle_range):
    struct_fmt = 'dddddddddddddd'
    struct_len = struct.calcsize(struct_fmt)
    #print(struct_len)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    count = 0
    results = []
    counter = 0
    slist = particle_range
    start_it = int(slist[0])
    end_it = int(slist[1])
    with open(file_name, "rb") as f:
        
        while True:
            if counter >= start_it: 
                record = pdata()
                ret = f.readinto(record)
                if ret == 0:
                    break
                #print(record.pnum)
                results.append(record)
                if counter > end_it:
                    break
            counter += 1
            
    p_lst = []
    return results