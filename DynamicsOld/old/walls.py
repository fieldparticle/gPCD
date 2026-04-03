
class CollisionWall():

    
    def __init__(self,itemcfg):
        self.pnum = 0
        self.itemcfg = itemcfg
        self.wall_xmin = 0.0
        self.wall_xmax = 0.0
        self.wall_ymin = 0.0
        self.wall_ymax = 0.0


     ##############################################################################################
    # Check for wall collsions
    #
    #
    #
    ##############################################################################################
    def check_wall_collision(self,pary,ii):
        self.pary = pary
        # ---------------------East Wall ---------------------------------------------------------
        if self.pary[ii].rx > self.wall_xmax-self.pary[ii].radius:
            
            # If this is the start of a collsion 
            if self.pary[ii].wcol_flag[0]  == False:
                self.pary[ii].cvx = abs(self.pary[ii].vx)
                self.pary[ii].cvy = abs(self.pary[ii].vy)
                # Center point of particle
                P = (self.pary[ii].rx, self.pary[ii].ry)
                # unit vector pointing in the direction of the wall
                v = (1, 0)
                # A point in the wall
                A = (self.itemcfg.wall_dim[1], self.itemcfg.wall_dim[3])
                # Direction of wall
                d = (0, 1)
                t,s,ipoint = intersect_ray_line_2d(P, v, A, d)
                #print(f"t:{t},s:{s},ipoint:{ipoint}")
                faux_center = P+2*t*np.array(v)
                # Create a pseudo particle
                wp = particle()
                wp.make_copy(self.pary[ii])
                wp.rx = faux_center[0]
                wp.ry = faux_center[1]
                wp.vx = 0.0
                wp.vy = 0.0
                self.pary[ii].wall_list[0]= wp
                self.pary[ii].wcol_flag[0] = True
                return True
            # If already in collsion
            else:
                wall_col = collsion()
                self.process_collision(self.pary[ii],self.pary[ii].wall_list[0],wall_col)
                return True
        # If out of collision clear collsion flag
        elif self.pary[ii].wcol_flag[0]  == True:
            self.pary[ii].wcol_flag[0] = False
            return False
                
        # West Wall ###############################################
        if self.pary[ii].rx < self.wall_xmin+self.pary[ii].radius:
            if self.pary[ii].wcol_flag[1]  == False:
                self.pary[ii].cvx = abs(self.pary[ii].vx)
                self.pary[ii].cvy = abs(self.pary[ii].vy)
                # Center point of particle
                P = (self.pary[ii].rx, self.pary[ii].ry)
                # unit vector pointing in the direction of the wall
                v = (-1, 0)
                # A point in the wall
                A = (self.itemcfg.wall_dim[0], self.itemcfg.wall_dim[3])
                # Direction of wall
                d = (0, 1)
                t,s,ipoint = intersect_ray_line_2d(P, v, A, d)
                #print(f"t:{t},s:{s},ipoint:{ipoint}")
                faux_center = P+2*t*np.array(v)
                # Create a pseudo particle
                wp = particle()
                wp.make_copy(self.pary[ii])
                wp.rx = faux_center[0]
                wp.ry = faux_center[1]
                wp.vx = 0.0
                wp.vy = 0.0
                self.pary[ii].wall_list[1] = wp
                self.pary[ii].wcol_flag[1] = True
                return True
            else:
                wall_col = collsion()
                self.process_collision(self.pary[ii],self.pary[ii].wall_list[1],wall_col)
                return True
        elif self.pary[ii].wcol_flag[1]  == True:
            self.pary[ii].wcol_flag[1] = False
            return False
    
        # Top Wall ###############################################
        if self.pary[ii].ry > self.wall_ymax-self.pary[ii].radius:
            if self.pary[ii].wcol_flag[2]  == False:

                self.pary[ii].cvx = abs(self.pary[ii].vx)
                self.pary[ii].cvy = abs(self.pary[ii].vy)
                P = (self.pary[ii].rx, self.pary[ii].ry)
                v = (0, 1)
                A = (self.itemcfg.wall_dim[1], self.itemcfg.wall_dim[3])
                d = (1, 0)
                t,s,ipoint = intersect_ray_line_2d(P, v, A, d)
                #print(f"t:{t},s:{s},ipoint:{ipoint}")
                faux_center = P+2*t*np.array(v)
                # Create a pseudo particle
                wp = particle()
                wp.make_copy(self.pary[ii])
                wp.rx = faux_center[0]
                wp.ry = faux_center[1]
                wp.vx = 0.0
                wp.vy = 0.0
                self.pary[ii].wall_list[2] = wp
                self.pary[ii].wcol_flag[2] = True
            else:
                wall_col = collsion()
                self.process_collision(self.pary[ii],self.pary[ii].wall_list[2],wall_col)
                return True
        elif self.pary[ii].wcol_flag[2]  == True:
            self.pary[ii].wcol_flag[2] = False
            return False
      
        # Bottom Wall ###############################################
        if self.pary[ii].ry < self.wall_ymin+self.pary[ii].radius:
            if self.pary[ii].wcol_flag[3]  == False:
                self.pary[ii].cvx = abs(self.pary[ii].vx)
                self.pary[ii].cvy = abs(self.pary[ii].vy)
                # Center point of particle
                P = (self.pary[ii].rx, self.pary[ii].ry)
                # unit vector pointing in the direction of the wall
                v = (0, -1)
                # A point in the wall
                A = (self.itemcfg.wall_dim[1], self.itemcfg.wall_dim[2])
                # Direction of wall
                d = (1, 0)
                t,s,ipoint = intersect_ray_line_2d(P, v, A, d)
                #print(f"t:{t},s:{s},ipoint:{ipoint}")
                faux_center = P+2*t*np.array(v)
                # Create a pseudo particle
                wp = particle()
                wp.make_copy(self.pary[ii])
                wp.rx = faux_center[0]
                wp.ry = faux_center[1]
                wp.vx = 0.0
                wp.vy = 0.0
                self.pary[ii].wall_list[3] = wp
                self.pary[ii].wcol_flag[3] = True
            else:
                wall_col = collsion()
                self.process_collision(self.pary[ii],self.pary[ii].wall_list[3],wall_col)
                return True
        elif self.pary[ii].wcol_flag[3]  == True:
            self.pary[ii].wcol_flag[3] = False
            return False
        
        return False