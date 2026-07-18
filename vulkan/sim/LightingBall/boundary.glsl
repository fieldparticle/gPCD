#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float wall_contact_offset = 0.062500000;
const float death_x_min = 1.000000000;
const float death_x_max = 10.000000000;
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

const uint CURVE_WALL_SEGMENT_COUNT = 1u;
const FunctionWallSegment CURVE_WALL_SEGMENTS[1] = FunctionWallSegment[1](
    FunctionWallSegment(0u, 1u, 2.000000000, 8.000000000, 8.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 4u)
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
