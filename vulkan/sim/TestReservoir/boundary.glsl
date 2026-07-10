#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float wall_contact_offset = 0.062500000;
const float death_x_min = 1.000000000;
const float death_x_max = 30.000000000;
const float death_y_min = 1.000000000;
const float death_y_max = 9.000000000;
const float death_z_min = 0.000000000;
const float death_z_max = 4.000000000;
struct FunctionWallSegment
{
    uint boundaryKind;
    uint independentAxis;
    float uStart;
    float uEnd;
    float fStart;
    float a1;
    float a2;
    float a3;
    float normalSign;
    uint wallFlag;
};

const uint CURVE_WALL_SEGMENT_COUNT = 4u;
const FunctionWallSegment CURVE_WALL_SEGMENTS[4] = FunctionWallSegment[4](
    FunctionWallSegment(1u, 0u, 2.000000000, 20.000000000, 2.000000000, 0.000000000, 0.000000000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(1u, 0u, 20.000000000, 2.000000000, 8.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 4u),
    FunctionWallSegment(0u, 0u, 20.000000000, 25.000000000, 2.000000000, 0.250000000, 0.000000000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 25.000000000, 20.000000000, 6.750000000, -0.250000000, 0.000000000, 0.000000000, 1.000000000, 4u)
);

#endif
