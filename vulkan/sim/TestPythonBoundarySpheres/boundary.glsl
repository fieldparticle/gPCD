#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float wall_contact_offset = 0.062500000;
#define CONTACT_FORCE_MEASURE  depth
#define WALL_MODEL_BOUNDARY_PARTICLE
const float death_x_min = 0.500000000;
const float death_x_max = 4.500000000;
const float death_y_min = 0.500000000;
const float death_y_max = 4.500000000;
const float death_z_min = 0.500000000;
const float death_z_max = 4.500000000;
struct ParametricCurveSegment
{
    vec4 xCoefficients;
    vec4 yCoefficients;
    uint wallFlag;
};

const uint CURVE_WALL_SEGMENT_COUNT = 4u;
const ParametricCurveSegment CURVE_WALL_SEGMENTS[4] = ParametricCurveSegment[4](
    ParametricCurveSegment(vec4(1.000000000, 0.000000000, 0.000000000, 0.000000000), vec4(4.000000000, -3.000000000, 0.000000000, 0.000000000), 1u),
    ParametricCurveSegment(vec4(4.000000000, 0.000000000, 0.000000000, 0.000000000), vec4(1.000000000, 3.000000000, 0.000000000, 0.000000000), 2u),
    ParametricCurveSegment(vec4(1.000000000, 3.000000000, 0.000000000, 0.000000000), vec4(1.000000000, 0.000000000, 0.000000000, 0.000000000), 3u),
    ParametricCurveSegment(vec4(4.000000000, -3.000000000, 0.000000000, 0.000000000), vec4(4.000000000, 0.000000000, 0.000000000, 0.000000000), 4u)
);

#endif
