from base.gPCD import Demo
from base.scenarios import configure_two_particle_horizontal_bonded
from run.output_dirs import resolve_base_class

BASE_MODEL = "field"
DT = None
SUBSTEPS = None


def configure_run(base):
    configure_two_particle_horizontal_bonded(base)
    if DT is not None:
        base.dt = float(DT)
    if SUBSTEPS is not None:
        base.substeps = int(SUBSTEPS)


if __name__ == "__main__":
    Demo(configure_run, base_class=resolve_base_class(BASE_MODEL)).run()
