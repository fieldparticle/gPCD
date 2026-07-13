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
    MaterialProperty(0u, 1.000000000, 0.000000000, COLOR_SCHEME_HSV, 0.000000000)
);

#endif
