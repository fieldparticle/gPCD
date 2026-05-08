import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from base.gPCD import Demo

RUN_CONFIGURATION = {
    "dt": 0.05,
    "substeps": 5,
    "window_size": (1000, 1000),
    "wall_box": (-5.0, 5.0, -5.0, 5.0),
    "zoom": 0.5,
    "max_contacts_per_particle": 8,
    "momentum_per_area": 0.001,
    "inverse_square_softening": 1.0,
}

PARTICLE_DATA = {
    0: {
        "location": {"use": 0, "x1": -2.0, "y1": 2.0, "x2": -2.15, "y2": 2.0},
        "vx": 0.05,
        "vy": -0.05,
        "mass": 1.0,
        "radius": 1.0,
        "fill": (100, 170, 255),
        "edge": (160, 210, 255),
    },
    1: {
        "location": {"use": 0, "x1": -1.0, "y1": -1.0, "x2": -1.0, "y2": -1.0},
        "vx": -0.05,
        "vy": 0.05,
        "mass": 1.0,
        "radius": 1.0,
        "fill": (255, 120, 120),
        "edge": (255, 180, 180),
    },
}


if __name__ == "__main__":
    demo = Demo()
    demo.run(PARTICLE_DATA, RUN_CONFIGURATION)
