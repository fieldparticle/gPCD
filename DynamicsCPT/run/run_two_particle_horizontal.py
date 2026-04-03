from base.scenarios import configure_two_particle_horizontal

PARTICLE_OVERRIDES = {
    # Example:
    # 0: {"x": -2.0, "y": 0.0, "vx": 1.0, "vy": 0.0, "mass": 1.0, "radius": 1.0},
    # 1: {"repulsion_accel_per_area": 8.0},
}
EXPORT_DATA_FILE = "two_particle_horizontal_collision_data.csv"


def configure_run(base):
    configure_two_particle_horizontal(base)
    for index, overrides in PARTICLE_OVERRIDES.items():
        base.particle_configs[index].update(overrides)


if __name__ == "__main__":
    from base.gPCD import Demo

    Demo(configure_run, export_data_file=EXPORT_DATA_FILE).run()
