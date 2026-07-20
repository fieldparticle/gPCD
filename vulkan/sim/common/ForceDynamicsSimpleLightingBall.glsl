#ifndef FORCE_DYNAMICS_SIMPLE_LIGHTING_BALL_GLSL
#define FORCE_DYNAMICS_SIMPLE_LIGHTING_BALL_GLSL

// Generated from C:/_DJ/gPCD/python/base/ForceDynamics.py by tools/ExportForceDynamicsSimpleGLSL.py.
// Analytic lighting-ball sphere evaluator for the simple generic 3D model.
// Do not hand edit generated dynamics content.

struct LightingBallCollisionResult
{
    bool handled;
    bool ok;
    BoundaryWallSegment segment;
};

bool IsLightingBallMarker(uint BoundaryID)
{
    if (LIGHTING_BALL_ENABLED == 0u || !IsBoundaryParticle(BoundaryID)) {
        return false;
    }
    uint materialID = uint(round(P[BoundaryID].material_id));
    return materialID == LIGHTING_BALL_MATERIAL_ID;
}

LightingBallCollisionResult NoLightingBallCollision()
{
    return LightingBallCollisionResult(
        false,
        true,
        BoundaryWallSegment(vec3(0.0), 0.0, 0.0, LIGHTING_BALL_WALL_FLAG, false));
}

// Python source: ForceDynamics.py:641
BoundaryWallSegment EvaluateLightingBallContact(uint SourceID)
{
    if (LIGHTING_BALL_ENABLED == 0u || LIGHTING_BALL_RADIUS <= 0.0) {
        return BoundaryWallSegment(
            vec3(0.0),
            0.0,
            0.0,
            LIGHTING_BALL_WALL_FLAG,
            false);
    }

    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    vec3 delta = sourcePosition - LIGHTING_BALL_CENTER;
    float centerDistance = length(delta);
    if (centerDistance <= EPSILON
            || isnan(centerDistance)
            || isinf(centerDistance)) {
        return BoundaryWallSegment(
            vec3(0.0),
            0.0,
            0.0,
            LIGHTING_BALL_WALL_FLAG,
            false);
    }

    float sourceRadius = P[SourceID].Data.x;
    float signedSurfaceDistance = centerDistance - LIGHTING_BALL_RADIUS;
    float penetrationDepth = sourceRadius - signedSurfaceDistance;
    if (penetrationDepth <= EPSILON) {
        float contactCenterDistance =
            max(0.0, 2.0 * sourceRadius - penetrationDepth);
        return BoundaryWallSegment(
            delta / centerDistance,
            0.0,
            contactCenterDistance,
            LIGHTING_BALL_WALL_FLAG,
            false);
    }

    vec3 normal = delta / centerDistance;
    float contactCenterDistance =
        max(0.0, 2.0 * sourceRadius - penetrationDepth);
    float overlapArea = particle_overlap_area(
        sourceRadius,
        sourceRadius,
        contactCenterDistance);
    return BoundaryWallSegment(
        normal,
        overlapArea,
        contactCenterDistance,
        LIGHTING_BALL_WALL_FLAG,
        true);
}

// Python source: ForceDynamics.py:680
LightingBallCollisionResult ProcessLightingBallCollision(
    uint SourceID,
    inout vec3 totalForce)
{
    totalForce += vec3(0.0);
    BoundaryWallSegment segment = EvaluateLightingBallContact(SourceID);
    if (!segment.valid) {
        return NoLightingBallCollision();
    }

    vec3 startVelocity = GetStartFrameVelocity(SourceID).xyz;
    float inwardSpeed = -dot(startVelocity, segment.normal);
    if (inwardSpeed <= EPSILON) {
        return NoLightingBallCollision();
    }

    P[SourceID].colFlg = 1u;
    return LightingBallCollisionResult(true, true, segment);
}

bool RegisterResolvedLightingBallContactStep(uint SourceID)
{
    return true;
}

#endif
