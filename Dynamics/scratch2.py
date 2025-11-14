
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

fig, ax = plt.subplots()
xdata, y1data, y2data = [], [], []
ln1, = plt.plot([], [], 'r', animated=True)
ln2, = plt.plot([], [], 'g', animated=True)

def init():
    ax.set_xlim(0, 2*np.pi)
    ax.set_ylim(-2, 2)
    return ln1, ln2

def update(frame):
    xdata.append(frame)
    y1data.append(np.sin(frame))
    y2data.append(np.cos(frame))
    ln1.set_data(xdata, y1data)
    ln2.set_data(xdata, y2data)
    return ln1, ln2

ani = FuncAnimation(fig, update, frames=np.linspace(0, 2*np.pi, 128),
                    init_func=init, blit=True)

plt.title("Animating Multiple Lines - how2matplotlib.com")
plt.show()