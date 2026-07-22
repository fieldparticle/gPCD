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
    material_id = segment_config.get("material_id", 0)
    try:
        material_id = float(material_id)
    except (TypeError, ValueError):
        errors.append(f"curve_wall_segments.{segment_name}.material_id must be numeric")
        material_id = None
    if material_id is not None and (
        not math.isfinite(material_id)
        or not material_id.is_integer()
        or int(material_id) < 0
    ):
        errors.append(
            f"curve_wall_segments.{segment_name}.material_id "
            "must be a non-negative integer"
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
        material_id,
    )
    if errors or any(value is None for value in values):
        return None, errors
    return tuple(float(value) for value in values), []


def parse_keyed_curve_wall_segments(raw_segments):
    """Parse the canonical key-value curve_wall_segments config object."""
    if not raw_segments:
        return (), ["curve_wall_segments is required and must not be empty"]
    if not isinstance(raw_segments, Mapping):
        return (), ["curve_wall_segments must be a key-value object"]

    errors = []
    parsed_segments = []
    for segment_name, segment_config in raw_segments.items():
        segment, segment_errors = parse_segment(segment_name, segment_config)
        errors.extend(segment_errors)
        if segment is not None:
            parsed_segments.append(segment)

    return tuple(parsed_segments), errors


def segment_values(segment):
    """Return function-wall values, including optional marker material id."""
    if len(segment) == 10:
        return (*tuple(float(value) for value in segment), 0.0)
    if len(segment) != 11:
        raise ValueError("function wall segment must contain 10 or 11 values")
    return tuple(float(value) for value in segment)


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
        _material_id,
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
        material_id,
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
        "material_id": int(round(material_id)),
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
        _material_id,
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


def sample_points(segment, maximum_spacing=1.0):
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
        _material_id,
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
        material_id = int(round(float(segment[10]))) if len(segment) >= 11 else 0
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
