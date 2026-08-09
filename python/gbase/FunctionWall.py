import math
from collections.abc import Mapping


BOUNDARY_KIND_REGULAR = 0
BOUNDARY_KIND_RESERVOIR = 1
AXIS_X = 0
AXIS_Y = 1

BOUNDARY_KIND_BY_NAME = {
    "regular": BOUNDARY_KIND_REGULAR,
    "reservoir": BOUNDARY_KIND_RESERVOIR,
}

FUNCTION_AXIS_BY_NAME = {
    "y_of_x": AXIS_X,
    "x_of_y": AXIS_Y,
}

WALL_PARAMETER_DEFAULT = -1.0
WALL_PARAMETER_FIELDS = (
    "wall_collision_stiffness_q",
    "wall_target_penetration_fraction",
    "wall_hard_penetration_fraction",
    "wall_compression_stiffness_gain",
    "wall_compression_stiffness_power",
)


def _required_field(segment_name, segment_config, field_name, errors):
    if field_name not in segment_config:
        errors.append(f"curve_wall_segments.{segment_name}.{field_name} is required")
        return None
    return segment_config[field_name]


def _required_number(segment_name, segment_config, field_name, errors):
    raw_value = _required_field(segment_name, segment_config, field_name, errors)
    if raw_value is None:
        return None
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        errors.append(f"curve_wall_segments.{segment_name}.{field_name} must be numeric")
        return None
    if not math.isfinite(value):
        errors.append(f"curve_wall_segments.{segment_name}.{field_name} must be finite")
        return None
    return value


def _optional_number(segment_name, segment_config, field_name, errors):
    if field_name not in segment_config:
        return None
    try:
        value = float(segment_config[field_name])
    except (TypeError, ValueError):
        errors.append(f"curve_wall_segments.{segment_name}.{field_name} must be numeric")
        return None
    if not math.isfinite(value):
        errors.append(f"curve_wall_segments.{segment_name}.{field_name} must be finite")
        return None
    return value


def _optional_material_id(segment_name, segment_config, field_name, fallback, errors):
    raw_value = segment_config.get(field_name, fallback)
    try:
        material_id = float(raw_value)
    except (TypeError, ValueError):
        errors.append(f"curve_wall_segments.{segment_name}.{field_name} must be numeric")
        return None
    if (
        not math.isfinite(material_id)
        or not material_id.is_integer()
        or int(material_id) < 0
    ):
        errors.append(
            f"curve_wall_segments.{segment_name}.{field_name} "
            "must be a non-negative integer"
        )
        return None
    return material_id


def _optional_nonnegative_wall_parameter(segment_name, segment_config, field_name, errors):
    value = _optional_number(segment_name, segment_config, field_name, errors)
    if value is None:
        return WALL_PARAMETER_DEFAULT
    if value < 0.0:
        errors.append(f"curve_wall_segments.{segment_name}.{field_name} must not be negative")
    return value


def _optional_fraction_wall_parameter(segment_name, segment_config, field_name, errors):
    value = _optional_number(segment_name, segment_config, field_name, errors)
    if value is None:
        return WALL_PARAMETER_DEFAULT
    if not 0.0 < value < 1.0:
        errors.append(f"curve_wall_segments.{segment_name}.{field_name} must be between 0 and 1")
    return value


