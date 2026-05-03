from base.gPCD import Demo
from run.output_dirs import export_path_for_dt, resolve_base_class

BASE_MODEL = "mom"
MULTI_CONTACT_MODE = "sum"
WALL_COLLISION_MODE = "wall_center_on_line"
OUTPUT_DIR_NAME = None

DT = 0.05
SUBSTEPS = 5
POST_COLLISION_FRAMES = None
ZOOM = 1.5
WALL_BOX = (-3.0, 3.0, -3.0, 3.0)

REPULSION_FORCE_PER_AREA = 0.01
MIN_COLLISION_STEPS = 24
ENFORCE_SPEED_LIMIT = True

EXPORT_DATA_FILE = export_path_for_dt(
    "wall_test_collision_data.csv",
    DT,
    output_dir_name=OUTPUT_DIR_NAME,
)

PARTICLE_OVERRIDES = {
    0: {
        "x": -2.0,
        "y": 0.0,
        "vx": 0.5,
        "vy": 0.0,
        "mass": 1.0,
        "radius": 1.0,
        "repulsion_force_per_area": REPULSION_FORCE_PER_AREA,
    },
    1: {
    "x": 1.0,
    "y": -1.0,
    "vx": -0.5,
    "vy": 0.1,
    "mass": 1.0,
    "radius": 1.0,
    "repulsion_force_per_area": REPULSION_FORCE_PER_AREA,
    },
}


def apply_wall_override(base):
    if WALL_BOX is None:
        return
    if WALL_BOX is False:
        base.clear_walls()
        return
    base.set_walls(*WALL_BOX)


def apply_particle_overrides(base):
    required_fields = ("x", "y", "vx", "vy", "mass", "radius")
    for index, overrides in sorted(PARTICLE_OVERRIDES.items()):
        if index < len(base.particle_configs):
            base.particle_configs[index].update(overrides)
            continue

        missing = [field for field in required_fields if field not in overrides]
        if missing:
            raise ValueError(
                f"Particle override {index} cannot create a new particle; missing fields: {', '.join(missing)}"
            )
        base.add_particle(
            x=overrides["x"],
            y=overrides["y"],
            vx=overrides["vx"],
            vy=overrides["vy"],
            mass=overrides["mass"],
            radius=overrides["radius"],
            **{key: value for key, value in overrides.items() if key not in required_fields},
        )


def configure_run(base):
    base.clear_particles()
    base.clear_walls()
    if DT is not None:
        base.dt = float(DT)
    if SUBSTEPS is not None:
        base.substeps = int(SUBSTEPS)
    base.set_scenario_options(post_collision_frames=POST_COLLISION_FRAMES)
    apply_wall_override(base)
    if BASE_MODEL == "mom" and hasattr(base, "set_momentum_response"):
        base.set_momentum_response(REPULSION_FORCE_PER_AREA)
    if BASE_MODEL == "mom" and hasattr(base, "set_multi_contact_mode"):
        base.set_multi_contact_mode(MULTI_CONTACT_MODE)
    if hasattr(base, "set_wall_collision_mode"):
        base.set_wall_collision_mode(WALL_COLLISION_MODE)
    base.set_collision_step_limit(MIN_COLLISION_STEPS)
    base.set_speed_limit_enforcement(ENFORCE_SPEED_LIMIT)
    apply_particle_overrides(base)


if __name__ == "__main__":
    demo = Demo(
        configure_run,
        export_data_file=EXPORT_DATA_FILE,
        base_class=resolve_base_class(BASE_MODEL),
    )
    if ZOOM is not None:
        demo.set_zoom(ZOOM)
    demo.run()
