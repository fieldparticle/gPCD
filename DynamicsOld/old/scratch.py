

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import math

fig, ax = plt.subplots(subplot_kw=dict(projection="3d"))

def atan360(x,y,z):
   angle = math.atan2(y,x)%(2*math.pi)
   return (angle)

def get_arrow1(theta):        
   x = 0#np.cos(theta)
   y = 0# np.sin(theta)
   z = 0
   u = np.cos(theta)
   v = np.sin(theta) #np.sin(theta)
   w = 0#np.cos(3*theta)
   return x,y,z,u,v,w

def get_arrow(theta):
    x = 0#np.cos(theta)
    y = 0# np.sin(theta)
    z = 0
    uu = np.cos(theta)
    vv = np.sin(theta) #np.sin(theta)
    ww = 0#np.cos(3*theta)

    ang = atan360(uu,vv,0)
    u = np.cos(ang)
    v = np.sin(ang) #np.sin(theta)
    w = 0#np.cos(3*theta)
    print(f"MyAng:{ ang:.4f},360 ang:{ ang*180.0/math.pi:.4f}, theta:{theta*180.0/math.pi:.4f}")
    return x,y,z,u,v,w

quiver1 = ax.quiver(*get_arrow(0),color='r')
quiver2 = ax.quiver(*get_arrow1(0),color='b')

ax.set_xlim(-2, 2)
ax.set_ylim(-2, 2)
ax.set_zlim(-2, 2)
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.view_init(elev=90, azim=-90, roll=0)

def update(theta):
    global quiver1
    global quiver2
    quiver1.remove()
    quiver2.remove()
    quiver1 = ax.quiver(*get_arrow(theta),color='r')
    quiver2 = ax.quiver(*get_arrow1(theta),color='b',alpha=.25)


ani = FuncAnimation(fig, update, frames=np.linspace(0.0,2*np.pi,200), interval=100,repeat=False)
plt.show()