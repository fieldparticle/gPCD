import math

from base.Base import Base as _Base


class AccelBase(_Base):
    """Acceleration-form collision integrator with per-particle writeback."""

    def __init__(self):
        super().__init__()
        self.default_accel_per_area = self.k
        self.rejection_accel_per_area = self.default_accel_per_area
        self.contact_refine_steps = 1
        self.release_fraction_per_substep = 0.35
        self.release_fraction_non_turning = 0.18
        self.bookkeeping_release_fraction = 0.25
        self.pair_contact_memory = {}
        self.wall_contact_memory = {}
        self.pair_internal_store = {}
        self.bookkeeping_internal = 0.0
        self.free_flight_settle_steps = 0
        self.stalled_settle_steps = 0
        self.last_settle_measure = None
        self.reset_contact_sampling_stats()

    def set_contact_response(self, force_per_area=None, accel_per_area=None):
        super().set_contact_response(force_per_area=force_per_area, accel_per_area=accel_per_area)
        if force_per_area is not None and accel_per_area is None:
            self.default_accel_per_area = None
        elif accel_per_area is not None:
            self.default_accel_per_area = float(accel_per_area)

    def reset(self):
        super().reset()
        self.pair_contact_memory = {}
        self.wall_contact_memory = {}
        self.pair_internal_store = {}
        self.bookkeeping_internal = 0.0
        self.free_flight_settle_steps = 0
        self.stalled_settle_steps = 0
        self.last_settle_measure = None
        self.reset_contact_sampling_stats()
        for particle in self.particles:
            particle["internal_direct"] = 0.0
            particle["internal_momentum"] = 0.0

    def build_collision_trace_row(self, sub_dt, extra=None):
        row = super().build_collision_trace_row(sub_dt, extra=extra)
        row["bookkeeping_internal"] = self.bookkeeping_internal
        row["free_flight_settle_steps"] = self.free_flight_settle_steps
        return row

    def reset_contact_sampling_stats(self):
        self.area_sum_in = 0.0
        self.area_sum_out = 0.0
        self.area_time_sum_in = 0.0
        self.area_time_sum_out = 0.0
        self.J_sum_in = 0.0
        self.J_sum_out = 0.0
        self.contact_samples_in = 0
        self.contact_samples_out = 0

    def bookkeeping_completion_tolerance(self):
        return max(1.0e-11, 10.0 * self.internal_momentum_tolerance)

    def bookkeeping_force_finalize_tolerance(self):
        return max(1.0e-9, 1000.0 * self.internal_momentum_tolerance)

    def sync_particle_internal_display(self):
        for particle in self.particles:
            particle["internal_momentum"] = particle.get("internal_direct", 0.0)
        for (i, j), value in self.pair_internal_store.items():
            half_value = 0.5 * value
            self.particles[i]["internal_momentum"] += half_value
            self.particles[j]["internal_momentum"] += half_value
        if self.particles and abs(self.bookkeeping_internal) > self.internal_momentum_tolerance:
            share = self.bookkeeping_internal / len(self.particles)
            for particle in self.particles:
                particle["internal_momentum"] += share

    def contact_force_from_area(self, area_geom, mass_i, mass_j=None):
        if mass_j is None:
            if self.rejection_accel_per_area is None:
                return self.k * area_geom
            return mass_i * self.rejection_accel_per_area * area_geom

        if self.rejection_accel_per_area is None:
            return self.k * area_geom

        total_mass = mass_i + mass_j
        if total_mass <= 0.0:
            raise ValueError("Particle contact requires positive total mass.")
        reduced_mass = (mass_i * mass_j) / total_mass
        return reduced_mass * self.rejection_accel_per_area * area_geom

    def elastic_pair_event_impulse(self, state_i, state_j, nx, ny):
        vix = state_i["px"] / state_i["mass"]
        viy = state_i["py"] / state_i["mass"]
        vjx = state_j["px"] / state_j["mass"]
        vjy = state_j["py"] / state_j["mass"]
        rel_vn = (vjx - vix) * nx + (vjy - viy) * ny
        if rel_vn >= 0.0:
            return 0.0
        inv_mass_sum = (1.0 / state_i["mass"]) + (1.0 / state_j["mass"])
        if inv_mass_sum <= 0.0:
            return 0.0
        return -(2.0 * rel_vn) / inv_mass_sum

    def elastic_wall_event_impulse(self, state, nx, ny):
        vx = state["px"] / state["mass"]
        vy = state["py"] / state["mass"]
        rel_vn = vx * nx + vy * ny
        if rel_vn >= 0.0:
            return 0.0
        return -2.0 * state["mass"] * rel_vn

    def particle_state_after_impulse(self, particle_state, nx, ny, J):
        return (
            particle_state["px"] + nx * J,
            particle_state["py"] + ny * J,
        )

    def scalar_change_for_pair_impulse(self, state_i, state_j, nx, ny, J):
        before = math.hypot(
            state_i["px"] / state_i["mass"],
            state_i["py"] / state_i["mass"],
        ) + math.hypot(
            state_j["px"] / state_j["mass"],
            state_j["py"] / state_j["mass"],
        )
        after_i_px, after_i_py = self.particle_state_after_impulse(state_i, nx, ny, -J)
        after_j_px, after_j_py = self.particle_state_after_impulse(state_j, nx, ny, J)
        after = math.hypot(
            after_i_px / state_i["mass"],
            after_i_py / state_i["mass"],
        ) + math.hypot(
            after_j_px / state_j["mass"],
            after_j_py / state_j["mass"],
        )
        return after - before

    def scalar_change_for_wall_impulse(self, particle_state, nx, ny, J):
        before = math.hypot(
            particle_state["px"] / particle_state["mass"],
            particle_state["py"] / particle_state["mass"],
        )
        after_px, after_py = self.particle_state_after_impulse(particle_state, nx, ny, J)
        after = math.hypot(
            after_px / particle_state["mass"],
            after_py / particle_state["mass"],
        )
        return after - before

    def total_abs_momentum_sum(self):
        total_abs_v = 0.0
        for particle in self.particles:
            total_abs_v += math.hypot(
                particle["px"] / particle["mass"],
                particle["py"] / particle["mass"],
            )
        return total_abs_v

    def initial_abs_momentum_sum(self):
        total_abs_v = 0.0
        for particle in self.particles:
            total_abs_v += math.hypot(particle["init_vx"], particle["init_vy"])
        return total_abs_v

    def total_internal_momentum(self):
        total = self.bookkeeping_internal + sum(self.pair_internal_store.values())
        for particle in self.particles:
            total += particle.get("internal_direct", 0.0)
        return total

    def normalize_internal_momentum(self):
        for key, value in list(self.pair_internal_store.items()):
            if abs(value) <= self.internal_momentum_tolerance:
                del self.pair_internal_store[key]
        for particle in self.particles:
            if abs(particle.get("internal_direct", 0.0)) <= self.internal_momentum_tolerance:
                particle["internal_direct"] = 0.0
        if abs(self.bookkeeping_internal) <= self.internal_momentum_tolerance:
            self.bookkeeping_internal = 0.0
        self.sync_particle_internal_display()

    def update_internal_momentum(self, particle, abs_v_before):
        abs_v_after = math.hypot(
            particle["px"] / particle["mass"],
            particle["py"] / particle["mass"],
        )
        particle["internal_direct"] = particle.get("internal_direct", 0.0) + (abs_v_before - abs_v_after)
        if abs(particle["internal_direct"]) <= self.internal_momentum_tolerance:
            particle["internal_direct"] = 0.0
        self.sync_particle_internal_display()

    def record_contact_sample(self, rel_vn, area_geom, applied_J, sub_dt):
        if rel_vn < 0.0:
            self.contact_samples_in += 1
            self.area_sum_in += area_geom
            self.area_time_sum_in += area_geom * sub_dt
            self.J_sum_in += applied_J
        else:
            self.contact_samples_out += 1
            self.area_sum_out += area_geom
            self.area_time_sum_out += area_geom * sub_dt
            self.J_sum_out += applied_J

    def release_bookkeeping_internal(self):
        if abs(self.bookkeeping_internal) <= self.internal_momentum_tolerance:
            self.bookkeeping_internal = 0.0
            return

        moving_particles = []
        for index, particle in enumerate(self.particles):
            vx = particle["px"] / particle["mass"]
            vy = particle["py"] / particle["mass"]
            speed = math.hypot(vx, vy)
            if speed > 1.0e-12:
                moving_particles.append((index, vx, vy, speed))

        if not moving_particles:
            return

        target_scalar = self.bookkeeping_internal * self.bookkeeping_release_fraction
        remaining = target_scalar
        released_total = 0.0
        for offset, (index, vx, vy, speed) in enumerate(moving_particles):
            particles_left = len(moving_particles) - offset
            target_share = remaining / particles_left
            applied_share = math.copysign(min(abs(target_share), speed), target_share)
            if abs(applied_share) <= self.internal_momentum_tolerance:
                continue
            ux = vx / speed
            uy = vy / speed
            particle = self.particles[index]
            particle["px"] += particle["mass"] * applied_share * ux
            particle["py"] += particle["mass"] * applied_share * uy
            released_total += applied_share
            remaining -= applied_share

        self.bookkeeping_internal -= released_total
        if abs(self.bookkeeping_internal) <= self.bookkeeping_completion_tolerance():
            self.bookkeeping_internal = 0.0

    def build_final_report_lines(self):
        lines = super().build_final_report_lines()
        extra_lines = [
            f"contact samples in    = {self.contact_samples_in}",
            f"contact samples out   = {self.contact_samples_out}",
            f"sum area in           = {self.area_sum_in:.8f}",
            f"sum area out          = {self.area_sum_out:.8f}",
            f"sum area*time in      = {self.area_time_sum_in:.8f}",
            f"sum area*time out     = {self.area_time_sum_out:.8f}",
            f"sum J in              = {self.J_sum_in:.8e}",
            f"sum J out             = {self.J_sum_out:.8e}",
        ]
        return lines[:-1] + extra_lines + [lines[-1]]

    def snapshot_particle(self, particle):
        return {
            "x": particle["x"],
            "y": particle["y"],
            "px": particle["px"],
            "py": particle["py"],
            "mass": particle["mass"],
            "radius": particle["radius"],
            "internal_momentum": particle["internal_momentum"],
        }

    def turn_sweep(self, prev_nx, prev_ny, nx, ny):
        dot = max(-1.0, min(1.0, prev_nx * nx + prev_ny * ny))
        cross = prev_nx * ny - prev_ny * nx
        return abs(math.atan2(cross, dot))

    def blended_contact_direction(self, prev_nx, prev_ny, nx, ny):
        blend_x = prev_nx + nx
        blend_y = prev_ny + ny
        mag = math.hypot(blend_x, blend_y)
        if mag <= 1.0e-12:
            return nx, ny
        return blend_x / mag, blend_y / mag

    def equal_radius_turn_area(self, radius, d_mid, delta_theta):
        d_mid = max(0.0, min(2.0 * radius, d_mid))
        chord_half_sq = max(0.0, radius * radius - 0.25 * d_mid * d_mid)
        return d_mid * math.sqrt(chord_half_sq) * abs(delta_theta)

    def release_fraction_for_turn(self, turn_sweep):
        turn_scale = min(1.0, abs(turn_sweep) / 0.20)
        return self.release_fraction_non_turning + (
            self.release_fraction_per_substep - self.release_fraction_non_turning
        ) * turn_scale

    def pair_transfer_effect(self, state_i, state_j, nx, ny, internal_i, internal_j, release_cap_i, release_cap_j, release_fraction):
        pair_internal = internal_i + internal_j
        if abs(pair_internal) <= self.internal_momentum_tolerance:
            return 0.0, 0.0, 0.0, 0.0, 0.0

        paced_cap = max(0.0, release_fraction) * (max(0.0, release_cap_i) + max(0.0, release_cap_j))
        target_release = math.copysign(
            min(abs(pair_internal), paced_cap),
            pair_internal,
        )
        if abs(target_release) <= self.internal_momentum_tolerance:
            return 0.0, 0.0, 0.0, 0.0, 0.0

        J = self.solve_impulse_for_scalar_target(
            lambda impulse: self.scalar_change_for_pair_impulse(state_i, state_j, nx, ny, impulse),
            target_release,
        )
        if abs(J) <= 1.0e-15:
            return 0.0, 0.0, 0.0, 0.0, 0.0

        released = self.scalar_change_for_pair_impulse(state_i, state_j, nx, ny, J)
        if abs(released) <= self.internal_momentum_tolerance:
            return 0.0, 0.0, 0.0, 0.0, 0.0

        return -nx * J, -ny * J, nx * J, ny * J, released

    def solve_coupled_pair_releases(self, snapshot, pair_contact_px, pair_contact_py, pair_contact_requests, pair_internal_delta):
        if not pair_contact_requests:
            return [0.0] * len(self.particles), [0.0] * len(self.particles), pair_internal_delta

        working_px = []
        working_py = []
        for index, state in enumerate(snapshot):
            working_px.append(state["px"] + pair_contact_px[index])
            working_py.append(state["py"] + pair_contact_py[index])

        release_delta_px = [0.0] * len(self.particles)
        release_delta_py = [0.0] * len(self.particles)

        outbound_requests = [request for request in pair_contact_requests if request["rel_vn"] >= 0.0]
        if not outbound_requests:
            return release_delta_px, release_delta_py, pair_internal_delta

        remaining_pair_internal = {}
        for request in outbound_requests:
            pair_key = request["pair_key"]
            if pair_key not in remaining_pair_internal:
                remaining_pair_internal[pair_key] = self.pair_internal_store.get(pair_key, 0.0) + pair_internal_delta.get(pair_key, 0.0)

        remaining_particle_budget = [0.0] * len(self.particles)
        remaining_request_cap_i = {}
        remaining_request_cap_j = {}
        for request in outbound_requests:
            request_id = id(request)
            remaining_request_cap_i[request_id] = max(0.0, request["cap_i"])
            remaining_request_cap_j[request_id] = max(0.0, request["cap_j"])
            remaining_particle_budget[request["i"]] += max(0.0, request["cap_i"])
            remaining_particle_budget[request["j"]] += max(0.0, request["cap_j"])

        ordered_requests = sorted(outbound_requests, key=lambda request: request["weight"], reverse=True)

        for _ in range(6):
            progress = False
            for request in ordered_requests:
                pair_key = request["pair_key"]
                pair_internal_value = remaining_pair_internal.get(pair_key, 0.0)
                if abs(pair_internal_value) <= self.internal_momentum_tolerance:
                    continue

                i = request["i"]
                j = request["j"]
                request_id = id(request)
                cap_i = min(remaining_particle_budget[i], remaining_request_cap_i[request_id])
                cap_j = min(remaining_particle_budget[j], remaining_request_cap_j[request_id])
                if cap_i <= self.internal_momentum_tolerance and cap_j <= self.internal_momentum_tolerance:
                    continue

                before_speed_i = math.hypot(working_px[i] / snapshot[i]["mass"], working_py[i] / snapshot[i]["mass"])
                before_speed_j = math.hypot(working_px[j] / snapshot[j]["mass"], working_py[j] / snapshot[j]["mass"])
                (
                    transfer_dpx_i,
                    transfer_dpy_i,
                    transfer_dpx_j,
                    transfer_dpy_j,
                    released_pair_internal,
                ) = self.pair_transfer_effect(
                    {"px": working_px[i], "py": working_py[i], "mass": snapshot[i]["mass"]},
                    {"px": working_px[j], "py": working_py[j], "mass": snapshot[j]["mass"]},
                    request["release_nx"],
                    request["release_ny"],
                    0.5 * pair_internal_value,
                    0.5 * pair_internal_value,
                    cap_i,
                    cap_j,
                    request["release_fraction"],
                )
                if abs(released_pair_internal) <= self.internal_momentum_tolerance:
                    continue

                working_px[i] += transfer_dpx_i
                working_py[i] += transfer_dpy_i
                working_px[j] += transfer_dpx_j
                working_py[j] += transfer_dpy_j
                release_delta_px[i] += transfer_dpx_i
                release_delta_py[i] += transfer_dpy_i
                release_delta_px[j] += transfer_dpx_j
                release_delta_py[j] += transfer_dpy_j
                remaining_pair_internal[pair_key] = pair_internal_value - released_pair_internal

                after_speed_i = math.hypot(working_px[i] / snapshot[i]["mass"], working_py[i] / snapshot[i]["mass"])
                after_speed_j = math.hypot(working_px[j] / snapshot[j]["mass"], working_py[j] / snapshot[j]["mass"])
                spent_i = max(0.0, after_speed_i - before_speed_i)
                spent_j = max(0.0, after_speed_j - before_speed_j)
                remaining_particle_budget[i] = max(0.0, remaining_particle_budget[i] - spent_i)
                remaining_particle_budget[j] = max(0.0, remaining_particle_budget[j] - spent_j)
                remaining_request_cap_i[request_id] = max(0.0, remaining_request_cap_i[request_id] - spent_i)
                remaining_request_cap_j[request_id] = max(0.0, remaining_request_cap_j[request_id] - spent_j)
                progress = True

            if not progress:
                break

        updated_pair_internal_delta = dict(pair_internal_delta)
        for pair_key, remaining_value in remaining_pair_internal.items():
            updated_pair_internal_delta[pair_key] = remaining_value - self.pair_internal_store.get(pair_key, 0.0)

        return release_delta_px, release_delta_py, updated_pair_internal_delta

    def wall_transfer_effect(self, particle_state, nx, ny, internal_value, release_cap, release_fraction):
        if abs(internal_value) <= self.internal_momentum_tolerance:
            return 0.0, 0.0, 0.0
        release = math.copysign(
            min(abs(internal_value), max(0.0, release_fraction) * max(0.0, release_cap)),
            internal_value,
        )
        if abs(release) <= self.internal_momentum_tolerance:
            return 0.0, 0.0, 0.0
        dpx = particle_state["mass"] * release * nx
        dpy = particle_state["mass"] * release * ny
        return dpx, dpy, -release

    def do_substep(self, sub_dt):
        contacts = self.get_contacts()
        wall_contacts = self.get_wall_contacts()
        bond_interactions = self.get_bond_interactions()
        self.active_pair_contact_count = len(contacts)
        self.active_wall_contact_count = len(wall_contacts)
        self.active_bond_contact_count = len(bond_interactions)
        self.active_contact_count = len(contacts) + len(wall_contacts) + len(bond_interactions)
        active_pair_keys = set()
        active_wall_keys = set()

        if self.active_contact_count == 0:
            self.release_bookkeeping_internal()
            self.normalize_internal_momentum()
            self.free_flight_settle_steps += 1
            settle_measure = abs(self.bookkeeping_internal)
            if self.last_settle_measure is not None and abs(settle_measure - self.last_settle_measure) <= 1.0e-15:
                self.stalled_settle_steps += 1
            else:
                self.stalled_settle_steps = 0
            self.last_settle_measure = settle_measure

            if (
                self.collision_started
                and not self.final_report_printed
                and (
                    abs(self.bookkeeping_internal) <= self.bookkeeping_completion_tolerance()
                    or (
                        self.free_flight_settle_steps >= 240
                        and settle_measure <= self.bookkeeping_force_finalize_tolerance()
                    )
                    or self.stalled_settle_steps >= 120
                )
            ):
                if abs(self.bookkeeping_internal) <= self.bookkeeping_force_finalize_tolerance():
                    self.bookkeeping_internal = 0.0
                self.normalize_internal_momentum()
                self.final_report_lines = self.build_final_report_lines()
                self.final_report_printed = True
                self.collision_complete = True

            for particle in self.particles:
                vx = particle["px"] / particle["mass"]
                vy = particle["py"] / particle["mass"]
                particle["x"] += vx * sub_dt
                particle["y"] += vy * sub_dt
            if self.trace_contact_active:
                self.record_collision_trace(
                    sub_dt,
                    extra={
                        "phase": "free",
                        "active_contact_count": 0,
                        "pair_contact_count": 0,
                        "wall_contact_count": 0,
                        "bond_contact_count": 0,
                        "current_area": 0.0,
                        "current_J": 0.0,
                        "step_max_turn_sweep": 0.0,
                    },
                )
                self.trace_contact_active = False
            self.clear_contact_history()
            self.advance_trace_time(sub_dt)
            return

        self.collision_started = True
        self.trace_contact_active = True
        self.free_flight_settle_steps = 0
        self.stalled_settle_steps = 0
        self.last_settle_measure = None
        self.current_area = 0.0
        self.current_J = 0.0
        self.phase = "outbound"
        self.rebound_mode = False

        snapshot = [self.snapshot_particle(particle) for particle in self.particles]
        delta_px = [0.0] * len(self.particles)
        delta_py = [0.0] * len(self.particles)

        for i, j, nx, ny, d, rest_distance, extension in bond_interactions:
            state_i = snapshot[i]
            state_j = snapshot[j]
            vix = state_i["px"] / state_i["mass"]
            viy = state_i["py"] / state_i["mass"]
            vjx = state_j["px"] / state_j["mass"]
            vjy = state_j["py"] / state_j["mass"]
            rel_vn = (vjx - vix) * nx + (vjy - viy) * ny

            spring_force = self.bond_settings["stiffness"] * extension
            spring_J = -spring_force * sub_dt
            delta_px[i] += -nx * spring_J
            delta_py[i] += -ny * spring_J
            delta_px[j] += nx * spring_J
            delta_py[j] += ny * spring_J

            damping_force = self.bond_settings["damping"] * rel_vn
            damping_J = -damping_force * sub_dt
            delta_px[i] += -nx * damping_J
            delta_py[i] += -ny * damping_J
            delta_px[j] += nx * damping_J
            delta_py[j] += ny * damping_J

        pair_requests = []
        wall_requests = []
        incident_weight_totals = [0.0] * len(self.particles)
        step_max_turn_sweep = 0.0

        for i, j, contact in contacts:
            if self.is_deep_bond_pair(i, j):
                continue
            pair_key = (min(i, j), max(i, j))
            self.activated_bond_pairs.add(pair_key)
            active_pair_keys.add(pair_key)
            nx, ny, alpha, delta, area_geom, area_pcnt, proxPercent, d = contact
            state_i = snapshot[i]
            state_j = snapshot[j]
            vix = state_i["px"] / state_i["mass"]
            viy = state_i["py"] / state_i["mass"]
            vjx = state_j["px"] / state_j["mass"]
            vjy = state_j["py"] / state_j["mass"]
            rel_vn = (vjx - vix) * nx + (vjy - viy) * ny

            force_mag = self.contact_force_from_area(area_geom, state_i["mass"], state_j["mass"])
            equivalent_J = force_mag * sub_dt

            prev_contact = self.pair_contact_memory.get(pair_key)
            turn_sweep = 0.0
            if prev_contact is not None:
                prev_nx, prev_ny, prev_area, prev_d = prev_contact
                turn_sweep = self.turn_sweep(prev_nx, prev_ny, nx, ny)
            self.pair_contact_memory[pair_key] = (nx, ny, area_geom, d)
            step_max_turn_sweep = max(step_max_turn_sweep, turn_sweep)

            request_weight = max(equivalent_J, 1.0e-12)
            pair_requests.append(
                {
                    "i": i,
                    "j": j,
                    "nx": nx,
                    "ny": ny,
                    "area_geom": area_geom,
                    "equivalent_J": equivalent_J,
                    "rel_vn": rel_vn,
                    "weight": request_weight,
                    "turn_sweep": turn_sweep,
                }
            )
            incident_weight_totals[i] += request_weight
            incident_weight_totals[j] += request_weight

        for i, wall_name, contact in wall_contacts:
            wall_key = (i, wall_name)
            active_wall_keys.add(wall_key)
            nx, ny, alpha, delta, area_geom, area_pcnt, proxPercent, d = contact
            state = snapshot[i]
            vx = state["px"] / state["mass"]
            vy = state["py"] / state["mass"]
            rel_vn = vx * nx + vy * ny

            force_mag = self.contact_force_from_area(area_geom, state["mass"])
            equivalent_J = force_mag * sub_dt

            prev_contact = self.wall_contact_memory.get(wall_key)
            if prev_contact is not None:
                prev_nx, prev_ny, prev_area, prev_d = prev_contact
            self.wall_contact_memory[wall_key] = (nx, ny, area_geom, d)
            request_weight = max(equivalent_J, 1.0e-12)
            wall_requests.append(
                {
                    "i": i,
                    "nx": nx,
                    "ny": ny,
                    "area_geom": area_geom,
                    "equivalent_J": equivalent_J,
                    "rel_vn": rel_vn,
                    "weight": request_weight,
                }
            )
            incident_weight_totals[i] += request_weight

        for request in pair_requests:
            i = request["i"]
            j = request["j"]
            share_i = request["weight"] / max(incident_weight_totals[i], request["weight"])
            share_j = request["weight"] / max(incident_weight_totals[j], request["weight"])
            contact_scale = 0.5 * (share_i + share_j)
            scaled_J = request["equivalent_J"] * contact_scale

            self.current_area = max(self.current_area, request["area_geom"])
            self.current_J = max(self.current_J, scaled_J)
            if request["rel_vn"] < 0.0:
                self.phase = "inbound"
                self.max_area_in = max(self.max_area_in, request["area_geom"])
                self.max_J_in = max(self.max_J_in, scaled_J)
            else:
                self.max_area_out = max(self.max_area_out, request["area_geom"])
                self.max_J_out = max(self.max_J_out, scaled_J)
                self.rebound_mode = True

            self.record_contact_sample(request["rel_vn"], request["area_geom"], scaled_J, sub_dt)
            delta_px[i] += -request["nx"] * scaled_J
            delta_py[i] += -request["ny"] * scaled_J
            delta_px[j] += request["nx"] * scaled_J
            delta_py[j] += request["ny"] * scaled_J

        for request in wall_requests:
            i = request["i"]
            share_i = request["weight"] / max(incident_weight_totals[i], request["weight"])
            scaled_J = request["equivalent_J"] * share_i

            self.current_area = max(self.current_area, request["area_geom"])
            self.current_J = max(self.current_J, scaled_J)
            if request["rel_vn"] < 0.0:
                self.phase = "inbound"
                self.max_area_in = max(self.max_area_in, request["area_geom"])
                self.max_J_in = max(self.max_J_in, scaled_J)
            else:
                self.max_area_out = max(self.max_area_out, request["area_geom"])
                self.max_J_out = max(self.max_J_out, scaled_J)
                self.rebound_mode = True

            self.record_contact_sample(request["rel_vn"], request["area_geom"], scaled_J, sub_dt)
            delta_px[i] += request["nx"] * scaled_J
            delta_py[i] += request["ny"] * scaled_J

        scalar_before = 0.0
        scalar_after = 0.0
        for index, particle in enumerate(self.particles):
            scalar_before += math.hypot(
                snapshot[index]["px"] / snapshot[index]["mass"],
                snapshot[index]["py"] / snapshot[index]["mass"],
            )
            particle["px"] += delta_px[index]
            particle["py"] += delta_py[index]
            scalar_after += math.hypot(
                particle["px"] / particle["mass"],
                particle["py"] / particle["mass"],
            )
            vx = particle["px"] / particle["mass"]
            vy = particle["py"] / particle["mass"]
            particle["x"] += vx * sub_dt
            particle["y"] += vy * sub_dt
            particle["internal_direct"] = 0.0

        self.bookkeeping_internal += scalar_before - scalar_after

        self.pair_internal_store = {}

        self.sync_particle_internal_display()

        self.pair_contact_memory = {
            key: value
            for key, value in self.pair_contact_memory.items()
            if key in active_pair_keys
        }
        self.wall_contact_memory = {
            key: value
            for key, value in self.wall_contact_memory.items()
            if key in active_wall_keys
        }
        self.pair_internal_store = {
            key: value
            for key, value in self.pair_internal_store.items()
            if key in active_pair_keys or abs(value) > self.internal_momentum_tolerance
        }
        self.record_collision_trace(
            sub_dt,
            extra={
                "step_max_turn_sweep": step_max_turn_sweep,
            },
        )
        self.advance_trace_time(sub_dt)
