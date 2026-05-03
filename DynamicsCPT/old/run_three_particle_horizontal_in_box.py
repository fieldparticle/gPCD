from base.gPCD import Demo
from base.scenarios import configure_three_particle_horizontal_in_box
from run.output_dirs import resolve_base_class

BASE_MODEL = "mom"
DT = 0.005
SUBSTEPS = 5
POST_COLLISION_FRAMES = None
ZOOM = None
WALL_BOX = None  # None = keep scenario default, False = clear walls, tuple = (start_x, end_x, start_y, end_y)


def apply_wall_override(base):
    if WALL_BOX is None:
        return
    if WALL_BOX is False:
        base.clear_walls()
        return
    base.set_walls(*WALL_BOX)


def configure_run(base):
    configure_three_particle_horizontal_in_box(base)
    if DT is not None:
        base.dt = float(DT)
    if SUBSTEPS is not None:
        base.substeps = int(SUBSTEPS)
    base.set_scenario_options(post_collision_frames=POST_COLLISION_FRAMES)
    apply_wall_override(base)


if __name__ == "__main__":
    demo = Demo(configure_run, base_class=resolve_base_class(BASE_MODEL))
    if ZOOM is not None:
        demo.set_zoom(ZOOM)
    demo.run()
