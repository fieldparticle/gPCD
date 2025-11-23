
from ParticleArray import *
from matplotlib.patches import Circle
import matplotlib.pyplot as plt
import math
from Utility import *
import numpy as np

pa = ParticleArray(None)
def process_collision(src,trg,radius,col_struct):
        
        try:
            A = np.array((src[0], src[1]))
            B = np.array((trg[0], trg[1]))
            c =  np.linalg.norm(A-B)
            a = radius
            b = radius
            cosAlpha = (b**2+c**2-a**2)/(2*b*c)
            # Unit vector pointing to centers
            u_AB = (B - A)/c
            # Normal vector
            pu_AB = np.array((u_AB[1], -u_AB[0])); 
            r = ((1-cosAlpha**2))
            #print(r)
            if r < 0.0:
                return False
            # The intersection points.
            col_struct.col_pointA = A + u_AB * (b*cosAlpha) + pu_AB * (b*np.sqrt(1-cosAlpha**2))
            col_struct.col_pointB = A + u_AB * (b*cosAlpha) - pu_AB * (b*np.sqrt(1-cosAlpha**2))
            # Vector from center opf particle
            col_struct.isec_vect = [[src[0],col_struct.col_pointA[0]],
                                [src[1],col_struct.col_pointA[0]]]
            # Bisector of line between intersection points
            O1 = (col_struct.col_pointA[0]+col_struct.col_pointB[0])/2.0
            O2 = (col_struct.col_pointA[1]+col_struct.col_pointB[1])/2.0

            # Print orientation vector from center of particle to bisector
            col_struct.orient_vec_print = [[src[0],O1],[src[0],O2]]
            # Orient vector
            col_struct.orient_vec = np.array([[src[0],src[1]],[O1,O2]])
             # Get length of orient vector.
            ol =  np.linalg.norm(col_struct.orient_vec) # this does not work
            ol1 = (src[0]-O1)**2
            ol2 = (src[1]-O2)**2
            ol = np.sqrt(ol1+ol2)
            # Find r1 
            r1 =abs(radius - ol)
            # Subtract from ol
            col_struct.prox_len = radius-2*r1
            # Convert to origin vector to get angle.
            ovec2 = origin_vector([src[0],O1],[src[1],O2])
            # Get orietn vector 360 degree angle.
            col_struct.orient_ang = atan360(ovec2[0],ovec2[1],0.0)
            proxvec = [[src[0],col_struct.prox_len*np.cos(col_struct.orient_ang)+src[0]], 
                       [src[1],col_struct.prox_len*np.sin(col_struct.orient_ang)+src[1]]]
            col_struct.prox_vec = proxvec
            col_struct.pen_factor = (1.0-col_struct.prox_len/radius)
           
            return True
            

        except BaseException as e:
            print(e)
        return False

def origin_vector(X,Y):
        outvec = [X[1]-X[0],Y[1]-Y[0]]
        return outvec

def plot_particles():


    fig,ax = plt.subplots()
    ccA = plt.Circle((2.0,2.0),0.8,color='blue',alpha=0.8,fill=False)
    ccB = plt.Circle((3.0,3.0),0.8,color='blue',alpha=0.8,fill=False)
    ccC = plt.Circle((3.0,1.0),0.8,color='blue',alpha=0.8,fill=False)
    
    ax.set_xlim([-2.0,5.0])
    ax.set_ylim([-2.0,5.0])
    ax.text(2.0,2.0,f"A")
    ax.text(3.0,3.0,f"B")
    ax.text(3.0,1.0,f"C")
    ax.add_patch(ccA)
    ax.add_patch(ccB)
    ax.add_patch(ccC)
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.set_aspect('equal', 'box')
    ax.grid(True)
    plt.show()
    #ax.show()


def main():
    Av_ang = 0.0
    Avx = 1.0*math.cos(Av_ang)
    Avy = 1.0*math.sin(Av_ang)
    Av = [Avx,Avy]

    Bvx = -0.5
    Bvy = -0.5
    Bv_ang = atan360(Bvx,Bvy,0.0)
    Bv = [Bvx,Bvy]
    
    col_array = []
    col_struct = collision()
    process_collision([2.0,2.0],[3.0,3.0],0.8,col_struct)

    # Get the source velocity components, magnitude, and angle
    col_struct.srcvx = Avx
    col_struct.srcvy = Avy
    col_struct.srcv = [Avx,Avy]
    col_struct.Av = np.linalg.norm(col_struct.srcv)
    col_struct.Aang = atan360(Avx,Avy,0.0)

    # Get the target velocity components, magnitude, and angle
    col_struct.trgvx = Bvx
    col_struct.trgvx = Bvy
    col_struct.trgv = [Bvx,Bvy]
    col_struct.Bv = np.linalg.norm(col_struct.trgv)
    col_struct.Bang = atan360(Bvx,Bvy,0.0)

    # For the source get component of velcoity in direction of the collision - 
    # This is cose of the difference between src vecloityangle and orientation angle
    col_struct.Acomp = col_struct.Av*math.cos( col_struct.Aang-col_struct.orient_ang )

    # For the target get component of velcoity in direction of the collision - 
    # This is cose of the difference between src vecloityangle and orientation angle
    col_struct.Bcomp = col_struct.Bv*math.cos( col_struct.Bang-col_struct.orient_ang )

    # Get vecoity components in direction of orientation vector
    col_struct.rel_vx = col_struct.Acomp*math.cos(col_struct.orient_ang)
    col_struct.rel_vy = col_struct.Acomp*math.sin(col_struct.orient_ang)
    col_array.append(col_struct)
    
    for ii in col_array:

        print(f"Orient Ang:{ii.orient_ang:.4f}, PctInstert:{ii.pen_factor:.4f}")


    plot_particles()

main()