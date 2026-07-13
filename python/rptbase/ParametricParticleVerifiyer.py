import math

from gbase.ParametricCurve import bounds as curve_bounds
from gbase.ParametricCurve import evaluate_point
from gbase.ParametricCurve import minimum_gap
from gbase.utilities import get_cell_dimensions


class ParametricParticleVerifiyer:
    """Verify configuration for 2D parametric particle geometry."""

    CURVE_GEOMETRY_VALUE_COUNT = 9
    LOWER_WALL_FLAG = 3
    UPPER_WALL_FLAG = 4
    PARTICLE_PLANE_Z = 1.0
    EPSILON = 1.0e-9

    def verify(self, itemcfg):
        """Validate a horizontal 2D chamber and paired parametric walls."""
        errors = []

        try:
            width, height, depth = get_cell_dimensions(itemcfg)
        except (TypeError, ValueError) as error:
            errors.append(str(error))
            width = height = depth = 0

        def read_number(key):
            raw_value = itemcfg.get(key)
            if raw_value is None:
                errors.append(f"{key} is required")
                return None
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                errors.append(f"{key} must be numeric")
                return None
            if not math.isfinite(value):
                errors.append(f"{key} must be finite")
                return None
            return value

        def read_values(key, expected_count):
            raw_values = itemcfg.get(key)
            if raw_values is None:
                errors.append(f"{key} is required")
                return None
            if len(raw_values) != expected_count:
                errors.append(
                    f"{key} must contain exactly {expected_count} values"
                )
                return None
            try:
                values = tuple(float(value) for value in raw_values)
            except (TypeError, ValueError):
                errors.append(f"{key} values must be numeric")
                return None
            if not all(math.isfinite(value) for value in values):
                errors.append(f"{key} values must be finite")
                return None
            return values

        chamber = read_values("chamber_bounds", 6)
        death = read_values("death_bounds", 6)
        piston_velocity = read_values("piston_velocity", 3)
        radius = read_number("radius")
        separation = read_number("particle_separation_distance")
        wall_contact_offset = read_number("wall_contact_offset")
        collision_stiffness_q = read_number("collision_stiffness_q")
        timestep = read_number("dt")
        piston_start_value = read_number("piston_start_frame")
        occupancy_value = read_number("cell_occupancy_list_size")

        if radius is not None and radius <= 0.0:
            errors.append("radius must be positive")
        if separation is not None and separation < 0.0:
            errors.append("particle_separation_distance must not be negative")
        if wall_contact_offset is not None and wall_contact_offset < 0.0:
            errors.append("wall_contact_offset must not be negative")
        if collision_stiffness_q is not None and collision_stiffness_q < 0.0:
            errors.append("collision_stiffness_q must not be negative")
        if timestep is not None and timestep <= 0.0:
            errors.append("dt must be positive")

        cell_occupancy_list_size = None
        minimum_cell_occupancy = None
        if (
            radius is not None
            and radius > 0.0
            and separation is not None
            and separation >= 0.0
        ):
            maximum_penetration_fraction = 0.5
            minimum_center_distance = (
                2.0 * radius
                - maximum_penetration_fraction * radius
            )
            cell_interaction_span = 1.0 + 2.0 * radius
            spatial_bin_size = minimum_center_distance / math.sqrt(2.0)
            bins_per_axis = int(
                math.ceil(cell_interaction_span / spatial_bin_size)
            )
            mobile_capacity = bins_per_axis * bins_per_axis
            boundary_marker_allowance = 8
            minimum_cell_occupancy = (
                mobile_capacity + boundary_marker_allowance
            )
            cell_occupancy_list_size = 1 << (
                minimum_cell_occupancy - 1
            ).bit_length()

        if occupancy_value is not None:
            if occupancy_value <= 0.0 or not occupancy_value.is_integer():
                errors.append(
                    "cell_occupancy_list_size must be a positive integer"
                )
            elif (
                cell_occupancy_list_size is not None
                and int(occupancy_value) < cell_occupancy_list_size
            ):
                errors.append(
                    "cell_occupancy_list_size is too small: configured "
                    f"{int(occupancy_value)}, required at least "
                    f"{cell_occupancy_list_size} for the configured radius "
                    "and maximum penetration"
                )

        piston_start_frame = None
        if piston_start_value is not None:
            if piston_start_value < 0.0:
                errors.append("piston_start_frame must not be negative")
            elif not piston_start_value.is_integer():
                errors.append("piston_start_frame must be an integer")
            else:
                piston_start_frame = int(piston_start_value)

        if piston_velocity is not None:
            if piston_velocity[0] <= 0.0:
                errors.append("piston_velocity x must be positive")
            if abs(piston_velocity[1]) > self.EPSILON:
                errors.append("horizontal piston_velocity y must be zero")
            if abs(piston_velocity[2]) > self.EPSILON:
                errors.append("2D piston_velocity z must be zero")

        if chamber is not None:
            if chamber[0] >= chamber[1]:
                errors.append("chamber_bounds x_start must be less than x_end")
            if chamber[2] >= chamber[3]:
                errors.append("chamber_bounds y_bottom must be less than y_top")
            if chamber[4] != 0.0 or chamber[5] != 3.0:
                errors.append("2D chamber_bounds require z_front=0 and z_back=3")

        if death is not None:
            for axis_name, minimum, maximum in (
                ("x", death[0], death[1]),
                ("y", death[2], death[3]),
                ("z", death[4], death[5]),
            ):
                if minimum >= maximum:
                    errors.append(
                        f"death_bounds {axis_name}_min must be less than "
                        f"{axis_name}_max"
                    )

        if depth and depth <= 3:
            errors.append("cell_array_depth must be greater than 3")

        if chamber is not None and width and height and depth:
            domain_limits = (
                ("x_start", chamber[0], 0.0, width - 1.0),
                ("x_end", chamber[1], 0.0, width - 1.0),
                ("y_bottom", chamber[2], 0.0, height - 1.0),
                ("y_top", chamber[3], 0.0, height - 1.0),
                ("z_front", chamber[4], 0.0, depth - 1.0),
                ("z_back", chamber[5], 0.0, depth - 1.0),
            )
            for name, value, lower, upper in domain_limits:
                if value < lower or value > upper:
                    errors.append(
                        f"chamber_bounds {name}={value:g} is outside "
                        f"[{lower:g}, {upper:g}]"
                    )

        if death is not None and width and height and depth:
            death_domain_limits = (
                ("x_min", death[0], 0.0, float(width)),
                ("x_max", death[1], 0.0, float(width)),
                ("y_min", death[2], 0.0, float(height)),
                ("y_max", death[3], 0.0, float(height)),
                ("z_min", death[4], 0.0, float(depth)),
                ("z_max", death[5], 0.0, float(depth)),
            )
            for name, value, lower, upper in death_domain_limits:
                if value < lower or value > upper:
                    errors.append(
                        f"death_bounds {name}={value:g} is outside "
                        f"[{lower:g}, {upper:g}]"
                    )

        if chamber is not None and death is not None:
            if (
                chamber[0] < death[0]
                or chamber[1] > death[1]
                or chamber[2] < death[2]
                or chamber[3] > death[3]
                or chamber[4] < death[4]
                or chamber[5] > death[5]
            ):
                errors.append("chamber_bounds must fit inside death_bounds")

        raw_segments = itemcfg.get("curve_wall_segments")
        curve_segments = []
        if raw_segments is None:
            errors.append("curve_wall_segments is required")
        elif len(raw_segments) == 0:
            errors.append("curve_wall_segments must not be empty")
        else:
            for segment_index, raw_segment in enumerate(raw_segments):
                if len(raw_segment) not in (self.CURVE_GEOMETRY_VALUE_COUNT, 10):
                    errors.append(
                        f"curve_wall_segments[{segment_index}] must contain "
                        f"{self.CURVE_GEOMETRY_VALUE_COUNT} or 10 values"
                    )
                    continue
                try:
                    segment = tuple(float(value) for value in raw_segment)
                except (TypeError, ValueError):
                    errors.append(
                        f"curve_wall_segments[{segment_index}] values must "
                        "be numeric"
                    )
                    continue
                if not all(math.isfinite(value) for value in segment):
                    errors.append(
                        f"curve_wall_segments[{segment_index}] values must "
                        "be finite"
                    )
                    continue
                segment = segment[:self.CURVE_GEOMETRY_VALUE_COUNT]
                wall_flag = segment[8]
                if (
                    not wall_flag.is_integer()
                    or int(wall_flag)
                    not in (self.LOWER_WALL_FLAG, self.UPPER_WALL_FLAG)
                ):
                    errors.append(
                        f"curve_wall_segments[{segment_index}] wall_flag "
                        "must be 3 or 4"
                    )
                derivative_coefficients = (
                    segment[1], segment[2], segment[3],
                    segment[5], segment[6], segment[7],
                )
                if all(abs(value) <= self.EPSILON for value in derivative_coefficients):
                    errors.append(
                        f"curve_wall_segments[{segment_index}] has zero length"
                    )
                curve_segments.append(segment)

        lower_segments = [
            segment
            for segment in curve_segments
            if int(round(segment[8])) == self.LOWER_WALL_FLAG
        ]
        upper_segments = [
            segment
            for segment in curve_segments
            if int(round(segment[8])) == self.UPPER_WALL_FLAG
        ]

        if len(lower_segments) != len(upper_segments):
            errors.append(
                "curve_wall_segments must contain the same number of lower "
                "and upper wall segments"
            )

        def validate_continuity(name, segments):
            for index in range(1, len(segments)):
                previous_end = evaluate_point(segments[index - 1], 1.0)
                current_start = evaluate_point(segments[index], 0.0)
                if not (
                    math.isclose(
                        previous_end[0], current_start[0], abs_tol=self.EPSILON
                    )
                    and math.isclose(
                        previous_end[1], current_start[1], abs_tol=self.EPSILON
                    )
                ):
                    errors.append(
                        f"{name} curve segments {index - 1} and {index} "
                        "are not position-continuous"
                    )

        validate_continuity("lower", lower_segments)
        validate_continuity("upper", upper_segments)

        for pair_index, (lower, upper) in enumerate(
            zip(lower_segments, upper_segments)
        ):
            if any(
                not math.isclose(lower[index], upper[index], abs_tol=self.EPSILON)
                for index in range(4)
            ):
                errors.append(
                    f"curve pair {pair_index} must use matching x(t) "
                    "coefficients"
                )
            paired_minimum_gap = minimum_gap(lower, upper)
            if paired_minimum_gap <= 0.0:
                errors.append(f"curve pair {pair_index} crosses or closes")
            elif radius is not None and paired_minimum_gap <= 2.0 * radius:
                errors.append(
                    f"curve pair {pair_index} is narrower than one particle "
                    "diameter"
                )

        for segment_index, segment in enumerate(curve_segments):
            x_min, x_max, y_min, y_max = curve_bounds(segment)
            if width and (x_min < 0.0 or x_max > width - 1.0):
                errors.append(
                    f"curve_wall_segments[{segment_index}] x extent "
                    "is outside the cell array"
                )
            if height and (y_min < 0.0 or y_max > height - 1.0):
                errors.append(
                    f"curve_wall_segments[{segment_index}] y extent "
                    "is outside the cell array"
                )
            if death is not None and (
                x_min < death[0]
                or x_max > death[1]
                or y_min < death[2]
                or y_max > death[3]
            ):
                errors.append(
                    f"curve_wall_segments[{segment_index}] is outside "
                    "death_bounds"
                )

        if chamber is not None and lower_segments and upper_segments:
            lower_start = evaluate_point(lower_segments[0], 0.0)
            upper_start = evaluate_point(upper_segments[0], 0.0)
            lower_chamber_end = evaluate_point(lower_segments[0], 1.0)
            upper_chamber_end = evaluate_point(upper_segments[0], 1.0)
            expected_values = (
                ("lower wall start x", lower_start[0], chamber[0]),
                ("lower wall start y", lower_start[1], chamber[2]),
                ("upper wall start x", upper_start[0], chamber[0]),
                ("upper wall start y", upper_start[1], chamber[3]),
                ("lower chamber end x", lower_chamber_end[0], chamber[1]),
                ("lower chamber end y", lower_chamber_end[1], chamber[2]),
                ("upper chamber end x", upper_chamber_end[0], chamber[1]),
                ("upper chamber end y", upper_chamber_end[1], chamber[3]),
            )
            for name, actual, expected in expected_values:
                if not math.isclose(actual, expected, abs_tol=self.EPSILON):
                    errors.append(
                        f"{name}={actual:g} does not match expected "
                        f"{expected:g} from chamber_bounds"
                    )

        if death is not None and radius is not None:
            particle_z = self.PARTICLE_PLANE_Z
            if (
                particle_z - radius < death[4]
                or particle_z + radius >= death[5]
            ):
                errors.append(
                    "the full particle extent at z=1 must fit inside "
                    "death_bounds"
                )

        for key in ("data_dir", "output_file_prefix"):
            value = itemcfg.get(key)
            if value is None or not str(value).strip():
                errors.append(f"{key} is required")

        if errors:
            raise ValueError(
                "ParametricParticleVerifiyer configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )

        curve_x_min = min(curve_bounds(segment)[0] for segment in curve_segments)
        curve_x_max = max(curve_bounds(segment)[1] for segment in curve_segments)
        curve_y_min = min(curve_bounds(segment)[2] for segment in curve_segments)
        curve_y_max = max(curve_bounds(segment)[3] for segment in curve_segments)

        print(
            "ParametricParticleVerifiyer configuration: PASS\n"
            f"  cell array: {width}x{height}x{depth}\n"
            f"  chamber bounds: {chamber}\n"
            f"  death bounds: {death}\n"
            f"  curve segments: {len(curve_segments)} "
            f"({len(lower_segments)} lower, {len(upper_segments)} upper)\n"
            f"  curve bounds: x=[{curve_x_min:g}, {curve_x_max:g}], "
            f"y=[{curve_y_min:g}, {curve_y_max:g}]\n"
            f"  piston velocity: {piston_velocity}\n"
            f"  piston start frame: {piston_start_frame}\n"
            f"  minimum cell occupancy: {minimum_cell_occupancy}\n"
            f"  generated cell occupancy list size: "
            f"{cell_occupancy_list_size}\n"
            f"  configured cell occupancy list size: "
            f"{occupancy_value}\n"
            f"  particle plane: z={self.PARTICLE_PLANE_Z:g}"
        )
        return {
            "cell_array_width": width,
            "cell_array_height": height,
            "cell_array_depth": depth,
            "chamber_bounds": chamber,
            "death_bounds": death,
            "curve_wall_segments": curve_segments,
            "lower_curve_segments": lower_segments,
            "upper_curve_segments": upper_segments,
            "radius": radius,
            "particle_separation_distance": separation,
            "wall_contact_offset": wall_contact_offset,
            "collision_stiffness_q": collision_stiffness_q,
            "dt": timestep,
            "piston_start_frame": piston_start_frame,
            "piston_velocity": piston_velocity,
            "particle_plane_z": self.PARTICLE_PLANE_Z,
            "cell_occupancy_list_size": cell_occupancy_list_size,
            "configured_cell_occupancy_list_size": occupancy_value,
        }
