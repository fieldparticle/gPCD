import numpy as np
from contextlib import asynccontextmanager
import time

class Simulation():

    
    def __init__(self,itemcfg,particle_arry):
        self.pa = particle_arry
        self.itemcfg = itemcfg

    def run(self):
        start = 0.0
        end = self.itemcfg.end_time
        step = self.itemcfg.dt
        time_line = np.arange(start, end, step).tolist()
        self.pa.start_plot()
        for tt in time_line:
            for pnum in range(len(self.pa.pary)):
                self.pa.move(pnum,0.05)
                self.pa.plot_particle(pnum,tt)
                print(pnum)
            self.pa.plot_cmd()
            time.sleep(1)
            #self.pa.print_p()

        return




