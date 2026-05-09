    
import struct

from pdata import pdata

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