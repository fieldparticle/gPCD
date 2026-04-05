from base.scenarios import configure_three_particle_horizontal
from run.output_dirs import export_path_for_dt, resolve_base_class

BASE_MODEL = "mom"
MULTI_CONTACT_MODE = "sum"
#MULTI_CONTACT_MODE = "normalize_shared"
#MULTI_CONTACT_MODE = "sequential_descending_j"
#MULTI_CONTACT_MODE = "sequential_ascending_j"


OUTPUT_DIR_NAME = "ThreeP005_mom_sum"

DT = 0.005
SUBSTEPS = 5
SWEEP_PARTICLE_INDEX = 2
SWEEP_AXIS = "y"
SWEEP_START = 3.0
SWEEP_STEP = 0.01
RUN_COUNT = 20
P0_START_Y = 0.0
P1_START_Y = -1.0
P2_START_Y = 1.0    
REPULSION_FORCE_PER_AREA = 0.01
MIN_COLLISION_STEPS = 24
ENFORCE_SPEED_LIMIT = True
particle_list = list(range(RUN_COUNT))
#particle_list = [0]


BASE_PARTICLE_OVERRIDES = {
    0: {
        "x": -1.0,
        "y": P0_START_Y,
        "vx": 0.1,
        "vy": 0.0,
        "repulsion_force_per_area": REPULSION_FORCE_PER_AREA,
    },
    1: {
        "x": 1.0,
        "y": P1_START_Y,
        "vx": -0.1,
        "vy": 0.0,
        "repulsion_force_per_area": REPULSION_FORCE_PER_AREA,
    },
    2: {
        "x": 1.0,
        "y": P2_START_Y,
        "vx": -0.1,
        "vy": 0.0,
        "repulsion_force_per_area": REPULSION_FORCE_PER_AREA,
    },
}
PARTICLE_OVERRIDES = {
    # Additional fixed overrides applied after BASE_PARTICLE_OVERRIDES.
    # Example:
    # 0: {"mass": 2.0},
}


def build_study_particle_overrides(study_index: int, sweep_value: float) -> dict[int, dict[str, float]]:
    overrides: dict[int, dict[str, float]] = {
        SWEEP_PARTICLE_INDEX: {SWEEP_AXIS: sweep_value},
    }

    # Add any per-study position edits here.
    # Example:
    y_value = study_index * SWEEP_STEP
    overrides.setdefault(1, {})["y"] = P1_START_Y - SWEEP_STEP * study_index
    #overrides.setdefault(1, {})["y"] = 0.1 * study_index
    overrides.setdefault(2, {})["y"] = P2_START_Y + SWEEP_STEP * study_index

    return overrides


def configure_run(base):
    configure_three_particle_horizontal(base)
    if DT is not None:
        base.dt = float(DT)
    if SUBSTEPS is not None:
        base.substeps = int(SUBSTEPS)
    if BASE_MODEL == "mom" and hasattr(base, "set_momentum_response"):
        base.set_momentum_response(REPULSION_FORCE_PER_AREA)
    if BASE_MODEL == "mom" and hasattr(base, "set_multi_contact_mode"):
        base.set_multi_contact_mode(MULTI_CONTACT_MODE)
    base.set_collision_step_limit(MIN_COLLISION_STEPS)
    base.set_speed_limit_enforcement(ENFORCE_SPEED_LIMIT)
    for index, overrides in BASE_PARTICLE_OVERRIDES.items():
        base.particle_configs[index].update(overrides)
    for index, overrides in PARTICLE_OVERRIDES.items():
        base.particle_configs[index].update(overrides)


if __name__ == "__main__":
    from base.gPCD import Demo

    base_class = resolve_base_class(BASE_MODEL)

    for ii in particle_list:
        sweep_value = SWEEP_START + ii * SWEEP_STEP
        particle_overrides = {
            index: dict(overrides)
            for index, overrides in BASE_PARTICLE_OVERRIDES.items()
        }
        for index, overrides in build_study_particle_overrides(ii, sweep_value).items():
            if index not in particle_overrides:
                particle_overrides[index] = {}
            particle_overrides[index].update(overrides)

        print(
            f"Running three-particle study {ii} with particle {SWEEP_PARTICLE_INDEX} "
            f"{SWEEP_AXIS}={sweep_value:.3f}"
        )
        export_data_file = export_path_for_dt(f"tph_{ii}.csv", DT, output_dir_name=OUTPUT_DIR_NAME)

        def configure_sweep_run(base):
            configure_three_particle_horizontal(base)
            if DT is not None:
                base.dt = float(DT)
            if SUBSTEPS is not None:
                base.substeps = int(SUBSTEPS)
            if BASE_MODEL == "mom" and hasattr(base, "set_momentum_response"):
                base.set_momentum_response(REPULSION_FORCE_PER_AREA)
            if BASE_MODEL == "mom" and hasattr(base, "set_multi_contact_mode"):
                base.set_multi_contact_mode(MULTI_CONTACT_MODE)
            base.set_collision_step_limit(MIN_COLLISION_STEPS)
            base.set_speed_limit_enforcement(ENFORCE_SPEED_LIMIT)
            for index, overrides in particle_overrides.items():
                base.particle_configs[index].update(overrides)
            for index, overrides in PARTICLE_OVERRIDES.items():
                base.particle_configs[index].update(overrides)

        Demo(
            configure_sweep_run,
            export_data_file=export_data_file,
            base_class=base_class,
        ).run()
