#ifndef MATERIAL_GLSL
#define MATERIAL_GLSL

const uint COLOR_SCHEME_COLLISION = 0u;
const uint COLOR_SCHEME_HSV = 1u;
const uint COLOR_SCHEME_WHITE = 2u;
const uint COLOR_SCHEME_RED = 3u;
const uint COLOR_SCHEME_GREEN = 4u;
const uint COLOR_SCHEME_BLUE = 5u;

struct MaterialProperty
{
    uint materialID;
    float relativeMass;
    float tempVel;
    uint colorScheme;
    float cellDensity;
};

const uint MATERIAL_PROPERTY_COUNT = 1u;
const MaterialProperty MATERIAL_PROPERTIES[1] = MaterialProperty[1](
    MaterialProperty(0u, 1.000000000, 0.000000000, 1u, 0.000000000)
);

const uint HSV_ON = 1u;
const float HSV_SAT = 1.00;
const float HSV_VAL = 1.00;
vec3 ncolcolor = vec3(0.0f,1.0f,0.0f);
vec3 colcolor = vec3(1.0f,0.0f,0.0f);
#endif
