import math


AXES = {
    "1": ("+x", 1.0, 0.0),
    "2": ("-x", -1.0, 0.0),
    "3": ("+y", 0.0, 1.0),
    "4": ("-y", 0.0, -1.0),
    "5": ("+x +y", 1.0, 1.0),
    "6": ("+x -y", 1.0, -1.0),
    "7": ("-x +y", -1.0, 1.0),
    "8": ("-x -y", -1.0, -1.0),
}


def read_float(prompt, minimum=None):
    while True:
        raw_value = input(prompt).strip()
        try:
            value = float(raw_value)
        except ValueError:
            print("Enter a number.")
            continue

        if minimum is not None and value < minimum:
            print(f"Enter a value greater than or equal to {minimum}.")
            continue

        return value


def read_optional_float(prompt, default, minimum=None):
    while True:
        raw_value = input(f"{prompt} [{default:.6g}]: ").strip()
        if raw_value == "":
            return default

        try:
            value = float(raw_value)
        except ValueError:
            print("Enter a number, or press Enter for the default.")
            continue

        if minimum is not None and value < minimum:
            print(f"Enter a value greater than or equal to {minimum}.")
            continue

        return value


def read_int(prompt, minimum=None):
    while True:
        raw_value = input(prompt).strip()
        try:
            value = int(raw_value)
        except ValueError:
            print("Enter a whole number.")
            continue

        if minimum is not None and value < minimum:
            print(f"Enter a value greater than or equal to {minimum}.")
            continue

        return value


def read_vector(prompt):
    print(prompt)
    x = read_float("  x: ")
    y = read_float("  y: ")
    return x, y


def choose_axis():
    print()
    print("Axis")
    for key, (label, _dx, _dy) in AXES.items():
        print(f"  {key}. {label}")

    while True:
        choice = input("Select axis: ").strip()
        if choice in AXES:
            return AXES[choice]
        print("Choose one of the listed axis options.")


def normalized_direction(dx, dy):
    magnitude = math.hypot(dx, dy)
    if magnitude == 0.0:
        return 0.0, 0.0
    return dx / magnitude, dy / magnitude


def vector_add(a, b):
    return a[0] + b[0], a[1] + b[1]


def vector_sub(a, b):
    return a[0] - b[0], a[1] - b[1]


def vector_scale(v, scale):
    return v[0] * scale, v[1] * scale


def circle_overlap_area(radius_i, radius_j, center_distance):
    if radius_i <= 0.0 or radius_j <= 0.0:
        return 0.0

    if center_distance >= radius_i + radius_j:
        return 0.0

    if center_distance <= abs(radius_i - radius_j):
        smaller = min(radius_i, radius_j)
        return math.pi * smaller * smaller

    distance = max(center_distance, 1.0e-12)
    r1_sq = radius_i * radius_i
    r2_sq = radius_j * radius_j
    alpha_arg = (distance * distance + r1_sq - r2_sq) / (2.0 * distance * radius_i)
    beta_arg = (distance * distance + r2_sq - r1_sq) / (2.0 * distance * radius_j)
    alpha = math.acos(max(-1.0, min(1.0, alpha_arg)))
    beta = math.acos(max(-1.0, min(1.0, beta_arg)))
    lens = 0.5 * math.sqrt(
        max(
            0.0,
            (-distance + radius_i + radius_j)
            * (distance + radius_i - radius_j)
            * (distance - radius_i + radius_j)
            * (distance + radius_i + radius_j),
        )
    )
    return r1_sq * alpha + r2_sq * beta - lens


def print_velocity(axis_label, direction_x, direction_y, speed_limit, screen_width, screen_height, frame_rate):
    unit_x, unit_y = normalized_direction(direction_x, direction_y)
    vx_per_second = speed_limit * unit_x
    vy_per_second = speed_limit * unit_y
    vx_per_frame = vx_per_second / frame_rate
    vy_per_frame = vy_per_second / frame_rate
    speed_per_frame = speed_limit / frame_rate

    print()
    print("Velocity Result")
    print(f"  axis:              {axis_label}")
    print(f"  screen:            {screen_width} x {screen_height} px")
    print(f"  frame rate:        {frame_rate:.6g} fps")
    print(f"  speed limit:       {speed_limit:.6g} px/sec")
    print(f"  speed per frame:   {speed_per_frame:.6g} px/frame")
    print(f"  vx, vy per second: ({vx_per_second:.6g}, {vy_per_second:.6g}) px/sec")
    print(f"  vx, vy per frame:  ({vx_per_frame:.6g}, {vy_per_frame:.6g}) px/frame")
    print()


