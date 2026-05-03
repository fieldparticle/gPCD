from base.scenarios import configure_two_particle_angled
from run.output_dirs import export_path_for_dt, resolve_base_class

PARTICLE_OVERRIDES = {
    # Example:
    # 0: {"x": -2.15, "y": 2.0, "vx": 0.5, "vy": -0.5},
    # 1: {"x": -1.0, "y": -1.0, "vx": -0.5, "vy": 0.5},
}
BASE_MODEL = "mom"
DT = 0.005
SUBSTEPS = 5
POST_COLLISION_FRAMES = None
ZOOM = None
WALL_BOX = None  # None = keep scenario default, False = clear walls, tuple = (start_x, end_x, start_y, end_y)
EXPORT_DATA_FILE = export_path_for_dt("two_particle_angled_collision_data.csv", DT)


def apply_wall_override(base):
    if WALL_BOX is None:
        return
    if WALL_BOX is False:
        base.clear_walls()
        return
    base.set_walls(*WALL_BOX)


def configure_run(base):
    configure_two_particle_angled(base)
    if DT is not None:
        base.dt = float(DT)
    if SUBSTEPS is not None:
        base.substeps = int(SUBSTEPS)
    base.set_scenario_options(post_collision_frames=POST_COLLISION_FRAMES)
    apply_wall_override(base)
    for index, overrides in PARTICLE_OVERRIDES.items():
        base.particle_configs[index].update(overrides)


if __name__ == "__main__":
    from base.gPCD import Demo

    demo = Demo(
        configure_run,
        export_data_file=EXPORT_DATA_FILE,
        base_class=resolve_base_class(BASE_MODEL),
    )
    if ZOOM is not None:
        demo.set_zoom(ZOOM)
    demo.run()
