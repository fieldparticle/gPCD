import argparse
import io
import sys
from pathlib import Path
from gbase import pdata
from gbase import BinaryFileUtilities

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from base import libconf
from base.gPCD import Demo
from base.libconf import AttrDict
import tkinter as tk
from tkinter import filedialog


#DEFAULT_CFG_FILE = Path("C:/_DJ/gPCD/python/cfg_gendata/TwoParticleHorizontal.cfg")

#DEFAULT_CFG_FILE = Path("C:/_DJ/gPCD/python/cfg_gendata/OneParticleBoundaryTest.cfg")
#DEFAULT_CFG_FILE = Path("C:/_DJ/gPCD/python/cfg_gendata/TwoParticleAngled.cfg")
WALL_MIN_MAX_KEYS = ("WallXMIN", "WallXMAX", "WallYMIN", "WallYMAX")


def load_runner_config(cfg_file):
    
    try:
        with io.open(cfg_file, encoding="utf-8") as f:
            return libconf.load(f)
    except OSError:
        raise SystemExit(f"gPCD failed to open config file: {cfg_file}")
    except libconf.ConfigParseError as e:
        raise SystemExit(f"gPCD failed to parse config file: {cfg_file}\n{e}")



def getParticleData(config):
    file_name = f"{config.data_dir}/{config.STUDY_NAME}.bin" 
    results = BinaryFileUtilities.read_all_particle_data(file_name)
    particle_data = AttrDict()
    for pp in results:
        if pp.pnum == 0:
            continue  # Skip null particle
        
        dict_location = {
            "use": 0,
            "x1": pp.rx,
            "y1": pp.ry,
            "z1": pp.rz,
            "x2": pp.rx,
            "y2": pp.ry,
            "z2": pp.rz}
        particle = AttrDict()
        particle["location"] = AttrDict(dict_location)
        particle["vx"] = pp.vx
        particle["vy"] = pp.vy
        particle["vz"] = pp.vz
        particle["mass"] = pp.molar_mass
        particle["radius"] = pp.radius
        particle["ptype"] = pp.ptype
        particle["state_flg"] = int(pp.state_flg)
        particle["inverse_square_softening"] = pp.inverse_square_softening
        particle["momentum_per_area"] = pp.momentum_per_area
        particle["edge"] = (100, 170, 255)
        particle["fill"] = (160, 210, 255)
        particle_data[pp.pnum] = particle
        print(f"Read particle: {pp.pnum} at ({pp.rx}, {pp.ry}, {pp.rz}) with velocity ({pp.vx}, {pp.vy}, {pp.vz})")
    return particle_data


def build_particle_data(config):
    
    if config.pdata_from_file == True:
        return getParticleData(config)
    else:
        particle_data = AttrDict()
        particles = config["PARTICLE_DATA"]

        for particle_index in range(len(particles)):
            particle_key = f"p{particle_index + 1}"
            particle = AttrDict(particles[particle_key])

            location = particle.get("location")
            if isinstance(location, dict):
                if "x2" not in location and "x1" in location:
                    location["x2"] = location["x1"]
                if "y2" not in location and "y1" in location:
                    location["y2"] = location["y1"]
                if "z2" not in location and "z1" in location:
                    location["z2"] = location["z1"]

            particle_data[particle_index] = particle

    return particle_data


def first_config_value(sections, key, default=None):
    for section in sections:
        if section is not None and key in section:
            return section[key]
    return default


def wall_box_from_min_max(section):
    if section is None or not all(key in section for key in WALL_MIN_MAX_KEYS):
        return None
    return tuple(float(section[key]) for key in WALL_MIN_MAX_KEYS)


def wall_box_from_array(section):
    if section is None or "walls" not in section:
        return None
    walls = section["walls"]
    if len(walls) < 4:
        raise SystemExit("gPCD wall config requires four values: xmin, xmax, ymin, ymax")
    return tuple(float(value) for value in walls[:4])


def build_run_configuration(config):
    run_configuration = AttrDict(config["RUN_CONFIGURATION"])
    if "data_dir" in config:
        run_configuration["data_dir"] = config["data_dir"]
    application = config.get("application")
    sections = (run_configuration, config, application)

    walls_on = first_config_value(sections, "walls_on")
    if walls_on is False:
        run_configuration["wall_box"] = False
        return run_configuration

    wall_box = first_config_value((run_configuration,), "wall_box")
    if wall_box is None:
        for section in sections:
            wall_box = wall_box_from_array(section) or wall_box_from_min_max(section)
            if wall_box is not None:
                break

    if wall_box is not None and (walls_on is True or walls_on is None):
        run_configuration["wall_box"] = tuple(float(value) for value in wall_box)

    return run_configuration


def parse_args():
    parser = argparse.ArgumentParser(description="Run the Python gPCD viewer from a shared libconfig file.")
    parser.add_argument(
        "cfg_file",
        nargs="?",
        type=Path,
        default=DEFAULT_CFG_FILE,
        help=f"Path to the shared libconfig file. Default: {DEFAULT_CFG_FILE}",
    )
    return parser.parse_args()

#******************************************************************
# Browse to an existing cfg file
#
def browseFolder():
    # Create the root window and hide it
    root = tk.Tk()
    root.withdraw()

    # Open a file selection dialog
    file_path = filedialog.askopenfilename(
        title="Select a File",
        filetypes=[("Config Files", "*.cfg;"), ("All Files", "*.*")])

    if not file_path:
        print("No file selected.")
        return
    
    print("Selected file:", file_path)

    global DEFAULT_CFG_FILE
    DEFAULT_CFG_FILE = file_path
    print(f"Selected configuration file: {DEFAULT_CFG_FILE}")

def run_analysis(cfg_file):
    config = load_runner_config(cfg_file)
    run_configuration = build_run_configuration(config)
    particle_data = build_particle_data(config)
    demo = Demo()
    demo.run(particle_data, run_configuration)

def main():
    browseFolder()
    args = parse_args()
    config = load_runner_config(args.cfg_file)
    run_configuration = build_run_configuration(config)
    particle_data = build_particle_data(config)

    demo = Demo()
    demo.run(particle_data, run_configuration)


if __name__ == "__main__":
    main()
