#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float wall_contact_offset = 0.062500000;
const float death_x_min = 0.500000000;
const float death_x_max = 4.500000000;
const float death_y_min = 0.500000000;
const float death_y_max = 4.500000000;
const float death_z_min = 0.500000000;
const float death_z_max = 4.500000000;
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
    FunctionWallSegment(0u, 1u, 1.000000000, 4.000000000, 1.000000000, 0.000000000, 0.000000000, 0.000000000, -1.000000000, 1u),
    FunctionWallSegment(0u, 1u, 1.000000000, 4.000000000, 4.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 2u),
    FunctionWallSegment(0u, 0u, 1.000000000, 4.000000000, 1.000000000, 0.000000000, 0.000000000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 1.000000000, 4.000000000, 4.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 4u)
);

#endif
