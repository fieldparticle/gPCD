

import math
def predict_mom(m1,vx1in,v1yin,m2,vx2in,vy2in):
    t1 = ((m1-m2)/(m1+m2))
    t2 = (2*m2/(m1+m2))
    #print(f"t1:{t1},t2:{t2}")
    vx1out = ((m1-m2)/(m1+m2))*vx1in + (2*m2/(m1+m2))*vx2in
    vy1out = ((m1-m2)/(m1+m2))*v1yin + (2*m2/(m1+m2))*vy2in
    
    vx2out = ((m1-m2)/(m1+m2))*vx2in + (2*m1/(m1+m2))*vx1in
    #print(f"vx1out:{vx1out},vx2out{vx2out}")
    return vx1out,vy1out

def atan360(x,y,z):
    angle = math.atan2(y,x)%(2*math.pi)
    return (angle)

def origin_vector(X,Y):
        outvec = [X[1]-X[0],Y[1]-Y[0]]
        return outvec

def vmag(x,y):
    return math.sqrt(x**2+y**2)

def get_sign(var):
     if var == 0.0:
          return 0
     ret = abs(var)/var
     return ret

def get_angle_area(ang_diff,radius):
     return 1/2*(radius**2)*ang_diff