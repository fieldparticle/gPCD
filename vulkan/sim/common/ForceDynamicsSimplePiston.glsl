#ifndef FORCE_DYNAMICS_SIMPLE_PISTON_GLSL
#define FORCE_DYNAMICS_SIMPLE_PISTON_GLSL

// Generated from C:/_DJ/gPCD/python/base/ForceDynamics.py by tools/ExportForceDynamicsSimpleGLSL.py.
// Optional analytic piston support for packed reservoir tests.
// Do not hand edit generated dynamics content.

#if defined(FORCE_DYNAMICS_SIMPLE_PISTON_AVAILABLE)

// Python source: ForceDynamics.py:215
bool PistonEnabled()
{
    return true;
}

// Python source: ForceDynamics.py:203
float GetPistonPosition(uint frame)
{
    if (frame < piston_start_frame) {
        return CHAMBER_MIN.x;
    }

    float elapsedFrames = float(frame - piston_start_frame);
    float position = CHAMBER_MIN.x
        + elapsedFrames * ShaderFlags.dt * PISTON_VELOCITY.x;
    return min(position, CHAMBER_MAX.x);
}

// Python source: ForceDynamics.py:226
vec3 GetPistonVelocity(uint frame)
{
    if (frame < piston_start_frame) {
        return vec3(0.0);
    }
    if (GetPistonPosition(frame) >= CHAMBER_MAX.x) {
        return vec3(0.0);
    }
    return PISTON_VELOCITY;
}

// Python source: ForceDynamics.py:237
BoundaryWallSegment EvaluatePistonWall(uint SourceID)
{
    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    if (sourcePosition.y < CHAMBER_MIN.y || sourcePosition.y > CHAMBER_MAX.y
            || sourcePosition.z < CHAMBER_MIN.z
            || sourcePosition.z > CHAMBER_MAX.z) {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 1u, false);
    }

    float radius = P[SourceID].Data.x;
    float offset = WallContactOffsetDistance(radius);
    float pistonX = GetPistonPosition(uint(ShaderFlags.frameNum));
    vec3 ghost = vec3(
        pistonX - radius + offset,
        sourcePosition.y,
        sourcePosition.z);
    vec3 normal = vec3(-1.0, 0.0, 0.0);
    float centerDistance = abs(ghost.x - sourcePosition.x);
    if (centerDistance >= 2.0 * radius) {
        return BoundaryWallSegment(normal, 0.0, centerDistance, 1u, false);
    }

    float overlapArea = particle_overlap_area(radius, radius, centerDistance);
    return BoundaryWallSegment(normal, overlapArea, centerDistance, 1u, true);
}

// Python source: ForceDynamics.py:262
bool ProcessPistonCollision(uint SourceID, inout vec3 totalForce)
{
    if (!PistonEnabled()) { return true; }

    BoundaryWallSegment segment = EvaluatePistonWall(SourceID);
    if (!segment.valid) { return true; }

    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius, sourceRadius, segment.centerDistance);
    float maximumDepthDistance =
        sourceRadius - WallContactOffsetDistance(sourceRadius);
    if (segment.centerDistance - maximumDepthDistance < -EPSILON) {
        return SetError(ERROR_WALL_TUNNELING);
    }

    vec3 pistonVelocity = GetPistonVelocity(uint(ShaderFlags.frameNum));
    if (!CheckPenetrationStepResolution(
            SourceID, segment.normal, sourceRadius, pistonVelocity)) {
        return false;
    }
    if (!RegisterMaximumDepthConstraint(
            SourceID,
            segment.normal,
            penetrationDepth,
            sourceRadius,
            pistonVelocity)) {
        return false;
    }

    P[SourceID].contactCount += 1u;
    ContactForceInput contact = ContactForceInput(
        segment.wallFlag,
        CONTACT_WALL,
        segment.normal,
        segment.overlapArea,
        penetrationDepth,
        pistonVelocity,
        true);
    return AccumulateContactForce(SourceID, contact, totalForce);
}

#endif

#endif
