import math

from gbase.FunctionWall import BOUNDARY_KIND_RESERVOIR
from gbase.FunctionWall import bounds as wall_bounds
from gbase.GenericGenData import GenericGenData


class GenStreaming(GenericGenData):
    """Generate timed inlet-release particles for free-flow simulations."""

    def validate_simulation_configuration(self):
        errors = []

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

        def required_positive_float(name):
            value = self.itemcfg.get(name)
            try:
                result = float(value)
            except (TypeError, ValueError):
                errors.append(f"{name} is required and must be numeric")
                return None
            if not math.isfinite(result):
                errors.append(f"{name} must be finite")
            elif result <= 0.0:
                errors.append(f"{name} must be positive")
            return result

        def required_nonnegative_float(name):
            value = self.itemcfg.get(name)
            try:
                result = float(value)
            except (TypeError, ValueError):
                errors.append(f"{name} is required and must be numeric")
                return None
            if not math.isfinite(result):
                errors.append(f"{name} must be finite")
            elif result < 0.0:
                errors.append(f"{name} must not be negative")
            return result

        def required_positive_int(name):
            value = self.itemcfg.get(name)
            if not isinstance(value, int) or value <= 0:
                errors.append(f"{name} must be a positive integer")
                return None
            return value

        dimensions = []
        for name in (
            "cell_array_width",
            "cell_array_height",
            "cell_array_depth",
        ):
            value = required_positive_int(name)
            if value is not None:
                dimensions.append(value)

        death_bounds = required_values("death_bounds", 6)
        particle_plane_z = required_nonnegative_float("particle_plane_z")
        initial_particle_velocity = required_values("initial_particle_velocity", 3)

        self.validate_penetration_fractions(errors)

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
                        f"curve_wall_segments[{index}] wall_flag must be positive"
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

        if not packing_curve_segments:
            errors.append(
                "curve_wall_segments must include at least one streaming inlet "
                "packing segment (boundary_kind=1)"
            )
            packing_bounds = ()
        else:
            packing_bounds = self.derive_packing_bounds(packing_curve_segments)

        particle_separation_distance = required_nonnegative_float(
            "particle_separation_distance"
        )
        release_start_frame = required_nonnegative_float(
            "streaming_release_start_frame"
        )
        release_columns = required_positive_int("streaming_release_columns")
        particles_per_wave = required_positive_int("streaming_particles_per_wave")
        spacing_factor = required_positive_float("streaming_spacing_factor")

        inlet_x = self.optional_axis_value("streaming_inlet_x", errors)
        inlet_y = self.optional_axis_value("streaming_inlet_y", errors)
        if inlet_x is None and inlet_y is None:
            errors.append("streaming_inlet_x or streaming_inlet_y is required")
        if inlet_x is not None and inlet_y is not None:
            errors.append("only one of streaming_inlet_x or streaming_inlet_y may be set")

        if death_bounds:
            for axis, minimum, maximum in (
                ("x", death_bounds[0], death_bounds[1]),
                ("y", death_bounds[2], death_bounds[3]),
                ("z", death_bounds[4], death_bounds[5]),
            ):
                if minimum >= maximum:
                    errors.append(
                        f"death_bounds {axis}_min must be less than {axis}_max"
                    )

        try:
            radius = float(self.itemcfg.radius)
        except (AttributeError, TypeError, ValueError):
            errors.append("radius is required and must be numeric")
            radius = None

        if radius is not None:
            if not math.isfinite(radius):
                errors.append("radius must be finite")
            elif radius <= 0.0:
                errors.append("radius must be positive")

        if packing_bounds and particle_plane_z is not None and len(dimensions) == 3:
            x_min, x_max, y_min, y_max = packing_bounds
            width, height, depth = dimensions
            if x_min < 0.0 or x_max > width or y_min < 0.0 or y_max > height:
                errors.append("streaming packing bounds must fit inside cell array")
            if particle_plane_z >= depth:
                errors.append("particle_plane_z must fit inside cell array")
            if abs((particle_plane_z - math.floor(particle_plane_z)) - 0.5) > 1.0e-9:
                errors.append("particle_plane_z must be centered in a cell")
            if radius is not None and (
                particle_plane_z - radius < 0.0
                or particle_plane_z + radius > depth
            ):
                errors.append("particle_plane_z particle radius must fit inside cell array")
            if death_bounds and (
                x_min < death_bounds[0]
                or x_max > death_bounds[1]
                or y_min < death_bounds[2]
                or y_max > death_bounds[3]
                or particle_plane_z - (radius or 0.0) < death_bounds[4]
                or particle_plane_z + (radius or 0.0) > death_bounds[5]
            ):
                errors.append("streaming packing bounds must fit inside death_bounds")

            inlet_value = inlet_x if inlet_x is not None else inlet_y
            if inlet_x is not None and not (0.0 <= inlet_value <= width):
                errors.append("streaming_inlet_x must fit inside cell array")
            if inlet_y is not None and not (0.0 <= inlet_value <= height):
                errors.append("streaming_inlet_y must fit inside cell array")

            for index, segment in enumerate(curve_segments):
                x_min, x_max, y_min, y_max = wall_bounds(segment)
                if x_min < 0.0 or x_max > width:
                    errors.append(
                        f"curve_wall_segments[{index}] x extent is outside cell array"
                    )
                if y_min < 0.0 or y_max > height:
                    errors.append(
                        f"curve_wall_segments[{index}] y extent is outside cell array"
                    )

        self.validate_material_properties(errors)

        if errors:
            raise ValueError(
                "Streaming configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )

        self.cell_array_width, self.cell_array_height, self.cell_array_depth = dimensions
        self.death_bounds = death_bounds
        self.curve_wall_segments = curve_segments
        self.packing_curve_segments = packing_curve_segments
        self.packing_bounds = packing_bounds
        self.particle_plane_z = particle_plane_z
        self.initial_particle_velocity = initial_particle_velocity
        self.particle_separation_distance = particle_separation_distance
        self.release_start_frame = release_start_frame
        self.release_columns = release_columns
        self.particles_per_wave = particles_per_wave
        self.streaming_spacing_factor = spacing_factor
        self.streaming_inlet_axis = "x" if inlet_x is not None else "y"
        self.streaming_inlet_value = inlet_x if inlet_x is not None else inlet_y
        self.number_configured_particles = 0
        self.explicit_particles = []
        self.radius = radius
        self.wall_contact_offset = float(self.itemcfg.wall_contact_offset)
        self.dt = float(self.itemcfg.dt)
        self.cell_occupancy_list_size = int(self.itemcfg.cell_occupancy_list_size)
        self.calculate_streaming_layout()
        return True

    def validate_penetration_fractions(self, errors):
        try:
            target = float(
                self.itemcfg.get(
                    "target_penetration_fraction",
                    self.itemcfg.get("max_penetration_fraction", 0.5),
                )
            )
        except (TypeError, ValueError):
            errors.append("target_penetration_fraction must be numeric")
            target = None
        try:
            hard = float(self.itemcfg.get("hard_penetration_fraction", 0.75))
        except (TypeError, ValueError):
            errors.append("hard_penetration_fraction must be numeric")
            hard = None
        if target is not None and (
            not math.isfinite(target) or not 0.0 < target < 1.0
        ):
            errors.append("target_penetration_fraction must be between 0 and 1")
        if hard is not None and (
            not math.isfinite(hard) or not 0.0 < hard < 1.0
        ):
            errors.append("hard_penetration_fraction must be between 0 and 1")
        if (
            target is not None
            and hard is not None
            and math.isfinite(target)
            and math.isfinite(hard)
            and hard <= target
        ):
            errors.append(
                "hard_penetration_fraction must be greater than "
                "target_penetration_fraction"
            )

    def optional_axis_value(self, name, errors):
        if name not in self.itemcfg:
            return None
        try:
            value = float(self.itemcfg.get(name))
        except (TypeError, ValueError):
            errors.append(f"{name} must be numeric")
            return None
        if not math.isfinite(value):
            errors.append(f"{name} must be finite")
            return None
        return value

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

    def frames_between_waves(self):
        velocity = self.stream_normal_speed()
        if velocity <= 0.0:
            raise ValueError("initial_particle_velocity must move away from inlet")
        clearance_distance = self.streaming_spacing_factor * 2.0 * self.radius
        distance_per_frame = velocity * self.dt
        return int(math.ceil(clearance_distance / distance_per_frame))

    def stream_normal_speed(self):
        if self.streaming_inlet_axis == "x":
            return abs(float(self.initial_particle_velocity[0]))
        return abs(float(self.initial_particle_velocity[1]))

    def calculate_streaming_layout(self):
        radius = self.radius
        center_spacing = 2.0 * radius + self.particle_separation_distance
        boundary_clearance = radius * (1.0 + self.wall_contact_offset) + 1.0e-9
        x_start, x_end, y_start, y_end = self.packing_bounds

        if self.streaming_inlet_axis == "y":
            span_min = x_start + boundary_clearance
            span_max = x_end - boundary_clearance
        else:
            span_min = y_start + boundary_clearance
            span_max = y_end - boundary_clearance
        usable_span = span_max - span_min
        if usable_span < 0.0:
            raise ValueError("streaming inlet span is too small for particles")

        max_particles = int(math.floor((usable_span / center_spacing) + 1.0e-12)) + 1
        if self.particles_per_wave > max_particles:
            raise ValueError(
                "streaming_particles_per_wave does not fit in the inlet span: "
                f"requested {self.particles_per_wave}, maximum {max_particles}"
            )

        occupied_span = (self.particles_per_wave - 1) * center_spacing
        first_span_center = span_min + 0.5 * (usable_span - occupied_span)

        self.particle_center_spacing = center_spacing
        self.boundary_particle_clearance = boundary_clearance
        self.frames_per_wave = self.frames_between_waves()
        self.streaming_first_span_center = first_span_center
        self.streaming_last_span_center = first_span_center + occupied_span
        self.streaming_particle_count = (
            self.release_columns * self.particles_per_wave
        )

        self.streaming_report_text = (
            "Streaming reservoir report:\n"
            f"  packing bounds: {self.packing_bounds}\n"
            f"  particle plane z: {self.particle_plane_z:g}\n"
            f"  inlet axis: {self.streaming_inlet_axis}\n"
            f"  inlet value: {self.streaming_inlet_value:g}\n"
            f"  release start frame: {self.release_start_frame:g}\n"
            f"  release columns/waves: {self.release_columns}\n"
            f"  particles per wave: {self.particles_per_wave}\n"
            f"  frames per wave: {self.frames_per_wave}\n"
            f"  radius: {radius:g}\n"
            f"  surface separation: {self.particle_separation_distance:g}\n"
            f"  center spacing: {center_spacing:g}\n"
            f"  boundary clearance: {boundary_clearance:g}\n"
            f"  mobile particle count: {self.streaming_particle_count}\n"
            f"  initial particle velocity: {self.initial_particle_velocity}"
        )
        return self.streaming_particle_count

    def add_streaming_mobile_particles(self):
        velocity = self.initial_particle_velocity
        first_center = self.streaming_first_span_center
        for column in range(self.release_columns):
            birth_frame = self.release_start_frame + column * self.frames_per_wave
            for row in range(self.particles_per_wave):
                span_center = first_center + row * self.particle_center_spacing
                if self.streaming_inlet_axis == "y":
                    position = (
                        span_center,
                        self.streaming_inlet_value,
                        self.particle_plane_z,
                    )
                else:
                    position = (
                        self.streaming_inlet_value,
                        span_center,
                        self.particle_plane_z,
                    )
                particle = self.add_mobile_particle(
                    position,
                    velocity,
                    radius=self.radius,
                    mass=1.0,
                    collision_stiffness_q=float(
                        self.itemcfg.get("collision_stiffness_q", 0.0)
                    ),
                )
                particle.state_flg = float(birth_frame)

        report_text = (
            "Streaming mobile-particle report:\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  first release frame: {self.release_start_frame:g}\n"
            f"  last release frame: "
            f"{self.release_start_frame + (self.release_columns - 1) * self.frames_per_wave:g}\n"
            f"  frames per wave: {self.frames_per_wave}\n"
            f"  particles per wave: {self.particles_per_wave}\n"
            f"  velocity: {self.initial_particle_velocity}\n"
            f"  first particle number: 1\n"
            f"  last particle number: {self.number_active_particles}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.number_active_particles

    def report_collision_feasibility(self):
        min_compression_frames = float(
            self.itemcfg.get("min_compression_frames", 3.0)
        )
        speed = self.stream_normal_speed()
        per_frame_distance = speed * self.dt
        report_text = (
            "Collision Feasibility:\n"
            "  model: streaming inlet release\n"
            f"  stream normal speed: {speed:.6f}\n"
            f"  dt: {self.dt:.6f}\n"
            f"  per-frame travel distance: {per_frame_distance:.6f}\n"
            f"  center spacing: {self.particle_center_spacing:.6f}\n"
            f"  frames per wave: {self.frames_per_wave}\n"
            f"  release spacing distance: "
            f"{self.frames_per_wave * per_frame_distance:.6f}\n"
            f"  minimum compression frames: {min_compression_frames:.3f}\n"
            "  status: OK"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return {
            "model": "streaming inlet release",
            "stream_normal_speed": speed,
            "per_frame_distance": per_frame_distance,
            "frames_per_wave": self.frames_per_wave,
            "status": "OK",
        }

    def report_cell_occupancy_capacity(self):
        """Report conservative occupancy for all timed release records."""
        pending_count = sum(
            1
            for particle in self.p_list
            if int(round(float(particle.pnum))) != 0
            and int(round(float(particle.ptype))) <= 0
            and float(particle.state_flg) > self.release_start_frame
        )
        report_text = (
            "Streaming cell occupancy note:\n"
            f"  pending mobile particles at frame zero: {pending_count}\n"
            "  occupancy capacity is checked against all timed release records\n"
            "  purpose: conservative runtime upper bound after particles are born"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return super().report_cell_occupancy_capacity()

    def runner(self):
        try:
            self.validate_simulation_configuration()
        except (AttributeError, TypeError, ValueError) as error:
            print(
                "Streaming configuration validation stopped:\n"
                f"{error}"
            )
            return False

        self.initialize_generation()
        try:
            print(self.streaming_report_text)
            self.write_validation_log(self.streaming_report_text)
            self.report_collision_feasibility()
            self.add_null_particle()
            self.add_streaming_mobile_particles()
            self.add_function_wall_markers()
            self.report_cell_occupancy_capacity()
            self.write_particle_bin()
            self.write_test_file()
            self.report_generated_bounds()
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self.close_bin_file()
            print(
                "Streaming generation stopped:\n"
                f"{type(error).__name__}: {error}"
            )
            return False

        report_text = (
            "Streaming generation complete:\n"
            f"  binary file: {self.test_bin_name}\n"
            f"  records: {self.count}\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  boundary markers: {self.number_boundary_particles}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return True
