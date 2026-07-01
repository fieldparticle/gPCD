import numpy as np
import os
import csv
import math
import sys


def get_run_configuration(config):
    """Return the active run configuration from flat or legacy cfg layouts."""
    if config is None:
        return {}
    if "RUN_CONFIGURATION" in config:
        return config.get("RUN_CONFIGURATION", {})
    return config


def get_cell_dimensions(config):
    """Return validated explicit cell counts for each axis."""
    run_cfg = get_run_configuration(config)
    dimension_keys = (
        "cell_array_width",
        "cell_array_height",
        "cell_array_depth",
    )
    present = [key in run_cfg for key in dimension_keys]
    if any(present) and not all(present):
        missing = [key for key, exists in zip(dimension_keys, present) if not exists]
        raise ValueError(
            "Cell-array dimensions must be provided together; missing "
            + ", ".join(missing)
        )

    if not all(present):
        raise ValueError(
            "Configuration requires cell_array_width, cell_array_height, "
            "and cell_array_depth"
        )
    values = [run_cfg[key] for key in dimension_keys]

    dimensions = []
    for key, raw_value in zip(dimension_keys, values):
        value = float(raw_value)
        if value <= 0.0 or not value.is_integer():
            raise ValueError(f"{key} must be a positive whole number")
        dimensions.append(int(value))
    return tuple(dimensions)


def hsv_angle(angle, value=1.0, sat=0.707):
    hue = (angle / (2.0 * math.pi)) % 1.0
    sat = max(0.0, min(1.0, sat))
    value = max(0.0, min(1.0, value))

    sector = hue * 6.0
    chroma = value * sat
    x = chroma * (1.0 - abs((sector % 2.0) - 1.0))
    match = value - chroma

    if sector < 1.0:
        red, green, blue = chroma, x, 0.0
    elif sector < 2.0:
        red, green, blue = x, chroma, 0.0
    elif sector < 3.0:
        red, green, blue = 0.0, chroma, x
    elif sector < 4.0:
        red, green, blue = 0.0, x, chroma
    elif sector < 5.0:
        red, green, blue = x, 0.0, chroma
    else:
        red, green, blue = chroma, 0.0, x

    return (
        int(round((red + match) * 255.0)),
        int(round((green + match) * 255.0)),
        int(round((blue + match) * 255.0)),
    )


