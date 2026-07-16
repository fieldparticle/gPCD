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
    return IsPhotonParticle(sourceID) && IsPhotonParticle(targetID);
}

#endif
