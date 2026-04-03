from base.scenarios import build_base, configure_two_particle_horizontal, configure_two_particle_angled, configure_three_particle_horizontal

scenarios = [
    ("two_particle_horizontal", configure_two_particle_horizontal),
    ("two_particle_angled", configure_two_particle_angled),
    ("three_particle_horizontal", configure_three_particle_horizontal),
]

for name, configure in scenarios:
    base = build_base(configure)
    steps = 0
    max_steps = 20000
    sub_dt = base.dt / base.substeps
    while steps < max_steps:
        for _ in range(base.substeps):
            base.do_substep(sub_dt)
        base.time += base.dt
        steps += 1
        if base.collision_started and base.active_contact_count == 0 and base.final_report_printed:
            break
    scalar_error = base.total_scalar_momentum_with_internal() - base.initial_abs_momentum_sum()
    momentum_x = sum(p["px"] for p in base.particles)
    momentum_y = sum(p["py"] for p in base.particles)
    print(name)
    print(f"  steps={steps}")
    print(f"  scalar_error={scalar_error:.12g}")
    print(f"  momentum=({momentum_x:.12g}, {momentum_y:.12g})")
    print(f"  internal_total={base.total_internal_momentum():.12g}")
    print(f"  pair_store={base.pair_internal_store}")
