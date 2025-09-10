import numpy as np
import matplotlib.pyplot as plt
import csv
import math
from ValuesDataBase import *
from AttrDictFields import *

data_list = []

from PlotterClass import *

class A_PBQR_CURVATURE(PlotterClass):
    
        
    def __init__(self,itemcfg,base):
        super().__init__(itemcfg,base)
        

    def do_plot(self,name,particle_counts,timings_ms):
        #timings_ms = [float(numeric_string) for numeric_string in tms]
        # === Example data (replace with your real measurements) ===
        #particle_counts = np.array([1e5, 2e6, 5e6, 1e7])
        #timings_ms = np.array([1.0, 10.5, 26.0, 70.0])  # measured timings in ms

        # === Fit quadratic: T(k) = a*k^2 + b*k + c ===
        coeffs = np.polyfit(particle_counts, timings_ms, deg=2)
        a2, b, c = coeffs
        curvature = 2 * a2  # second derivative (constant for quadratic)
        print(f"Quadratic fit: T(k) = {a2:.3e} k^2 + {b:.3e} k + {c:.3e}")
        print(f"Upper bound on curvature (2a): {curvature:.3e} ms / particle^2")
        a = a2
        an = a2*(11088896**2)
        print(f"a={a} quadratic contribution:{an}")
        val_time = np.max(timings_ms)*1000
        max_val =an/(np.max(timings_ms)*1000)
        print(f"Total t:{val_time} contribution:{max_val}")
        one_percent_error = 0.01*val_time
        max_n = math.sqrt(one_percent_error/a2)
        print(f"Estimated noticable value:{max_n}")

        # === Compute fitted curve and curvature band ===
        k_space = np.linspace(np.min(particle_counts), np.max(particle_counts), 200)
        T_fit = a * k_space**2 + b * k_space + c

        # The curvature bound: how much the slope could change from the mid-range
        mid_k = 0.5 * (np.min(particle_counts) + np.max(particle_counts))
        delta_slope = curvature * (k_space - mid_k)
        # Integrate the slope change into timing offset (approximate visual band)
        # This just makes a symmetric ±band for illustration
        curvature_band = np.abs(delta_slope) * (k_space - mid_k) * 0.5
        upper_band = T_fit + curvature_band
        lower_band = T_fit - curvature_band

        # === Plot ===
        fig = plt.figure(figsize=(10, 6))
        ax = fig.gca()
        plt.scatter(particle_counts, timings_ms, color="black")
        plt.plot(k_space, T_fit, color="blue")
        plt.fill_between(k_space, lower_band, upper_band, color="blue", alpha=0.2)
        self.do_commands(plt,fig,ax)

        #plt.xlabel("Particle count")
        #plt.ylabel("Time (ms)")
        #plt.title("Quadratic Fit with Curvature Bound Visualization")
        leg_list = self.do_legend()
        ax.legend(leg_list)
        #plt.legend()
        plt.grid(True)
        plt.tight_layout()
        filename = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}{name}.png"
        plt.savefig(filename, dpi=150)
        self.include.append(filename)
        plt.close()
        prefix_name = self.itemcfg.name.replace('_','')
        vdb = ValuesDataBase(self.bobj)
        vals_list = AttrDictFields()

        vals_list[f"{prefix_name}{name}StartRow"] = 10
        vals_list[f"{prefix_name}{name}StartRowParticlesVal"] = int(float(data_list[0][6]))
        vals_list[f"{prefix_name}{name}a"] = f"{a2:0.3e}"
        vals_list[f"{prefix_name}{name}b"] = f"{b:0.3e}"
        vals_list[f"{prefix_name}{name}c"] = f"{c:0.3e}"
        vals_list[f"{prefix_name}{name}UpperBoundCurvature"] = f"{curvature:0.3e}"
        vals_list[f"{prefix_name}{name}QuadraticContribution"] = f"{an:0.5f}"
        vals_list[f"{prefix_name}{name}TotalTime"] = f"{val_time:0.4f}"
        vals_list[f"{prefix_name}{name}TotalTimeCont"] = f"{max_val:0.3e}"
        max_as_int = int(float(max_n))
        vals_list[f"{prefix_name}{name}EstimateNoticeableN"] = max_as_int
        vdb.write_values(vals_list)
        

    def run(self):
        with open(self.itemcfg.input_data_file, mode='r') as file:
            csv_reader = csv.reader(file)
            for ii in range(0,10):
                next(csv_reader)  # Skip the header
            for row in csv_reader:
                data_list.append(row)

        print(f"Start row:10 for val:{data_list[0][0]}")
        transposed = list(zip(*data_list))
        pc = np.array(transposed[6]).astype(float)
        particle_counts = [int(numeric_string) for numeric_string in pc]

        gms = np.array(transposed[4]).astype(float)
        cms = np.array(transposed[3]).astype(float)
        both = np.add(gms,cms)

        self.do_plot('tot',particle_counts,both)
       
        self.do_plot('gms',particle_counts,gms)
        self.do_plot('cms',particle_counts,cms)

        self.itemcfg['input_images'] = self.include
        return
