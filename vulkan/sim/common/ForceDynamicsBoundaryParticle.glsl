#ifndef FORCE_DYNAMICS_BOUNDARY_PARTICLE_GLSL
#define FORCE_DYNAMICS_BOUNDARY_PARTICLE_GLSL

// Generated from base/ForceDynamics.py by tools/ExportForceDynamicsGLSL.py.
// Generic boundary-particle wall helpers. Requires ForceDynamics.glsl.
// Do not hand edit generated dynamics content.

// Forward declarations for boundary-particle methods.
bool IsBoundaryParticle(uint ParticleID);
uint BoundaryParticleWallFlag(uint SourceID, uint BoundaryID);
uint BoundaryParticleVerticalWallFlag(uint SourceID, uint BoundaryID);
BoundaryWallSegment EvaluateHorizontalWallSegment(uint SourceID, uint BoundaryID);
BoundaryWallSegment EvaluateVerticalWallSegment(uint SourceID, uint BoundaryID);
bool ProcessBoundaryParticleWallCollision(uint SourceID, uint BoundaryID, inout vec3 totalForce);
bool InitializeBoundaryParticleWallContactState(uint SourceID, uint BoundaryID);
BoundaryWallSegment EvaluateCDNozzleWallSegment(uint SourceID, uint BoundaryID);
#if defined(FORCE_DYNAMICS_LINEAR_RESERVOIR_AVAILABLE)
BoundaryWallSegment EvaluateLinearWallSegment(uint SourceID, uint BoundaryID);
#endif
BoundaryWallSegment EvaluateWallSegment(uint SourceID, uint BoundaryID);

// Python source: ForceDynamics.py:1090
bool IsBoundaryParticle(uint ParticleID)
{
    return P[ParticleID].ptype > 0.5;
}

// Python source: ForceDynamics.py:140
uint BoundaryParticleWallFlag(uint SourceID, uint BoundaryID)
{
    if (!IsBoundaryParticle(BoundaryID)) {
        return 0u;
    }

    vec4 boundary_position = GetParticlePosition(BoundaryID);
    float mid_y = 0.5 * (BOUNDARY_YMIN + BOUNDARY_YMAX);
    return (boundary_position.y < mid_y) ? 3u : 4u;
}

// Python source: ForceDynamics.py:177
uint BoundaryParticleVerticalWallFlag(uint SourceID, uint BoundaryID)
{
    if (!IsBoundaryParticle(BoundaryID)) {
        return 0u;
    }

    vec4 boundary_position = GetParticlePosition(BoundaryID);
    float mid_x = 0.5 * (BOUNDARY_XMIN + BOUNDARY_XMAX);
    return (boundary_position.x < mid_x) ? 1u : 2u;
}

// Python source: ForceDynamics.py:333
BoundaryWallSegment EvaluateHorizontalWallSegment(uint SourceID, uint BoundaryID)
{
    uint wall_flag = BoundaryParticleWallFlag(SourceID, BoundaryID);
    if (wall_flag == 0u) {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);
    }

    vec4 source_position = GetParticlePosition(SourceID);
    vec4 boundary_position = GetParticlePosition(BoundaryID);
    float radius = P[SourceID].Data.x;
    float offset = WallContactOffsetDistance(radius);
    vec3 ghost = vec3(0.0);
    vec3 normal = vec3(0.0);

    if (wall_flag == 3u) {
        ghost = vec3(source_position.x, boundary_position.y - radius + offset, source_position.z);
        normal = vec3(0.0, -1.0, 0.0);
    } else if (wall_flag == 4u) {
        ghost = vec3(source_position.x, boundary_position.y + radius - offset, source_position.z);
        normal = vec3(0.0, 1.0, 0.0);
    } else {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, wall_flag, false);
    }

    vec3 delta = ghost - source_position.xyz;
    float center_distance = length(delta);
    if (center_distance >= 2.0 * radius) {
        return BoundaryWallSegment(normal, 0.0, center_distance, wall_flag, false);
    }

    float overlap_area = particle_overlap_area(radius, radius, center_distance);
    return BoundaryWallSegment(normal, overlap_area, center_distance, wall_flag, true);
}

