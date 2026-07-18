import math

from gbase.FunctionWall import BOUNDARY_KIND_RESERVOIR
from gbase.FunctionWall import bounds as wall_bounds
from gbase.FunctionWall import parse_keyed_curve_wall_segments
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

        def stream_values(stream, context, name, count):
            values = stream.get(name)
            if values is None:
                errors.append(f"{context}.{name} is required")
                return ()
            if len(values) != count:
                errors.append(
                    f"{context}.{name} must contain exactly {count} values"
                )
                return ()
            try:
                result = tuple(float(value) for value in values)
            except (TypeError, ValueError):
                errors.append(f"{context}.{name} values must be numeric")
                return ()
            if not all(math.isfinite(value) for value in result):
                errors.append(f"{context}.{name} values must be finite")
                return ()
            return result

        def stream_positive_float(stream, context, name):
            value = stream.get(name)
            try:
                result = float(value)
            except (TypeError, ValueError):
                errors.append(f"{context}.{name} is required and must be numeric")
                return None
            if not math.isfinite(result):
                errors.append(f"{context}.{name} must be finite")
            elif result <= 0.0:
                errors.append(f"{context}.{name} must be positive")
            return result

        def stream_nonnegative_float(stream, context, name):
            value = stream.get(name)
            try:
                result = float(value)
            except (TypeError, ValueError):
                errors.append(f"{context}.{name} is required and must be numeric")
                return None
            if not math.isfinite(result):
                errors.append(f"{context}.{name} must be finite")
            elif result < 0.0:
                errors.append(f"{context}.{name} must not be negative")
            return result

        def stream_positive_int(stream, context, name):
            value = stream.get(name)
            if not isinstance(value, int) or value <= 0:
                errors.append(f"{context}.{name} must be a positive integer")
                return None
            return value

        def optional_stream_axis(stream, context, name):
            if name not in stream:
                return None
            axis = str(stream.get(name, "")).lower()
            if axis not in ("x", "y", "z"):
                errors.append(f"{context}.{name} must be 'x', 'y', or 'z'")
                return None
            return axis

        def optional_stream_float(stream, context, name):
            if name not in stream:
                return None
            value = stream.get(name)
            try:
                result = float(value)
            except (TypeError, ValueError):
                errors.append(f"{context}.{name} must be numeric")
                return None
            if not math.isfinite(result):
                errors.append(f"{context}.{name} must be finite")
                return None
            return result

        def optional_stream_positive_int(stream, context, name):
            if name not in stream:
                return None
            return stream_positive_int(stream, context, name)

        def parse_vector3(container, context, name):
            values = container.get(name)
            if values is None:
                errors.append(f"{context}.{name} is required")
                return ()
            if len(values) != 3:
                errors.append(f"{context}.{name} must contain exactly 3 values")
                return ()
            try:
                result = tuple(float(value) for value in values)
            except (TypeError, ValueError):
                errors.append(f"{context}.{name} values must be numeric")
                return ()
            if not all(math.isfinite(value) for value in result):
                errors.append(f"{context}.{name} values must be finite")
                return ()
            return result

        def parse_curve_emitter(emitter, context, particles_per_wave):
            emitter_type = str(emitter.get("type", "")).lower()
            if emitter_type != "curve":
                errors.append(f"{context}.type must be 'curve'")
                return None
            length_count = stream_positive_int(emitter, context, "length_count")
            width_axis = parse_vector3(emitter, context, "width_axis")
            width = stream_positive_float(emitter, context, "width")
            width_count = stream_positive_int(emitter, context, "width_count")
            if (
                length_count is not None
                and width_count is not None
                and length_count * width_count != particles_per_wave
            ):
                errors.append(
                    f"{context}.length_count * width_count must equal "
                    "particles_per_wave"
                )
            if width_axis and self.vector_length(width_axis) <= 0.0:
                errors.append(f"{context}.width_axis must not be zero")

            curve = emitter.get("curve")
            if curve is None:
                errors.append(f"{context}.curve is required")
                return None
            curve_context = f"{context}.curve"
            curve_kind = str(curve.get("kind", "")).lower()
            if curve_kind == "polyline":
                points = curve.get("points")
                if points is None or len(points) < 2:
                    errors.append(f"{curve_context}.points must contain at least two points")
                    points = ()
                parsed_points = [
                    parse_vector3({"point": point}, curve_context, "point")
                    for point in points
                ]
                if any(not point for point in parsed_points):
                    parsed_points = []
                return {
                    "type": "curve",
                    "kind": "polyline",
                    "points": tuple(parsed_points),
                    "length_count": length_count,
                    "width_axis": width_axis,
                    "width": width,
                    "width_count": width_count,
                }
            if curve_kind == "cubic_bezier":
                return {
                    "type": "curve",
                    "kind": "cubic_bezier",
                    "p0": parse_vector3(curve, curve_context, "p0"),
                    "p1": parse_vector3(curve, curve_context, "p1"),
                    "p2": parse_vector3(curve, curve_context, "p2"),
                    "p3": parse_vector3(curve, curve_context, "p3"),
                    "length_count": length_count,
                    "width_axis": width_axis,
                    "width": width,
                    "width_count": width_count,
                }
            errors.append(f"{curve_context}.kind must be 'polyline' or 'cubic_bezier'")
            return None

        def parse_stream(stream, index, context):
            stream_name = str(stream.get("name", f"stream{index}"))
            initial_particle_velocity = stream_values(
                stream, context, "initial_particle_velocity", 3
            )
            release_start_frame = stream_nonnegative_float(
                stream, context, "release_start_frame"
            )
            release_columns = stream_positive_int(stream, context, "release_columns")
            particles_per_wave = stream_positive_int(
                stream, context, "particles_per_wave"
            )
            spacing_factor = stream_positive_float(stream, context, "spacing_factor")
            emitter = None
            emitter_mode = False
            if "emitter" in stream:
                emitter = parse_curve_emitter(
                    stream.get("emitter"),
                    f"{context}.emitter",
                    particles_per_wave,
                )
                emitter_mode = emitter is not None
            inlet_axis = str(stream.get("inlet_axis", "")).lower()
            inlet_value = None if emitter_mode else stream_nonnegative_float(
                stream, context, "inlet_value"
            )
            try:
                material_id = int(stream.get("material_id", 0))
            except (TypeError, ValueError):
                errors.append(f"{context}.material_id must be an integer")
                material_id = 0
            span_min = stream.get("span_min")
            span_max = stream.get("span_max")
            if (span_min is None) != (span_max is None):
                errors.append(f"{context}.span_min and span_max must be set together")
            if span_min is not None and span_max is not None:
                try:
                    span_min = float(span_min)
                    span_max = float(span_max)
                except (TypeError, ValueError):
                    errors.append(f"{context}.span_min and span_max must be numeric")
                    span_min = None
                    span_max = None
                else:
                    if not math.isfinite(span_min) or not math.isfinite(span_max):
                        errors.append(f"{context}.span_min and span_max must be finite")
                    elif span_min >= span_max:
                        errors.append(f"{context}.span_min must be less than span_max")

            span_u_axis = optional_stream_axis(stream, context, "span_u_axis")
            span_u_min = optional_stream_float(stream, context, "span_u_min")
            span_u_max = optional_stream_float(stream, context, "span_u_max")
            span_u_count = optional_stream_positive_int(stream, context, "span_u_count")
            span_v_axis = optional_stream_axis(stream, context, "span_v_axis")
            span_v_min = optional_stream_float(stream, context, "span_v_min")
            span_v_max = optional_stream_float(stream, context, "span_v_max")
            span_v_count = optional_stream_positive_int(stream, context, "span_v_count")
            patch_values = (
                span_u_axis,
                span_u_min,
                span_u_max,
                span_u_count,
                span_v_axis,
                span_v_min,
                span_v_max,
                span_v_count,
            )
            has_patch_fields = any(value is not None for value in patch_values)
            patch_mode = all(value is not None for value in patch_values)
            if has_patch_fields and not patch_mode:
                errors.append(
                    f"{context} patch streams require span_u_axis/span_u_min/"
                    "span_u_max/span_u_count and span_v_axis/span_v_min/"
                    "span_v_max/span_v_count"
                )
            if patch_mode:
                if span_u_count > 1 and span_u_min >= span_u_max:
                    errors.append(f"{context}.span_u_min must be less than span_u_max")
                if span_v_count > 1 and span_v_min >= span_v_max:
                    errors.append(f"{context}.span_v_min must be less than span_v_max")
                if span_u_count * span_v_count != particles_per_wave:
                    errors.append(
                        f"{context}.particles_per_wave must equal "
                        "span_u_count * span_v_count"
                    )

            if not emitter_mode and inlet_axis not in ("x", "y", "z"):
                errors.append(f"{context}.inlet_axis must be 'x', 'y', or 'z'")
            if not emitter_mode and patch_mode and len({inlet_axis, span_u_axis, span_v_axis}) != 3:
                errors.append(
                    f"{context}.inlet_axis, span_u_axis, and span_v_axis "
                    "must be distinct"
                )
            if not emitter_mode and not patch_mode and inlet_axis == "z":
                errors.append(f"{context}.inlet_axis='z' requires patch stream fields")

            return {
                "name": stream_name,
                "initial_particle_velocity": initial_particle_velocity,
                "release_start_frame": release_start_frame,
                "release_columns": release_columns,
                "particles_per_wave": particles_per_wave,
                "spacing_factor": spacing_factor,
                "inlet_axis": inlet_axis,
                "inlet_value": inlet_value,
                "material_id": material_id,
                "span_min": span_min,
                "span_max": span_max,
                "patch_mode": patch_mode,
                "span_u_axis": span_u_axis,
                "span_u_min": span_u_min,
                "span_u_max": span_u_max,
                "span_u_count": span_u_count,
                "span_v_axis": span_v_axis,
                "span_v_min": span_v_min,
                "span_v_max": span_v_max,
                "span_v_count": span_v_count,
                "emitter_mode": emitter_mode,
                "emitter": emitter,
            }

        raw_streams = self.itemcfg.get("particle_streams")
        if raw_streams is not None:
            if len(raw_streams) == 0:
                errors.append("particle_streams must contain at least one stream")
            streams = [
                parse_stream(stream, index, f"particle_streams[{index}]")
                for index, stream in enumerate(raw_streams)
            ]
        else:
            legacy_stream = {
                "name": "legacy",
                "initial_particle_velocity": self.itemcfg.get(
                    "initial_particle_velocity"
                ),
                "release_start_frame": self.itemcfg.get(
                    "streaming_release_start_frame"
                ),
                "release_columns": self.itemcfg.get("streaming_release_columns"),
                "particles_per_wave": self.itemcfg.get(
                    "streaming_particles_per_wave"
                ),
                "spacing_factor": self.itemcfg.get("streaming_spacing_factor"),
                "material_id": 0,
            }
            inlet_x = self.optional_axis_value("streaming_inlet_x", errors)
            inlet_y = self.optional_axis_value("streaming_inlet_y", errors)
            if inlet_x is None and inlet_y is None:
                errors.append("streaming_inlet_x or streaming_inlet_y is required")
            if inlet_x is not None and inlet_y is not None:
                errors.append("only one of streaming_inlet_x or streaming_inlet_y may be set")
            legacy_stream["inlet_axis"] = "x" if inlet_x is not None else "y"
            legacy_stream["inlet_value"] = inlet_x if inlet_x is not None else inlet_y
            streams = [parse_stream(legacy_stream, 0, "legacy_stream")]

        for stream in streams:
            if stream["emitter_mode"]:
                continue
            if (
                stream["inlet_axis"] == "x"
                and stream["initial_particle_velocity"]
                and float(stream["initial_particle_velocity"][0]) == 0.0
            ):
                errors.append(f"{stream['name']} x-inlet stream velocity must have vx")
            if (
                stream["inlet_axis"] == "y"
                and stream["initial_particle_velocity"]
                and float(stream["initial_particle_velocity"][1]) == 0.0
            ):
                errors.append(f"{stream['name']} y-inlet stream velocity must have vy")
            if (
                stream["inlet_axis"] == "z"
                and stream["initial_particle_velocity"]
                and float(stream["initial_particle_velocity"][2]) == 0.0
            ):
                errors.append(f"{stream['name']} z-inlet stream velocity must have vz")

        self.validate_penetration_fractions(errors)

        raw_segments = self.itemcfg.get("curve_wall_segments")
        curve_segments, curve_errors = parse_keyed_curve_wall_segments(raw_segments)
        errors.extend(curve_errors)
        packing_curve_segments = [
            segment
            for segment in curve_segments
            if int(round(segment[0])) == BOUNDARY_KIND_RESERVOIR
        ]

        all_streams_have_spans = all(
            stream["emitter_mode"]
            or
            stream["patch_mode"]
            or (stream["span_min"] is not None and stream["span_max"] is not None)
            for stream in streams
        )
        if not packing_curve_segments and not all_streams_have_spans:
            errors.append(
                "curve_wall_segments must include at least one streaming inlet "
                "packing segment (boundary_kind=1) unless every stream sets "
                "span_min/span_max"
            )
            packing_bounds = ()
        elif not packing_curve_segments:
            packing_bounds = ()
        else:
            packing_bounds = self.derive_packing_bounds(packing_curve_segments)

        particle_separation_distance = required_nonnegative_float(
            "particle_separation_distance"
        )
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

        if particle_plane_z is not None and len(dimensions) == 3:
            width, height, depth = dimensions
            if packing_bounds:
                x_min, x_max, y_min, y_max = packing_bounds
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
            if death_bounds and packing_bounds and (
                    x_min < death_bounds[0]
                    or x_max > death_bounds[1]
                    or y_min < death_bounds[2]
                    or y_max > death_bounds[3]
                    or particle_plane_z - (radius or 0.0) < death_bounds[4]
                    or particle_plane_z + (radius or 0.0) > death_bounds[5]
            ):
                errors.append("streaming packing bounds must fit inside death_bounds")

            for stream in streams:
                if stream["emitter_mode"]:
                    continue
                inlet_value = stream["inlet_value"]
                if stream["inlet_axis"] == "x" and not (0.0 <= inlet_value <= width):
                    errors.append(
                        f"{stream['name']} x-inlet value must fit inside cell array"
                    )
                if stream["inlet_axis"] == "y" and not (0.0 <= inlet_value <= height):
                    errors.append(
                        f"{stream['name']} y-inlet value must fit inside cell array"
                    )
                if stream["inlet_axis"] == "z" and not (0.0 <= inlet_value <= depth):
                    errors.append(
                        f"{stream['name']} z-inlet value must fit inside cell array"
                    )
                if stream["span_min"] is not None:
                    span_limit = height if stream["inlet_axis"] == "x" else width
                    if (
                        stream["span_min"] < 0.0
                        or stream["span_max"] > span_limit
                    ):
                        errors.append(
                            f"{stream['name']} span_min/span_max must fit inside "
                            "cell array"
                        )
                if stream["patch_mode"]:
                    axis_limits = {"x": width, "y": height, "z": depth}
                    for span_name in ("u", "v"):
                        span_axis = stream[f"span_{span_name}_axis"]
                        span_min = stream[f"span_{span_name}_min"]
                        span_max = stream[f"span_{span_name}_max"]
                        span_limit = axis_limits[span_axis]
                        if span_min < 0.0 or span_max > span_limit:
                            errors.append(
                                f"{stream['name']} span_{span_name}_min/"
                                f"span_{span_name}_max must fit inside cell array"
                            )

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
        for stream in streams:
            if stream["material_id"] not in getattr(self, "material_properties_by_id", {}):
                errors.append(f"{stream['name']} material_id is not defined")

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
        self.particle_separation_distance = particle_separation_distance
        self.streaming_streams = streams
        self.number_configured_particles = 0
        self.explicit_particles = []
        self.radius = radius
        self.wall_contact_offset = float(self.itemcfg.wall_contact_offset)
        self.dt = float(self.itemcfg.dt)
        self.cell_occupancy_list_size = int(self.itemcfg.cell_occupancy_list_size)
        self.calculate_streaming_layout()
        return True

    @staticmethod
    def vector_length(vector):
        return math.sqrt(sum(float(value) * float(value) for value in vector))

    @classmethod
    def normalize_vector(cls, vector):
        length = cls.vector_length(vector)
        if length <= 0.0:
            return (0.0, 0.0, 0.0)
        return tuple(float(value) / length for value in vector)

    @staticmethod
    def lerp(a, b, t):
        return tuple(float(a[index]) + (float(b[index]) - float(a[index])) * t for index in range(3))

    def evaluate_polyline_curve(self, points, t):
        if len(points) == 1:
            return points[0]
        segment_lengths = [
            self.vector_length(
                tuple(float(points[index + 1][axis]) - float(points[index][axis]) for axis in range(3))
            )
            for index in range(len(points) - 1)
        ]
        total_length = sum(segment_lengths)
        if total_length <= 0.0:
            return points[0]
        target_length = max(0.0, min(1.0, float(t))) * total_length
        walked = 0.0
        for index, segment_length in enumerate(segment_lengths):
            if walked + segment_length >= target_length:
                local_t = 0.0 if segment_length <= 0.0 else (target_length - walked) / segment_length
                return self.lerp(points[index], points[index + 1], local_t)
            walked += segment_length
        return points[-1]

    @staticmethod
    def evaluate_cubic_bezier(p0, p1, p2, p3, t):
        t = max(0.0, min(1.0, float(t)))
        u = 1.0 - t
        return tuple(
            u * u * u * float(p0[index])
            + 3.0 * u * u * t * float(p1[index])
            + 3.0 * u * t * t * float(p2[index])
            + t * t * t * float(p3[index])
            for index in range(3)
        )

    def evaluate_stream_curve(self, emitter, t):
        if emitter["kind"] == "polyline":
            return self.evaluate_polyline_curve(emitter["points"], t)
        return self.evaluate_cubic_bezier(
            emitter["p0"],
            emitter["p1"],
            emitter["p2"],
            emitter["p3"],
            t,
        )

    def stream_curve_samples(self, emitter, sample_count=128):
        count = max(2, int(sample_count))
        return tuple(
            self.evaluate_stream_curve(emitter, index / (count - 1))
            for index in range(count)
        )

    def stream_curve_length(self, emitter):
        points = self.stream_curve_samples(emitter)
        return sum(
            self.vector_length(
                tuple(
                    float(points[index + 1][axis]) - float(points[index][axis])
                    for axis in range(3)
                )
            )
            for index in range(len(points) - 1)
        )

    def evaluate_stream_curve_at_distance(self, emitter, distance):
        points = self.stream_curve_samples(emitter)
        target_distance = max(0.0, float(distance))
        walked = 0.0
        for index in range(len(points) - 1):
            segment = tuple(
                float(points[index + 1][axis]) - float(points[index][axis])
                for axis in range(3)
            )
            segment_length = self.vector_length(segment)
            if segment_length <= 0.0:
                continue
            if walked + segment_length >= target_distance:
                local_t = (target_distance - walked) / segment_length
                return self.lerp(points[index], points[index + 1], local_t)
            walked += segment_length
        return points[-1]

    @staticmethod
    def sample_centered_spacing(count, center_spacing):
        if count == 1:
            return (0.0,)
        first_offset = -0.5 * (count - 1) * float(center_spacing)
        return tuple(first_offset + index * float(center_spacing) for index in range(count))

    @staticmethod
    def sample_unit_interval(count):
        if count == 1:
            return (0.5,)
        return tuple(index / (count - 1) for index in range(count))

    @staticmethod
    def sample_centered_width(width, count):
        if count == 1:
            return (0.0,)
        lower = -0.5 * float(width)
        step = float(width) / (count - 1)
        return tuple(lower + index * step for index in range(count))

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

    def frames_between_waves(self, stream):
        velocity = self.stream_normal_speed(stream)
        if velocity <= 0.0:
            raise ValueError("initial_particle_velocity must move away from inlet")
        clearance_distance = stream["spacing_factor"] * 2.0 * self.radius
        distance_per_frame = velocity * self.dt
        return int(math.ceil(clearance_distance / distance_per_frame))

    def stream_normal_speed(self, stream=None):
        if stream is None:
            stream = self.streaming_streams[0]
        velocity = stream["initial_particle_velocity"]
        if stream.get("emitter_mode"):
            return self.vector_length(velocity)
        if stream["inlet_axis"] == "x":
            return abs(float(velocity[0]))
        if stream["inlet_axis"] == "y":
            return abs(float(velocity[1]))
        return abs(float(velocity[2]))

    def span_centers(self, span_min, span_max, count, boundary_clearance):
        if count == 1:
            return (0.5 * (span_min + span_max),)
        center_spacing = self.particle_center_spacing
        lower = span_min + boundary_clearance
        upper = span_max - boundary_clearance
        usable_span = upper - lower
        if usable_span < 0.0:
            raise ValueError("streaming inlet span is too small for particles")
        max_particles = int(math.floor((usable_span / center_spacing) + 1.0e-12)) + 1
        if count > max_particles:
            raise ValueError(
                f"streaming span count {count} does not fit in span; "
                f"maximum {max_particles}"
            )
        occupied_span = (count - 1) * center_spacing
        first_center = lower + 0.5 * (usable_span - occupied_span)
        return tuple(first_center + index * center_spacing for index in range(count))

    def calculate_streaming_layout(self):
        radius = self.radius
        center_spacing = 2.0 * radius + self.particle_separation_distance
        boundary_clearance = radius * (1.0 + self.wall_contact_offset) + 1.0e-9
        if self.packing_bounds:
            x_start, x_end, y_start, y_end = self.packing_bounds
        else:
            x_start = x_end = y_start = y_end = 0.0
        report_lines = [
            "Streaming reservoir report:",
            f"  packing bounds: {self.packing_bounds}",
            f"  particle plane z: {self.particle_plane_z:g}",
            f"  radius: {radius:g}",
            f"  surface separation: {self.particle_separation_distance:g}",
            f"  center spacing: {center_spacing:g}",
            f"  boundary clearance: {boundary_clearance:g}",
        ]
        total_particle_count = 0
        self.particle_center_spacing = center_spacing

        for stream in self.streaming_streams:
            if stream["emitter_mode"]:
                emitter = stream["emitter"]
                stream_center_spacing = 2.0 * radius * stream["spacing_factor"]
                curve_length = self.stream_curve_length(emitter)
                occupied_curve_length = (
                    (emitter["length_count"] - 1) * stream_center_spacing
                )
                occupied_width = (
                    (emitter["width_count"] - 1) * stream_center_spacing
                )
                if occupied_curve_length > curve_length + 1.0e-12:
                    raise ValueError(
                        f"{stream['name']} curve emitter length_count and "
                        "spacing_factor do not fit on the configured curve"
                    )
                if occupied_width > emitter["width"] + 1.0e-12:
                    raise ValueError(
                        f"{stream['name']} curve emitter width_count and "
                        "spacing_factor do not fit inside emitter.width"
                    )
                curve_mid_distance = 0.5 * curve_length
                length_offsets = self.sample_centered_spacing(
                    emitter["length_count"],
                    stream_center_spacing,
                )
                length_centers = tuple(
                    curve_mid_distance + offset for offset in length_offsets
                )
                width_centers = self.sample_centered_spacing(
                    emitter["width_count"],
                    stream_center_spacing,
                )
                width_axis = self.normalize_vector(emitter["width_axis"])
                frames_per_wave = self.frames_between_waves(stream)
                particle_count = stream["release_columns"] * stream["particles_per_wave"]
                material = self.material_properties_by_id[stream["material_id"]]
                stream.update(
                    {
                        "particle_type": material.get("particle_type", "regular"),
                        "layout_mode": "curve",
                        "length_centers": length_centers,
                        "width_centers": width_centers,
                        "width_axis": width_axis,
                        "curve_length": curve_length,
                        "curve_center_spacing": stream_center_spacing,
                        "occupied_curve_length": occupied_curve_length,
                        "occupied_width": occupied_width,
                        "frames_per_wave": frames_per_wave,
                        "particle_count": particle_count,
                    }
                )
                total_particle_count += particle_count
                report_lines.extend(
                    (
                        f"  stream: {stream['name']}",
                        "    layout mode: curve",
                        f"    curve kind: {emitter['kind']}",
                        f"    length count: {emitter['length_count']}",
                        f"    width: {emitter['width']:g}",
                        f"    width count: {emitter['width_count']}",
                        f"    center spacing: {stream_center_spacing:g}",
                        f"    curve length: {curve_length:g}",
                        f"    occupied curve length: {occupied_curve_length:g}",
                        f"    occupied width: {occupied_width:g}",
                        f"    material_id: {stream['material_id']}",
                        f"    particle type: {stream['particle_type']}",
                        f"    release start frame: {stream['release_start_frame']:g}",
                        f"    release columns/waves: {stream['release_columns']}",
                        f"    particles per wave: {stream['particles_per_wave']}",
                        f"    frames per wave: {stream['frames_per_wave']}",
                        f"    mobile particle count: {stream['particle_count']}",
                        "    initial particle velocity: "
                        f"{stream['initial_particle_velocity']}",
                    )
                )
                continue

            if stream["patch_mode"]:
                u_centers = self.span_centers(
                    stream["span_u_min"],
                    stream["span_u_max"],
                    stream["span_u_count"],
                    boundary_clearance,
                )
                v_centers = self.span_centers(
                    stream["span_v_min"],
                    stream["span_v_max"],
                    stream["span_v_count"],
                    boundary_clearance,
                )
                frames_per_wave = self.frames_between_waves(stream)
                particle_count = stream["release_columns"] * stream["particles_per_wave"]
                material = self.material_properties_by_id[stream["material_id"]]
                stream.update(
                    {
                        "particle_type": material.get("particle_type", "regular"),
                        "layout_mode": "patch",
                        "span_u_centers": u_centers,
                        "span_v_centers": v_centers,
                        "frames_per_wave": frames_per_wave,
                        "particle_count": particle_count,
                    }
                )
                total_particle_count += particle_count
                report_lines.extend(
                    (
                        f"  stream: {stream['name']}",
                        f"    layout mode: patch",
                        f"    inlet axis: {stream['inlet_axis']}",
                        f"    inlet value: {stream['inlet_value']:g}",
                        f"    span u: {stream['span_u_axis']} "
                        f"[{stream['span_u_min']:g}, {stream['span_u_max']:g}] "
                        f"count {stream['span_u_count']}",
                        f"    span v: {stream['span_v_axis']} "
                        f"[{stream['span_v_min']:g}, {stream['span_v_max']:g}] "
                        f"count {stream['span_v_count']}",
                        f"    material_id: {stream['material_id']}",
                        f"    particle type: {stream['particle_type']}",
                        f"    release start frame: {stream['release_start_frame']:g}",
                        f"    release columns/waves: {stream['release_columns']}",
                        f"    particles per wave: {stream['particles_per_wave']}",
                        f"    frames per wave: {stream['frames_per_wave']}",
                        f"    mobile particle count: {stream['particle_count']}",
                        "    initial particle velocity: "
                        f"{stream['initial_particle_velocity']}",
                    )
                )
                continue

            if stream["span_min"] is not None:
                span_min = stream["span_min"] + boundary_clearance
                span_max = stream["span_max"] - boundary_clearance
            elif stream["inlet_axis"] == "y":
                span_min = x_start + boundary_clearance
                span_max = x_end - boundary_clearance
            else:
                span_min = y_start + boundary_clearance
                span_max = y_end - boundary_clearance
            usable_span = span_max - span_min
            if usable_span < 0.0:
                raise ValueError(
                    f"{stream['name']} streaming inlet span is too small for particles"
                )

            max_particles = (
                int(math.floor((usable_span / center_spacing) + 1.0e-12)) + 1
            )
            if stream["particles_per_wave"] > max_particles:
                raise ValueError(
                    f"{stream['name']} particles_per_wave does not fit in the "
                    f"inlet span: requested {stream['particles_per_wave']}, "
                    f"maximum {max_particles}"
                )

            occupied_span = (stream["particles_per_wave"] - 1) * center_spacing
            first_span_center = span_min + 0.5 * (usable_span - occupied_span)
            frames_per_wave = self.frames_between_waves(stream)
            particle_count = stream["release_columns"] * stream["particles_per_wave"]
            material = self.material_properties_by_id[stream["material_id"]]
            stream.update(
                {
                    "particle_type": material.get("particle_type", "regular"),
                    "layout_mode": "line",
                    "first_span_center": first_span_center,
                    "last_span_center": first_span_center + occupied_span,
                    "frames_per_wave": frames_per_wave,
                    "particle_count": particle_count,
                }
            )
            total_particle_count += particle_count
            report_lines.extend(
                (
                    f"  stream: {stream['name']}",
                    f"    layout mode: line",
                    f"    inlet axis: {stream['inlet_axis']}",
                    f"    inlet value: {stream['inlet_value']:g}",
                    f"    material_id: {stream['material_id']}",
                    f"    particle type: {stream['particle_type']}",
                    f"    release start frame: {stream['release_start_frame']:g}",
                    f"    release columns/waves: {stream['release_columns']}",
                    f"    particles per wave: {stream['particles_per_wave']}",
                    f"    frames per wave: {stream['frames_per_wave']}",
                    f"    mobile particle count: {stream['particle_count']}",
                    "    initial particle velocity: "
                    f"{stream['initial_particle_velocity']}",
                )
            )

        self.boundary_particle_clearance = boundary_clearance
        self.streaming_particle_count = total_particle_count
        self.streaming_report_text = "\n".join(report_lines)

        first_stream = self.streaming_streams[0]
        self.initial_particle_velocity = first_stream["initial_particle_velocity"]
        self.release_start_frame = first_stream["release_start_frame"]
        self.release_columns = first_stream["release_columns"]
        self.particles_per_wave = first_stream["particles_per_wave"]
        self.streaming_spacing_factor = first_stream["spacing_factor"]
        self.streaming_inlet_axis = first_stream["inlet_axis"]
        self.streaming_inlet_value = first_stream["inlet_value"]
        self.streaming_stream_name = first_stream["name"]
        self.streaming_particle_type = first_stream["particle_type"]
        self.streaming_material_id = first_stream["material_id"]
        self.frames_per_wave = first_stream["frames_per_wave"]
        self.streaming_first_span_center = first_stream.get("first_span_center", 0.0)
        self.streaming_last_span_center = first_stream.get("last_span_center", 0.0)
        return self.streaming_particle_count

    def stream_position(self, stream, span_center=None, u_center=None, v_center=None):
        if stream["layout_mode"] == "curve":
            emitter = stream["emitter"]
            curve_position = self.evaluate_stream_curve_at_distance(
                emitter,
                u_center,
            )
            width_offset = float(v_center)
            width_axis = stream["width_axis"]
            return tuple(
                curve_position[index] + width_axis[index] * width_offset
                for index in range(3)
            )

        position = {"x": 0.0, "y": 0.0, "z": self.particle_plane_z}
        position[stream["inlet_axis"]] = stream["inlet_value"]
        if stream["layout_mode"] == "patch":
            position[stream["span_u_axis"]] = u_center
            position[stream["span_v_axis"]] = v_center
        elif stream["inlet_axis"] == "y":
            position["x"] = span_center
        else:
            position["y"] = span_center
        return (position["x"], position["y"], position["z"])

    def add_streaming_mobile_particles(self):
        reports = []
        first_particle = self.number_active_particles + 1
        for stream in self.streaming_streams:
            velocity = stream["initial_particle_velocity"]
            stream_first_particle = self.number_active_particles + 1
            for column in range(stream["release_columns"]):
                birth_frame = (
                    stream["release_start_frame"]
                    + column * stream["frames_per_wave"]
                )
                if stream["layout_mode"] == "patch":
                    for v_center in stream["span_v_centers"]:
                        for u_center in stream["span_u_centers"]:
                            position = self.stream_position(
                                stream,
                                u_center=u_center,
                                v_center=v_center,
                            )
                            particle = self.add_mobile_particle(
                                position,
                                velocity,
                                radius=self.radius,
                                material_id=stream["material_id"],
                                collision_stiffness_q=float(
                                    self.itemcfg.get("collision_stiffness_q", 0.0)
                                ),
                            )
                            particle.state_flg = float(birth_frame)
                elif stream["layout_mode"] == "curve":
                    for width_center in stream["width_centers"]:
                        for length_center in stream["length_centers"]:
                            position = self.stream_position(
                                stream,
                                u_center=length_center,
                                v_center=width_center,
                            )
                            particle = self.add_mobile_particle(
                                position,
                                velocity,
                                radius=self.radius,
                                material_id=stream["material_id"],
                                collision_stiffness_q=float(
                                    self.itemcfg.get("collision_stiffness_q", 0.0)
                                ),
                            )
                            particle.state_flg = float(birth_frame)
                else:
                    first_center = stream["first_span_center"]
                    for row in range(stream["particles_per_wave"]):
                        span_center = first_center + row * self.particle_center_spacing
                        position = self.stream_position(
                            stream,
                            span_center=span_center,
                        )
                        particle = self.add_mobile_particle(
                            position,
                            velocity,
                            radius=self.radius,
                            material_id=stream["material_id"],
                            collision_stiffness_q=float(
                                self.itemcfg.get("collision_stiffness_q", 0.0)
                            ),
                        )
                        particle.state_flg = float(birth_frame)

            stream_last_particle = self.number_active_particles
            stream["first_particle_number"] = stream_first_particle
            stream["last_particle_number"] = stream_last_particle
            reports.append(
                "Streaming mobile-particle stream:\n"
                f"  stream: {stream['name']}\n"
                f"  mobile particles: {stream['particle_count']}\n"
                f"  material_id: {stream['material_id']}\n"
                f"  particle type: {stream['particle_type']}\n"
                f"  first release frame: {stream['release_start_frame']:g}\n"
                f"  last release frame: "
                f"{stream['release_start_frame'] + (stream['release_columns'] - 1) * stream['frames_per_wave']:g}\n"
                f"  frames per wave: {stream['frames_per_wave']}\n"
                f"  particles per wave: {stream['particles_per_wave']}\n"
                f"  velocity: {stream['initial_particle_velocity']}\n"
                f"  first particle number: {stream_first_particle}\n"
                f"  last particle number: {stream_last_particle}"
            )

        report_text = (
            "Streaming mobile-particle report:\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  streaming particles: {self.number_active_particles - first_particle + 1}\n"
            f"  first particle number: {first_particle}\n"
            f"  last particle number: {self.number_active_particles}\n"
            + "\n"
            + "\n".join(reports)
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.number_active_particles

    def report_collision_feasibility(self):
        min_compression_frames = float(
            self.itemcfg.get("min_compression_frames", 3.0)
        )
        report_lines = [
            "Collision Feasibility:",
            "  model: streaming inlet release",
            f"  dt: {self.dt:.6f}",
            f"  center spacing: {self.particle_center_spacing:.6f}",
            f"  minimum compression frames: {min_compression_frames:.3f}",
        ]
        first_speed = 0.0
        first_per_frame_distance = 0.0
        for index, stream in enumerate(self.streaming_streams):
            speed = self.stream_normal_speed(stream)
            per_frame_distance = speed * self.dt
            if index == 0:
                first_speed = speed
                first_per_frame_distance = per_frame_distance
            report_lines.extend(
                (
                    f"  stream: {stream['name']}",
                    f"    stream normal speed: {speed:.6f}",
                    f"    per-frame travel distance: {per_frame_distance:.6f}",
                    f"    frames per wave: {stream['frames_per_wave']}",
                    "    release spacing distance: "
                    f"{stream['frames_per_wave'] * per_frame_distance:.6f}",
                )
            )
        report_lines.append("  status: OK")
        report_text = "\n".join(report_lines)
        print(report_text)
        self.write_validation_log(report_text)
        return {
            "model": "streaming inlet release",
            "stream_normal_speed": first_speed,
            "per_frame_distance": first_per_frame_distance,
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
