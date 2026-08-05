#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float wall_contact_offset = 0.062500000;
const float death_x_min = 1.000000000;
const float death_x_max = 498.000000000;
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
    FunctionWallSegment(1u, 0u, 2.000000000, 402.000000000, 15.000000000, 0.000000000, 0.000000000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 402.000000000, 412.000000000, 15.000000000, 0.000000000, 0.000000000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 412.000000000, 432.000000000, 15.000000000, 0.325000000, -0.008125000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 432.000000000, 437.000000000, 18.250000000, 0.000000000, 0.000000000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 437.000000000, 457.000000000, 18.250000000, 0.000000000, -0.008125000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(0u, 0u, 457.000000000, 467.000000000, 15.000000000, 0.000000000, 0.000000000, 0.000000000, -1.000000000, 3u),
    FunctionWallSegment(1u, 0u, 2.000000000, 402.000000000, 35.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 4u),
    FunctionWallSegment(0u, 0u, 402.000000000, 412.000000000, 35.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 4u),
    FunctionWallSegment(0u, 0u, 412.000000000, 432.000000000, 35.000000000, -0.325000000, 0.008125000, 0.000000000, 1.000000000, 4u),
    FunctionWallSegment(0u, 0u, 432.000000000, 437.000000000, 31.750000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 4u),
    FunctionWallSegment(0u, 0u, 437.000000000, 457.000000000, 31.750000000, 0.000000000, 0.008125000, 0.000000000, 1.000000000, 4u),
    FunctionWallSegment(0u, 0u, 457.000000000, 467.000000000, 35.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 4u)
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

struct LightingSurfaceObjectMetadata
{
    uint surfaceType;
    uint surfaceID;
    uint materialID;
    uint vertexOffset;
    uint vertexCount;
    uint indexCount;
    uint sphereLatSegments;
    uint sphereLonSegments;
    vec4 initialSurfaceColor;
    float depositRadius;
};

struct LightingSurfaceWallMetadata
{
    vec3 origin;
    vec3 uAxis;
    vec3 vAxis;
    float uLength;
    float vLength;
    uint uStepCount;
    uint vStepCount;
    uint wallFlag;
};

const uint LIGHTING_SURFACE_OBJECT_COUNT = 0u;
const LightingSurfaceObjectMetadata LIGHTING_SURFACE_OBJECTS[1] = LightingSurfaceObjectMetadata[1](
    LightingSurfaceObjectMetadata(0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, vec4(0.000000000, 0.000000000, 0.000000000, 1.000000000), 0.000000000)
);

#define LIGHTING_SPHERE_SURFACE_MAP_DEFINED 1
const uint LIGHTING_SPHERE_SURFACE_MAP_SURFACE_ID = 0u;
const uint LIGHTING_SPHERE_SURFACE_MAP_COUNT = 0u;
const uint LIGHTING_SPHERE_SURFACE_MAP_MATERIAL_IDS[1] = uint[1](0u);
const vec4 LIGHTING_SPHERE_SURFACE_MAP_ALBEDOS[1] = vec4[1](vec4(0.0));

#define LIGHTING_SPHERE_DECAL_MAP_DEFINED 1
const uint LIGHTING_SPHERE_DECAL_MAP_SURFACE_ID = 0u;
const uint LIGHTING_SPHERE_DECAL_MAP_COUNT = 0u;
const uvec4 LIGHTING_SPHERE_DECAL_MAP_CELLS[1] = uvec4[1](uvec4(0u));
const vec4 LIGHTING_SPHERE_DECAL_MAP_ALBEDOS[1] = vec4[1](vec4(0.0));

#define REFLECTING_WALL_LIGHT_MAP_DEFINED 1
const uint REFLECTING_WALL_LIGHT_MAP_ENABLED = 0u;
const uint REFLECTING_WALL_LIGHT_MAP_SURFACE_ID = 0u;
const uint REFLECTING_WALL_LIGHT_MAP_WIDTH = 1u;
const uint REFLECTING_WALL_LIGHT_MAP_HEIGHT = 1u;
const uint REFLECTING_WALL_LIGHT_MAP_COUNT = 1u;
const uint REFLECTING_WALL_PHOTON_SPLAT_COUNT = 1u;
const float REFLECTING_WALL_PHOTON_SPLAT_RADIUS = 10.000000000;
const float REFLECTING_WALL_PHOTON_SPLAT_ALPHA = 0.059999999;
const vec4 REFLECTING_WALL_GLASS_TINT = vec4(0.079999998, 0.119999997, 0.140000001, 0.349999994);
const float REFLECTING_WALL_REFLECTION_GAIN = 1.500000000;
const float REFLECTING_WALL_FRESNEL_STRENGTH = 0.250000000;

const uint RECTANGLE_WALL_SEGMENT_COUNT = 0u;
const RectangleWallSegment RECTANGLE_WALL_SEGMENTS[1] = RectangleWallSegment[1](
    RectangleWallSegment(vec3(0.000000000), vec3(1.000000000, 0.000000000, 0.000000000), vec3(0.000000000, 1.000000000, 0.000000000), 0.000000000, 0.000000000, vec3(0.000000000, 0.000000000, 1.000000000), 0u)
);

const uint LIGHTING_SURFACE_WALL_COUNT = 0u;
const LightingSurfaceWallMetadata LIGHTING_SURFACE_WALLS[1] = LightingSurfaceWallMetadata[1](
    LightingSurfaceWallMetadata(vec3(0.000000000), vec3(1.000000000, 0.000000000, 0.000000000), vec3(0.000000000, 1.000000000, 0.000000000), 0.000000000, 0.000000000, 1u, 1u, 0u)
);

#define HAS_BOUNDARY
#endif
