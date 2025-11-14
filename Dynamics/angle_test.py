import numpy as np

class angle_test():

    def origin_vector(vec4):
        outvec = [vec4[2]-vec4[0],vec4[3]-vec4[1]]
        return outvec
    
    def atan2piPt(vec2):
        angle = np.arctan(vec2[0],vec2[1])
        print(angle)

    
ang = angle_test()
ang.origin_vector([])