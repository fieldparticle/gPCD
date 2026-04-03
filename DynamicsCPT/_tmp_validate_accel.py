from base.scenarios import build_base, configure_two_particle_horizontal, configure_three_particle_horizontal
for name, configure in [("two_particle_horizontal", configure_two_particle_horizontal), ("three_particle_horizontal", configure_three_particle_horizontal)]:
    base = build_base(configure)
    steps = 0
    sub_dt = base.dt / base.substeps
    while steps < 40000:
        for _ in range(base.substeps):
            base.do_substep(sub_dt)
        base.time += base.dt
        steps += 1
        if base.collision_complete:
            break
    print(name)
    print(f"  collision_complete={base.collision_complete}")
    print(f"  scalar_error={(base.total_scalar_momentum_with_internal() - base.initial_abs_momentum_sum()):.12g}")
    print(f"  internal_total={base.total_internal_momentum():.12g}")
