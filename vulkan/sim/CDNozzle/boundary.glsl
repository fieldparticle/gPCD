#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float wall_contact_offset = 0.062500000;
const float death_x_min = 1.000000000;
const float death_x_max = 198.000000000;
const float death_y_min = 12.000000000;
const float death_y_max = 38.000000000;
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

const uint CURVE_WALL_SEGMENT_COUNT = 12u;
const FunctionWallSegment CURVE_WALL_SEGMENTS[12] = FunctionWallSegment[12](
    FunctionWallSegment(1u, 0u, 2.000000000, 102.000000000, 15.000000000, 0.000000000, 0.000000000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(1u, 0u, 2.000000000, 102.000000000, 35.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 4u),
    FunctionWallSegment(0u, 0u, 102.000000000, 112.000000000, 15.000000000, 0.000000000, 0.000000000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 102.000000000, 112.000000000, 35.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 4u),
    FunctionWallSegment(0u, 0u, 112.000000000, 132.000000000, 15.000000000, 0.250000000, -0.006250000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 112.000000000, 132.000000000, 35.000000000, -0.250000000, 0.006250000, 0.000000000, 1.000000000, 4u),
    FunctionWallSegment(0u, 0u, 132.000000000, 137.000000000, 17.500000000, 0.000000000, 0.000000000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 132.000000000, 137.000000000, 32.500000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 4u),
    FunctionWallSegment(0u, 0u, 137.000000000, 157.000000000, 17.500000000, 0.000000000, -0.006250000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 137.000000000, 157.000000000, 32.500000000, 0.000000000, 0.006250000, 0.000000000, 1.000000000, 4u),
    FunctionWallSegment(0u, 0u, 157.000000000, 167.000000000, 15.000000000, 0.000000000, 0.000000000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 157.000000000, 167.000000000, 35.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 4u)
);

struct RectangleWallSegment
{
    vec3 origin;
    vec3 uAxis;
    vec3 vAxis;
    float uLength;
    float vLength;
    vec3 inwardNormal;
    uint wallFlag;
};

const uint RECTANGLE_WALL_SEGMENT_COUNT = 0u;
const RectangleWallSegment RECTANGLE_WALL_SEGMENTS[1] = RectangleWallSegment[1](
    RectangleWallSegment(vec3(0.000000000), vec3(1.000000000, 0.000000000, 0.000000000), vec3(0.000000000, 1.000000000, 0.000000000), 0.000000000, 0.000000000, vec3(0.000000000, 0.000000000, 1.000000000), 0u)
);

#define HAS_BOUNDARY
#endif
