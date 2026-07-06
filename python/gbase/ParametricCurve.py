import math


def evaluate_point(segment, parameter):
    """Return the point on a cubic parametric segment at parameter t."""
    ax, bx, cx, dx, ay, by, cy, dy, _wall_flag = segment
    t = float(parameter)
    t_squared = t * t
    t_cubed = t_squared * t
    return (
        ax + bx * t + cx * t_squared + dx * t_cubed,
        ay + by * t + cy * t_squared + dy * t_cubed,
    )


def evaluate_tangent(segment, parameter):
    """Return the unnormalized curve tangent at parameter t."""
    _ax, bx, cx, dx, _ay, by, cy, dy, _wall_flag = segment
    t = float(parameter)
    t_squared = t * t
    return (
        bx + 2.0 * cx * t + 3.0 * dx * t_squared,
        by + 2.0 * cy * t + 3.0 * dy * t_squared,
    )


def _evaluate_second_derivative(segment, parameter):
    _ax, _bx, cx, dx, _ay, _by, cy, dy, _wall_flag = segment
    t = float(parameter)
    return (
        2.0 * cx + 6.0 * dx * t,
        2.0 * cy + 6.0 * dy * t,
    )


def closest_point(segment, point, sample_count=16, iteration_count=12):
    """Return closest t, curve point, and squared distance to a 2D point."""
    point_x = float(point[0])
    point_y = float(point[1])

    def distance_squared(parameter):
        curve_x, curve_y = evaluate_point(segment, parameter)
        dx = curve_x - point_x
        dy = curve_y - point_y
        return dx * dx + dy * dy

    samples = [index / sample_count for index in range(sample_count + 1)]
    distances = [distance_squared(parameter) for parameter in samples]
    candidate_indices = {0, sample_count}
    for index in range(1, sample_count):
        if (
            distances[index] <= distances[index - 1]
            and distances[index] <= distances[index + 1]
        ):
            candidate_indices.add(index)

    candidates = []
    for index in candidate_indices:
        parameter = samples[index]
        lower = samples[max(0, index - 1)]
        upper = samples[min(sample_count, index + 1)]
        for _ in range(iteration_count):
            curve_x, curve_y = evaluate_point(segment, parameter)
            tangent_x, tangent_y = evaluate_tangent(segment, parameter)
            second_x, second_y = _evaluate_second_derivative(
                segment,
                parameter,
            )
            delta_x = curve_x - point_x
            delta_y = curve_y - point_y
            first_derivative = delta_x * tangent_x + delta_y * tangent_y
            second_derivative = (
                tangent_x * tangent_x
                + tangent_y * tangent_y
                + delta_x * second_x
                + delta_y * second_y
            )
            if abs(second_derivative) <= 1.0e-14:
                break
            next_parameter = parameter - first_derivative / second_derivative
            next_parameter = max(lower, min(upper, next_parameter))
            if abs(next_parameter - parameter) <= 1.0e-12:
                parameter = next_parameter
                break
            parameter = next_parameter
        candidates.append(
            (distance_squared(parameter), parameter)
        )

    best_distance, best_parameter = min(candidates)
    return (
        best_parameter,
        evaluate_point(segment, best_parameter),
        best_distance,
    )


def _quadratic_roots(a, b, c, epsilon=1.0e-12):
    if abs(a) <= epsilon:
        if abs(b) <= epsilon:
            return []
        return [-c / b]
    discriminant = b * b - 4.0 * a * c
    if discriminant < -epsilon:
        return []
    root_term = math.sqrt(max(0.0, discriminant))
    denominator = 2.0 * a
    return [
        (-b - root_term) / denominator,
        (-b + root_term) / denominator,
    ]


def extrema_parameters(segment):
    """Return endpoints and interior x/y extrema parameters in [0, 1]."""
    _ax, bx, cx, dx, _ay, by, cy, dy, _wall_flag = segment
    parameters = {0.0, 1.0}
    for linear, quadratic, cubic in ((bx, cx, dx), (by, cy, dy)):
        for root in _quadratic_roots(
            3.0 * cubic,
            2.0 * quadratic,
            linear,
        ):
            if 0.0 < root < 1.0:
                parameters.add(root)
    return sorted(parameters)


def bounds(segment):
    """Return xmin, xmax, ymin, ymax for a parametric segment."""
    points = [
        evaluate_point(segment, parameter)
        for parameter in extrema_parameters(segment)
    ]
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    return (
        min(x_values),
        max(x_values),
        min(y_values),
        max(y_values),
    )


def minimum_gap(lower_segment, upper_segment):
    """Return the minimum upper-y minus lower-y for paired segments."""
    a = upper_segment[4] - lower_segment[4]
    b = upper_segment[5] - lower_segment[5]
    c = upper_segment[6] - lower_segment[6]
    d = upper_segment[7] - lower_segment[7]
    parameters = {0.0, 1.0}
    for root in _quadratic_roots(3.0 * d, 2.0 * c, b):
        if 0.0 < root < 1.0:
            parameters.add(root)
    return min(
        a + b * t + c * t * t + d * t * t * t
        for t in parameters
    )
