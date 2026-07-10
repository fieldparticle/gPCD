import math

from gbase.GenericGenData import GenericGenData
from gbase.FunctionWall import BOUNDARY_KIND_RESERVOIR
from gbase.FunctionWall import bounds as wall_bounds


class GenReservoir(GenericGenData):
    """Generate a packed reservoir using the GenericGenData output contract."""

    def validate_simulation_configuration(self):
        errors = []

        def optional_bool(name, default=False):
            value = self.itemcfg.get(name, default)
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in ("true", "yes", "on", "1"):
                    return True
                if lowered in ("false", "no", "off", "0"):
                    return False
            errors.append(f"{name} must be true or false")
            return bool(default)

        def required_values(name, count):
            values = self.itemcfg.get(name)
            if values is None:
                errors.append(f"{name} is required")
                return ()
            if len(values) != count:
                errors.append(f"{name} must contain exactly {count} values")
                return ()
            try:
                result = tuple(float(value) for value in values)
            except (TypeError, ValueError):
                errors.append(f"{name} values must be numeric")
                return ()
            if not all(math.isfinite(value) for value in result):
                errors.append(f"{name} values must be finite")
                return ()
            return result

        dimensions = []
        for name in (
            "cell_array_width",
            "cell_array_height",
            "cell_array_depth",
        ):
            value = self.itemcfg.get(name)
            if not isinstance(value, int) or value <= 0:
                errors.append(f"{name} must be a positive integer")
            else:
                dimensions.append(value)

        try:
            target_penetration_fraction = float(
                self.itemcfg.get(
                    "target_penetration_fraction",
                    self.itemcfg.get("max_penetration_fraction", 0.5),
                )
            )
        except (TypeError, ValueError):
            errors.append("target_penetration_fraction must be numeric")
            target_penetration_fraction = None

        try:
            hard_penetration_fraction = float(
                self.itemcfg.get("hard_penetration_fraction", 0.75)
            )
        except (TypeError, ValueError):
            errors.append("hard_penetration_fraction must be numeric")
            hard_penetration_fraction = None

        if target_penetration_fraction is not None:
            if not math.isfinite(target_penetration_fraction):
                errors.append("target_penetration_fraction must be finite")
            elif not 0.0 < target_penetration_fraction < 1.0:
                errors.append("target_penetration_fraction must be between 0 and 1")

        if hard_penetration_fraction is not None:
            if not math.isfinite(hard_penetration_fraction):
                errors.append("hard_penetration_fraction must be finite")
            elif not 0.0 < hard_penetration_fraction < 1.0:
                errors.append("hard_penetration_fraction must be between 0 and 1")

        if (
            target_penetration_fraction is not None
            and hard_penetration_fraction is not None
            and math.isfinite(target_penetration_fraction)
            and math.isfinite(hard_penetration_fraction)
            and hard_penetration_fraction <= target_penetration_fraction
        ):
            errors.append(
                "hard_penetration_fraction must be greater than "
                "target_penetration_fraction"
            )

        death_bounds = required_values("death_bounds", 6)
        packing_z_bounds = required_values("packing_z_bounds", 2)
        initial_particle_velocity = required_values("initial_particle_velocity", 3)

        piston_enabled = optional_bool(
            "piston_enabled",
            self.itemcfg.get("piston_velocity") is not None,
        )
        piston_velocity = (0.0, 0.0, 0.0)
        if piston_enabled:
            piston_velocity = required_values("piston_velocity", 3)

        raw_segments = self.itemcfg.get("curve_wall_segments")
        curve_segments = []
        packing_curve_segments = []
        if not raw_segments:
            errors.append("curve_wall_segments is required and must not be empty")
        else:
            for index, raw_segment in enumerate(raw_segments):
                if len(raw_segment) != 10:
                    errors.append(
                        f"curve_wall_segments[{index}] must contain 10 values"
                    )
                    continue
                try:
                    segment = tuple(float(value) for value in raw_segment)
                except (TypeError, ValueError):
                    errors.append(
                        f"curve_wall_segments[{index}] values must be numeric"
                    )
                    continue
                if not all(math.isfinite(value) for value in segment):
                    errors.append(
                        f"curve_wall_segments[{index}] values must be finite"
                    )
                    continue
                (
                    boundary_kind,
                    independent_axis,
                    u_start,
                    u_end,
                    _f_start,
                    _a1,
                    _a2,
                    _a3,
                    normal_sign,
                    wall_flag,
                ) = segment
                if (
                    not boundary_kind.is_integer()
                    or int(boundary_kind) not in (0, 1)
                ):
                    errors.append(
                        f"curve_wall_segments[{index}] boundary_kind must be 0 or 1"
                    )
                if (
                    not independent_axis.is_integer()
                    or int(independent_axis) not in (0, 1)
                ):
                    errors.append(
                        f"curve_wall_segments[{index}] independent_axis must be 0 or 1"
                    )
                if not wall_flag.is_integer() or int(wall_flag) <= 0:
                    errors.append(
                        f"curve_wall_segments[{index}] wall_flag must be a positive integer"
                    )
                if abs(u_end - u_start) <= 1.0e-12:
                    errors.append(f"curve_wall_segments[{index}] has zero length")
                if normal_sign == 0.0:
                    errors.append(
                        f"curve_wall_segments[{index}] normal_sign must not be zero"
                    )
                curve_segments.append(segment)
                if int(round(boundary_kind)) == BOUNDARY_KIND_RESERVOIR:
                    packing_curve_segments.append(segment)

        packing_bounds = ()
        if not packing_curve_segments:
            errors.append(
                "curve_wall_segments must include at least one reservoir "
                "boundary segment (boundary_kind=1)"
            )
        else:
            packing_bounds = self.derive_packing_bounds(packing_curve_segments)

        separation = self.itemcfg.get("particle_separation_distance")
        try:
            particle_separation_distance = float(separation)
        except (TypeError, ValueError):
            errors.append("particle_separation_distance is required and numeric")
            particle_separation_distance = None

        piston_start_frame = self.itemcfg.get("piston_start_frame", 0)
        try:
            piston_start_frame_value = float(piston_start_frame)
        except (TypeError, ValueError):
            errors.append("piston_start_frame must be numeric")
            piston_start_frame_value = None

        piston_start_offset = self.itemcfg.get("piston_start_offset", 0.0)
        try:
            piston_start_offset_value = float(piston_start_offset)
        except (TypeError, ValueError):
            errors.append("piston_start_offset must be numeric")
            piston_start_offset_value = None

        if particle_separation_distance is not None:
            if not math.isfinite(particle_separation_distance):
                errors.append("particle_separation_distance must be finite")
            elif particle_separation_distance < 0.0:
                errors.append("particle_separation_distance must not be negative")

        if piston_start_frame_value is not None:
            if not math.isfinite(piston_start_frame_value):
                errors.append("piston_start_frame must be finite")
            elif piston_start_frame_value < 0.0:
                errors.append("piston_start_frame must not be negative")
            elif not piston_start_frame_value.is_integer():
                errors.append("piston_start_frame must be an integer")

        if piston_start_offset_value is not None:
            if not math.isfinite(piston_start_offset_value):
                errors.append("piston_start_offset must be finite")
            elif piston_start_offset_value < 0.0:
                errors.append("piston_start_offset must not be negative")

        if packing_bounds and packing_z_bounds and len(dimensions) == 3:
            x_start, x_end, y_bottom, y_top = packing_bounds
            z_front, z_back = packing_z_bounds
            piston_x_start = x_start - (piston_start_offset_value or 0.0)
            if x_start >= x_end:
                errors.append("packing curves: x_start must be less than x_end")
            if y_bottom >= y_top:
                errors.append("packing curves: y_bottom must be less than y_top")
            if z_front >= z_back:
                errors.append("packing_z_bounds: z_front must be less than z_back")
            if (
                x_start < 0.0
                or x_end > dimensions[0]
                or y_bottom < 0.0
                or y_top > dimensions[1]
                or z_front < 0.0
                or z_back > dimensions[2]
            ):
                errors.append("packing bounds must fit inside the cell array")
            if (
                death_bounds
                and (
                    x_start < death_bounds[0]
                    or x_end > death_bounds[1]
                    or y_bottom < death_bounds[2]
                    or y_top > death_bounds[3]
                    or z_front < death_bounds[4]
                    or z_back > death_bounds[5]
                )
            ):
                errors.append("packing bounds must fit inside death_bounds")
            if piston_x_start < 0.0:
                errors.append("piston_x_start must fit inside the cell array")
            if death_bounds and piston_x_start < death_bounds[0]:
                errors.append("piston_x_start must fit inside death_bounds")

        if initial_particle_velocity:
            if not all(math.isfinite(value) for value in initial_particle_velocity):
                errors.append("initial_particle_velocity values must be finite")

        if piston_enabled and piston_velocity:
            if not all(math.isfinite(value) for value in piston_velocity):
                errors.append("piston_velocity values must be finite")

        if death_bounds and len(dimensions) == 3:
            width, height, depth = dimensions
            for axis, minimum, maximum, domain_maximum in (
                ("x", death_bounds[0], death_bounds[1], width),
                ("y", death_bounds[2], death_bounds[3], height),
                ("z", death_bounds[4], death_bounds[5], depth),
            ):
                if minimum >= maximum:
                    errors.append(
                        f"death_bounds {axis}_min must be less than {axis}_max"
                    )
                if minimum < 0.0 or maximum > domain_maximum:
                    errors.append(
                        f"death_bounds {axis} range must fit inside the cell array"
                    )

            for index, segment in enumerate(curve_segments):
                x_min, x_max, y_min, y_max = wall_bounds(segment)
                if x_min < 0.0 or x_max > width:
                    errors.append(
                        f"curve_wall_segments[{index}] x extent is outside the cell array"
                    )
                if y_min < 0.0 or y_max > height:
                    errors.append(
                        f"curve_wall_segments[{index}] y extent is outside the cell array"
                    )

        if errors:
            raise ValueError(
                "Reservoir configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )

        self.cell_array_width, self.cell_array_height, self.cell_array_depth = dimensions
        self.death_bounds = death_bounds
        self.curve_wall_segments = curve_segments
        self.packing_curve_segments = packing_curve_segments
        self.packing_bounds = packing_bounds
        self.packing_z_bounds = packing_z_bounds
        self.piston_start_offset = piston_start_offset_value or 0.0
        self.piston_x_start = packing_bounds[0] - self.piston_start_offset
        self.piston_x_stop = packing_bounds[1]
        self.initial_particle_velocity = initial_particle_velocity
        self.piston_enabled = piston_enabled
        self.piston_velocity = piston_velocity
        self.particle_separation_distance = particle_separation_distance
        self.piston_start_frame = int(piston_start_frame_value)
        self.number_configured_particles = 0
        self.explicit_particles = []
        self.radius = float(self.itemcfg.radius)
        self.wall_contact_offset = float(self.itemcfg.wall_contact_offset)
        self.dt = float(self.itemcfg.dt)
        self.cell_occupancy_list_size = int(self.itemcfg.cell_occupancy_list_size)
        self.calculate_chamber_packing()
        return True

    def derive_packing_bounds(self, packing_curve_segments):
        x_min_values = []
        x_max_values = []
        y_min_values = []
        y_max_values = []
        for segment in packing_curve_segments:
            x_min, x_max, y_min, y_max = wall_bounds(segment)
            x_min_values.append(x_min)
            x_max_values.append(x_max)
            y_min_values.append(y_min)
            y_max_values.append(y_max)
        return (
            min(x_min_values),
            max(x_max_values),
            min(y_min_values),
            max(y_max_values),
        )

    def calculate_chamber_packing(self):
        radius = self.radius
        center_spacing = 2.0 * radius + self.particle_separation_distance
        boundary_clearance = radius * (1.0 + self.wall_contact_offset) + 1.0e-9
        x_start, x_end, y_bottom, y_top = self.packing_bounds
        z_front, z_back = self.packing_z_bounds
        z_center = 0.5 * (z_front + z_back)

        x_center_min = x_start + boundary_clearance
        x_center_max = x_end - boundary_clearance
        y_center_min = y_bottom + boundary_clearance
        y_center_max = y_top - boundary_clearance

        usable_x = x_center_max - x_center_min
        usable_y = y_center_max - y_center_min
        if usable_x < 0.0 or usable_y < 0.0:
            raise ValueError("packing bounds are too small for particle clearance")

        x_count = int(math.floor((usable_x / center_spacing) + 1.0e-12)) + 1
        y_count = int(math.floor((usable_y / center_spacing) + 1.0e-12)) + 1
        occupied_x = (x_count - 1) * center_spacing
        occupied_y = (y_count - 1) * center_spacing
        first_x = x_center_min + 0.5 * (usable_x - occupied_x)
        first_y = y_center_min + 0.5 * (usable_y - occupied_y)

        self.packing_x_count = x_count
        self.packing_y_count = y_count
        self.packing_particle_count = x_count * y_count
        self.particle_center_spacing = center_spacing
        self.boundary_particle_clearance = boundary_clearance
        self.particle_plane_z = z_center
        self.packing_first_center = (first_x, first_y, z_center)
        self.packing_last_center = (
            first_x + occupied_x,
            first_y + occupied_y,
            z_center,
        )

        self.packing_report_text = (
            "Reservoir packing report:\n"
            f"  packing bounds: {self.packing_bounds}\n"
            f"  packing z bounds: {self.packing_z_bounds}\n"
            f"  piston x range: {self.piston_x_start:g} to {self.piston_x_stop:g}\n"
            f"  radius: {radius:g}\n"
            f"  surface separation: {self.particle_separation_distance:g}\n"
            f"  center spacing: {center_spacing:g}\n"
            f"  boundary clearance: {boundary_clearance:g}\n"
            f"  grid: {x_count} columns x {y_count} rows\n"
            f"  particle count: {self.packing_particle_count}\n"
            f"  first center: {self.packing_first_center}\n"
            f"  last center: {self.packing_last_center}\n"
            f"  initial particle velocity: {self.initial_particle_velocity}\n"
            f"  piston enabled: {self.piston_enabled}\n"
            f"  piston velocity: {self.piston_velocity}"
        )
        return self.packing_particle_count

    def add_reservoir_mobile_particles(self):
        first_x, first_y, particle_z = self.packing_first_center
        velocity = self.initial_particle_velocity

        for column in range(self.packing_x_count):
            particle_x = first_x + column * self.particle_center_spacing
            for row in range(self.packing_y_count):
                particle_y = first_y + row * self.particle_center_spacing
                self.add_mobile_particle(
                    (particle_x, particle_y, particle_z),
                    velocity,
                    radius=self.radius,
                    mass=1.0,
                    collision_stiffness_q=float(
                        self.itemcfg.get("collision_stiffness_q", 0.0)
                    ),
                )

        report_text = (
            "Reservoir mobile-particle report:\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  velocity: {self.initial_particle_velocity}\n"
            f"  first particle number: 1\n"
            f"  last particle number: {self.number_active_particles}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.number_active_particles

    def report_collision_feasibility(self):
        """Print piston-driven collision timing estimates for reservoir packing."""
        min_compression_frames = float(
            self.itemcfg.get("min_compression_frames", 3.0)
        )
        target_penetration_fraction = float(
            self.itemcfg.get(
                "target_penetration_fraction",
                self.itemcfg.get("max_penetration_fraction", 0.5),
            )
        )
        hard_penetration_fraction = float(
            self.itemcfg.get("hard_penetration_fraction", 0.75)
        )
        piston_normal_speed = abs(float(self.piston_velocity[0]))
        per_frame_closing_distance = piston_normal_speed * self.dt
        target_penetration_depth = target_penetration_fraction * self.radius
        hard_penetration_depth = hard_penetration_fraction * self.radius

        first_x, _first_y, _particle_z = self.packing_first_center
        piston_to_first_gap = first_x - self.radius - self.piston_x_start
        particle_gap = self.particle_separation_distance

        def frames_for_distance(distance):
            if distance <= 0.0:
                return 0.0
            if per_frame_closing_distance <= 0.0:
                return math.inf
            return distance / per_frame_closing_distance

        frames_to_first_piston_contact = frames_for_distance(piston_to_first_gap)
        frames_to_neighbor_contact = frames_for_distance(particle_gap)
        frames_to_target_depth = frames_for_distance(target_penetration_depth)
        frames_to_hard_depth = frames_for_distance(hard_penetration_depth)
        time_to_first_piston_contact = frames_to_first_piston_contact * self.dt
        time_to_neighbor_contact = frames_to_neighbor_contact * self.dt
        time_to_target_depth = frames_to_target_depth * self.dt
        time_to_hard_depth = frames_to_hard_depth * self.dt
        stiffness_at_contact = float(self.itemcfg.get("collision_stiffness_q", 0.0))
        force_at_target_depth = stiffness_at_contact * target_penetration_depth
        source_dv_per_frame_at_max = force_at_target_depth * self.dt
        relative_dv_per_frame_at_max = source_dv_per_frame_at_max
        if (
            piston_normal_speed > 0.0
            and frames_to_target_depth > 0.0
            and math.isfinite(frames_to_target_depth)
            and target_penetration_depth > 0.0
            and self.dt > 0.0
        ):
            required_stiffness_for_max_depth = piston_normal_speed / (
                frames_to_target_depth * target_penetration_depth * self.dt
            )
        else:
            required_stiffness_for_max_depth = 0.0
        if piston_normal_speed <= 0.0:
            frames_to_cancel_relative_speed = 0.0
        elif relative_dv_per_frame_at_max > 0.0:
            frames_to_cancel_relative_speed = (
                piston_normal_speed / relative_dv_per_frame_at_max
            )
        else:
            frames_to_cancel_relative_speed = math.inf
        time_to_cancel_relative_speed = frames_to_cancel_relative_speed * self.dt

        if not self.piston_enabled:
            status = "PISTON_DISABLED"
        elif piston_normal_speed <= 0.0:
            status = "NO_PISTON_COMPRESSION"
        elif frames_to_hard_depth < 1.0:
            status = "ERROR"
        elif frames_to_target_depth < min_compression_frames:
            status = "WARNING"
        elif frames_to_cancel_relative_speed > frames_to_target_depth:
            status = "WARNING_STIFFNESS"
        else:
            status = "OK"

        report_text = (
            "Collision Feasibility:\n"
            f"  model: reservoir piston compression\n"
            f"  piston normal speed: {piston_normal_speed:.6f}\n"
            f"  dt: {self.dt:.6f}\n"
            f"  per-frame closing distance: {per_frame_closing_distance:.6f}\n"
            f"  particle surface gap: {particle_gap:.6f}\n"
            f"  piston-to-first-particle gap: {piston_to_first_gap:.6f}\n"
            f"  frames to first piston contact: "
            f"{frames_to_first_piston_contact:.3f}\n"
            f"  time to first piston contact: "
            f"{time_to_first_piston_contact:.6f}\n"
            f"  frames to neighbor contact: {frames_to_neighbor_contact:.3f}\n"
            f"  time to neighbor contact: {time_to_neighbor_contact:.6f}\n"
            f"  target penetration depth: {target_penetration_depth:.6f}\n"
            f"  hard penetration depth: {hard_penetration_depth:.6f}\n"
            f"  frames from contact to target depth: {frames_to_target_depth:.3f}\n"
            f"  time from contact to target depth: {time_to_target_depth:.6f}\n"
            f"  frames from contact to hard depth: {frames_to_hard_depth:.3f}\n"
            f"  time from contact to hard depth: {time_to_hard_depth:.6f}\n"
            f"  minimum compression frames: {min_compression_frames:.3f}\n"
            f"  stiffness at contact: {stiffness_at_contact:.6f}\n"
            f"  force at target depth: {force_at_target_depth:.6f}\n"
            f"  source dv/frame at max: {source_dv_per_frame_at_max:.6f}\n"
            f"  relative dv/frame at max: {relative_dv_per_frame_at_max:.6f}\n"
            f"  frames to cancel relative speed: "
            f"{frames_to_cancel_relative_speed:.3f}\n"
            f"  time to cancel relative speed: "
            f"{time_to_cancel_relative_speed:.6f}\n"
            f"  required stiffness for max-depth response: "
            f"{required_stiffness_for_max_depth:.6f}\n"
            f"  status: {status}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return {
            "model": "reservoir piston compression",
            "piston_normal_speed": piston_normal_speed,
            "per_frame_closing_distance": per_frame_closing_distance,
            "particle_gap": particle_gap,
            "piston_to_first_gap": piston_to_first_gap,
            "frames_to_first_piston_contact": frames_to_first_piston_contact,
            "time_to_first_piston_contact": time_to_first_piston_contact,
            "frames_to_neighbor_contact": frames_to_neighbor_contact,
            "time_to_neighbor_contact": time_to_neighbor_contact,
            "target_penetration_depth": target_penetration_depth,
            "hard_penetration_depth": hard_penetration_depth,
            "frames_to_target_depth": frames_to_target_depth,
            "time_to_target_depth": time_to_target_depth,
            "frames_to_hard_depth": frames_to_hard_depth,
            "time_to_hard_depth": time_to_hard_depth,
            "stiffness_at_contact": stiffness_at_contact,
            "force_at_target_depth": force_at_target_depth,
            "source_dv_per_frame_at_max": source_dv_per_frame_at_max,
            "relative_dv_per_frame_at_max": relative_dv_per_frame_at_max,
            "frames_to_cancel_relative_speed": frames_to_cancel_relative_speed,
            "time_to_cancel_relative_speed": time_to_cancel_relative_speed,
            "required_stiffness_for_max_depth": required_stiffness_for_max_depth,
            "status": status,
        }

    def write_test_file(self):
        test_file_name = super().write_test_file()
        with open(test_file_name, "a", encoding="ascii") as output:
            output.write(f"piston_start_frame = {self.piston_start_frame};\n")
            output.write(f"piston_x_start = {self.piston_x_start:.9f};\n")
            output.write(f"piston_x_stop = {self.piston_x_stop:.9f};\n")
            output.write(f"piston_enabled = {1 if self.piston_enabled else 0};\n")
            output.write(f"piston_velocity_x = {self.piston_velocity[0]:.9f};\n")
            output.write(f"piston_velocity_y = {self.piston_velocity[1]:.9f};\n")
            output.write(f"piston_velocity_z = {self.piston_velocity[2]:.9f};\n")
        return test_file_name

    def runner(self):
        try:
            self.validate_simulation_configuration()
        except (AttributeError, TypeError, ValueError) as error:
            print(
                "Reservoir configuration validation stopped:\n"
                f"{error}"
            )
            return False

        self.initialize_generation()
        try:
            print(self.packing_report_text)
            self.write_validation_log(self.packing_report_text)
            self.report_collision_feasibility()
            self.add_null_particle()
            self.add_reservoir_mobile_particles()
            self.add_function_wall_markers()
            self.report_cell_occupancy_capacity()
            self.write_particle_bin()
            self.write_test_file()
            self.report_generated_bounds()
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self.close_bin_file()
            print(
                "Reservoir generation stopped:\n"
                f"{type(error).__name__}: {error}"
            )
            return False

        report_text = (
            "Reservoir generation complete:\n"
            f"  binary file: {self.test_bin_name}\n"
            f"  records: {self.count}\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  boundary markers: {self.number_boundary_particles}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return True
