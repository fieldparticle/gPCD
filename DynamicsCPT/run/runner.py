import argparse
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from base import libconf
from base.gPCD import Demo
from base.libconf import AttrDict


DEFAULT_CFG_FILE = Path("C:/_DJ/gPCD/vulkan/sim/BoundarySpheresMotion/two_particle_horz.cfg")
WALL_MIN_MAX_KEYS = ("WallXMIN", "WallXMAX", "WallYMIN", "WallYMAX")


def load_runner_config(cfg_file):
    try:
        with io.open(cfg_file, encoding="utf-8") as f:
            return libconf.load(f)
    except OSError:
        raise SystemExit(f"gPCD failed to open config file: {cfg_file}")
    except libconf.ConfigParseError as e:
        raise SystemExit(f"gPCD failed to parse config file: {cfg_file}\n{e}")


def build_particle_data(config):
    particle_data = AttrDict()
    particles = config["PARTICLE_DATA"]

    for particle_index in range(len(particles)):
        particle_key = f"p{particle_index + 1}"
        particle_data[particle_index] = AttrDict(particles[particle_key])

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


def main():
    args = parse_args()
    config = load_runner_config(args.cfg_file)
    run_configuration = build_run_configuration(config)
    particle_data = build_particle_data(config)

    demo = Demo()
    demo.run(particle_data, run_configuration)


if __name__ == "__main__":
    main()
