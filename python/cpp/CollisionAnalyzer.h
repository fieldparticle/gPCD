#pragma once

#include <cstddef>
#include <string>
#include <vector>

namespace gpcd {

struct Vec2 {
    double x = 0.0;
    double y = 0.0;
};

enum class ErrorLevel {
    Info,
    Warning,
    Error,
};

struct Output {
    ErrorLevel error_level = ErrorLevel::Info;
    std::string parameter;
    std::string description;
};

struct CollisionAnalyzerParameters {
    double substep_dt = 0.0;
    double collision_radius = 0.0;
    double relative_speed = 0.0;
    double relative_move_per_substep = 0.0;

    bool has_geometric_collision = false;
    double geometric_entry_time = 0.0;
    double geometric_exit_time = 0.0;
    double geometric_duration = 0.0;
    double geometric_substeps = 0.0;
    std::size_t geometric_first_sample = 0;
    std::size_t geometric_last_sample = 0;
    std::size_t geometric_sampled_substeps = 0;

    double speed_limit_min_substeps = 0.0;

    std::size_t response_overlap_substeps = 0;
    std::size_t response_first_overlap_substep = 0;
    std::size_t response_last_overlap_substep = 0;
    bool response_had_overlap = false;
    bool response_contact_ended = false;
    double response_peak_overlap_depth = 0.0;
    double response_peak_overlap_area = 0.0;
    Vec2 response_final_p1;
    Vec2 response_final_p2;
    Vec2 response_final_v1;
    Vec2 response_final_v2;
    double response_final_relative_speed = 0.0;
};

class CollisionAnalyzer {
public:
    void Create(
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
        std::size_t max_response_substeps);

    std::vector<Output> Analyze();

    const CollisionAnalyzerParameters& GetParameters() const;

private:
    struct Inputs {
        Vec2 p1;
        Vec2 v1;
        double r1 = 0.0;
        double m1 = 0.0;
        Vec2 p2;
        Vec2 v2;
        double r2 = 0.0;
        double m2 = 0.0;
        double frame_rate = 0.0;
        int substeps_per_frame = 0;
        double speed_limit = 0.0;
        double momentum_per_area = 0.0;
        double inverse_square_softening = 0.0;
        std::size_t max_response_substeps = 0;
    };

    struct ContactResponse {
        double momentum = 0.0;
        Vec2 normal;
        double overlap_area = 0.0;
        double overlap_depth = 0.0;
    };

    std::vector<Output> ValidateInputs() const;
    void AnalyzeGeometric();
    void AnalyzeResponse();
    ContactResponse ResponseMomentum(Vec2 position, Vec2 target_position, double radius, double target_radius) const;

    static double Dot(Vec2 a, Vec2 b);
    static double Length(Vec2 v);
    static Vec2 Add(Vec2 a, Vec2 b);
    static Vec2 Sub(Vec2 a, Vec2 b);
    static Vec2 Scale(Vec2 v, double scale);
    static double CircleOverlapArea(double radius_i, double radius_j, double center_distance);
    static std::string FormatDouble(double value);

    Inputs inputs_;
    CollisionAnalyzerParameters params_;
};

} // namespace gpcd
