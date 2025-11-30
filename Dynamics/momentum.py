import numpy as np
import matplotlib.pyplot as plt
from particle import *


p1=particle()
p1.rx = 1.0
p1.ry = 1.0
p1.vx = 1.0
p1.vy = 0.0
p1.radius = 1.0
p1.molar_mass = 1.0

p2=particle()
p2.rx = 1.0
p2.ry = 1.0
p2.vx = -0.5
p2.vy = 0.0
p2.radius = 1.0
p2.molar_mass = 1.0
p1_vox = []
p1_voy = []
p1_vmag = []

p2_vox = []
p2_voy = []
p2_vmag = []
pcnt_ary = []
for ii in range(21):
    
    if ii < 10:
        ctr = 10
        pcnt = (1-ii/10)
    else:
        ctr = ii - 10
        pcnt = (ctr/10)

    pcnt_ary.append(pcnt)
    p1_vox.append(((p1.molar_mass-p2.molar_mass)/(p1.molar_mass+p2.molar_mass))*p1.vx*pcnt + (2*p2.molar_mass/(p1.molar_mass+p2.molar_mass))*p2.vx*pcnt)
    p1_voy.append(((p1.molar_mass-p2.molar_mass)/(p1.molar_mass+p2.molar_mass))*p1.vy*pcnt + (2*p2.molar_mass/(p1.molar_mass+p2.molar_mass))*p2.vy*pcnt)
    p1_vmag.append(np.linalg.norm([p1_vox,p1_voy]))

    p2_vox.append(((p2.molar_mass-p2.molar_mass)/(p2.molar_mass+p2.molar_mass))*p2.vx*pcnt + (2*p2.molar_mass/(p2.molar_mass+p2.molar_mass))*p1.vx*pcnt)
    p2_voy.append(((p2.molar_mass-p2.molar_mass)/(p2.molar_mass+p2.molar_mass))*p2.vy*pcnt + (2*p2.molar_mass/(p2.molar_mass+p2.molar_mass))*p1.vy*pcnt)
    p2_vmag.append(np.linalg.norm([p2_vox,p2_voy]))



    #print(f"pcnt:{pcnt:0.4f}")
    #print(f"p1_vxin:{p1.vx},p1_vxout:{p1_vox},p1_vyin:{p1.vy},p1_vyout:{p1_voy}")
    #print(f"p2_vxin:{p2.vx},p2_vxout:{p2_vox},p2_vyin:{p2.vy},p2_vyout:{p2_voy}")

plt.plot(range(21),p1_vmag)
plt.plot(range(21),p2_vmag)
plt.plot(range(21),pcnt_ary)
plt.show()