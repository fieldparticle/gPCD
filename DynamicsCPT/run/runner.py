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
    run_configuration = config["RUN_CONFIGURATION"]
    particle_data = build_particle_data(config)

    demo = Demo()
    demo.run(particle_data, run_configuration)


if __name__ == "__main__":
    main()
