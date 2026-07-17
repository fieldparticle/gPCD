#ifndef FORCE_DYNAMICS_SIMPLE_BOUNDARY_PARTICLE_GLSL
#define FORCE_DYNAMICS_SIMPLE_BOUNDARY_PARTICLE_GLSL

// Generated from C:/_DJ/gPCD/python/base/ForceDynamics.py by tools/ExportForceDynamicsSimpleGLSL.py.
// Boundary-particle locality helpers for the simple generic model.
// Do not hand edit generated dynamics content.

// Python source: ForceDynamics.py:737
bool BoundaryMarkerApplies(uint SourceID, uint BoundaryID)
{
    if (!IsBoundaryParticle(BoundaryID)) { return false; }
    vec4 sourcePosition = GetParticlePosition(SourceID);
    vec4 boundaryPosition = GetParticlePosition(BoundaryID);
    return abs(sourcePosition.x - boundaryPosition.x) <= 1.0
        && abs(sourcePosition.y - boundaryPosition.y) <= 1.0
        && abs(sourcePosition.z - boundaryPosition.z) <= 1.0;
}

bool ProcessFunctionWallCollision(
    uint SourceID, BoundaryWallSegment segment, inout vec3 totalForce);

#endif
