#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float wall_contact_offset = 0.062500000;
const float death_x_min = 1.000000000;
const float death_x_max = 38.000000000;
const float death_y_min = 1.000000000;
const float death_y_max = 38.000000000;
const float death_z_min = 1.000000000;
const float death_z_max = 38.000000000;
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
    float wallCollisionStiffnessQ;
    float wallTargetPenetrationFraction;
    float wallHardPenetrationFraction;
    float wallCompressionStiffnessGain;
    float wallCompressionStiffnessPower;
};

const uint CURVE_WALL_SEGMENT_COUNT = 0u;
const FunctionWallSegment CURVE_WALL_SEGMENTS[1] = FunctionWallSegment[1](
    FunctionWallSegment(0u, 0u, 0.000000000, 0.000000000, 0.000000000, 0.000000000, 0.000000000, 0.000000000, 1.000000000, 0u, -1.000000000, -1.000000000, -1.000000000, -1.000000000, -1.000000000)
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

const uint LIGHTING_SURFACE_OBJECT_COUNT = 3u;
const LightingSurfaceObjectMetadata LIGHTING_SURFACE_OBJECTS[3] = LightingSurfaceObjectMetadata[3](
    LightingSurfaceObjectMetadata(2u, 2000u, 2u, 0u, 6561u, 38400u, 0u, 0u, vec4(0.000000000, 0.000000000, 0.000000000, 1.000000000), 0.650000000),
    LightingSurfaceObjectMetadata(2u, 3000u, 3u, 6561u, 121u, 600u, 0u, 0u, vec4(0.000000000, 0.000000000, 0.000000000, 1.000000000), 0.500000000),
    LightingSurfaceObjectMetadata(1u, 1000u, 1u, 6682u, 2112u, 11904u, 32u, 64u, vec4(0.000000000, 0.000000000, 0.000000000, 1.000000000), 0.000000000)
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
const uint REFLECTING_WALL_LIGHT_MAP_ENABLED = 1u;
const uint REFLECTING_WALL_LIGHT_MAP_SURFACE_ID = 3000u;
const uint REFLECTING_WALL_LIGHT_MAP_WIDTH = 64u;
const uint REFLECTING_WALL_LIGHT_MAP_HEIGHT = 64u;
const uint REFLECTING_WALL_LIGHT_MAP_COUNT = 4096u;
const uint REFLECTING_WALL_PHOTON_SPLAT_COUNT = 68033u;
const float REFLECTING_WALL_PHOTON_SPLAT_RADIUS = 10.000000000;
const float REFLECTING_WALL_PHOTON_SPLAT_ALPHA = 0.059999999;
const vec4 REFLECTING_WALL_GLASS_TINT = vec4(0.079999998, 0.119999997, 0.140000001, 0.349999994);
const float REFLECTING_WALL_REFLECTION_GAIN = 1.500000000;
const float REFLECTING_WALL_FRESNEL_STRENGTH = 0.250000000;

const uint RECTANGLE_WALL_SEGMENT_COUNT = 2u;
const RectangleWallSegment RECTANGLE_WALL_SEGMENTS[2] = RectangleWallSegment[2](
    RectangleWallSegment(vec3(27.000000000, 14.000000000, 14.000000000), vec3(0.000000000, 1.000000000, 0.000000000), vec3(0.000000000, 0.000000000, 1.000000000), 14.000000000, 14.000000000, normalize(vec3(-1.000000000, 0.000000000, 0.000000000)), 2000u),
    RectangleWallSegment(vec3(13.000000000, 14.000000000, 5.000000000), vec3(1.000000000, 0.000000000, 0.000000000), vec3(0.000000000, 1.000000000, 0.000000000), 14.000000000, 14.000000000, normalize(vec3(0.000000000, 0.000000000, 1.000000000)), 3000u)
);

const uint LIGHTING_SURFACE_WALL_COUNT = 2u;
const LightingSurfaceWallMetadata LIGHTING_SURFACE_WALLS[2] = LightingSurfaceWallMetadata[2](
    LightingSurfaceWallMetadata(vec3(27.000000000, 14.000000000, 14.000000000), vec3(0.000000000, 1.000000000, 0.000000000), vec3(0.000000000, 0.000000000, 1.000000000), 14.000000000, 14.000000000, 80u, 80u, 2000u),
    LightingSurfaceWallMetadata(vec3(13.000000000, 14.000000000, 5.000000000), vec3(1.000000000, 0.000000000, 0.000000000), vec3(0.000000000, 1.000000000, 0.000000000), 14.000000000, 14.000000000, 10u, 10u, 3000u)
);

#define HAS_BOUNDARY
#define HAS_SPHERE
#define HAS_LIGHTING_SPHERE
#endif