def parse_segment(segment_name, segment_config):
    """Parse one canonical key-value wall segment into numeric internal form."""
    errors = []

    if not isinstance(segment_config, Mapping):
        return None, [
            f"curve_wall_segments.{segment_name} must be a key-value object"
        ]

    boundary_kind_name = _required_field(
        segment_name, segment_config, "boundary_kind", errors
    )
    function_name = _required_field(segment_name, segment_config, "function", errors)
    boundary_kind = BOUNDARY_KIND_BY_NAME.get(str(boundary_kind_name))
    independent_axis = FUNCTION_AXIS_BY_NAME.get(str(function_name))
    if boundary_kind is None and boundary_kind_name is not None:
        errors.append(
            f"curve_wall_segments.{segment_name}.boundary_kind "
            "must be \"regular\" or \"reservoir\""
        )
    if independent_axis is None and function_name is not None:
        errors.append(
            f"curve_wall_segments.{segment_name}.function "
            "must be \"y_of_x\" or \"x_of_y\""
        )

    u_start = _required_number(segment_name, segment_config, "u_start", errors)
    u_end = _required_number(segment_name, segment_config, "u_end", errors)
    f_start = _required_number(segment_name, segment_config, "f_start", errors)
    a1 = _required_number(segment_name, segment_config, "a1", errors)
    a2 = _required_number(segment_name, segment_config, "a2", errors)
    a3 = _required_number(segment_name, segment_config, "a3", errors)
    normal_sign = _required_number(
        segment_name, segment_config, "normal_sign", errors
    )
    wall_flag = _required_number(segment_name, segment_config, "wall_flag", errors)
    legacy_material_id = segment_config.get("material_id", 0)
    boundary_particle_material_id = _optional_material_id(
        segment_name,
        segment_config,
        "boundary_particle_material_id",
        legacy_material_id,
        errors,
    )
    boundary_visual_material_id = _optional_material_id(
        segment_name,
        segment_config,
        "boundary_visual_material_id",
        boundary_particle_material_id
        if boundary_particle_material_id is not None
        else legacy_material_id,
        errors,
    )
    wall_collision_stiffness_q = _optional_nonnegative_wall_parameter(
        segment_name,
        segment_config,
        "wall_collision_stiffness_q",
        errors,
    )
    wall_target_penetration_fraction = _optional_fraction_wall_parameter(
        segment_name,
        segment_config,
        "wall_target_penetration_fraction",
        errors,
    )
    wall_hard_penetration_fraction = _optional_fraction_wall_parameter(
        segment_name,
        segment_config,
        "wall_hard_penetration_fraction",
        errors,
    )
    wall_compression_stiffness_gain = _optional_nonnegative_wall_parameter(
        segment_name,
        segment_config,
        "wall_compression_stiffness_gain",
        errors,
    )
    wall_compression_stiffness_power = _optional_nonnegative_wall_parameter(
        segment_name,
        segment_config,
        "wall_compression_stiffness_power",
        errors,
    )

    if u_start is not None and u_end is not None and abs(u_end - u_start) <= 1.0e-12:
        errors.append(f"curve_wall_segments.{segment_name} has zero length")
    if normal_sign is not None and normal_sign == 0.0:
        errors.append(
            f"curve_wall_segments.{segment_name}.normal_sign must not be zero"
        )
    if wall_flag is not None and (
        not wall_flag.is_integer() or int(wall_flag) <= 0
    ):
        errors.append(
            f"curve_wall_segments.{segment_name}.wall_flag "
            "must be a positive integer"
        )
    if (
        wall_target_penetration_fraction >= 0.0
        and wall_hard_penetration_fraction >= 0.0
        and wall_hard_penetration_fraction <= wall_target_penetration_fraction
    ):
        errors.append(
            f"curve_wall_segments.{segment_name}.wall_hard_penetration_fraction "
            "must be greater than wall_target_penetration_fraction"
        )

    values = (
        boundary_kind,
        independent_axis,
        u_start,
        u_end,
        f_start,
        a1,
        a2,
        a3,
        normal_sign,
        wall_flag,
        boundary_particle_material_id,
        boundary_visual_material_id,
        wall_collision_stiffness_q,
        wall_target_penetration_fraction,
        wall_hard_penetration_fraction,
        wall_compression_stiffness_gain,
        wall_compression_stiffness_power,
    )
    if errors or any(value is None for value in values):
        return None, errors
    return tuple(float(value) for value in values), []


def _prepare_group_segment(segment_name, segment_config, previous_segment):
    """Expand grouped curve authoring with optional length chaining."""
    errors = []
    prepared_config = dict(segment_config)

    if "length" not in prepared_config:
        return prepared_config, errors

    length = _optional_number(segment_name, prepared_config, "length", errors)
    if length is None:
        return prepared_config, errors
    if abs(length) <= 1.0e-12:
        errors.append(f"curve_wall_segments.{segment_name}.length must not be zero")
        return prepared_config, errors

    if previous_segment is None:
        u_start = _optional_number(segment_name, prepared_config, "u_start", errors)
        _optional_number(segment_name, prepared_config, "f_start", errors)
        if u_start is None:
            errors.append(
                f"curve_wall_segments.{segment_name}.u_start is required "
                "for the first segment in a grouped curve"
            )
        if "f_start" not in prepared_config:
            errors.append(
                f"curve_wall_segments.{segment_name}.f_start is required "
                "for the first segment in a grouped curve"
            )
        if u_start is not None:
            expected_u_end = u_start + length
            configured_u_end = _optional_number(
                segment_name,
                prepared_config,
                "u_end",
                errors,
            )
            if configured_u_end is None and "u_end" not in prepared_config:
                prepared_config["u_end"] = expected_u_end
            elif (
                configured_u_end is not None
                and abs(configured_u_end - expected_u_end) > 1.0e-9
            ):
                errors.append(
                    f"curve_wall_segments.{segment_name}.u_end must equal "
                    "u_start + length"
                )
        return prepared_config, errors

    (
        _boundary_kind,
        _independent_axis,
        previous_u_start,
        previous_u_end,
        _previous_f_start,
        _a1,
        _a2,
        _a3,
        _normal_sign,
        _wall_flag,
        _boundary_particle_material_id,
        _boundary_visual_material_id,
        *_wall_parameters,
    ) = segment_values(previous_segment)

    if "u_start" not in prepared_config:
        prepared_config["u_start"] = previous_u_end
    if "f_start" not in prepared_config:
        prepared_config["f_start"], _slope = evaluate_function(
            previous_segment,
            previous_u_end,
        )
    expected_u_end = float(prepared_config["u_start"]) + length
    configured_u_end = _optional_number(
        segment_name,
        prepared_config,
        "u_end",
        errors,
    )
    if configured_u_end is None and "u_end" not in prepared_config:
        prepared_config["u_end"] = expected_u_end
    elif (
        configured_u_end is not None
        and abs(configured_u_end - expected_u_end) > 1.0e-9
    ):
        errors.append(
            f"curve_wall_segments.{segment_name}.u_end must equal "
            "u_start + length"
        )

    return prepared_config, errors