// Python source: ForceDynamics.py:377
BoundaryWallSegment EvaluateVerticalWallSegment(uint SourceID, uint BoundaryID)
{
    uint wall_flag = BoundaryParticleVerticalWallFlag(SourceID, BoundaryID);
    if (wall_flag == 0u) {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);
    }

    vec4 source_position = GetParticlePosition(SourceID);
    vec4 boundary_position = GetParticlePosition(BoundaryID);
    float radius = P[SourceID].Data.x;
    float offset = WallContactOffsetDistance(radius);
    vec3 ghost = vec3(0.0);
    vec3 normal = vec3(0.0);

    if (wall_flag == 1u) {
        ghost = vec3(boundary_position.x - radius + offset, source_position.y, source_position.z);
        normal = vec3(-1.0, 0.0, 0.0);
    } else if (wall_flag == 2u) {
        ghost = vec3(boundary_position.x + radius - offset, source_position.y, source_position.z);
        normal = vec3(1.0, 0.0, 0.0);
    } else {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, wall_flag, false);
    }

    vec3 delta = ghost - source_position.xyz;
    float center_distance = length(delta);
    if (center_distance >= 2.0 * radius) {
        return BoundaryWallSegment(normal, 0.0, center_distance, wall_flag, false);
    }

    float overlap_area = particle_overlap_area(radius, radius, center_distance);
    return BoundaryWallSegment(normal, overlap_area, center_distance, wall_flag, true);
}

// Python source: ForceDynamics.py:659
bool ProcessBoundaryParticleWallCollision(uint SourceID, uint BoundaryID, inout vec3 totalForce)
{
    BoundaryWallSegment segment = EvaluateWallSegment(SourceID, BoundaryID);
    if (!segment.valid) {
        return true;
    }
    float source_radius = P[SourceID].Data.x;
    float penetration_depth = ParticlePenetrationDepth(
        source_radius, source_radius, segment.centerDistance);
    float maximum_depth_distance = source_radius
        - WallContactOffsetDistance(source_radius);
    if (segment.centerDistance - maximum_depth_distance < -EPSILON) {
        return SetError(ERROR_WALL_TUNNELING);
    }
    if (!CheckPenetrationStepResolution(
            SourceID, segment.normal, source_radius, vec3(0.0))) {
        return false;
    }
    if (!RegisterMaximumDepthConstraint(
            SourceID, segment.normal, penetration_depth, source_radius,
            vec3(0.0))) {
        return false;
    }
    ContactForceInput contact = ContactForceInput(
        segment.wallFlag,
        CONTACT_WALL,
        segment.normal,
        segment.overlapArea,
        penetration_depth,
        vec3(0.0),
        segment.valid
    );
    return AccumulateContactForce(SourceID, contact, totalForce);
}

// Python source: ForceDynamics.py:671
bool InitializeBoundaryParticleWallContactState(uint SourceID, uint BoundaryID)
{
    // TODO: generate body for InitializeBoundaryParticleWallContactState.
    return false;
}

// Python source: ForceDynamics.py:324
BoundaryWallSegment EvaluateWallSegment(uint SourceID, uint BoundaryID)
{
    uint evaluator_id = uint(round(P[BoundaryID].Data.z));
    if (evaluator_id == 1u) {
        return EvaluateHorizontalWallSegment(SourceID, BoundaryID);
    }
    if (evaluator_id == 2u) {
        return EvaluateVerticalWallSegment(SourceID, BoundaryID);
    }
    if (evaluator_id == 3u) {
    #if defined(FORCE_DYNAMICS_CD_NOZZLE_AVAILABLE)
        return EvaluateCDNozzleWallSegment(SourceID, BoundaryID);
    #else
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);
    #endif
    }
    if (evaluator_id == 4u) {
    #if defined(FORCE_DYNAMICS_LINEAR_RESERVOIR_AVAILABLE)
        return EvaluateLinearWallSegment(SourceID, BoundaryID);
    #else
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);
    #endif
    }
    return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);
}


#endif
