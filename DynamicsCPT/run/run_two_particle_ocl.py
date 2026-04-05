from base.scenarios import configure_two_particle_ocl
import csv
from pathlib import Path
from run.output_dirs import export_path_for_dt, resolve_base_class

BASE_MODEL = "mom"
MULTI_CONTACT_MODE = "sum"
OUTPUT_DIR_NAME = None
DT = 0.005
SUBSTEPS = 5
Y_START = 0.0
Y_STEP = 0.05
RUN_COUNT = 40
REPULSION_FORCE_PER_AREA = 0.001
MIN_COLLISION_STEPS = 24
ENFORCE_SPEED_LIMIT = True
particle_list = list(range(40))
#particle_list = [0,10]

def write_no_collision_export(export_data_file, y_value):
    export_path = Path(export_data_file)
    if not export_path.is_absolute():
        export_path = Path(__file__).resolve().parents[1] / export_path
    export_path.parent.mkdir(parents=True, exist_ok=True)

    closest_approach_time = 2.0
    trace_row = {
        "time": closest_approach_time,
        "sub_dt": 0.0,
        "phase": "no_collision",
        "collision_started": 0,
        "rebound_mode": 0,
        "active_contact_count": 0,
        "pair_contact_count": 0,
        "wall_contact_count": 0,
        "bond_contact_count": 0,
        "current_area": 0.0,
        "current_J": 0.0,
        "max_area_in": 0.0,
        "max_area_out": 0.0,
        "max_J_in": 0.0,
        "max_J_out": 0.0,
        "step_turn_area": 0.0,
        "step_max_turn_area": 0.0,
        "step_max_turn_sweep": 0.0,
        "p0_x": 0.0,
        "p0_y": 0.0,
        "p0_vx": -1.0,
        "p0_vy": 0.0,
        "p0_px": -1.0,
        "p0_py": 0.0,
        "p0_internal_p": 0.0,
        "p0_radius": 1.0,
        "p0_mass": 1.0,
        "p1_x": 0.0,
        "p1_y": y_value,
        "p1_vx": 1.0,
        "p1_vy": 0.0,
        "p1_px": 1.0,
        "p1_py": 0.0,
        "p1_internal_p": 0.0,
        "p1_radius": 1.0,
        "p1_mass": 1.0,
        "p2_x": "",
        "p2_y": "",
        "p2_vx": "",
        "p2_vy": "",
        "p2_px": "",
        "p2_py": "",
        "p2_internal_p": "",
        "p2_radius": "",
        "p2_mass": "",
        "p3_x": "",
        "p3_y": "",
        "p3_vx": "",
        "p3_vy": "",
        "p3_px": "",
        "p3_py": "",
        "p3_internal_p": "",
        "p3_radius": "",
        "p3_mass": "",
        "bookkeeping_internal": 0.0,
    }

    with export_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trace_row.keys()))
        writer.writeheader()
        writer.writerow(trace_row)

    summary_path = export_path.with_name(f"{export_path.stem}_summary{export_path.suffix}")
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        writer.writerow(["collision status", "no collision"])
        writer.writerow(["reason", "tangent_or_miss"])
        writer.writerow(["particle 00 init pos", "(2.00000000, 0.00000000)"])
        writer.writerow(["particle 01 init pos", f"(-2.00000000, {y_value:.8f})"])
        writer.writerow(["closest approach time", f"{closest_approach_time:.8f}"])
        writer.writerow(["closest approach distance", f"{y_value:.8f}"])
        writer.writerow(["sum turn area", "0.00000000"])
        writer.writerow(["max turn area", "0.00000000"])
        writer.writerow(["max turn sweep", "0.00000000"])

if __name__ == "__main__":
    from base.gPCD import Demo
    base_class = resolve_base_class(BASE_MODEL)
    
    for ii in particle_list:
        y_value = Y_START + ii * Y_STEP
        particle_overrides = {
            0: {"x": 1.1, "y": 0.0, "vx": -0.1, "vy": 0.0, "repulsion_force_per_area": REPULSION_FORCE_PER_AREA},
            1: {"x": -1.1, "y": y_value, "vx": 0.1, "vy": 0.0, "repulsion_force_per_area": REPULSION_FORCE_PER_AREA},
            
        }
        print(f"Running simulation with particle 1 at y={y_value:.2f}")
        export_data_file = export_path_for_dt(f"tpocl_{ii}.csv", DT, output_dir_name=OUTPUT_DIR_NAME)

        if y_value >= 2.0:
            print("No positive-overlap collision for this study; writing zero-area export instead.")
            write_no_collision_export(export_data_file, y_value)
            continue

        def configure_run(base):
            configure_two_particle_ocl(base)
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

        Demo(configure_run, export_data_file=export_data_file, base_class=base_class).run()
