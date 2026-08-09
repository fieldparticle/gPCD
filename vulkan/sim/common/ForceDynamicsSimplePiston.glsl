#ifndef FORCE_DYNAMICS_SIMPLE_PISTON_GLSL
#define FORCE_DYNAMICS_SIMPLE_PISTON_GLSL

// Generated from C:/_DJ/gPCD/python/base/ForceDynamics.py by tools/ExportForceDynamicsSimpleGLSL.py.
// Optional analytic piston support for packed reservoir tests.
// Do not hand edit generated dynamics content.

#if defined(FORCE_DYNAMICS_SIMPLE_PISTON_AVAILABLE)

// Python source: ForceDynamics.py:661
bool PistonEnabled()
{
    return true;
}

// Python source: ForceDynamics.py:650
float GetPistonPosition(uint frame)
{
    uint pistonStartFrame = uint(piston_start_frame);
    if (frame < pistonStartFrame) {
        return piston_x_start;
    }

    float elapsedFrames = float(frame - pistonStartFrame);
    vec3 pistonVelocity = vec3(
        piston_velocity_x,
        piston_velocity_y,
        piston_velocity_z);
    float position = piston_x_start
        + elapsedFrames * piston_dt * pistonVelocity.x;
    return min(position, piston_x_stop);
}

// Python source: ForceDynamics.py:675
vec3 GetPistonVelocity(uint frame)
{
    uint pistonStartFrame = uint(piston_start_frame);
    if (frame < pistonStartFrame) {
        return vec3(0.0);
    }
    if (GetPistonPosition(frame) >= piston_x_stop) {
        return vec3(0.0);
    }
    return vec3(
        piston_velocity_x,
        piston_velocity_y,
        piston_velocity_z);
}

// Python source: ForceDynamics.py:686
BoundaryWallSegment EvaluatePistonWall(uint SourceID)
{
    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
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
        return BoundaryWallSegment(
            normal,
            0.0,
            centerDistance,
            1u,
            -1.0,
            -1.0,
            -1.0,
            -1.0,
            -1.0,
            false);
    }

    float overlapArea = particle_overlap_area(radius, radius, centerDistance);
    return BoundaryWallSegment(
        normal,
        overlapArea,
        centerDistance,
        1u,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        true);
}

// Python source: ForceDynamics.py:700
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
        return SetError(ERROR_WALL_TUNNELING, SourceID);
    }

    vec3 pistonVelocity = GetPistonVelocity(uint(ShaderFlags.frameNum));
    if (!CheckPenetrationStepResolution(
            SourceID,
            segment.normal,
            sourceRadius,
            pistonVelocity,
            CONTACT_WALL,
            -1.0)) {
        return false;
    }
    if (!RegisterMaximumDepthConstraint(
            SourceID,
            segment.normal,
            penetrationDepth,
            sourceRadius,
            pistonVelocity,
            CONTACT_WALL,
            -1.0)) {
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
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        true);
    return AccumulateContactForce(SourceID, contact, totalForce);
}

bool CheckResolvedPistonContactStep(uint SourceID)
{
    if (!PistonEnabled()) { return true; }

    BoundaryWallSegment segment = EvaluatePistonWall(SourceID);
    if (!segment.valid) { return true; }

    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius,
        sourceRadius,
        segment.centerDistance);
    return CheckResolvedContactStep(
        SourceID,
        segment.normal,
        penetrationDepth,
        sourceRadius,
        GetPistonVelocity(uint(ShaderFlags.frameNum)),
        CONTACT_WALL,
        -1.0);
}

bool RegisterResolvedPistonContactStep(uint SourceID)
{
    if (!PistonEnabled()) { return true; }

    BoundaryWallSegment segment = EvaluatePistonWall(SourceID);
    if (!segment.valid) { return true; }

    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius,
        sourceRadius,
        segment.centerDistance);
    return RegisterContactStepConstraint(
        SourceID,
        segment.normal,
        penetrationDepth,
        sourceRadius,
        GetPistonVelocity(uint(ShaderFlags.frameNum)),
        CONTACT_WALL,
        -1.0);
}

#endif

#endif
