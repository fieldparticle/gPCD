#ifndef FORCE_DYNAMICS_SIMPLE_FUNCTION_WALL_GLSL
#define FORCE_DYNAMICS_SIMPLE_FUNCTION_WALL_GLSL

// Generated from C:/_DJ/gPCD/python/base/ForceDynamics.py by tools/ExportForceDynamicsSimpleGLSL.py.
// Function-wall evaluator for the simple generic model.
// Do not hand edit generated dynamics content.

vec2 FunctionWallValueSlope(FunctionWallSegment segment, float u)
{
    float du = u - segment.uStart;
    float du2 = du * du;
    float value = segment.fStart
        + segment.a1 * du
        + segment.a2 * du2
        + segment.a3 * du2 * du;
    float slope = segment.a1
        + 2.0 * segment.a2 * du
        + 3.0 * segment.a3 * du2;
    return vec2(value, slope);
}

bool FunctionWallEvaluateAtPoint(
    FunctionWallSegment segment,
    vec2 point,
    out vec2 wallPoint,
    out vec2 normal)
{
    float u = point.x;
    if (segment.independentAxis == 1u) {
        u = point.y;
    }

    float lower = min(segment.uStart, segment.uEnd);
    float upper = max(segment.uStart, segment.uEnd);
    if (u < lower - EPSILON || u > upper + EPSILON) {
        return false;
    }

    vec2 valueSlope = FunctionWallValueSlope(segment, u);
    if (segment.independentAxis == 0u) {
        wallPoint = vec2(u, valueSlope.x);
        if (segment.normalSign >= 0.0) {
            normal = normalize(vec2(-valueSlope.y, 1.0));
        } else {
            normal = normalize(vec2(valueSlope.y, -1.0));
        }
    } else {
        wallPoint = vec2(valueSlope.x, u);
        if (segment.normalSign >= 0.0) {
            normal = normalize(vec2(1.0, -valueSlope.y));
        } else {
            normal = normalize(vec2(-1.0, valueSlope.y));
        }
    }
    return !(any(isnan(wallPoint))
        || any(isinf(wallPoint))
        || any(isnan(normal))
        || any(isinf(normal)));
}

float FunctionWallPhysicalPenetration(
    FunctionWallSegment segment,
    vec2 point,
    float radius)
{
    vec2 wallPoint;
    vec2 normal;
    if (!FunctionWallEvaluateAtPoint(segment, point, wallPoint, normal)) {
        return -1.0;
    }
    float signedOutwardDistance = dot(point - wallPoint, normal);
    return radius + signedOutwardDistance;
}

FunctionWallSegment SelectFunctionWallSegment(uint SourceID, uint BoundaryID)
{
    vec2 marker = GetParticlePosition(BoundaryID).xy;
    FunctionWallSegment selected = CURVE_WALL_SEGMENTS[0];
    float bestDistanceSq = 3.402823466e+38;
    for (uint index = 0u; index < CURVE_WALL_SEGMENT_COUNT; ++index) {
        FunctionWallSegment candidate = CURVE_WALL_SEGMENTS[index];
        vec2 wallPoint;
        vec2 normal;
        if (!FunctionWallEvaluateAtPoint(candidate, marker, wallPoint, normal)) {
            continue;
        }
        float distanceSq = dot(wallPoint - marker, wallPoint - marker);
        if (distanceSq < bestDistanceSq) {
            bestDistanceSq = distanceSq;
            selected = candidate;
        }
    }
    return selected;
}

// Python source: ForceDynamics.py:248
BoundaryWallSegment EvaluateFunctionWallSegment(uint SourceID, uint BoundaryID)
{
    FunctionWallSegment selected = SelectFunctionWallSegment(SourceID, BoundaryID);
    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    vec2 wallPoint;
    vec2 normal2d;
    if (!FunctionWallEvaluateAtPoint(selected, sourcePosition.xy, wallPoint, normal2d)) {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, selected.wallFlag, false);
    }

    float radius = P[SourceID].Data.x;
    float penetrationDepth = FunctionWallPhysicalPenetration(
        selected,
        sourcePosition.xy,
        radius);
    if (penetrationDepth <= EPSILON) {
        float centerDistance = max(0.0, 2.0 * radius - penetrationDepth);
        return BoundaryWallSegment(
            vec3(normal2d, 0.0),
            0.0,
            centerDistance,
            selected.wallFlag,
            false);
    }

    float centerDistance = max(0.0, 2.0 * radius - penetrationDepth);
    float overlapArea = particle_overlap_area(radius, radius, centerDistance);
    return BoundaryWallSegment(
        vec3(normal2d, 0.0),
        overlapArea,
        centerDistance,
        selected.wallFlag,
        true);
}

#endif
