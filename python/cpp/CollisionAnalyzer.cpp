#include "CollisionAnalyzer.h"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <limits>
#include <sstream>

namespace gpcd {

namespace {
constexpr double kEpsilon = 1.0e-12;
constexpr double kPi = 3.141592653589793238462643383279502884;
}

void CollisionAnalyzer::Create(
    Vec2 p1,
    Vec2 v1,
    double r1,
    double m1,
    Vec2 p2,
    Vec2 v2,
    double r2,
    double m2,
    double frame_rate,
    int substeps_per_frame,
    double speed_limit,
    double momentum_per_area,
    double inverse_square_softening,
    std::size_t max_response_substeps)
{
    inputs_.p1 = p1;
    inputs_.v1 = v1;
    inputs_.r1 = r1;
    inputs_.m1 = m1;
    inputs_.p2 = p2;
    inputs_.v2 = v2;
    inputs_.r2 = r2;
    inputs_.m2 = m2;
    inputs_.frame_rate = frame_rate;
    inputs_.substeps_per_frame = substeps_per_frame;
    inputs_.speed_limit = speed_limit;
    inputs_.momentum_per_area = momentum_per_area;
    inputs_.inverse_square_softening = inverse_square_softening;
    inputs_.max_response_substeps = max_response_substeps;
}

std::vector<Output> CollisionAnalyzer::Analyze()
{
    params_ = CollisionAnalyzerParameters{};
    std::vector<Output> outputs = ValidateInputs();

    const bool has_error = std::any_of(outputs.begin(), outputs.end(), [](const Output& output) {
        return output.error_level == ErrorLevel::Error;
    });
    if (has_error) {
        return outputs;
    }

    params_.substep_dt = 1.0 / (inputs_.frame_rate * static_cast<double>(inputs_.substeps_per_frame));
    params_.collision_radius = inputs_.r1 + inputs_.r2;
    params_.relative_speed = Length(Sub(inputs_.v2, inputs_.v1));
    params_.relative_move_per_substep = params_.relative_speed * params_.substep_dt;
    if (inputs_.speed_limit > 0.0) {
        params_.speed_limit_min_substeps =
            ((inputs_.r1 + inputs_.r2) / inputs_.speed_limit)
            * inputs_.frame_rate
            * static_cast<double>(inputs_.substeps_per_frame);
    } else {
        params_.speed_limit_min_substeps = std::numeric_limits<double>::infinity();
    }

    AnalyzeGeometric();
    AnalyzeResponse();

    if (!params_.has_geometric_collision) {
        outputs.push_back({
            ErrorLevel::Info,
            "geometric_collision",
            "The constant-velocity paths do not overlap from the current starting state."
        });
    }

    if (params_.geometric_substeps > 0.0 && params_.geometric_substeps < 1.0) {
        outputs.push_back({
            ErrorLevel::Warning,
            "geometric_substeps",
            "The constant-velocity collision lasts less than one simulation substep."
        });
    }

    if (params_.response_had_overlap && params_.response_overlap_substeps < 3) {
        outputs.push_back({
            ErrorLevel::Warning,
            "response_overlap_substeps",
            "The response calculation has fewer than 3 sampled substeps in collision."
        });
    }

    if (!params_.response_had_overlap && params_.has_geometric_collision) {
        outputs.push_back({
            ErrorLevel::Warning,
            "response_overlap_substeps",
            "The geometric solution predicts a collision, but the response simulation sampled no overlap."
        });
    }

    if (params_.relative_move_per_substep > 2.0 * params_.collision_radius) {
        outputs.push_back({
            ErrorLevel::Warning,
            "relative_move_per_substep",
            "Relative motion can cross the whole geometric collision window in one substep."
        });
    } else if (params_.relative_move_per_substep > params_.collision_radius) {
        outputs.push_back({
            ErrorLevel::Warning,
            "relative_move_per_substep",
            "Relative motion is larger than r1+r2 in one substep."
        });
    }

    if (params_.response_had_overlap && !params_.response_contact_ended) {
        outputs.push_back({
            ErrorLevel::Warning,
            "max_response_substeps",
            "The response simulation reached max_response_substeps before contact clearly ended."
        });
    }

    outputs.push_back({
        ErrorLevel::Info,
        "geometric_substeps",
        "Constant-velocity overlap span is " + FormatDouble(params_.geometric_substeps) + " substeps."
    });
    outputs.push_back({
        ErrorLevel::Info,
        "response_overlap_substeps",
        "Response-aware sampled overlap count is "
            + std::to_string(params_.response_overlap_substeps)
            + " substeps."
    });
    outputs.push_back({
        ErrorLevel::Info,
        "speed_limit_min_substeps",
        "Speed-limit lower bound is "
            + FormatDouble(params_.speed_limit_min_substeps)
            + " substeps."
    });

    return outputs;
}

const CollisionAnalyzerParameters& CollisionAnalyzer::GetParameters() const
{
    return params_;
}

std::vector<Output> CollisionAnalyzer::ValidateInputs() const
{
    std::vector<Output> outputs;

    if (inputs_.r1 <= 0.0) {
        outputs.push_back({ErrorLevel::Error, "r1", "Particle 1 radius must be greater than zero."});
    }
    if (inputs_.r2 <= 0.0) {
        outputs.push_back({ErrorLevel::Error, "r2", "Particle 2 radius must be greater than zero."});
    }
    if (inputs_.m1 <= 0.0) {
        outputs.push_back({ErrorLevel::Error, "m1", "Particle 1 mass must be greater than zero."});
    }
    if (inputs_.m2 <= 0.0) {
        outputs.push_back({ErrorLevel::Error, "m2", "Particle 2 mass must be greater than zero."});
    }
    if (inputs_.frame_rate <= 0.0) {
        outputs.push_back({ErrorLevel::Error, "frame_rate", "Frame rate must be greater than zero."});
    }
    if (inputs_.substeps_per_frame <= 0) {
        outputs.push_back({ErrorLevel::Error, "substeps_per_frame", "Substeps per frame must be greater than zero."});
    }
    if (inputs_.speed_limit < 0.0) {
        outputs.push_back({ErrorLevel::Error, "speed_limit", "Speed limit cannot be negative."});
    }
    if (inputs_.momentum_per_area < 0.0) {
        outputs.push_back({ErrorLevel::Error, "momentum_per_area", "momentum_per_area cannot be negative."});
    }
    if (inputs_.inverse_square_softening <= 0.0) {
        outputs.push_back({
            ErrorLevel::Error,
            "inverse_square_softening",
            "inverse_square_softening must be greater than zero."
        });
    }
    if (inputs_.max_response_substeps == 0) {
        outputs.push_back({
            ErrorLevel::Error,
            "max_response_substeps",
            "max_response_substeps must be greater than zero."
        });
    }

    return outputs;
}

void CollisionAnalyzer::AnalyzeGeometric()
{
    const Vec2 relative_position = Sub(inputs_.p2, inputs_.p1);
    const Vec2 relative_velocity = Sub(inputs_.v2, inputs_.v1);
    const double collision_radius = inputs_.r1 + inputs_.r2;

    const double a = Dot(relative_velocity, relative_velocity);
    const double b = 2.0 * Dot(relative_position, relative_velocity);
    const double c = Dot(relative_position, relative_position) - collision_radius * collision_radius;

    if (c <= 0.0 && a <= kEpsilon) {
        params_.has_geometric_collision = true;
        params_.geometric_entry_time = 0.0;
        params_.geometric_exit_time = std::numeric_limits<double>::infinity();
        params_.geometric_duration = std::numeric_limits<double>::infinity();
        params_.geometric_substeps = std::numeric_limits<double>::infinity();
        return;
    }

    if (a <= kEpsilon) {
        return;
    }

    const double discriminant = b * b - 4.0 * a * c;
    if (discriminant < 0.0) {
        return;
    }

    const double root = std::sqrt(discriminant);
    const double entry_time = (-b - root) / (2.0 * a);
    const double exit_time = (-b + root) / (2.0 * a);

    if (exit_time < 0.0) {
        return;
    }

    params_.has_geometric_collision = true;
    params_.geometric_entry_time = std::max(0.0, entry_time);
    params_.geometric_exit_time = exit_time;
    params_.geometric_duration = params_.geometric_exit_time - params_.geometric_entry_time;
    const double sample_rate = inputs_.frame_rate * static_cast<double>(inputs_.substeps_per_frame);
    params_.geometric_substeps = params_.geometric_duration * sample_rate;

    const double first_sample = std::ceil(params_.geometric_entry_time * sample_rate);
    const double last_sample = std::floor(params_.geometric_exit_time * sample_rate);
    if (last_sample >= first_sample) {
        params_.geometric_first_sample = static_cast<std::size_t>(first_sample);
        params_.geometric_last_sample = static_cast<std::size_t>(last_sample);
        params_.geometric_sampled_substeps =
            params_.geometric_last_sample - params_.geometric_first_sample + 1;
    }
}

void CollisionAnalyzer::AnalyzeResponse()
{
    Vec2 pos1 = inputs_.p1;
    Vec2 pos2 = inputs_.p2;
    Vec2 vel1 = inputs_.v1;
    Vec2 vel2 = inputs_.v2;
    bool started = false;

    for (std::size_t step = 0; step < inputs_.max_response_substeps; ++step) {
        const ContactResponse response1 = ResponseMomentum(pos1, pos2, inputs_.r1, inputs_.r2);
        const ContactResponse response2 = ResponseMomentum(pos2, pos1, inputs_.r2, inputs_.r1);
        const bool overlapping = response1.overlap_depth > 0.0 || response2.overlap_depth > 0.0;

        if (overlapping) {
            started = true;
            params_.response_had_overlap = true;
            ++params_.response_overlap_substeps;
            if (params_.response_overlap_substeps == 1) {
                params_.response_first_overlap_substep = step;
            }
            params_.response_last_overlap_substep = step;
            params_.response_peak_overlap_depth = std::max(
                params_.response_peak_overlap_depth,
                std::max(response1.overlap_depth, response2.overlap_depth));
            params_.response_peak_overlap_area = std::max(
                params_.response_peak_overlap_area,
                std::max(response1.overlap_area, response2.overlap_area));

            vel1 = Add(vel1, Scale(response1.normal, -response1.momentum / inputs_.m1));
            vel2 = Add(vel2, Scale(response2.normal, -response2.momentum / inputs_.m2));
        } else if (started) {
            params_.response_contact_ended = true;
            break;
        }

        pos1 = Add(pos1, Scale(vel1, params_.substep_dt));
        pos2 = Add(pos2, Scale(vel2, params_.substep_dt));
    }

    if (!started) {
        params_.response_contact_ended = true;
    }

    params_.response_final_p1 = pos1;
    params_.response_final_p2 = pos2;
    params_.response_final_v1 = vel1;
    params_.response_final_v2 = vel2;
    params_.response_final_relative_speed = Length(Sub(vel2, vel1));
}

CollisionAnalyzer::ContactResponse CollisionAnalyzer::ResponseMomentum(
    Vec2 position,
    Vec2 target_position,
    double radius,
    double target_radius) const
{
    ContactResponse response;
    const Vec2 delta = Sub(target_position, position);
    const double distance = Length(delta);
    const double radius_sum = radius + target_radius;

    if (distance >= radius_sum) {
        return response;
    }

    if (distance <= kEpsilon) {
        response.normal = {1.0, 0.0};
    } else {
        response.normal = Scale(delta, 1.0 / distance);
    }

    response.overlap_depth = radius_sum - distance;
    response.overlap_area = CircleOverlapArea(radius, target_radius, distance);
    const double softening = std::max(inputs_.inverse_square_softening, kEpsilon);
    const double weight = 1.0 / std::max(distance * distance, softening * softening);
    response.momentum = inputs_.momentum_per_area * response.overlap_area * weight;
    return response;
}

double CollisionAnalyzer::Dot(Vec2 a, Vec2 b)
{
    return a.x * b.x + a.y * b.y;
}

double CollisionAnalyzer::Length(Vec2 v)
{
    return std::sqrt(Dot(v, v));
}

Vec2 CollisionAnalyzer::Add(Vec2 a, Vec2 b)
{
    return {a.x + b.x, a.y + b.y};
}

Vec2 CollisionAnalyzer::Sub(Vec2 a, Vec2 b)
{
    return {a.x - b.x, a.y - b.y};
}

Vec2 CollisionAnalyzer::Scale(Vec2 v, double scale)
{
    return {v.x * scale, v.y * scale};
}

double CollisionAnalyzer::CircleOverlapArea(double radius_i, double radius_j, double center_distance)
{
    if (radius_i <= 0.0 || radius_j <= 0.0) {
        return 0.0;
    }

    if (center_distance >= radius_i + radius_j) {
        return 0.0;
    }

    if (center_distance <= std::abs(radius_i - radius_j)) {
        const double smaller = std::min(radius_i, radius_j);
        return kPi * smaller * smaller;
    }

    const double distance = std::max(center_distance, kEpsilon);
    const double r1_sq = radius_i * radius_i;
    const double r2_sq = radius_j * radius_j;
    const double alpha_arg = (distance * distance + r1_sq - r2_sq) / (2.0 * distance * radius_i);
    const double beta_arg = (distance * distance + r2_sq - r1_sq) / (2.0 * distance * radius_j);
    const double alpha = std::acos(std::clamp(alpha_arg, -1.0, 1.0));
    const double beta = std::acos(std::clamp(beta_arg, -1.0, 1.0));
    const double lens = 0.5 * std::sqrt(std::max(
        0.0,
        (-distance + radius_i + radius_j)
            * (distance + radius_i - radius_j)
            * (distance - radius_i + radius_j)
            * (distance + radius_i + radius_j)));

    return r1_sq * alpha + r2_sq * beta - lens;
}

std::string CollisionAnalyzer::FormatDouble(double value)
{
    if (std::isinf(value)) {
        return "infinite";
    }

    std::ostringstream stream;
    stream << std::setprecision(6) << value;
    return stream.str();
}

} // namespace gpcd
