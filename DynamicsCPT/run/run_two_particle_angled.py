from base.scenarios import configure_two_particle_angled

PARTICLE_OVERRIDES = {
    # Example:
    # 0: {"x": -2.15, "y": 2.0, "vx": 0.5, "vy": -0.5},
    # 1: {"x": -1.0, "y": -1.0, "vx": -0.5, "vy": 0.5},
}
EXPORT_DATA_FILE = "two_particle_angled_collision_data.csv"


def configure_run(base):
    configure_two_particle_angled(base)
    for index, overrides in PARTICLE_OVERRIDES.items():
        base.particle_configs[index].update(overrides)


if __name__ == "__main__":
    from base.gPCD import Demo

    Demo(configure_run, export_data_file=EXPORT_DATA_FILE).run()
