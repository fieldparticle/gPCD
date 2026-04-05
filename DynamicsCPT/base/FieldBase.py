import math

from base.Base import Base as _Base


class FieldBase(_Base):
    """Field-overlap particle method with particles treated as field sources."""

    def __init__(self):
        super().__init__()
        self.default_accel_per_area = self.k
        self.rejection_accel_per_area = self.default_accel_per_area
        self.field_repulsion_accel_per_area = self.default_accel_per_area
        self.field_repulsion_force_per_area = None
        self.contact_refine_steps = 1
        self.release_fraction_per_substep = 0.35
        self.release_fraction_non_turning = 0.18
        self.pair_field_memory = {}
        self.wall_field_memory = {}
        self.pair_internal_store = {}
        self.bookkeeping_internal = 0.0
        self.bookkeeping_internal_x = 0.0
        self.bookkeeping_internal_y = 0.0
        self.reset_contact_sampling_stats()
        self.pair_contact_memory = self.pair_field_memory
        self.wall_contact_memory = self.wall_field_memory

    def set_contact_response(self, force_per_area=None, accel_per_area=None):
        super().set_contact_response(force_per_area=force_per_area, accel_per_area=accel_per_area)
        if force_per_area is not None and accel_per_area is None:
            self.default_accel_per_area = None
            self.field_repulsion_force_per_area = self.k
            self.field_repulsion_accel_per_area = None
        elif accel_per_area is not None:
            self.default_accel_per_area = float(accel_per_area)
            self.field_repulsion_accel_per_area = self.default_accel_per_area
            self.field_repulsion_force_per_area = None

    def add_particle(
        self,
        x,
        y,
        vx,
        vy,
        mass,
        radius,
        repulsion_force_per_area=None,
        repulsion_accel_per_area=None,
    ):
        super().add_particle(x=x, y=y, vx=vx, vy=vy, mass=mass, radius=radius)
        cfg = self.particle_configs[-1]
        if repulsion_force_per_area is not None and repulsion_accel_per_area is not None:
            raise ValueError("Specify either repulsion_force_per_area or repulsion_accel_per_area, not both.")
        if repulsion_force_per_area is not None:
            cfg["repulsion_force_per_area"] = float(repulsion_force_per_area)
            cfg["repulsion_accel_per_area"] = None
        elif repulsion_accel_per_area is not None:
            cfg["repulsion_force_per_area"] = None
            cfg["repulsion_accel_per_area"] = float(repulsion_accel_per_area)
        else:
            cfg["repulsion_force_per_area"] = self.field_repulsion_force_per_area
            cfg["repulsion_accel_per_area"] = self.field_repulsion_accel_per_area

    def reset(self):
        super().reset()
        self.pair_field_memory = {}
        self.wall_field_memory = {}
        self.pair_internal_store = {}
        self.bookkeeping_internal = 0.0
        self.bookkeeping_internal_x = 0.0
        self.bookkeeping_internal_y = 0.0
        self.sum_turn_area = 0.0
        self.max_turn_area = 0.0
        self.max_turn_sweep = 0.0
        self.reset_contact_sampling_stats()
        self.pair_contact_memory = self.pair_field_memory
        self.wall_contact_memory = self.wall_field_memory
        for particle, cfg in zip(self.particles, self.particle_configs):
            force_value = cfg.get("repulsion_force_per_area", self.field_repulsion_force_per_area)
            accel_value = cfg.get("repulsion_accel_per_area", self.field_repulsion_accel_per_area)
            # Overrides in run files often update only one mode after scenario setup.
            # If both are present, prefer the explicitly supplied force form.
            if force_value is not None and accel_value is not None:
                accel_value = None
            particle["internal_direct"] = 0.0
            particle["internal_direct_x"] = 0.0
            particle["internal_direct_y"] = 0.0
            particle["internal_momentum_x"] = 0.0
            particle["internal_momentum_y"] = 0.0
            particle["internal_momentum"] = 0.0
            particle["repulsion_force_per_area"] = force_value
            particle["repulsion_accel_per_area"] = accel_value

    def build_collision_trace_row(self, sub_dt, extra=None):
        row = super().build_collision_trace_row(sub_dt, extra=extra)
        row["bookkeeping_internal"] = self.bookkeeping_internal
        row["bookkeeping_internal_x"] = self.bookkeeping_internal_x
        row["bookkeeping_internal_y"] = self.bookkeeping_internal_y
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
        self.particle_area_sum_in = {}
        self.particle_area_sum_out = {}
        self.particle_samples_in = {}
        self.particle_samples_out = {}

    def resolve_pair_repulsion_coefficients(self, particle_i, particle_j):
        force_i = particle_i.get("repulsion_force_per_area")
        force_j = particle_j.get("repulsion_force_per_area")
        accel_i = particle_i.get("repulsion_accel_per_area")
        accel_j = particle_j.get("repulsion_accel_per_area")

        if accel_i is not None or accel_j is not None:
            accel_values = [value for value in (accel_i, accel_j) if value is not None]
            return None, sum(accel_values) / len(accel_values)

        force_values = [value for value in (force_i, force_j) if value is not None]
        if not force_values:
            return self.field_repulsion_force_per_area, self.field_repulsion_accel_per_area
        return sum(force_values) / len(force_values), None

    def resolve_wall_repulsion_coefficients(self, particle):
        force_value = particle.get("repulsion_force_per_area")
        accel_value = particle.get("repulsion_accel_per_area")
        if accel_value is not None:
            return None, accel_value
        return force_value, None

    def sync_particle_internal_display(self):
        for particle in self.particles:
            particle["internal_momentum_x"] = particle.get("internal_direct_x", 0.0)
            particle["internal_momentum_y"] = particle.get("internal_direct_y", 0.0)
        for (i, j), value in self.pair_internal_store.items():
            if isinstance(value, tuple):
                half_px = 0.5 * value[0]
                half_py = 0.5 * value[1]
            else:
                half_px = 0.5 * value
                half_py = 0.0
            self.particles[i]["internal_momentum_x"] += half_px
            self.particles[i]["internal_momentum_y"] += half_py
            self.particles[j]["internal_momentum_x"] += half_px
            self.particles[j]["internal_momentum_y"] += half_py
        for particle in self.particles:
            particle["internal_momentum"] = math.hypot(
                particle["internal_momentum_x"],
                particle["internal_momentum_y"],
            )

    def field_coupling_from_overlap(
        self,
        overlap_area,
        mass_i,
        mass_j=None,
        radius_i=None,
        radius_j=None,
        source_distance=None,
        delta=None,
        force_per_area=None,
        accel_per_area=None,
    ):
        del radius_i, radius_j, source_distance, delta
        if force_per_area is None and accel_per_area is None:
            force_per_area = self.field_repulsion_force_per_area
            accel_per_area = self.field_repulsion_accel_per_area
        if mass_j is None:
            if accel_per_area is None:
                return force_per_area * overlap_area
            return mass_i * accel_per_area * overlap_area

        if accel_per_area is None:
            return force_per_area * overlap_area

        total_mass = mass_i + mass_j
        if total_mass <= 0.0:
            raise ValueError("Field overlap requires positive total mass.")
        reduced_mass = (mass_i * mass_j) / total_mass
        return reduced_mass * accel_per_area * overlap_area

    def contact_force_from_area(self, area_geom, mass_i, mass_j=None):
        return self.field_coupling_from_overlap(area_geom, mass_i, mass_j)

    def field_contact_step_transfer(
        self,
        overlap_area,
        sub_dt,
        mass_i,
        mass_j=None,
        radius_i=None,
        radius_j=None,
        source_distance=None,
        delta=None,
        force_per_area=None,
        accel_per_area=None,
    ):
        coupling = self.field_coupling_from_overlap(
            overlap_area,
            mass_i,
            mass_j,
            radius_i=radius_i,
            radius_j=radius_j,
            source_distance=source_distance,
            delta=delta,
            force_per_area=force_per_area,
            accel_per_area=accel_per_area,
        )
        return coupling * sub_dt

    def pair_contact_request_scale(self, request, pair_requests):
        del request, pair_requests
        return 1.0

    def ordered_pair_requests(self, pair_requests):
        return pair_requests

    def get_particle_field_overlaps(self):
        return self.get_contacts()

    def get_wall_field_overlaps(self):
        return self.get_wall_contacts()

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

    def total_internal_momentum_vector(self):
        total_x = 0.0
        total_y = 0.0
        for value in self.pair_internal_store.values():
            if isinstance(value, tuple):
                total_x += value[0]
                total_y += value[1]
            else:
                total_x += value
        for particle in self.particles:
            total_x += particle.get("internal_direct_x", 0.0)
            total_y += particle.get("internal_direct_y", 0.0)
        return total_x, total_y

    def total_internal_momentum(self):
        total = 0.0
        for particle in self.particles:
            total += particle.get("internal_momentum", 0.0)
        return total

    def normalize_internal_momentum(self):
        for key, value in list(self.pair_internal_store.items()):
            magnitude = math.hypot(value[0], value[1]) if isinstance(value, tuple) else abs(value)
            if magnitude <= self.internal_momentum_tolerance:
                del self.pair_internal_store[key]
        for particle in self.particles:
            if math.hypot(
                particle.get("internal_direct_x", 0.0),
                particle.get("internal_direct_y", 0.0),
            ) <= self.internal_momentum_tolerance:
                particle["internal_direct"] = 0.0
                particle["internal_direct_x"] = 0.0
                particle["internal_direct_y"] = 0.0
        self.sync_particle_internal_display()

    def update_internal_momentum(self, particle, px_before, py_before):
        particle["internal_direct_x"] = particle.get("internal_direct_x", 0.0) + (px_before - particle["px"])
        particle["internal_direct_y"] = particle.get("internal_direct_y", 0.0) + (py_before - particle["py"])
        particle["internal_direct"] = math.hypot(
            particle["internal_direct_x"],
            particle["internal_direct_y"],
        )
        if abs(particle["internal_direct"]) <= self.internal_momentum_tolerance:
            particle["internal_direct"] = 0.0
            particle["internal_direct_x"] = 0.0
            particle["internal_direct_y"] = 0.0
        self.sync_particle_internal_display()

    def record_field_sample(self, rel_vn, overlap_area, applied_J, sub_dt, particle_indices=None):
        if rel_vn < 0.0:
            self.contact_samples_in += 1
            self.area_sum_in += overlap_area
            self.area_time_sum_in += overlap_area * sub_dt
            self.J_sum_in += applied_J
            if particle_indices is not None:
                for index in particle_indices:
                    self.particle_area_sum_in[index] = self.particle_area_sum_in.get(index, 0.0) + overlap_area
                    self.particle_samples_in[index] = self.particle_samples_in.get(index, 0) + 1
        else:
            self.contact_samples_out += 1
            self.area_sum_out += overlap_area
            self.area_time_sum_out += overlap_area * sub_dt
            self.J_sum_out += applied_J
            if particle_indices is not None:
                for index in particle_indices:
                    self.particle_area_sum_out[index] = self.particle_area_sum_out.get(index, 0.0) + overlap_area
                    self.particle_samples_out[index] = self.particle_samples_out.get(index, 0) + 1

    def record_contact_sample(self, rel_vn, area_geom, applied_J, sub_dt, particle_indices=None):
        self.record_field_sample(rel_vn, area_geom, applied_J, sub_dt, particle_indices=particle_indices)

    def remaining_outbound_area_budget(self, particle_index):
        return max(
            0.0,
            self.particle_area_sum_in.get(particle_index, 0.0)
            - self.particle_area_sum_out.get(particle_index, 0.0),
        )

    def symmetrically_close_area_stats(self):
        self.area_sum_in = 0.5 * (self.area_sum_in + self.area_sum_out)
        self.area_sum_out = self.area_sum_in
        self.area_time_sum_in = 0.5 * (self.area_time_sum_in + self.area_time_sum_out)
        self.area_time_sum_out = self.area_time_sum_in
        self.J_sum_in = 0.5 * (self.J_sum_in + self.J_sum_out)
        self.J_sum_out = self.J_sum_in

        particle_indices = set(self.particle_area_sum_in) | set(self.particle_area_sum_out)
        for index in particle_indices:
            balanced_area = 0.5 * (
                self.particle_area_sum_in.get(index, 0.0)
                + self.particle_area_sum_out.get(index, 0.0)
            )
            self.particle_area_sum_in[index] = balanced_area
            self.particle_area_sum_out[index] = balanced_area

    def build_final_report_lines(self):
        lines = super().build_final_report_lines()
        extra_lines = [
            f"field samples in      = {self.contact_samples_in}",
            f"field samples out     = {self.contact_samples_out}",
            f"sum area in           = {self.area_sum_in:.8f}",
            f"sum area out          = {self.area_sum_out:.8f}",
            f"sum area*time in      = {self.area_time_sum_in:.8f}",
            f"sum area*time out     = {self.area_time_sum_out:.8f}",
            f"sum J in              = {self.J_sum_in:.8e}",
            f"sum J out             = {self.J_sum_out:.8e}",
            f"sum turn area         = {self.sum_turn_area:.8f}",
            f"max turn area         = {self.max_turn_area:.8f}",
            f"max turn sweep        = {self.max_turn_sweep:.8f}",
        ]
        for index in range(len(self.particles)):
            area_in = self.particle_area_sum_in.get(index, 0.0)
            area_out = self.particle_area_sum_out.get(index, 0.0)
            samples_in = self.particle_samples_in.get(index, 0)
            samples_out = self.particle_samples_out.get(index, 0)
            avg_in = area_in / samples_in if samples_in else 0.0
            avg_out = area_out / samples_out if samples_out else 0.0
            extra_lines.append(
                f"particle {index:02d} area_in/out/diff = ({area_in:.8f}, {area_out:.8f}, {area_in - area_out:.8f})"
            )
            extra_lines.append(
                f"particle {index:02d} samples_in/out   = ({samples_in}, {samples_out})"
            )
            extra_lines.append(
                f"particle {index:02d} avg_area_in/out  = ({avg_in:.8f}, {avg_out:.8f})"
            )
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
            "internal_momentum_x": particle.get("internal_momentum_x", 0.0),
            "internal_momentum_y": particle.get("internal_momentum_y", 0.0),
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
        contacts = self.get_particle_field_overlaps()
        wall_contacts = self.get_wall_field_overlaps()
        bond_interactions = self.get_bond_interactions()
        self.active_pair_contact_count = len(contacts)
        self.active_wall_contact_count = len(wall_contacts)
        self.active_bond_contact_count = len(bond_interactions)
        self.active_contact_count = len(contacts) + len(wall_contacts) + len(bond_interactions)

        refine_steps = max(
            self.contact_refine_steps,
            self.contact_refine_requirement(contacts, wall_contacts, sub_dt),
        )
        if (
            self.active_contact_count > 0
            and refine_steps > 1
            and sub_dt > self.min_contact_sub_dt
        ):
            refined_dt = sub_dt / refine_steps
            for _ in range(refine_steps):
                self.do_substep(refined_dt)
            return

        active_pair_keys = set()
        active_wall_keys = set()

        if self.active_contact_count == 0:
            self.bookkeeping_internal = 0.0
            self.bookkeeping_internal_x = 0.0
            self.bookkeeping_internal_y = 0.0
            self.step_internal_momentum = 0.0
            self.step_internal_momentum_by_particle = [0.0] * len(self.particles)
            self.normalize_internal_momentum()

            if self.collision_started and not self.final_report_printed:
                self.symmetrically_close_area_stats()
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
                        "step_turn_area": 0.0,
                        "step_max_turn_area": 0.0,
                        "step_max_turn_sweep": 0.0,
                    },
                )
                self.trace_contact_active = False
            self.clear_contact_history()
            self.advance_trace_time(sub_dt)
            return

        self.collision_started = True
        self.trace_contact_active = True
        self.bookkeeping_internal = 0.0
        self.bookkeeping_internal_x = 0.0
        self.bookkeeping_internal_y = 0.0
        self.step_internal_momentum = 0.0
        self.step_internal_momentum_by_particle = [0.0] * len(self.particles)
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
        step_turn_area = 0.0
        step_max_turn_area = 0.0
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

            force_per_area, accel_per_area = self.resolve_pair_repulsion_coefficients(
                self.particles[i],
                self.particles[j],
            )

            prev_contact = self.pair_field_memory.get(pair_key)
            turn_sweep = 0.0
            turn_area = 0.0
            if prev_contact is not None:
                prev_nx, prev_ny, prev_area, prev_d = prev_contact
                turn_sweep = self.turn_sweep(prev_nx, prev_ny, nx, ny)
                if abs(state_i["radius"] - state_j["radius"]) <= 1.0e-12:
                    d_mid = 0.5 * (prev_d + d)
                    turn_area = self.equal_radius_turn_area(
                        state_i["radius"],
                        d_mid,
                        turn_sweep,
                    )
            self.pair_field_memory[pair_key] = (nx, ny, area_geom, d)
            effective_pair_area = area_geom
            self.sum_turn_area += turn_area
            self.max_turn_area = max(self.max_turn_area, turn_area)
            self.max_turn_sweep = max(self.max_turn_sweep, turn_sweep)
            step_turn_area += turn_area
            step_max_turn_area = max(step_max_turn_area, turn_area)
            step_max_turn_sweep = max(step_max_turn_sweep, turn_sweep)

            equivalent_J = self.field_contact_step_transfer(
                effective_pair_area,
                sub_dt,
                state_i["mass"],
                state_j["mass"],
                radius_i=state_i["radius"],
                radius_j=state_j["radius"],
                source_distance=d,
                force_per_area=force_per_area,
                accel_per_area=accel_per_area,
            )

            pair_requests.append(
                {
                    "i": i,
                    "j": j,
                    "nx": nx,
                    "ny": ny,
                    "area_geom": area_geom,
                    "turn_area": turn_area,
                    "area_effective": effective_pair_area,
                    "equivalent_J": equivalent_J,
                    "rel_vn": rel_vn,
                    "turn_sweep": turn_sweep,
                }
            )

        for i, wall_name, contact in wall_contacts:
            wall_key = (i, wall_name)
            active_wall_keys.add(wall_key)
            nx, ny, alpha, delta, area_geom, area_pcnt, proxPercent, d = contact
            state = snapshot[i]
            vx = state["px"] / state["mass"]
            vy = state["py"] / state["mass"]
            rel_vn = vx * nx + vy * ny

            force_per_area, accel_per_area = self.resolve_wall_repulsion_coefficients(self.particles[i])
            equivalent_J = self.field_contact_step_transfer(
                area_geom,
                sub_dt,
                state["mass"],
                radius_i=state["radius"],
                delta=delta,
                force_per_area=force_per_area,
                accel_per_area=accel_per_area,
            )

            prev_contact = self.wall_field_memory.get(wall_key)
            if prev_contact is not None:
                prev_nx, prev_ny, prev_area, prev_d = prev_contact
            self.wall_field_memory[wall_key] = (nx, ny, area_geom, d)
            wall_requests.append(
                {
                    "i": i,
                    "nx": nx,
                    "ny": ny,
                    "area_geom": area_geom,
                    "equivalent_J": equivalent_J,
                    "rel_vn": rel_vn,
                }
            )

        for request in self.ordered_pair_requests(pair_requests):
            i = request["i"]
            j = request["j"]
            scaled_J = request["equivalent_J"] * self.pair_contact_request_scale(request, pair_requests)
            effective_area = request["area_effective"]

            self.current_area = max(self.current_area, request["area_effective"])
            self.current_J = max(self.current_J, scaled_J)
            if request["rel_vn"] < 0.0:
                self.phase = "inbound"
                self.max_area_in = max(self.max_area_in, request["area_effective"])
                self.max_J_in = max(self.max_J_in, scaled_J)
            else:
                self.rebound_mode = True
                effective_area = request["area_effective"]
                self.max_area_out = max(self.max_area_out, effective_area)
                self.max_J_out = max(self.max_J_out, scaled_J)

            self.record_contact_sample(
                request["rel_vn"],
                effective_area,
                scaled_J,
                sub_dt,
                particle_indices=(i, j),
            )
            delta_px[i] += -request["nx"] * scaled_J
            delta_py[i] += -request["ny"] * scaled_J
            delta_px[j] += request["nx"] * scaled_J
            delta_py[j] += request["ny"] * scaled_J

        for request in wall_requests:
            i = request["i"]
            scaled_J = request["equivalent_J"]
            effective_area = request["area_geom"]

            self.current_area = max(self.current_area, request["area_geom"])
            self.current_J = max(self.current_J, scaled_J)
            if request["rel_vn"] < 0.0:
                self.phase = "inbound"
                self.max_area_in = max(self.max_area_in, request["area_geom"])
                self.max_J_in = max(self.max_J_in, scaled_J)
            else:
                self.rebound_mode = True
                effective_area = request["area_geom"]
                self.max_area_out = max(self.max_area_out, effective_area)
                self.max_J_out = max(self.max_J_out, scaled_J)

            self.record_contact_sample(
                request["rel_vn"],
                effective_area,
                scaled_J,
                sub_dt,
                particle_indices=(i,),
            )
            delta_px[i] += request["nx"] * scaled_J
            delta_py[i] += request["ny"] * scaled_J

        self.step_internal_momentum_by_particle = [
            math.hypot(delta_px[index], delta_py[index]) for index in range(len(self.particles))
        ]
        self.step_internal_momentum = sum(self.step_internal_momentum_by_particle)

        for index, particle in enumerate(self.particles):
            particle["internal_direct_x"] = particle.get("internal_direct_x", 0.0) + delta_px[index]
            particle["internal_direct_y"] = particle.get("internal_direct_y", 0.0) + delta_py[index]
            particle["internal_direct"] = math.hypot(
                particle["internal_direct_x"],
                particle["internal_direct_y"],
            )
            particle["px"] += delta_px[index]
            particle["py"] += delta_py[index]
            vx = particle["px"] / particle["mass"]
            vy = particle["py"] / particle["mass"]
            particle["x"] += vx * sub_dt
            particle["y"] += vy * sub_dt

        self.pair_internal_store = {}

        self.sync_particle_internal_display()

        self.pair_field_memory = {
            key: value
            for key, value in self.pair_field_memory.items()
            if key in active_pair_keys
        }
        self.wall_field_memory = {
            key: value
            for key, value in self.wall_field_memory.items()
            if key in active_wall_keys
        }
        self.pair_contact_memory = self.pair_field_memory
        self.wall_contact_memory = self.wall_field_memory
        self.pair_internal_store = {
            key: value
            for key, value in self.pair_internal_store.items()
            if key in active_pair_keys or abs(value) > self.internal_momentum_tolerance
        }
        self.record_collision_trace(
            sub_dt,
            extra={
                "step_turn_area": step_turn_area,
                "step_max_turn_area": step_max_turn_area,
                "step_max_turn_sweep": step_max_turn_sweep,
            },
        )
        self.advance_trace_time(sub_dt)
