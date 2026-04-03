import math
import bisect


class Base:
    def __init__(self):
        self.particles = []
        self.particle_configs = []
        self.walls = None
        self.bond_settings = {"enabled": False}
        self.activated_bond_pairs = set()
        self.deep_bond_pairs = set()
        self.scenario_options = {}
        self.BG = (20, 20, 30)
        self.WHITE = (235, 235, 235)
        self.BLUE_FILL = (100, 170, 255, 120)
        self.RED_FILL = (255, 120, 120, 120)
        self.BLUE_EDGE = (160, 210, 255)
        self.RED_EDGE = (255, 180, 180)
        self.GREEN = (120, 255, 140)
        self.YELLOW = (255, 220, 120)

        # Physical parameters
        self.dt = 0.005
        self.substeps = 5
        self.k = 8.0
        self.rejection_accel_per_area = None
        self.contact_refine_steps = 8
        self.min_collision_steps = None
        self.enforce_speed_limit = False
        self.min_contact_sub_dt = 5.0e-5
        self.internal_momentum_tolerance = 1.0e-12
        self.time = 0.0
        self.collision_complete = False
        self.final_report_lines = []
        self.collision_trace_particle_limit = 4
        self.collision_trace = []
        self.trace_sim_time = 0.0
        self.trace_contact_active = False

    def load_default_particles(self):
        raise NotImplementedError(
            "Configure particles from a scenario script instead of editing Base.py."
        )

    def add_particle(self, x, y, vx, vy, mass, radius, **extra_config):
            if mass <= 0.0:
                raise ValueError("Particle mass must be positive.")
            if radius <= 0.0:
                raise ValueError("Particle radius must be positive.")

            particle_config = {
                "x": float(x),
                "y": float(y),
                "vx": float(vx),
                "vy": float(vy),
                "mass": float(mass),
                "radius": float(radius),
            }
            particle_config.update(extra_config)
            self.particle_configs.append(particle_config)

    def set_walls(self, start_x, end_x, start_y, end_y):
        start_x = float(start_x)
        end_x = float(end_x)
        start_y = float(start_y)
        end_y = float(end_y)
        if end_x <= start_x or end_y <= start_y:
            raise ValueError("Walls must define a positive-area box.")
        self.walls = {
            "start_x": start_x,
            "end_x": end_x,
            "start_y": start_y,
            "end_y": end_y,
        }

    def clear_walls(self):
        self.walls = None

    def set_bonding(
        self,
        stiffness,
        damping,
        pair_indices=None,
        rest_length_offset=0.0,
        max_distance=None,
        activate_on_contact_only=True,
        activation_distance=None,
    ):
        self.bond_settings = {
            "enabled": True,
            "stiffness": float(stiffness),
            "damping": float(damping),
            "pair_indices": pair_indices,
            "rest_length_offset": float(rest_length_offset),
            "max_distance": None if max_distance is None else float(max_distance),
            "activate_on_contact_only": bool(activate_on_contact_only),
            "activation_distance": None if activation_distance is None else float(activation_distance),
        }

    def clear_bonding(self):
        self.bond_settings = {"enabled": False}
        self.activated_bond_pairs = set()
        self.deep_bond_pairs = set()

    def set_contact_response(self, force_per_area=None, accel_per_area=None):
        if force_per_area is not None and accel_per_area is not None:
            raise ValueError("Specify either force_per_area or accel_per_area, not both.")
        if force_per_area is None and accel_per_area is None:
            raise ValueError("A contact response value is required.")

        if force_per_area is not None:
            force_per_area = float(force_per_area)
            if force_per_area < 0.0:
                raise ValueError("force_per_area must be non-negative.")
            self.k = force_per_area
            self.rejection_accel_per_area = None
            return

        accel_per_area = float(accel_per_area)
        if accel_per_area < 0.0:
            raise ValueError("accel_per_area must be non-negative.")
        self.rejection_accel_per_area = accel_per_area

    def set_collision_step_limit(self, min_collision_steps=None):
        if min_collision_steps is None:
            self.min_collision_steps = None
            return

        min_collision_steps = int(min_collision_steps)
        if min_collision_steps < 1:
            raise ValueError("min_collision_steps must be at least 1.")
        self.min_collision_steps = min_collision_steps

    def set_speed_limit_enforcement(self, enforce=True):
        self.enforce_speed_limit = bool(enforce)

    def set_scenario_options(self, **options):
        self.scenario_options = dict(options)

    def clear_particles(self):
        self.particles = []
        self.particle_configs = []

    def total_momentum(self):
            total_px = 0.0
            total_py = 0.0
            for particle in self.particles:
                total_px += particle["px"]
                total_py += particle["py"]
            return total_px, total_py

    def total_kinetic_energy(self):
        total_ke = 0.0
        for particle in self.particles:
            total_ke += (particle["px"] ** 2 + particle["py"] ** 2) / (2.0 * particle["mass"])
        return total_ke

    def total_abs_momentum_sum(self):
        total_abs_p = 0.0
        for particle in self.particles:
            total_abs_p += math.hypot(particle["px"], particle["py"])
        return total_abs_p

    def total_internal_momentum(self):
        total_internal_p = 0.0
        for particle in self.particles:
            total_internal_p += particle["internal_momentum"]
        return total_internal_p

    def total_scalar_momentum_with_internal(self):
        return self.total_abs_momentum_sum() + self.total_internal_momentum()

    def initial_abs_momentum_sum(self):
        total_abs_p = 0.0
        for particle in self.particles:
            total_abs_p += math.hypot(
                particle["mass"] * particle["init_vx"],
                particle["mass"] * particle["init_vy"],
            )
        return total_abs_p
    
    def get_contacts(self):
            contacts = []
            for i in range(len(self.particles)):
                p_i = self.particles[i]
                for j in range(i + 1, len(self.particles)):
                    p_j = self.particles[j]
                    contact = self.particle_contact(
                        p_i["x"],
                        p_i["y"],
                        p_j["x"],
                        p_j["y"],
                        p_i["radius"],
                        p_j["radius"],
                    )
                    if contact is not None:
                        contacts.append((i, j, contact))
            return contacts

    def get_wall_contacts(self):
            contacts = []
            if self.walls is None:
                return contacts

            for index, particle in enumerate(self.particles):
                x = particle["x"]
                y = particle["y"]
                radius = particle["radius"]

                left_contact = self.wall_contact(radius - (x - self.walls["start_x"]), 1.0, 0.0, radius)
                if left_contact is not None:
                    contacts.append((index, "left", left_contact))

                right_contact = self.wall_contact(radius - (self.walls["end_x"] - x), -1.0, 0.0, radius)
                if right_contact is not None:
                    contacts.append((index, "right", right_contact))

                bottom_contact = self.wall_contact(radius - (y - self.walls["start_y"]), 0.0, 1.0, radius)
                if bottom_contact is not None:
                    contacts.append((index, "bottom", bottom_contact))

                top_contact = self.wall_contact(radius - (self.walls["end_y"] - y), 0.0, -1.0, radius)
                if top_contact is not None:
                    contacts.append((index, "top", top_contact))

            return contacts

    def get_bond_interactions(self):
            interactions = []
            if not self.bond_settings.get("enabled", False):
                return interactions

            pair_indices = self.bond_settings.get("pair_indices")
            if pair_indices is None:
                pair_indices = [
                    (i, j)
                    for i in range(len(self.particles))
                    for j in range(i + 1, len(self.particles))
                ]

            max_distance = self.bond_settings.get("max_distance")
            rest_length_offset = self.bond_settings.get("rest_length_offset", 0.0)

            for i, j in pair_indices:
                pair_key = (min(i, j), max(i, j))
                particle_i = self.particles[i]
                particle_j = self.particles[j]
                dx = particle_j["x"] - particle_i["x"]
                dy = particle_j["y"] - particle_i["y"]
                d = math.hypot(dx, dy)

                if d < 1.0e-14:
                    nx = 1.0
                    ny = 0.0
                else:
                    nx = dx / d
                    ny = dy / d

                if max_distance is not None and d > max_distance:
                    continue

                if (
                    self.bond_settings.get("activate_on_contact_only", False)
                    and pair_key not in self.activated_bond_pairs
                ):
                    continue

                activation_distance = self.bond_settings.get("activation_distance")
                if activation_distance is not None:
                    if d <= activation_distance:
                        self.deep_bond_pairs.add(pair_key)
                    elif pair_key not in self.deep_bond_pairs:
                        continue

                rest_distance = particle_i["radius"] + particle_j["radius"] + rest_length_offset
                extension = d - rest_distance
                interactions.append((i, j, nx, ny, d, rest_distance, extension))

            return interactions

    def is_deep_bond_pair(self, i, j):
            return (min(i, j), max(i, j)) in self.deep_bond_pairs

    def particle_contact(self, x1, y1, x2, y2, r1, r2):
        dx = x2 - x1
        dy = y2 - y1

        d2 = dx * dx + dy * dy
        d = math.sqrt(d2)

        sum_r = r1 + r2
        if d >= sum_r:
            return None

        if d < 1.0e-14:
            nx = 1.0
            ny = 0.0
            alpha = 0.0
        else:
            nx = dx / d
            ny = dy / d
            alpha = (math.atan2(dy, dx) + 2.0 * math.pi) % (2.0 * math.pi)

        delta = sum_r - d
        proxPercent = 1.0 - delta / max(min(r1, r2), 1.0e-12)

        if d <= abs(r1 - r2) + 1.0e-14:
            min_r = min(r1, r2)
            area = math.pi * min_r * min_r
        else:
            term1 = r1 * r1 * math.acos(max(-1.0, min(1.0, (d * d + r1 * r1 - r2 * r2) / (2.0 * d * r1))))
            term2 = r2 * r2 * math.acos(max(-1.0, min(1.0, (d * d + r2 * r2 - r1 * r1) / (2.0 * d * r2))))
            term3 = 0.5 * math.sqrt(
                max(
                    0.0,
                    (-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2),
                )
            )
            area = term1 + term2 - term3

        tot_area = math.pi * min(r1, r2) ** 2
        area_pcnt = area / max(tot_area, 1.0e-12)

        return nx, ny, alpha, delta, area, area_pcnt, proxPercent, d

    def wall_contact(self, delta, nx, ny, radius):
        if delta <= 0.0:
            return None

        delta = min(delta, radius)
        d = radius - delta
        alpha = (math.atan2(ny, nx) + 2.0 * math.pi) % (2.0 * math.pi)
        proxPercent = 1.0 - delta / max(radius, 1.0e-12)

        if d <= 0.0:
            area = 0.5 * math.pi * radius * radius
        else:
            theta = 2.0 * math.acos(max(-1.0, min(1.0, d / radius)))
            area = 0.5 * radius * radius * (theta - math.sin(theta))

        tot_area = 0.5 * math.pi * radius * radius
        area_pcnt = area / max(tot_area, 1.0e-12)

        return nx, ny, alpha, delta, area, area_pcnt, proxPercent, d

    def sort_J_table(self):
        self.J_table.sort(key=lambda pair: pair[0])
        self.J_deltas = [pair[0] for pair in self.J_table]

    def lookup_inbound_J(self, delta):
        if len(self.J_table) == 0:
            return None
        if len(self.J_table) == 1:
            return self.J_table[0][1]

        if delta <= self.J_deltas[0]:
            return self.J_table[0][1]
        if delta >= self.J_deltas[-1]:
            return self.J_table[-1][1]

        i = bisect.bisect_left(self.J_deltas, delta)

        d0, j0 = self.J_table[i - 1]
        d1, j1 = self.J_table[i]

        if abs(d1 - d0) < 1.0e-14:
            return 0.5 * (j0 + j1)

        t = (delta - d0) / (d1 - d0)
        return j0 + t * (j1 - j0)

    def clear_contact_history(self):
        self.J_table.clear()
        self.J_deltas.clear()
        self.rebound_mode = False
        self.current_area = 0.0
        self.current_J = 0.0
        self.phase = "free"

    def particle_contact_span(self, radius_i, radius_j):
        return float(radius_i) + float(radius_j)

    def wall_contact_span(self, radius):
        return float(radius)

    def max_relative_speed_for_contact_span(self, contact_span, sub_dt=None):
        if self.min_collision_steps is None:
            return math.inf
        if sub_dt is None:
            sub_dt = self.dt / self.substeps
        if contact_span <= 1.0e-12 or sub_dt <= 0.0:
            return math.inf
        return contact_span / (self.min_collision_steps * sub_dt)

    def particle_contact_speed_limit(self, radius_i, radius_j, sub_dt=None):
        return self.max_relative_speed_for_contact_span(
            self.particle_contact_span(radius_i, radius_j),
            sub_dt=sub_dt,
        )

    def wall_contact_speed_limit(self, radius, sub_dt=None):
        return self.max_relative_speed_for_contact_span(
            self.wall_contact_span(radius),
            sub_dt=sub_dt,
        )

    def configured_particle_speed_violations(self, sub_dt=None):
        if self.min_collision_steps is None:
            return []

        if sub_dt is None:
            sub_dt = self.dt / self.substeps

        violations = []
        for i in range(len(self.particle_configs)):
            cfg_i = self.particle_configs[i]
            for j in range(i + 1, len(self.particle_configs)):
                cfg_j = self.particle_configs[j]
                rel_vx = cfg_j["vx"] - cfg_i["vx"]
                rel_vy = cfg_j["vy"] - cfg_i["vy"]
                rel_speed = math.hypot(rel_vx, rel_vy)
                speed_limit = self.particle_contact_speed_limit(
                    cfg_i["radius"],
                    cfg_j["radius"],
                    sub_dt=sub_dt,
                )
                if rel_speed > speed_limit:
                    violations.append(
                        {
                            "kind": "particle_pair",
                            "indices": (i, j),
                            "relative_speed": rel_speed,
                            "speed_limit": speed_limit,
                        }
                    )
        return violations

    def validate_configured_speed_limits(self, sub_dt=None):
        violations = self.configured_particle_speed_violations(sub_dt=sub_dt)
        if not violations:
            return

        messages = []
        for violation in violations:
            i, j = violation["indices"]
            messages.append(
                f"pair ({i}, {j}) relative speed {violation['relative_speed']:.8f} exceeds "
                f"limit {violation['speed_limit']:.8f}"
            )
        raise ValueError(
            "Configured collision speed limit exceeded for the current minimum collision step setting: "
            + "; ".join(messages)
        )

    def particle_contact_refine_requirement(self, contacts, sub_dt):
        if not contacts or self.min_collision_steps is None:
            return 1

        required = 1
        for i, j, _contact in contacts:
            particle_i = self.particles[i]
            particle_j = self.particles[j]
            vix = particle_i["px"] / particle_i["mass"]
            viy = particle_i["py"] / particle_i["mass"]
            vjx = particle_j["px"] / particle_j["mass"]
            vjy = particle_j["py"] / particle_j["mass"]
            rel_speed = math.hypot(vjx - vix, vjy - viy)
            contact_span = particle_i["radius"] + particle_j["radius"]
            if contact_span <= 1.0e-12:
                continue
            steps_needed = math.ceil(rel_speed * sub_dt * self.min_collision_steps / contact_span)
            required = max(required, steps_needed)
        return required

    def wall_contact_refine_requirement(self, wall_contacts, sub_dt):
        if not wall_contacts or self.min_collision_steps is None:
            return 1

        required = 1
        for i, _wall_name, _contact in wall_contacts:
            particle = self.particles[i]
            vx = particle["px"] / particle["mass"]
            vy = particle["py"] / particle["mass"]
            speed = math.hypot(vx, vy)
            contact_span = particle["radius"]
            if contact_span <= 1.0e-12:
                continue
            steps_needed = math.ceil(speed * sub_dt * self.min_collision_steps / contact_span)
            required = max(required, steps_needed)
        return required

    def contact_refine_requirement(self, contacts, wall_contacts, sub_dt):
        return max(
            1,
            self.particle_contact_refine_requirement(contacts, sub_dt),
            self.wall_contact_refine_requirement(wall_contacts, sub_dt),
        )

    def build_collision_trace_row(self, sub_dt, extra=None):
        row = {
            "time": self.trace_sim_time + sub_dt,
            "sub_dt": sub_dt,
            "phase": self.phase,
            "collision_started": int(self.collision_started),
            "rebound_mode": int(self.rebound_mode),
            "active_contact_count": self.active_contact_count,
            "pair_contact_count": getattr(self, "active_pair_contact_count", 0),
            "wall_contact_count": getattr(self, "active_wall_contact_count", 0),
            "bond_contact_count": getattr(self, "active_bond_contact_count", 0),
            "current_area": self.current_area,
            "current_J": self.current_J,
            "max_area_in": self.max_area_in,
            "max_area_out": self.max_area_out,
            "max_J_in": self.max_J_in,
            "max_J_out": self.max_J_out,
        }
        if extra:
            row.update(extra)

        for index in range(self.collision_trace_particle_limit):
            prefix = f"p{index}_"
            if index < len(self.particles):
                particle = self.particles[index]
                row[f"{prefix}x"] = particle["x"]
                row[f"{prefix}y"] = particle["y"]
                row[f"{prefix}vx"] = particle["px"] / particle["mass"]
                row[f"{prefix}vy"] = particle["py"] / particle["mass"]
                row[f"{prefix}px"] = particle["px"]
                row[f"{prefix}py"] = particle["py"]
                row[f"{prefix}internal_p"] = particle.get("internal_momentum", 0.0)
                row[f"{prefix}radius"] = particle["radius"]
                row[f"{prefix}mass"] = particle["mass"]
            else:
                row[f"{prefix}x"] = ""
                row[f"{prefix}y"] = ""
                row[f"{prefix}vx"] = ""
                row[f"{prefix}vy"] = ""
                row[f"{prefix}px"] = ""
                row[f"{prefix}py"] = ""
                row[f"{prefix}internal_p"] = ""
                row[f"{prefix}radius"] = ""
                row[f"{prefix}mass"] = ""
        return row

    def record_collision_trace(self, sub_dt, extra=None):
        self.collision_trace.append(self.build_collision_trace_row(sub_dt, extra=extra))

    def advance_trace_time(self, sub_dt):
        self.trace_sim_time += sub_dt

    def particle_rejection_impulse(self, area_geom, sub_dt, mass_i, mass_j):
        if self.rejection_accel_per_area is None:
            return self.k * area_geom * sub_dt

        total_mass = mass_i + mass_j
        if total_mass <= 0.0:
            raise ValueError("Particle contact requires positive total mass.")
        reduced_mass = (mass_i * mass_j) / total_mass
        return reduced_mass * self.rejection_accel_per_area * area_geom * sub_dt

    def wall_rejection_impulse(self, area_geom, sub_dt, mass):
        if self.rejection_accel_per_area is None:
            return self.k * area_geom * sub_dt
        return mass * self.rejection_accel_per_area * area_geom * sub_dt

    def update_internal_momentum(self, particle, abs_p_before):
        abs_p_after = math.hypot(particle["px"], particle["py"])
        particle["internal_momentum"] += abs_p_before - abs_p_after
        if abs(particle["internal_momentum"]) <= self.internal_momentum_tolerance:
            particle["internal_momentum"] = 0.0

    def pair_scalar_change_for_impulse(self, particle_i, particle_j, nx, ny, J):
        before = math.hypot(particle_i["px"], particle_i["py"]) + math.hypot(
            particle_j["px"], particle_j["py"]
        )
        after_i_px = particle_i["px"] - nx * J
        after_i_py = particle_i["py"] - ny * J
        after_j_px = particle_j["px"] + nx * J
        after_j_py = particle_j["py"] + ny * J
        after = math.hypot(after_i_px, after_i_py) + math.hypot(after_j_px, after_j_py)
        return after - before

    def wall_scalar_change_for_impulse(self, particle, nx, ny, J):
        before = math.hypot(particle["px"], particle["py"])
        after_px = particle["px"] + nx * J
        after_py = particle["py"] + ny * J
        after = math.hypot(after_px, after_py)
        return after - before

    def solve_impulse_for_scalar_target(self, scalar_change_fn, target_change):
        if abs(target_change) <= 1.0e-15:
            return 0.0

        sign = 1.0 if target_change > 0.0 else -1.0
        low = 0.0
        low_value = 0.0
        high = max(abs(target_change), 1.0e-9)
        bracketed = False

        for _ in range(60):
            high_value = scalar_change_fn(sign * high)
            if not math.isfinite(high_value):
                return 0.0
            if (target_change > 0.0 and high_value >= target_change) or (
                target_change < 0.0 and high_value <= target_change
            ):
                bracketed = True
                break
            low = high
            low_value = high_value
            high *= 2.0
        if not bracketed:
            return 0.0

        for _ in range(60):
            mid = 0.5 * (low + high)
            mid_value = scalar_change_fn(sign * mid)
            if not math.isfinite(mid_value):
                return 0.0
            if abs(mid_value - target_change) <= 1.0e-15:
                return sign * mid
            if (target_change > 0.0 and mid_value < target_change) or (
                target_change < 0.0 and mid_value > target_change
            ):
                low = mid
                low_value = mid_value
            else:
                high = mid
                high_value = mid_value

        if abs(low_value - target_change) <= abs(high_value - target_change):
            return sign * low
        return sign * high

    def transfer_internal_to_pair(self, i, j, nx, ny):
        particle_i = self.particles[i]
        particle_j = self.particles[j]
        internal_total = particle_i["internal_momentum"] + particle_j["internal_momentum"]
        if abs(internal_total) <= self.internal_momentum_tolerance:
            return 0.0

        J = self.solve_impulse_for_scalar_target(
            lambda impulse: self.pair_scalar_change_for_impulse(particle_i, particle_j, nx, ny, impulse),
            internal_total,
        )
        if abs(J) <= 1.0e-15:
            return 0.0

        before_release = math.hypot(particle_i["px"], particle_i["py"]) + math.hypot(
            particle_j["px"], particle_j["py"]
        )
        particle_i["px"] -= nx * J
        particle_i["py"] -= ny * J
        particle_j["px"] += nx * J
        particle_j["py"] += ny * J
        after_release = math.hypot(particle_i["px"], particle_i["py"]) + math.hypot(
            particle_j["px"], particle_j["py"]
        )
        released = after_release - before_release

        if abs(released) <= 1.0e-15:
            return 0.0

        contributors = []
        if particle_i["internal_momentum"] * internal_total > 0.0:
            contributors.append((particle_i, abs(particle_i["internal_momentum"])))
        if particle_j["internal_momentum"] * internal_total > 0.0:
            contributors.append((particle_j, abs(particle_j["internal_momentum"])))
        contributor_total = sum(weight for _, weight in contributors)
        if contributor_total <= self.internal_momentum_tolerance:
            return 0.0

        for particle, weight in contributors:
            particle["internal_momentum"] -= released * (weight / contributor_total)
        return released

    def transfer_internal_to_wall(self, i, nx, ny):
        particle = self.particles[i]
        internal_total = particle["internal_momentum"]
        if abs(internal_total) <= self.internal_momentum_tolerance:
            return 0.0

        J = self.solve_impulse_for_scalar_target(
            lambda impulse: self.wall_scalar_change_for_impulse(particle, nx, ny, impulse),
            internal_total,
        )
        if abs(J) <= 1.0e-15:
            return 0.0

        before_release = math.hypot(particle["px"], particle["py"])
        particle["px"] += nx * J
        particle["py"] += ny * J
        released = math.hypot(particle["px"], particle["py"]) - before_release
        if abs(released) <= 1.0e-15:
            return 0.0

        particle["internal_momentum"] -= released
        return released

    def normalize_internal_momentum(self):
        for particle in self.particles:
            if abs(particle["internal_momentum"]) <= self.internal_momentum_tolerance:
                particle["internal_momentum"] = 0.0

    def build_final_report_lines(self):
        p_total_x, p_total_y = self.total_momentum()
        p_error_x = p_total_x - self.initial_total_momentum_x
        p_error_y = p_total_y - self.initial_total_momentum_y
        p_error_mag = math.hypot(p_error_x, p_error_y)
        abs_p_total = self.total_abs_momentum_sum()
        initial_abs_p_total = self.initial_abs_momentum_sum()
        abs_p_error = abs_p_total - initial_abs_p_total
        internal_p_total = self.total_internal_momentum()
        scalar_p_total = self.total_scalar_momentum_with_internal()
        scalar_p_error = scalar_p_total - initial_abs_p_total
        ke = self.total_kinetic_energy()
        ke_error = ke - self.initial_ke

        area_diff = abs(self.max_area_in - self.max_area_out)
        J_diff = abs(self.max_J_in - self.max_J_out)

        lines = [
            "===== FINAL COLLISION REPORT =====",
            f"time                 = {self.time:.8f}",
            f"initial momentum     = ({self.initial_total_momentum_x:.8f}, {self.initial_total_momentum_y:.8f})",
            f"final momentum       = ({p_total_x:.8f}, {p_total_y:.8f})",
            f"momentum error mag   = {p_error_mag:.8e}",
            f"initial |p| sum      = {initial_abs_p_total:.8f}",
            f"final |p| sum        = {abs_p_total:.8f}",
            f"|p| sum error        = {abs_p_error:.8e}",
            f"internal |p| sum     = {internal_p_total:.8f}",
            f"scalar |p|+internal  = {scalar_p_total:.8f}",
            f"scalar total error   = {scalar_p_error:.8e}",
            f"initial KE           = {self.initial_ke:.8f}",
            f"final KE             = {ke:.8f}",
            f"KE error             = {ke_error:.8e}",
            f"max area in          = {self.max_area_in:.8f}",
            f"max area out         = {self.max_area_out:.8f}",
            f"max area diff        = {area_diff:.8e}",
            f"max J in             = {self.max_J_in:.8e}",
            f"max J out            = {self.max_J_out:.8e}",
            f"max J diff           = {J_diff:.8e}",
            f"max raw p drift      = {self.max_pair_momentum_drift:.8e}",
            f"max replay mismatch  = {self.max_outbound_replay_mismatch:.8e}",
            f"active contacts      = {self.active_contact_count}",
        ]
        for index, particle in enumerate(self.particles):
            vx = particle["px"] / particle["mass"]
            vy = particle["py"] / particle["mass"]
            lines.append(f"particle {index:02d} init pos = ({particle['init_x']:.8f}, {particle['init_y']:.8f})")
            lines.append(f"particle {index:02d} pos   = ({particle['x']:.8f}, {particle['y']:.8f})")
            lines.append(f"particle {index:02d} vel   = ({vx:.8f}, {vy:.8f})")
            lines.append(f"particle {index:02d} mom   = ({particle['px']:.8f}, {particle['py']:.8f})")
        lines.append("==================================")
        return lines

    def print_final_report(self):
        print()
        for line in self.build_final_report_lines():
            print(line)
        print()


    def do_substep(self, sub_dt):
            contacts = self.get_contacts()
            wall_contacts = self.get_wall_contacts()
            bond_interactions = self.get_bond_interactions()
            self.active_pair_contact_count = len(contacts)
            self.active_wall_contact_count = len(wall_contacts)
            self.active_bond_contact_count = len(bond_interactions)
            self.active_contact_count = len(contacts) + len(wall_contacts) + len(bond_interactions)

            if (
                (contacts or wall_contacts or bond_interactions)
                and max(self.contact_refine_steps, self.contact_refine_requirement(contacts, wall_contacts, sub_dt)) > 1
                and sub_dt > self.min_contact_sub_dt
            ):
                refine_steps = max(
                    self.contact_refine_steps,
                    self.contact_refine_requirement(contacts, wall_contacts, sub_dt),
                )
                refined_dt = sub_dt / refine_steps
                for _ in range(refine_steps):
                    self.do_substep(refined_dt)
                return

            if not contacts and not wall_contacts and not bond_interactions:
                # If a real collision had started and final report has not yet been printed,
                # then separation means collision is over.
                if self.collision_started and not self.final_report_printed:
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
                        },
                    )
                    self.trace_contact_active = False
                self.clear_contact_history()
                self.advance_trace_time(sub_dt)
                return

            # we are in contact
            self.collision_started = True
            self.trace_contact_active = True
            self.current_area = 0.0
            self.current_J = 0.0
            self.phase = "outbound"
            self.rebound_mode = False

            for i, j, nx, ny, d, rest_distance, extension in bond_interactions:
                particle_i = self.particles[i]
                particle_j = self.particles[j]
                vix = particle_i["px"] / particle_i["mass"]
                viy = particle_i["py"] / particle_i["mass"]
                vjx = particle_j["px"] / particle_j["mass"]
                vjy = particle_j["py"] / particle_j["mass"]
                rel_vn = (vjx - vix) * nx + (vjy - viy) * ny

                spring_J = self.bond_settings["stiffness"] * extension * sub_dt
                particle_i["px"] += nx * spring_J
                particle_i["py"] += ny * spring_J
                particle_j["px"] -= nx * spring_J
                particle_j["py"] -= ny * spring_J

                abs_pi_before_damping = math.hypot(particle_i["px"], particle_i["py"])
                abs_pj_before_damping = math.hypot(particle_j["px"], particle_j["py"])
                damping_J = self.bond_settings["damping"] * rel_vn * sub_dt
                particle_i["px"] += nx * damping_J
                particle_i["py"] += ny * damping_J
                particle_j["px"] -= nx * damping_J
                particle_j["py"] -= ny * damping_J
                self.update_internal_momentum(particle_i, abs_pi_before_damping)
                self.update_internal_momentum(particle_j, abs_pj_before_damping)

            for i, j, contact in contacts:
                if self.is_deep_bond_pair(i, j):
                    continue
                self.activated_bond_pairs.add((min(i, j), max(i, j)))
                nx, ny, alpha, delta, area_geom, area_pcnt, proxPercent, d = contact
                particle_i = self.particles[i]
                particle_j = self.particles[j]
                abs_pi_before = math.hypot(particle_i["px"], particle_i["py"])
                abs_pj_before = math.hypot(particle_j["px"], particle_j["py"])
                vix = particle_i["px"] / particle_i["mass"]
                viy = particle_i["py"] / particle_i["mass"]
                vjx = particle_j["px"] / particle_j["mass"]
                vjy = particle_j["py"] / particle_j["mass"]
                rel_vn = (vjx - vix) * nx + (vjy - viy) * ny

                J = self.particle_rejection_impulse(
                    area_geom,
                    sub_dt,
                    particle_i["mass"],
                    particle_j["mass"],
                )
                self.current_area = max(self.current_area, area_geom)
                self.current_J = max(self.current_J, J)

                if rel_vn < 0.0:
                    self.phase = "inbound"
                    self.max_area_in = max(self.max_area_in, area_geom)
                    self.max_J_in = max(self.max_J_in, J)
                else:
                    self.max_area_out = max(self.max_area_out, area_geom)
                    self.max_J_out = max(self.max_J_out, J)
                    self.rebound_mode = True

                p_target_x = particle_i["px"] + particle_j["px"]
                p_target_y = particle_i["py"] + particle_j["py"]

                particle_i["px"] -= nx * J
                particle_i["py"] -= ny * J
                particle_j["px"] += nx * J
                particle_j["py"] += ny * J

                p_total_x = particle_i["px"] + particle_j["px"]
                p_total_y = particle_i["py"] + particle_j["py"]
                err_x = p_total_x - p_target_x
                err_y = p_total_y - p_target_y
                err_mag = math.hypot(err_x, err_y)
                self.max_pair_momentum_drift = max(self.max_pair_momentum_drift, err_mag)
                total_mass = particle_i["mass"] + particle_j["mass"]
                particle_i["px"] -= (particle_i["mass"] / total_mass) * err_x
                particle_i["py"] -= (particle_i["mass"] / total_mass) * err_y
                particle_j["px"] -= (particle_j["mass"] / total_mass) * err_x
                particle_j["py"] -= (particle_j["mass"] / total_mass) * err_y
                self.update_internal_momentum(particle_i, abs_pi_before)
                self.update_internal_momentum(particle_j, abs_pj_before)
                if rel_vn >= 0.0:
                    self.transfer_internal_to_pair(i, j, nx, ny)

            for i, wall_name, contact in wall_contacts:
                nx, ny, alpha, delta, area_geom, area_pcnt, proxPercent, d = contact
                particle = self.particles[i]
                abs_p_before = math.hypot(particle["px"], particle["py"])
                vx = particle["px"] / particle["mass"]
                vy = particle["py"] / particle["mass"]
                rel_vn = vx * nx + vy * ny

                J = self.wall_rejection_impulse(area_geom, sub_dt, particle["mass"])
                self.current_area = max(self.current_area, area_geom)
                self.current_J = max(self.current_J, J)

                if rel_vn < 0.0:
                    self.phase = "inbound"
                    self.max_area_in = max(self.max_area_in, area_geom)
                    self.max_J_in = max(self.max_J_in, J)
                else:
                    self.max_area_out = max(self.max_area_out, area_geom)
                    self.max_J_out = max(self.max_J_out, J)
                    self.rebound_mode = True

                particle["px"] += nx * J
                particle["py"] += ny * J
                self.update_internal_momentum(particle, abs_p_before)
                if rel_vn >= 0.0:
                    self.transfer_internal_to_wall(i, nx, ny)

            for particle in self.particles:
                vx = particle["px"] / particle["mass"]
                vy = particle["py"] / particle["mass"]
                particle["x"] += vx * sub_dt
                particle["y"] += vy * sub_dt
            self.record_collision_trace(sub_dt)
            self.advance_trace_time(sub_dt)

    def reset(self):
        if len(self.particle_configs) < 2:
            raise ValueError("Reset requires at least 2 configured particles.")

        palette = [
            (self.BLUE_FILL, self.BLUE_EDGE),
            (self.RED_FILL, self.RED_EDGE),
            ((120, 255, 140, 120), (160, 255, 180)),
            ((255, 220, 120, 120), (255, 235, 160)),
            ((255, 160, 220, 120), (255, 190, 230)),
            ((160, 220, 255, 120), (190, 235, 255)),
        ]

        self.particles = []
        self.time = 0.0
        self.collision_complete = False
        self.final_report_lines = []
        self.collision_trace = []
        self.trace_sim_time = 0.0
        self.trace_contact_active = False
        self.activated_bond_pairs = set()
        self.deep_bond_pairs = set()

        for index, cfg in enumerate(self.particle_configs):
            fill_color, edge_color = palette[index % len(palette)]
            self.particles.append(
                {
                    "x": cfg["x"],
                    "y": cfg["y"],
                    "px": cfg["mass"] * cfg["vx"],
                    "py": cfg["mass"] * cfg["vy"],
                    "mass": cfg["mass"],
                    "radius": cfg["radius"],
                    "fill": fill_color,
                    "edge": edge_color,
                    "init_x": cfg["x"],
                    "init_y": cfg["y"],
                    "init_vx": cfg["vx"],
                    "init_vy": cfg["vy"],
                    "internal_momentum": 0.0,
                }
            )

        

        self.initial_total_momentum_x, self.initial_total_momentum_y = self.total_momentum()
        self.initial_ke = self.total_kinetic_energy()

        if self.enforce_speed_limit:
            self.validate_configured_speed_limits()

        # record inbound impulse-vs-penetration
        self.J_table = []
        self.J_deltas = []
        self.rebound_mode = False

        # collision lifecycle flags
        self.collision_started = False
        self.final_report_printed = False

        # diagnostics
        self.max_area_in = 0.0
        self.max_area_out = 0.0
        self.max_J_in = 0.0
        self.max_J_out = 0.0
        self.max_pair_momentum_drift = 0.0
        self.max_outbound_replay_mismatch = 0.0
        self.current_area = 0.0
        self.current_J = 0.0
        self.phase = "free"
        self.active_contact_count = 0
        self.active_pair_contact_count = 0
        self.active_wall_contact_count = 0
        self.active_bond_contact_count = 0

    
    