def collision_interval(p1, v1, r1, p2, v2, r2):
    px = p2[0] - p1[0]
    py = p2[1] - p1[1]
    vx = v2[0] - v1[0]
    vy = v2[1] - v1[1]
    collision_radius = r1 + r2

    a = vx * vx + vy * vy
    b = 2.0 * (px * vx + py * vy)
    c = px * px + py * py - collision_radius * collision_radius

    if c <= 0.0 and a == 0.0:
        return {
            "status": "already_overlapping_static",
            "relative_speed": 0.0,
            "collision_radius": collision_radius,
            "closest_distance": math.hypot(px, py),
            "entry_time": 0.0,
            "exit_time": math.inf,
        }

    if a == 0.0:
        return {
            "status": "no_collision_static",
            "relative_speed": 0.0,
            "collision_radius": collision_radius,
            "closest_distance": math.hypot(px, py),
        }

    closest_time = -b / (2.0 * a)
    closest_x = px + vx * closest_time
    closest_y = py + vy * closest_time
    closest_distance = math.hypot(closest_x, closest_y)
    discriminant = b * b - 4.0 * a * c

    if discriminant < 0.0:
        return {
            "status": "no_collision",
            "relative_speed": math.sqrt(a),
            "collision_radius": collision_radius,
            "closest_distance": closest_distance,
            "closest_time": closest_time,
        }

    root = math.sqrt(discriminant)
    entry_time = (-b - root) / (2.0 * a)
    exit_time = (-b + root) / (2.0 * a)

    if exit_time < 0.0:
        return {
            "status": "collision_in_past",
            "relative_speed": math.sqrt(a),
            "collision_radius": collision_radius,
            "closest_distance": closest_distance,
            "closest_time": closest_time,
            "entry_time": entry_time,
            "exit_time": exit_time,
        }

    return {
        "status": "collision",
        "relative_speed": math.sqrt(a),
        "collision_radius": collision_radius,
        "closest_distance": closest_distance,
        "closest_time": closest_time,
        "entry_time": max(0.0, entry_time),
        "raw_entry_time": entry_time,
        "exit_time": exit_time,
    }


def print_collision_result(result, sample_rate, sample_name="frame"):
    dt = 1.0 / sample_rate
    relative_speed = result["relative_speed"]
    relative_pixels_per_sample = relative_speed * dt
    collision_radius = result["collision_radius"]

    print()
    print(f"Collision {sample_name.capitalize()} Estimate")
    print(f"  status:                    {result['status']}")
    print(f"  relative speed:            {relative_speed:.6g} px/sec")
    print(f"  relative move per {sample_name}:   {relative_pixels_per_sample:.6g} px/{sample_name}")
    print(f"  collision radius r1+r2:    {collision_radius:.6g} px")
    print(f"  closest center distance:   {result['closest_distance']:.6g} px")

    if result["status"] not in ("collision", "already_overlapping_static"):
        print()
        return

    if result["exit_time"] == math.inf:
        print("  duration:                  infinite")
        print("  frames in collision:       infinite")
        print()
        return

    entry_time = result["entry_time"]
    exit_time = result["exit_time"]
    duration = exit_time - entry_time
    continuous_samples = duration * sample_rate
    first_sample = math.ceil(entry_time * sample_rate)
    last_sample = math.floor(exit_time * sample_rate)
    sampled_count = max(0, last_sample - first_sample + 1)

    print(f"  entry time:                {entry_time:.6g} sec")
    print(f"  exit time:                 {exit_time:.6g} sec")
    print(f"  duration:                  {duration:.6g} sec")
    print(f"  continuous {sample_name} span:     {continuous_samples:.6g} {sample_name}s")
    print(f"  sampled {sample_name} range:       {first_sample} to {last_sample}")
    print(f"  sampled {sample_name}s overlapping:{sampled_count}")

    if continuous_samples < 1.0:
        print(f"  warning:                   collision lasts less than one {sample_name}")
    if relative_pixels_per_sample > 2.0 * collision_radius:
        print(f"  warning:                   relative motion can cross the whole collision window in one {sample_name}")
    elif relative_pixels_per_sample > collision_radius:
        print(f"  warning:                   relative motion is larger than r1+r2 per {sample_name}")
    print()


