from base.scenarios import configure_two_particle_horizontal
from run.output_dirs import export_path_for_dt, resolve_base_class

PARTICLE_OVERRIDES = {
    # Example:
    # 0: {"x": -2.0, "y": 0.0, "vx": 1.0, "vy": 0.0, "mass": 1.0, "radius": 1.0},
    # 1: {"repulsion_accel_per_area": 8.0},
}
BASE_MODEL = "field"
DT = None
SUBSTEPS = None
EXPORT_DATA_FILE = export_path_for_dt("two_particle_horizontal_collision_data.csv", DT)


def configure_run(base):
    configure_two_particle_horizontal(base)
    if DT is not None:
        base.dt = float(DT)
    if SUBSTEPS is not None:
        base.substeps = int(SUBSTEPS)
    for index, overrides in PARTICLE_OVERRIDES.items():
        base.particle_configs[index].update(overrides)


if __name__ == "__main__":
    from base.gPCD import Demo

    Demo(
        configure_run,
        export_data_file=EXPORT_DATA_FILE,
        base_class=resolve_base_class(BASE_MODEL),
    ).run()
