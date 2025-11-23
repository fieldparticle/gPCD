

import math
def atan360(x,y,z):
    angle = math.atan2(y,x)%(2*math.pi)
    return (angle)

def origin_vector(X,Y):
        outvec = [X[1]-X[0],Y[1]-Y[0]]
        return outvec

def vmag(x,y):
    return math.sqrt(x**2+y**2)