def parse_keyed_curve_wall_segments(raw_segments):
    """Parse flat or grouped key-value curve_wall_segments config objects."""
    if not raw_segments:
        return (), ["curve_wall_segments is required and must not be empty"]
    if not isinstance(raw_segments, Mapping):
        return (), ["curve_wall_segments must be a key-value object"]

    errors = []
    parsed_segments = []
    for segment_name, segment_config in raw_segments.items():
        if isinstance(segment_config, Mapping) and "segments" in segment_config:
            curve_segments = segment_config.get("segments")
            if not isinstance(curve_segments, Mapping):
                errors.append(
                    f"curve_wall_segments.{segment_name}.segments "
                    "must be a key-value object"
                )
                continue

            inherited = {
                key: value
                for key, value in segment_config.items()
                if key != "segments"
            }
            previous_segment = None
            for child_name, child_config in curve_segments.items():
                child_path = f"{segment_name}.{child_name}"
                if not isinstance(child_config, Mapping):
                    segment, segment_errors = parse_segment(child_path, child_config)
                else:
                    merged_config = dict(inherited)
                    merged_config.update(child_config)
                    prepared_config, segment_errors = _prepare_group_segment(
                        child_path,
                        merged_config,
                        previous_segment,
                    )
                    if not segment_errors:
                        segment, segment_errors = parse_segment(
                            child_path,
                            prepared_config,
                        )
                    else:
                        segment = None
                errors.extend(segment_errors)
                if segment is not None:
                    parsed_segments.append(segment)
                    previous_segment = segment
            continue

        segment, segment_errors = parse_segment(segment_name, segment_config)
        errors.extend(segment_errors)
        if segment is not None:
            parsed_segments.append(segment)

    return tuple(parsed_segments), errors


def segment_values(segment):
    """Return function-wall values with particle and visual material ids."""
    wall_defaults = (WALL_PARAMETER_DEFAULT,) * len(WALL_PARAMETER_FIELDS)
    if len(segment) == 10:
        values = tuple(float(value) for value in segment)
        return (*values, 0.0, 0.0, *wall_defaults)
    if len(segment) == 11:
        values = tuple(float(value) for value in segment)
        return (*values, values[10], *wall_defaults)
    if len(segment) == 12:
        values = tuple(float(value) for value in segment)
        return (*values, *wall_defaults)
    if len(segment) == 17:
        return tuple(float(value) for value in segment)
    raise ValueError("function wall segment must contain 10, 11, 12, or 17 values")


def evaluate_function(segment, independent_value):
    """Evaluate f(u) and f'(u) for one function-wall segment."""
    (
        _boundary_kind,
        _independent_axis,
        u_start,
        _u_end,
        f_start,
        a1,
        a2,
        a3,
        _normal_sign,
        _wall_flag,
        _boundary_particle_material_id,
        _boundary_visual_material_id,
        *_wall_parameters,
    ) = segment_values(segment)
    du = float(independent_value) - u_start
    value = f_start + a1 * du + a2 * du * du + a3 * du * du * du
    slope = a1 + 2.0 * a2 * du + 3.0 * a3 * du * du
    return value, slope


def _normalize(vector_x, vector_y):
    length = math.hypot(vector_x, vector_y)
    if length <= 1.0e-12:
        return None
    return vector_x / length, vector_y / length


