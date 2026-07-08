#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float wall_contact_offset = 0.062500000;
#define CONTACT_FORCE_MEASURE  depth
#define WALL_MODEL_BOUNDARY_PARTICLE
const float death_x_min = 1.000000000;
const float death_x_max = 30.000000000;
const float death_y_min = 1.000000000;
const float death_y_max = 9.000000000;
const float death_z_min = 0.000000000;
const float death_z_max = 4.000000000;
struct ParametricCurveSegment
{
    vec4 xCoefficients;
    vec4 yCoefficients;
    uint wallFlag;
};

const uint CURVE_WALL_SEGMENT_COUNT = 4u;
const ParametricCurveSegment CURVE_WALL_SEGMENTS[4] = ParametricCurveSegment[4](
    ParametricCurveSegment(vec4(2.000000000, 18.000000000, 0.000000000, 0.000000000), vec4(2.000000000, 0.000000000, 0.000000000, 0.000000000), 3u),
    ParametricCurveSegment(vec4(20.000000000, -18.000000000, 0.000000000, 0.000000000), vec4(8.000000000, 0.000000000, 0.000000000, 0.000000000), 4u),
    ParametricCurveSegment(vec4(20.000000000, 5.000000000, 0.000000000, 0.000000000), vec4(2.000000000, 1.250000000, 0.000000000, 0.000000000), 3u),
    ParametricCurveSegment(vec4(25.000000000, -5.000000000, 0.000000000, 0.000000000), vec4(6.750000000, 1.250000000, 0.000000000, 0.000000000), 4u)
);

#endif
