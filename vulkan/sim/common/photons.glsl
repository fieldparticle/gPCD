#ifndef PHOTONS_GLSL
#define PHOTONS_GLSL

uint GetParticleType(uint particleID)
{
    uint materialID = uint(round(P[particleID].material_id));
    for (uint ii = 0u; ii < MATERIAL_PROPERTY_COUNT; ++ii) {
        if (MATERIAL_PROPERTIES[ii].materialID == materialID) {
            return MATERIAL_PROPERTIES[ii].particleType;
        }
    }
    return PARTICLE_TYPE_REGULAR;
}

bool IsPhotonParticle(uint particleID)
{
    return GetParticleType(particleID) == PARTICLE_TYPE_PHOTON;
}

bool ShouldSkipParticlePair(uint sourceID, uint targetID)
{
    bool sourcePhoton = IsPhotonParticle(sourceID);
    bool targetPhoton = IsPhotonParticle(targetID);
    return (sourcePhoton && targetPhoton) || (!sourcePhoton && targetPhoton);
}

vec3 ReflectFixedSpeed(vec3 velocity, vec3 normal)
{
    float speed = length(velocity);
    float normalLength = length(normal);
    if (speed <= 0.0 || normalLength <= 0.0) {
        return velocity;
    }

    vec3 unitNormal = normal / normalLength;
    vec3 reflected = velocity - 2.0 * dot(velocity, unitNormal) * unitNormal;
    float reflectedLength = length(reflected);
    if (reflectedLength <= 0.0) {
        return velocity;
    }
    return speed * reflected / reflectedLength;
}

#endif