def evaluate_wall_at_point(segment, point):
    """Return wall point, outward normal, and metadata for a source point.

    The marker/cell broad phase only decides whether this evaluator should run.
    The particle xy position and wall function own the physical geometry.
    """
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
        boundary_particle_material_id,
        _boundary_visual_material_id,
        *_wall_parameters,
    ) = segment_values(segment)
    independent_axis = int(round(independent_axis))
    if independent_axis not in (AXIS_X, AXIS_Y):
        return None

    point_x = float(point[0])
    point_y = float(point[1])
    if independent_axis == AXIS_X:
        u = point_x
    else:
        u = point_y

    lower = min(u_start, u_end)
    upper = max(u_start, u_end)
    if u < lower - 1.0e-12 or u > upper + 1.0e-12:
        return None

    function_value, slope = evaluate_function(segment, u)
    if independent_axis == AXIS_X:
        wall_point = (u, function_value)
        if normal_sign >= 0.0:
            normal = _normalize(-slope, 1.0)
        else:
            normal = _normalize(slope, -1.0)
    else:
        wall_point = (function_value, u)
        if normal_sign >= 0.0:
            normal = _normalize(1.0, -slope)
        else:
            normal = _normalize(-1.0, slope)

    if normal is None:
        return None
    return {
        "boundary_kind": int(round(boundary_kind)),
        "independent_axis": independent_axis,
        "wall_point": wall_point,
        "normal": normal,
        "wall_flag": int(round(wall_flag)),
        "material_id": int(round(boundary_particle_material_id)),
    }


def physical_penetration(segment, point, radius):
    """Return physical penetration from particle center to outward wall normal."""
    evaluation = evaluate_wall_at_point(segment, point)
    if evaluation is None:
        return None
    wall_x, wall_y = evaluation["wall_point"]
    normal_x, normal_y = evaluation["normal"]
    signed_outward_distance = (
        (float(point[0]) - wall_x) * normal_x
        + (float(point[1]) - wall_y) * normal_y
    )
    return float(radius) + signed_outward_distance


def bounds(segment):
    """Return xmin, xmax, ymin, ymax for a function-wall segment."""
    (
        _boundary_kind,
        independent_axis,
        u_start,
        u_end,
        _f_start,
        _a1,
        _a2,
        _a3,
        _normal_sign,
        _wall_flag,
        _boundary_particle_material_id,
        _boundary_visual_material_id,
        *_wall_parameters,
    ) = segment_values(segment)
    independent_axis = int(round(independent_axis))
    samples = [u_start, u_end]
    if independent_axis == AXIS_X:
        points = [(u, evaluate_function(segment, u)[0]) for u in samples]
    elif independent_axis == AXIS_Y:
        points = [(evaluate_function(segment, u)[0], u) for u in samples]
    else:
        raise ValueError("independent_axis must be 0 or 1")
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    return min(x_values), max(x_values), min(y_values), max(y_values)


def sample_points(segment, maximum_spacing=0.5):
    """Return sampled wall points along a function-wall segment."""
    (
        _boundary_kind,
        independent_axis,
        u_start,
        u_end,
        _f_start,
        _a1,
        _a2,
        _a3,
        _normal_sign,
        _wall_flag,
        _boundary_particle_material_id,
        _boundary_visual_material_id,
        *_wall_parameters,
    ) = segment_values(segment)
    independent_axis = int(round(independent_axis))
    length = abs(u_end - u_start)
    intervals = max(1, int(math.ceil(length / max(1.0e-12, maximum_spacing))))
    points = []
    for index in range(intervals + 1):
        t = index / intervals
        u = u_start + (u_end - u_start) * t
        f_value, _slope = evaluate_function(segment, u)
        if independent_axis == AXIS_X:
            points.append((u, f_value))
        elif independent_axis == AXIS_Y:
            points.append((f_value, u))
    return points


def wall_marker_positions(segments, plane_z):
    """Return one locality marker per integer cell per physical wall."""
    return [record[:3] for record in wall_marker_records(segments, plane_z)]


def wall_marker_records(segments, plane_z):
    """Return marker x/y/z/material_id records for each physical wall."""
    marker_cells = set()
    records = []
    for segment in segments:
        wall_flag = int(round(float(segment[9])))
        material_id = int(round(segment_values(segment)[10]))
        for point_x, point_y in sample_points(segment):
            marker_cell = (
                round(point_x),
                round(point_y),
                round(float(plane_z)),
                wall_flag,
            )
            if marker_cell in marker_cells:
                continue
            marker_cells.add(marker_cell)
            records.append(
                (
                    float(marker_cell[0]),
                    float(marker_cell[1]),
                    float(marker_cell[2]),
                    float(material_id),
                )
            )
    return records
