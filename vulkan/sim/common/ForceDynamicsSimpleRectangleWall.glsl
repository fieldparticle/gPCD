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
    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    float sourceRadius = P[SourceID].Data.x;
    RectangleWallSegment selected = RECTANGLE_WALL_SEGMENTS[0];
    float bestScore = -3.402823466e+38;
    for (uint index = 0u; index < RECTANGLE_WALL_SEGMENT_COUNT; ++index) {
        RectangleWallSegment candidate = RECTANGLE_WALL_SEGMENTS[index];
        float uCoord = 0.0;
        float vCoord = 0.0;
        float signedInwardDistance = 0.0;
        if (!RectangleWallProjectPoint(
                candidate,
                sourcePosition,
                uCoord,
                vCoord,
                signedInwardDistance)) {
            continue;
        }

        float penetrationDepth = sourceRadius - signedInwardDistance;
        float score = penetrationDepth > EPSILON
            ? 1000000.0 + penetrationDepth
            : -abs(signedInwardDistance);
        if (score > bestScore) {
            bestScore = score;
            selected = candidate;
        }
    }
    return selected;
}

// Python source: ForceDynamics.py:407
BoundaryWallSegment EvaluateRectangleWallSegmentContact(
    uint SourceID, RectangleWallSegment selected)
{
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
            -1.0,
            -1.0,
            -1.0,
            -1.0,
            -1.0,
            false);
    }

    float centerDistance = max(0.0, 2.0 * radius - penetrationDepth);
    float overlapArea = particle_overlap_area(radius, radius, centerDistance);
    return BoundaryWallSegment(
        forcePathNormal,
        overlapArea,
        centerDistance,
        selected.wallFlag,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        true);
}

BoundaryWallSegment EvaluateRectangleWallSegment(uint SourceID, uint BoundaryID)
{
    RectangleWallSegment selected = SelectRectangleWallSegment(SourceID, BoundaryID);
    return EvaluateRectangleWallSegmentContact(SourceID, selected);
}

BoundaryWallContactSet EvaluateRectangleWallContacts(uint SourceID)
{
    BoundaryWallContactSet contacts;
    contacts.count = 0u;
    float sourceRadius = P[SourceID].Data.x;

    for (uint segmentIndex = 0u;
            segmentIndex < RECTANGLE_WALL_SEGMENT_COUNT;
            ++segmentIndex) {
        BoundaryWallSegment segment = EvaluateRectangleWallSegmentContact(
            SourceID,
            RECTANGLE_WALL_SEGMENTS[segmentIndex]);
        if (!segment.valid) {
            continue;
        }

        float penetrationDepth = ParticlePenetrationDepth(
            sourceRadius,
            sourceRadius,
            segment.centerDistance);
        bool replaced = false;
        for (uint contactIndex = 0u;
                contactIndex < contacts.count;
                ++contactIndex) {
            if (contacts.segments[contactIndex].wallFlag != segment.wallFlag) {
                continue;
            }
            float previousDepth = ParticlePenetrationDepth(
                sourceRadius,
                sourceRadius,
                contacts.segments[contactIndex].centerDistance);
            if (penetrationDepth > previousDepth) {
                contacts.segments[contactIndex] = segment;
            }
            replaced = true;
            break;
        }
        if (replaced) {
            continue;
        }
        if (contacts.count >= DUP_LIST_SIZE) {
            SetError(ERROR_CONTACT_LIST_MISSING, SourceID);
            return contacts;
        }
        contacts.segments[contacts.count] = segment;
        contacts.count += 1u;
    }

    return contacts;
}

#endif
