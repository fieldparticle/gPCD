    
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
            print(f"pnum: {record.pnum}, ptype:{record.ptype},live frame:{record.state_flg},vx:{record.vx:.2f},vy:{record.vy:.2f} x: {record.rx:.2f}, y: {record.ry:.2f}, z: {record.rz:.2f}")
            count += 1
            if ret == 0:
                break
            
    p_lst = []
    print(f"Total particles in file {file_name}: {count}")
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

def test_ArrayToIndex(x,y,z,side_length,max_loc):
    # This is the count of cells which is 1 greater than side length
    w = side_length
    h = side_length
    indxLoc = 0
    rx = round(x)
    ry = round(y)
    rz = round(z)
    try :
        indxLoc =  rx + w * (ry + h * rz)
    except BaseException as e:
        print("At Array to index:{e}")
    if indxLoc >= max_loc:
        print(f"Index out of bounds: {indxLoc} >= {max_loc}")
        return -1
    return 0
'''
    uint w = WIDTH;
    uint h = HEIGHT;
    uint d = DEPTH;

    if (loc.x >= w || loc.y >= h || loc.z >= d) {
        return npos;
    }

    uint indxLoc = loc.x + w * (loc.y + h * loc.z);
    if (indxLoc >= MAX_CELL_ARRAY_LOCATIONS) {
        return npos;
    }
    return indxLoc;
    '''