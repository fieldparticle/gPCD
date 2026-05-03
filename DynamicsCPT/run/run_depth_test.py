from base.gPCD import Demo
from run.output_dirs import export_path_for_dt, resolve_base_class
from pathlib import Path
import csv

BASE_MODEL = "mom"
MULTI_CONTACT_MODE = "sum"
WALL_COLLISION_MODE = "wall_center_on_line"
OUTPUT_DIR_NAME = "data/depth_test"

DT = 0.005
SUBSTEPS = 5
POST_COLLISION_FRAMES = 10
ZOOM = 1.5
WALL_BOX = (-3.5, 3.5, -3.0, 3.0)

REPULSION_FORCE_PER_AREA_START = 0.001
REPULSION_FORCE_PER_AREA_STEP = 0.005
FORCE_RUN_COUNT = 10
STUDY_FORCE_VALUES: list[float] | None = None
STARTING_VELOCITY = 0.1
VELOCITY_STEP = 0.1
VELOCITY_RUN_COUNT = 10
STUDY_VELOCITY_VALUES: list[float] | None = None
MIN_COLLISION_STEPS = 24
ENFORCE_SPEED_LIMIT = False
force_study_list = list(range(FORCE_RUN_COUNT))
velocity_study_list = list(range(VELOCITY_RUN_COUNT))

BASE_PARTICLE_OVERRIDES = {
    0: {
        "x": -1.05,
        "y": 0.0,
        "vx": STARTING_VELOCITY,
        "vy": 0.0,
        "mass": 1.0,
        "radius": 1.0,
    },
    1: {
        "x": 1.05,
        "y": 0.0,
        "vx": -STARTING_VELOCITY,
        "vy": 0.0,
        "mass": 1.0,
        "radius": 1.0,
    },
}

PARTICLE_OVERRIDES = {
    # Additional fixed per-particle edits after BASE_PARTICLE_OVERRIDES.
}


def force_value_for_study(study_index: int) -> float:
    if STUDY_FORCE_VALUES is not None:
        return float(STUDY_FORCE_VALUES[study_index])
    return float(REPULSION_FORCE_PER_AREA_START + study_index * REPULSION_FORCE_PER_AREA_STEP)


def velocity_value_for_study(study_index: int) -> float:
    if STUDY_VELOCITY_VALUES is not None:
        return float(STUDY_VELOCITY_VALUES[study_index])
    return float(STARTING_VELOCITY + study_index * VELOCITY_STEP)


def apply_wall_override(base):
    if WALL_BOX is None:
        return
    if WALL_BOX is False:
        base.clear_walls()
        return
    base.set_walls(*WALL_BOX)


def apply_particle_overrides(base, particle_overrides):
    required_fields = ("x", "y", "vx", "vy", "mass", "radius")
    for index, overrides in sorted(particle_overrides.items()):
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


def configure_run(base, particle_overrides, repulsion_force_per_area):
    base.clear_particles()
    base.clear_walls()
    if DT is not None:
        base.dt = float(DT)
    if SUBSTEPS is not None:
        base.substeps = int(SUBSTEPS)
    base.set_scenario_options(post_collision_frames=POST_COLLISION_FRAMES)
    apply_wall_override(base)
    if BASE_MODEL == "mom" and hasattr(base, "set_momentum_response"):
        base.set_momentum_response(repulsion_force_per_area)
    if BASE_MODEL == "mom" and hasattr(base, "set_multi_contact_mode"):
        base.set_multi_contact_mode(MULTI_CONTACT_MODE)
    if hasattr(base, "set_wall_collision_mode"):
        base.set_wall_collision_mode(WALL_COLLISION_MODE)
    base.set_collision_step_limit(MIN_COLLISION_STEPS)
    base.set_speed_limit_enforcement(ENFORCE_SPEED_LIMIT)
    apply_particle_overrides(base, particle_overrides)


def append_study_metadata(export_data_file, velocity_index, velocity_value, force_index, repulsion_force_per_area):
    export_path = Path(export_data_file)
    if not export_path.is_absolute():
        export_path = Path(__file__).resolve().parents[1] / export_path
    summary_path = export_path.with_name(f"{export_path.stem}_summary{export_path.suffix}")
    if not summary_path.exists():
        return
    rows = []
    with summary_path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    rows.extend(
        [
            ["study velocity index", f"{velocity_index}"],
            ["study velocity", f"{velocity_value:.8f}"],
            ["study force index", f"{force_index}"],
            ["study repulsion force per area", f"{repulsion_force_per_area:.8f}"],
        ]
    )
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


if __name__ == "__main__":
    base_class = resolve_base_class(BASE_MODEL)

    if STUDY_FORCE_VALUES is not None:
        force_study_list = list(range(len(STUDY_FORCE_VALUES)))
    if STUDY_VELOCITY_VALUES is not None:
        velocity_study_list = list(range(len(STUDY_VELOCITY_VALUES)))

    for velocity_index in velocity_study_list:
        velocity_value = velocity_value_for_study(velocity_index)
        for force_index in force_study_list:
            repulsion_force_per_area = force_value_for_study(force_index)
            particle_overrides = {
                index: dict(overrides)
                for index, overrides in BASE_PARTICLE_OVERRIDES.items()
            }
            for index, overrides in PARTICLE_OVERRIDES.items():
                if index not in particle_overrides:
                    particle_overrides[index] = {}
                particle_overrides[index].update(overrides)

            particle_overrides.setdefault(0, {})["vx"] = velocity_value
            particle_overrides.setdefault(0, {})["vy"] = 0.0
            particle_overrides.setdefault(1, {})["vx"] = -velocity_value
            particle_overrides.setdefault(1, {})["vy"] = 0.0

            for overrides in particle_overrides.values():
                overrides["repulsion_force_per_area"] = repulsion_force_per_area

            print(
                f"Running depth study v{velocity_index} f{force_index} with "
                f"velocity={velocity_value:.8f}, "
                f"REPULSION_FORCE_PER_AREA={repulsion_force_per_area:.8f}"
            )
            export_data_file = export_path_for_dt(
                f"depth_v{velocity_index}_f{force_index}.csv",
                DT,
                output_dir_name=OUTPUT_DIR_NAME,
            )

            def configure_study_run(base):
                configure_run(base, particle_overrides, repulsion_force_per_area)

            demo = Demo(
                configure_study_run,
                export_data_file=export_data_file,
                base_class=base_class,
            )
            if ZOOM is not None:
                demo.set_zoom(ZOOM)
            demo.run()
            append_study_metadata(
                export_data_file,
                velocity_index,
                velocity_value,
                force_index,
                repulsion_force_per_area,
            )
