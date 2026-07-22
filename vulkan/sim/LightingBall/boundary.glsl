#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float wall_contact_offset = 0.062500000;
const float death_x_min = 1.000000000;
const float death_x_max = 19.000000000;
const float death_y_min = 1.000000000;
const float death_y_max = 19.000000000;
const float death_z_min = 1.000000000;
const float death_z_max = 21.000000000;
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

const uint CURVE_WALL_SEGMENT_COUNT = 0u;
const FunctionWallSegment CURVE_WALL_SEGMENTS[1] = FunctionWallSegment[1](
    FunctionWallSegment(0u, 0u, 0.000000000, 0.000000000, 0.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 0u)
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

const uint RECTANGLE_WALL_SEGMENT_COUNT = 6u;
const RectangleWallSegment RECTANGLE_WALL_SEGMENTS[6] = RectangleWallSegment[6](
    RectangleWallSegment(vec3(3.000000000, 1.000000000, 1.000000000), vec3(0.000000000, 1.000000000, 0.000000000), vec3(0.000000000, 0.000000000, 1.000000000), 8.000000000, 12.000000000, normalize(vec3(1.000000000, 0.000000000, 0.000000000)), 1u),
    RectangleWallSegment(vec3(11.000000000, 1.000000000, 1.000000000), vec3(0.000000000, 1.000000000, 0.000000000), vec3(0.000000000, 0.000000000, 1.000000000), 8.000000000, 12.000000000, normalize(vec3(-1.000000000, 0.000000000, 0.000000000)), 2u),
    RectangleWallSegment(vec3(3.000000000, 1.000000000, 1.000000000), vec3(1.000000000, 0.000000000, 0.000000000), vec3(0.000000000, 0.000000000, 1.000000000), 8.000000000, 12.000000000, normalize(vec3(0.000000000, 1.000000000, 0.000000000)), 3u),
    RectangleWallSegment(vec3(3.000000000, 9.000000000, 1.000000000), vec3(1.000000000, 0.000000000, 0.000000000), vec3(0.000000000, 0.000000000, 1.000000000), 8.000000000, 12.000000000, normalize(vec3(0.000000000, -1.000000000, 0.000000000)), 4u),
    RectangleWallSegment(vec3(3.000000000, 1.000000000, 1.000000000), vec3(1.000000000, 0.000000000, 0.000000000), vec3(0.000000000, 1.000000000, 0.000000000), 8.000000000, 8.000000000, normalize(vec3(0.000000000, 0.000000000, 1.000000000)), 5u),
    RectangleWallSegment(vec3(3.000000000, 1.000000000, 13.000000000), vec3(1.000000000, 0.000000000, 0.000000000), vec3(0.000000000, 1.000000000, 0.000000000), 8.000000000, 8.000000000, normalize(vec3(0.000000000, 0.000000000, -1.000000000)), 6u)
);

#define HAS_BOUNDARY
#endif
