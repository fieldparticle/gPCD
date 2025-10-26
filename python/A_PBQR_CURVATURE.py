import numpy as np
import matplotlib.pyplot as mplt
import csv
import math
from ValuesDataBase import *
from AttrDictFields import *



from PlotterClass import *

class A_PBQR_CURVATURE(PlotterClass):
    
        
    def __init__(self,itemcfg,base):
        super().__init__(itemcfg,base)

    def curvature_thresholds(self,a, b, c, eps=0.01, dT=1e-5):
    
        cabs, babs = abs(c), abs(b)
        # 1) Relative to linear (large-N approx and exact with 'a')
        N_eps_lin = eps*babs/cabs if cabs>0 else float('inf')
        disc = (eps*b)**2 + 4*eps*cabs*a
        N_eps_exact = ((eps*b) + math.sqrt(max(disc, 0.0))) / (2*cabs) if cabs>0 else float('inf')
        # 2) Slope criterion
        N_eps_slope = eps*babs/(2*cabs) if cabs>0 else float('inf')
        # 3) Absolute timing resolution
        N_dT = math.sqrt(dT/cabs) if cabs>0 else float('inf')
        return {
            "N_eps_lin_approx": N_eps_lin,
            "N_eps_exact": N_eps_exact,
            "N_eps_slope": N_eps_slope,
            "N_dT": N_dT,
            "N_noticeable": max(N_eps_exact, N_eps_slope, N_dT)
        }


        

    def do_plot(self,name,particle_counts,timings_ms):
        #timings_ms = [float(numeric_string) for numeric_string in tms]
        # === Example data (replace with your real measurements) ===
        #particle_counts = np.array([1e5, 2e6, 5e6, 1e7])
        #timings_ms = np.array([1.0, 10.5, 26.0, 70.0])  # measured timings in ms

        # === Fit quadratic: T(k) = a*k^2 + b*k + c ===
        coeffs = np.polyfit(particle_counts, timings_ms, deg=2)
        a2, b, c = coeffs

        ##### Curvature is second derivative of tendline ###############
        curvature = 2 * a2  # second derivative (constant for quadratic)

        print(f"Quadratic fit: T(k) = {a2:.3e} k^2 + {b:.3e} k + {c:.3e}\n")
        print(f"Upper bound on curvature (2a): {curvature:.3e} ms / particle^2\n")
        a = a2
        xmaN = particle_counts[-1]
        ###### quadratic contribution to per-particle #################
        del_little_t =  a2*xmaN

        ###### delta big T total quadratic contribution ########################
        an = a2*(xmaN**2)
        delt= curvature*xmaN*xmaN

        maxT = timings_ms[-1]
        ###### total time quadratic contribution divided by time is the fraction of Curavture to the max time ########################
        val_time = np.max(timings_ms)
        max_val =an/(np.max(timings_ms))

        print(f"Total t:{val_time} contribution:{max_val}\n")
        one_percent_error = 0.01*val_time
        max_n = 0
        if a2 > 0:
            a2 = abs(a2)
            max_n = -math.sqrt(one_percent_error/a2)
            print(f"Estimated noticable value:{max_n}\n")

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

        one_percent =  0.01*val_time
        #quad_effect = math.sqrt(one_percent/a)
        # === Plot ===
        ##------------------------------------------
        plt,fig,ax = self.__new_figure__()
        self.__do_commands__(plt,fig,ax)
        ##-------------------------------------------
        plt.scatter(particle_counts, timings_ms, color="black")
        plt.plot(k_space, T_fit, color="blue")
        plt.fill_between(k_space, lower_band, upper_band, color="blue", alpha=0.2)
        plt.pause(0.01)
        ##-------------------------------------------
        leg_list = self.__do_legend__()
        plt.legend(leg_list)
        ##-------------------------------------------
        
        
        ##-------------------------------------------
        #self.plt.tight_layout()
        filename = f"{self.itemcfg.plots_dir}/{self.itemcfg.name}{name}.png"
        self.__clean_files__(filename)
        plt.savefig(filename, dpi=self.itemcfg.dpi)
        self.include.append(filename)
        plt.close()
        
        
        del_t1 = curvature*xmaN
        del_t2 = del_t1*xmaN
        del_t2_frc = del_t2/(val_time)
        del_t2_pct = del_t2_frc*100
        if 'tot' in name:
            self.vals_list[f"{self.prefix_name}{name}"] = 'Total'
        elif 'gms' in name:
            self.vals_list[f"{self.prefix_name}{name}"] = 'Graphics'
        elif 'cms' in name:
            self.vals_list[f"{self.prefix_name}{name}"] = 'Compute'
        
                       
        self.vals_list[f"{self.prefix_name}{name}StartRow"] = 10
        self.vals_list[f"{self.prefix_name}{name}MaxParticles"] = f"{xmaN}"
        self.vals_list[f"{self.prefix_name}{name}a"] = f"{a2:0.3e}"
        self.vals_list[f"{self.prefix_name}{name}b"] = f"{b:0.3e}"
        self.vals_list[f"{self.prefix_name}{name}c"] = f"{c:0.3e}"
        self.vals_list[f"{self.prefix_name}{name}twoa"] = f"{2*a:0.3e}"
        self.vals_list[f"{self.prefix_name}{name}UpperBoundCurvature"] = f"{abs(curvature):0.3e}"
        self.vals_list[f"{self.prefix_name}{name}QuadraticContributionta"] = f"{abs(del_t1):0.4e}"
        self.vals_list[f"{self.prefix_name}{name}QuadraticContributiontb"] = f"{abs(del_t2):0.4e}"
        self.vals_list[f"{self.prefix_name}{name}QuadraticContributionfrc"] = f"{abs(max_val):0.6f}"
        self.vals_list[f"{self.prefix_name}{name}QuadraticContributionpct"] = f"{abs(max_val*100):0.2f}"
        self.vals_list[f"{self.prefix_name}{name}TotalTime"] = f"{abs(val_time):0.6f}"
        self.vals_list[f"{self.prefix_name}{name}TotalTimeCont"] = f"{abs(delt):0.4f}"
        max_as_int = int(float(max_n))
        self.vals_list[f"{self.prefix_name}{name}EstimateNoticeableN"] = f"{max_as_int:,}"
        rescale = 2*a*1E7*1E6 
        self.vals_list[f"{self.prefix_name}{name}Rescale"] = f"{rescale:0.4e}"
        
        

    def run(self):
        data_list = []
        with open(self.itemcfg.input_data_file, mode='r') as file:
            csv_reader = csv.reader(file)
            for ii in range(0,28):
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

        
        print("-------------------------- gms ----------------------------")
        self.do_plot('gms',particle_counts,gms)
        print("-------------------------- cms ----------------------------")
        self.do_plot('cms',particle_counts,cms)
        print("-------------------------- TOT ----------------------------")
        self.do_plot('tot',particle_counts,both)

        self.itemcfg['input_images'] = self.include
        self.vals_list[f"{self.prefix_name}StartRowParticlesVal"] = int(float(data_list[0][6]))
        self.__write_vals__()
        return


