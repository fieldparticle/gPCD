from particle import *
import matplotlib as plt
import numpy as np
class DrawParticle():

    def __init__(self,itemcfg):
        self.itemcfg = itemcfg

    #******************************************************************
    # plot the particles
    #
    def plot_particle(self,particle):
        p_count = 0
        # Get the number facets for smoothness
        sphere_facets = self.itemcfg.sphere_facets
        # Set up the sphere data
        theta = np.linspace(0, 2 * np.pi, sphere_facets)
        phi = np.linspace(0, np.pi, sphere_facets)
        theta, phi = np.meshgrid(theta, phi)
        # Set the default color
        pcolor = self.itemcfg.particle_color
        # If plotting as points just do a scatter
        if self.itemcfg.as_points == True:    
            px = [[dic.rx] for dic in self.particle_data]
            py= [[dic.ry] for dic in self.particle_data]
            pz = [[dic.rz] for dic in self.particle_data]
            #px = self.particle_data[:]
            self.ax.scatter(px,py,pz)
        # If doing spheres 
        else:
            # Convert to Cartesian coordinates
            x = particle.rx + particle.radius * np.sin(phi) * np.cos(theta)
            y = particle.ry + particle.radius * np.sin(phi) * np.sin(theta)
            z = particle.rz + particle.radius * np.cos(phi)
            # If the particle is in collision use a different color
            if particle.ptype == 1:
                if self.itemcfg.vary_color == False:
                    self.ax.plot_surface(x, y, z, color='blue',alpha=0.8)
                else:
                    self.ax.plot_surface(x, y, z,alpha=0.8)
            # Else uese standar color
            else:
                if self.itemcfg.vary_color == False:
                    self.ax.plot_surface(x, y, z, color=pcolor,alpha=0.8)
                else:
                    self.ax.plot_surface(x, y, z,alpha=0.8)
            #print(f"Particle {p_count} Loc: <{ii.rx:2f},{ii.ry:2f},{ii.rz:2f})>")
            
            