def print_collision_result_for_substeps(result, frame_rate, substeps):
    print_collision_result(result, frame_rate * substeps, "substep")


def run_collision_frames():
    print()
    print("Collision Frame Calculator")
    p1 = read_vector("Particle 1 position in pixels")
    r1 = read_float("Particle 1 radius in pixels: ", minimum=0.0)
    v1 = read_vector("Particle 1 velocity in pixels per second")

    p2 = read_vector("Particle 2 position in pixels")
    r2 = read_float("Particle 2 radius in pixels: ", minimum=0.0)
    v2 = read_vector("Particle 2 velocity in pixels per second")

    frame_rate = read_float("Frame rate in frames per second: ", minimum=0.000001)
    result = collision_interval(p1, v1, r1, p2, v2, r2)
    print_collision_result(result, frame_rate)


def response_momentum(position, target_position, radius, target_radius, momentum_per_area, softening):
    dx = target_position[0] - position[0]
    dy = target_position[1] - position[1]
    distance = math.hypot(dx, dy)
    radius_sum = radius + target_radius

    if distance >= radius_sum:
        return 0.0, (0.0, 0.0), 0.0, 0.0

    if distance <= 1.0e-12:
        normal = (1.0, 0.0)
    else:
        normal = (dx / distance, dy / distance)

    overlap_depth = radius_sum - distance
    overlap_area = circle_overlap_area(radius, target_radius, distance)
    weight = 1.0 / max(distance * distance, max(softening, 1.0e-12) ** 2)
    momentum = momentum_per_area * overlap_area * weight
    return momentum, normal, overlap_area, overlap_depth


def simulate_response_collision(
    p1,
    v1,
    r1,
    m1,
    p2,
    v2,
    r2,
    m2,
    frame_rate,
    substeps,
    momentum_per_area,
    softening,
    max_steps,
):
    dt = 1.0 / (frame_rate * substeps)
    pos1 = p1
    pos2 = p2
    vel1 = v1
    vel2 = v2
    overlap_steps = 0
    first_overlap_step = None
    last_overlap_step = None
    peak_overlap_depth = 0.0
    peak_overlap_area = 0.0
    started = False

    for step in range(max_steps):
        momentum1, normal12, area1, depth1 = response_momentum(
            pos1,
            pos2,
            r1,
            r2,
            momentum_per_area,
            softening,
        )
        momentum2, normal21, area2, depth2 = response_momentum(
            pos2,
            pos1,
            r2,
            r1,
            momentum_per_area,
            softening,
        )
        overlapping = depth1 > 0.0 or depth2 > 0.0

        if overlapping:
            started = True
            overlap_steps += 1
            if first_overlap_step is None:
                first_overlap_step = step
            last_overlap_step = step
            peak_overlap_depth = max(peak_overlap_depth, depth1, depth2)
            peak_overlap_area = max(peak_overlap_area, area1, area2)

            vel1 = vector_add(vel1, vector_scale(normal12, -momentum1 / m1))
            vel2 = vector_add(vel2, vector_scale(normal21, -momentum2 / m2))
        elif started:
            break

        pos1 = vector_add(pos1, vector_scale(vel1, dt))
        pos2 = vector_add(pos2, vector_scale(vel2, dt))

    final_relative_speed = math.hypot(*(vector_sub(vel2, vel1)))
    return {
        "dt": dt,
        "overlap_steps": overlap_steps,
        "first_overlap_step": first_overlap_step,
        "last_overlap_step": last_overlap_step,
        "peak_overlap_depth": peak_overlap_depth,
        "peak_overlap_area": peak_overlap_area,
        "final_p1": pos1,
        "final_p2": pos2,
        "final_v1": vel1,
        "final_v2": vel2,
        "final_relative_speed": final_relative_speed,
        "ended": not started or overlap_steps == 0 or last_overlap_step < max_steps - 1,
        "max_steps": max_steps,
    }


def speed_limit_collision_substeps(radius_i, radius_j, speed_limit, frame_rate, substeps):
    if speed_limit <= 0.0:
        return math.inf
    return ((radius_i + radius_j) / speed_limit) * frame_rate * substeps


