#ifndef FORCE_DYNAMICS_SIMPLE_RECTANGLE_WALL_GLSL
#define FORCE_DYNAMICS_SIMPLE_RECTANGLE_WALL_GLSL

// Generated from C:/_DJ/gPCD/python/base/ForceDynamics.py by tools/ExportForceDynamicsSimpleGLSL.py.
// Rectangle-wall evaluator for the simple generic 3D model.
// Do not hand edit generated dynamics content.

bool RectangleWallProjectPoint(
    RectangleWallSegment segment,
    vec3 point,
    out float uCoord,
    out float vCoord,
    out float signedInwardDistance)
{
    vec3 inwardNormal = normalize(segment.inwardNormal);
    if (any(isnan(inwardNormal)) || any(isinf(inwardNormal))) {
        return false;
    }

    vec3 rel = point - segment.origin;
    uCoord = dot(rel, segment.uAxis);
    vCoord = dot(rel, segment.vAxis);
    if (uCoord < -EPSILON || uCoord > segment.uLength + EPSILON) {
        return false;
    }
    if (vCoord < -EPSILON || vCoord > segment.vLength + EPSILON) {
        return false;
    }

    signedInwardDistance = dot(rel, inwardNormal);
    return true;
}

float RectangleWallPhysicalPenetration(
    RectangleWallSegment segment,
    vec3 point,
    float radius)
{
    float uCoord = 0.0;
    float vCoord = 0.0;
    float signedInwardDistance = 0.0;
    if (!RectangleWallProjectPoint(
            segment,
            point,
            uCoord,
            vCoord,
            signedInwardDistance)) {
        return -1.0;
    }
    return radius - signedInwardDistance;
}

RectangleWallSegment SelectRectangleWallSegment(uint SourceID, uint BoundaryID)
{
    vec3 marker = GetParticlePosition(BoundaryID).xyz;
    RectangleWallSegment selected = RECTANGLE_WALL_SEGMENTS[0];
    float bestDistance = 3.402823466e+38;
    for (uint index = 0u; index < RECTANGLE_WALL_SEGMENT_COUNT; ++index) {
        RectangleWallSegment candidate = RECTANGLE_WALL_SEGMENTS[index];
        float uCoord = 0.0;
        float vCoord = 0.0;
        float signedInwardDistance = 0.0;
        if (!RectangleWallProjectPoint(
                candidate,
                marker,
                uCoord,
                vCoord,
                signedInwardDistance)) {
            continue;
        }

        float distance = abs(signedInwardDistance);
        if (distance < bestDistance) {
            bestDistance = distance;
            selected = candidate;
        }
    }
    return selected;
}

// Python source: ForceDynamics.py:296
BoundaryWallSegment EvaluateRectangleWallSegment(uint SourceID, uint BoundaryID)
{
    RectangleWallSegment selected = SelectRectangleWallSegment(SourceID, BoundaryID);
    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    float radius = P[SourceID].Data.x;
    float penetrationDepth = RectangleWallPhysicalPenetration(
        selected,
        sourcePosition,
        radius);

    vec3 inwardNormal = normalize(selected.inwardNormal);
    vec3 forcePathNormal = -inwardNormal;
    if (penetrationDepth <= EPSILON
        || any(isnan(forcePathNormal))
        || any(isinf(forcePathNormal))) {
        float centerDistance = max(0.0, 2.0 * radius - penetrationDepth);
        return BoundaryWallSegment(
            forcePathNormal,
            0.0,
            centerDistance,
            selected.wallFlag,
            false);
    }

    float centerDistance = max(0.0, 2.0 * radius - penetrationDepth);
    float overlapArea = particle_overlap_area(radius, radius, centerDistance);
    return BoundaryWallSegment(
        forcePathNormal,
        overlapArea,
        centerDistance,
        selected.wallFlag,
        true);
}

#endif
