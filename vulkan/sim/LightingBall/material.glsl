#ifndef MATERIAL_GLSL
#define MATERIAL_GLSL

const uint COLOR_MODE_COLLISION = 0u;
const uint COLOR_MODE_VELOCITY = 1u;
const uint COLOR_MODE_SOLID = 2u;
const uint COLOR_MODE_LUMENS = 3u;

const uint PARTICLE_TYPE_REGULAR = 0u;
const uint PARTICLE_TYPE_PHOTON = 1u;

struct MaterialProperty
{
    uint materialID;
    uint particleType;
    float relativeMass;
    float tempVel;
    uint colorMode;
    vec4 color;
    float cellDensity;
};

const uint MATERIAL_PROPERTY_COUNT = 2u;
const MaterialProperty MATERIAL_PROPERTIES[2] = MaterialProperty[2](
    MaterialProperty(0u, 1u, 1.000000000, 0.000000000, 3u, vec4(1.000000000, 1.000000000, 1.000000000, 1.000000000), 0.000000000),
    MaterialProperty(1u, 0u, 1.000000000, 0.000000000, 2u, vec4(0.000000000, 1.000000000, 0.000000000, 1.000000000), 0.000000000)
);

const uint HSV_ON = 0u;
const float HSV_SAT = 0.000f;
const float HSV_VAL = 0.000f;
vec3 ncolcolor = vec3(0.0f,1.0f,0.0f);
vec3 colcolor = vec3(1.0f,0.0f,0.0f);
#endif