class ParticleUtilities():

    col_count = 0
    def __init__(self, width, col_ary_size, height=None, depth=None):
        self.width = int(width)
        self.height = self.width if height is None else int(height)
        self.depth = self.width if depth is None else int(depth)
        if self.width <= 0 or self.height <= 0 or self.depth <= 0:
            raise ValueError("Cell-array dimensions must be positive")
        self.side_len = self.width
        self.max_location = self.width * self.height * self.depth
        self.col_ary_size = col_ary_size
        self.cell_array = np.zeros(
            (self.max_location, col_ary_size), dtype=np.uint32
        )
        self.lock_array = np.zeros(self.max_location, dtype=np.uint32)
        self.sizeof_int = 32
        
    def get_cell_array_len(self):
        return self.cell_array.size
    
    def get_lock_array_len(self):
        return len(self.lock_array)
    
    def get_cell_array_len_bytes(self):
        return self.cell_array.size*4
    
    def get_lock_array_len_bytes(self):
        return len(self.lock_array)*4
    
    def IndexToArray(self,index):
        index = int(index)
        if index < 0 or index >= self.max_location:
            return None
        plane = self.width * self.height
        z = index // plane
        remainder = index % plane
        y = remainder // self.width
        x = remainder % self.width
        return [x, y, z]
    

    def gen_cell_ary(self,plist,file_name):

        cell_len = self.get_cell_array_len()
        cell_bytes = self.get_cell_array_len_bytes()
        lock_len = self.get_lock_array_len()
        lock_bytes  = self.get_lock_array_len_bytes()
        print(f"Cell Array L:{cell_len},Bytes:{cell_bytes} type_bytes:{self.sizeof_int}")
        print(f"Lock Array L:{lock_len},Bytes:{lock_bytes} num_bytes:")

        if(len(plist)>1E4):
            return
        # for all particles
        for pp in plist:
            if int(pp.pnum) == 0:
                continue
            self.fill_particle_corner_array(pp)
            z = pp.zlink
            if int(pp.pnum) < 128:
                print(f"P:{pp.pnum} [{z[0]} {z[1]} {z[2]} {z[3]} {z[4]} {z[5]} {z[6]} {z[7]}]")
            if(self.add_particle_to_cell_array(pp) == 1):
                return

        file_prefix = os.path.splitext(file_name)[0]
        try :
            with open(file_name,'w',newline='') as csv_file:
                outfl = csv.writer(csv_file)
                outfl.writerows(self.cell_array)
        except BaseException as e:
            print(e)
        

    def detect_collsions(self,plist,outfile):
        self.col_count = 0
        ary = [int(round(plist[1].rx)),int(round(plist[1].ry)),int(round(plist[1].rz))]
        old_cnr_idx = self.ArrayToIndex(ary)
        cell_parts = plist
        count = 1
        '''
        cell_parts.append(plist[1])
        for Findex in range(2,len(plist)):
            ary = [int(round(plist[Findex].rx)),int(round(plist[Findex].ry)),int(round(plist[Findex].rz))]
            cnr_idx = self.ArrayToIndex(ary)
            if old_cnr_idx == cnr_idx:
                count+=1
                cell_parts.append(plist[Findex])
                #print(f"{Findex}")
            else:
                break
        '''
        duplist = [0]*self.max_location
        
        for ii in cell_parts:
            for jj in cell_parts:
                if ii.pnum == jj.pnum:
                    continue
                ret = self.particle_contact(ii,jj,duplist)    
       
        return [count,self.col_count]

    def detect_collions_all(self,plist):
        Tindex = 0
        break_point = 0
        col_count = 0
        # Runt thru the particle list for the FROM particle numbers
        for Findex in range(1,len(plist)):
            duplist = [0]*self.max_location
            try:
                # Get the FROM particle object from particle number
                F = plist[Findex]
                # Iterate of the corner locations
                for ii in range(0,8):       
                    # For the corner location at loc
                    loc = int(F.zlink[ii])
                    # if the corner locatin does not euqal null
                    if loc != 0:
                        # for all occupants at loc in cell array    
                        for jj in range(0,self.col_ary_size):
                            # Get the number of the TO particle
                            Tindex = int(self.cell_array[loc][jj])
                            # If its this particle don't cmapre
                            if(Findex != Tindex):
                                # if the slot is not equal to zero  (which mean no more particvles in this cell
                                if (Tindex) != 0:
                                    # Get the object for the TO particle
                                    T = plist[Tindex]
                                    # Check the two objects for contact
                                    ret = self.particle_contact(F,T,duplist)    


                    #print(f"P:{F.pnum},{loc}")
            except BaseException as e:
                print(f"At detect collsions:",e)
                return 
        print(f"Total collisons {self.col_count}")

    def norm(self,p1,p2):
        dsq = ( (p1[0]-p2[0])*(p1[0]-p2[0]) ) + ( (p1[1]-p2[1])*(p1[1]-p2[1]) ) + ( (p1[2]-p2[2])*(p1[2]-p2[2]) )
        dist = math.sqrt(dsq)
        return dist

    def particle_contact(self,F,T,duplist):
        break_point = 0
        #print(f"Comparing:{int(F.pnum)} -> {int(T.pnum)}")
        
        # Get the center of the FROM particle
        Fvec = np.array([F.rx,F.ry,F.rz])
        # Get the center of the TO particle
        Tvec = np.array([T.rx,T.ry,T.rz])
        # Get the length norm which is distance betwen the points
        dist = np.linalg.norm(Fvec - Tvec)
        # A check
        #dist2 = self.norm(Fvec,Tvec)
        # Set the dup flag False
        flg_dup = False
        if int(F.pnum) == 63:
            break_point = 0
        # Test the distance between particles aganst the sum of their radii.
        # If dist is less the process the collsion
        if dist < (T.radius + F.radius):
            # for this slot in the duplist. 
            for dd in duplist:
                # If we start/get to a null slot before we find the TO particle
                # there is no duplicate so set the dup flag False and break
                if dd == 0:
                    flg_dup = False
                    duplist[dd] = int(T.pnum)
                    break

                # If we find the TO particle in the duplicates list
                # the set the duplicates flag true and return - do not test/count the collsions
                if int(T.pnum) == dd:
                    flg_dup = True
                    return 0
            # Increase colsions 
            self.col_count+=1
            #print(f"P:{F.pnum} and {T.pnum} collison {self.col_count}")
            return 1
   

    def add_particle_to_cell_array(self,p):
        cell_array_location = 0
        slot = 0
        # For all of the corner locations in the particle's corner array
        for ii in range(len(p.zlink)):
            # Get the location in the cell array to put this corner
            cell_array_location = int(p.zlink[ii])

            # If the particle corner location is 0 there are no more corners
            # so return
            if cell_array_location == 0:
                return 0
            
            # If the cell_array_location is not 0 then test for bounds
            # The cell locatin cannot be greater than the size of the cell array
            
            if cell_array_location < 0 or cell_array_location >= self.max_location:
                print(f"particle corner at {cell_array_location} exceeds cell columns at {self.col_ary_size}")
                print(f"P:{int(p.pnum)} at ({cell_array_location})<{round(p.rx)},{round(p.ry)},{round(p.rz)}>")
                print(f"[",end=' ')
                for jj in range(len(p.zlink)):
                    print(f"{p.zlink[jj]}",end=' ')
                print("]")
                return 1

            # Get a slot in the cell array occupancy list from the lock array
            slot = self.lock_array[cell_array_location]  
            # Increment the value at the location in the lock array
            self.lock_array[cell_array_location] = (self.lock_array[cell_array_location] + 1)

            # If the slot exceeds the width of the particle corner array throw an error    
            if slot >= self.col_ary_size:
                print(f"slot at {slot} exceeds maxlocation at {self.col_ary_size}")
                return 0
            try :
                # If it is a valed slot number then place this corner into the cell arrray
                # at the locationa of the corner and at the assigned slot 
                self.cell_array[cell_array_location][slot] = int(p.pnum)
            except BaseException as e:
                print(f"Slot:{slot} is out of range for {self.col_ary_size}")
                return 0



    def ArrayToIndex(self,loc,p=None):
        try:
            x, y, z = (int(loc[0]), int(loc[1]), int(loc[2]))
        except (TypeError, ValueError, IndexError):
            return -1
        if (
            x < 0 or x >= self.width
            or y < 0 or y >= self.height
            or z < 0 or z >= self.depth
        ):
            return -1
        return x + self.width * (y + self.height * z)
    

    def fill_particle_corner_array(self,p):
        cx 		= p.rx
        cy 		= p.ry
        cz 		= p.rz
        R 		= p.radius
        npos = -1
        dupcntr = 0
        
        # Clean particle corner array
        for ii in range(8):
            p.zlink[ii] = 0

        ary = [int(round(cx+R)),int(round(cy+R)),int(round(cz-R))]
        cnr_idx = self.ArrayToIndex(ary,p)
        p.zlink[dupcntr] = cnr_idx

        ary = [int(round(cx+R)),int(round(cy+R)),int(round(cz+R))]
        cnr_idx = self.ArrayToIndex(ary,p)
        if (cnr_idx != p.zlink[0]):
            dupcntr+=1
            p.zlink[dupcntr] = cnr_idx
            
        ary = [int(round(cx-R)),int(round(cy+R)),int(round(cz+R))]
        cnr_idx = self.ArrayToIndex(ary,p)
        if (p.zlink[0] != cnr_idx and 
            p.zlink[1] != cnr_idx):
            dupcntr+=1
            p.zlink[dupcntr] = cnr_idx
        
        ary = [int(round(cx-R)),int(round(cy+R)),int(round(cz-R))]
        cnr_idx = self.ArrayToIndex(ary,p)
        if (p.zlink[0] != cnr_idx and 
            p.zlink[1] != cnr_idx and
            p.zlink[2] != cnr_idx):
            dupcntr+=1
            p.zlink[dupcntr] = cnr_idx
            
        ary = [int(round(cx+R)),int(round(cy-R)),int(round(cz+R))]
        cnr_idx = self.ArrayToIndex(ary,p)
        if (p.zlink[0] != cnr_idx and
            p.zlink[1] != cnr_idx and
            p.zlink[2] != cnr_idx and
            p.zlink[3] != cnr_idx):
            dupcntr+=1
            p.zlink[dupcntr] = cnr_idx
        
        
        ary = [int(round(cx+R)),int(round(cy-R)),int(round(cz-R))]
        cnr_idx = self.ArrayToIndex(ary,p)
        if (p.zlink[0] != cnr_idx and 
            p.zlink[1] != cnr_idx and
            p.zlink[2] != cnr_idx and
            p.zlink[3] != cnr_idx and
            p.zlink[4] != cnr_idx):
            dupcntr+=1
            p.zlink[dupcntr] = cnr_idx
        
        
        
        ary = [int(round(cx-R)),int(round(cy-R)),int(round(cz+R))]
        cnr_idx = self.ArrayToIndex(ary,p)
        if (p.zlink[0] != cnr_idx and
            p.zlink[1] != cnr_idx and
            p.zlink[2] != cnr_idx and
            p.zlink[3] != cnr_idx and
            p.zlink[4] != cnr_idx and
            p.zlink[5] != cnr_idx):
            dupcntr+=1
            p.zlink[dupcntr] = cnr_idx
        
        ary = [int(round(cx-R)),int(round(cy-R)),int(round(cz-R))]
        cnr_idx = self.ArrayToIndex(ary,p)
        if (p.zlink[0] != cnr_idx and
            p.zlink[1] != cnr_idx and
            p.zlink[2] != cnr_idx and
            p.zlink[3] != cnr_idx and
            p.zlink[4] != cnr_idx and
            p.zlink[5] != cnr_idx and 
            p.zlink[6] != cnr_idx):
            dupcntr+=1
            p.zlink[dupcntr] = cnr_idx
        
        
        
