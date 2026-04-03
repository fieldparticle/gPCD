import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle

class Sim(FuncAnimation):

   
    def __init__(self,itemcfg,particle_arry):
        self.pa = particle_arry
        self.itemcfg = itemcfg
        self.x_pos = 0.5
        self.y_pos = 0.5
        self.radius = 0.5
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.set_aspect('equal')
   

    def update(self,frame):
        self.x_pos = self.x_pos+0.001
        circle = Circle((self.x_pos,self.y_pos), 0, fill=False)
        self.ax.add_patch(circle)
        circle.set_radius(self.radius)
        return circle,

    def start_animate(self):
        ani = FuncAnimation(self.fig, self.update, frames=range(50), interval=1000, blit=True)
        self.ax.set_title('How to Draw a Circle Using Matplotlib - Animated Circle')
        plt.text(0.5, 0.1, 'how2matplotlib.com', ha='center')
        plt.show()

#s = Sim(None,None)
#s.start_animate()