def run_response_collision_steps():
    print()
    print("Response-Aware Collision Substep Calculator")
    p1 = read_vector("Particle 1 position in pixels")
    r1 = read_float("Particle 1 radius in pixels: ", minimum=0.0)
    m1 = read_float("Particle 1 mass: ", minimum=0.000001)
    v1 = read_vector("Particle 1 velocity in pixels per second")

    p2 = read_vector("Particle 2 position in pixels")
    r2 = read_float("Particle 2 radius in pixels: ", minimum=0.0)
    m2 = read_float("Particle 2 mass: ", minimum=0.000001)
    v2 = read_vector("Particle 2 velocity in pixels per second")

    frame_rate = read_float("Frame rate in frames per second: ", minimum=0.000001)
    substeps = read_int("Simulation substeps per frame: ", minimum=1)
    default_speed_limit = max(math.hypot(*v1), math.hypot(*v2))
    speed_limit = read_optional_float(
        "System speed limit in pixels per second",
        default_speed_limit,
        minimum=0.0,
    )
    momentum_per_area = read_float("momentum_per_area: ", minimum=0.0)
    softening = read_float("inverse_square_softening: ", minimum=0.000001)
    max_steps = read_int("Maximum substeps to simulate: ", minimum=1)

    geometric = collision_interval(p1, v1, r1, p2, v2, r2)
    response = simulate_response_collision(
        p1,
        v1,
        r1,
        m1,
        p2,
        v2,
        r2,
        m2,
        frame_rate,
        substeps,
        momentum_per_area,
        softening,
        max_steps,
    )

    print()
    print("Geometric Constant-Velocity Estimate")
    print_collision_result_for_substeps(geometric, frame_rate, substeps)

    relative_speed = geometric["relative_speed"]
    relative_move_per_substep = relative_speed * response["dt"]
    collision_radius = r1 + r2
    speed_limit_substeps = speed_limit_collision_substeps(r1, r2, speed_limit, frame_rate, substeps)

    print("Response-Aware Substep Estimate")
    print(f"  substep dt:                {response['dt']:.6g} sec")
    print(f"  speed-limit min substeps:  {speed_limit_substeps:.6g}")
    print(f"  relative move per substep: {relative_move_per_substep:.6g} px/substep")
    print(f"  collision radius r1+r2:    {collision_radius:.6g} px")
    print(f"  overlap substeps counted:  {response['overlap_steps']}")
    print(f"  first overlap substep:     {response['first_overlap_step']}")
    print(f"  last overlap substep:      {response['last_overlap_step']}")
    print(f"  peak overlap depth:        {response['peak_overlap_depth']:.6g} px")
    print(f"  peak overlap area:         {response['peak_overlap_area']:.6g} px^2")
    print(f"  final v1:                  ({response['final_v1'][0]:.6g}, {response['final_v1'][1]:.6g}) px/sec")
    print(f"  final v2:                  ({response['final_v2'][0]:.6g}, {response['final_v2'][1]:.6g}) px/sec")
    print(f"  final relative speed:      {response['final_relative_speed']:.6g} px/sec")

    if response["overlap_steps"] == 0:
        print("  warning:                   no sampled overlap was detected")
    elif response["overlap_steps"] < 3:
        print("  warning:                   collision response has fewer than 3 substeps")
    if relative_move_per_substep > 2.0 * collision_radius:
        print("  warning:                   relative motion can cross the whole collision window in one substep")
    elif relative_move_per_substep > collision_radius:
        print("  warning:                   relative motion is larger than r1+r2 per substep")
    if not response["ended"]:
        print("  warning:                   simulation hit max_steps before the contact clearly ended")
    print()


def run_once():
    axis_label, direction_x, direction_y = choose_axis()
    speed_limit = read_float("Desired speed limit in pixels per second: ", minimum=0.0)
    screen_width = read_int("Screen width in pixels: ", minimum=1)
    screen_height = read_int("Screen height in pixels: ", minimum=1)
    frame_rate = read_float("Frame rate in frames per second: ", minimum=0.000001)

    print_velocity(
        axis_label,
        direction_x,
        direction_y,
        speed_limit,
        screen_width,
        screen_height,
        frame_rate,
    )


def main():
    while True:
        print("Particle Velocity Calculator")
        print("  1. Calculate velocity")
        print("  2. Estimate collision frames")
        print("  3. Estimate collision substeps with response")
        print("  4. Exit")
        choice = input("Select option: ").strip()

        if choice == "1":
            run_once()
        elif choice == "2":
            run_collision_frames()
        elif choice == "3":
            run_response_collision_steps()
        elif choice == "4":
            break
        else:
            print("Choose 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
