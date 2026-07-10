import math


BOUNDARY_KIND_REGULAR = 0
BOUNDARY_KIND_RESERVOIR = 1
AXIS_X = 0
AXIS_Y = 1


def segment_values(segment):
    """Return the ten function-wall values."""
    if len(segment) != 10:
        raise ValueError("function wall segment must contain exactly 10 values")
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
    marker_cells = set()
    positions = []
    for segment in segments:
        wall_flag = int(round(float(segment[9])))
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
            positions.append(tuple(float(value) for value in marker_cell[:3]))
    return positions
