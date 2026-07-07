#ifndef FORCE_DYNAMICS_SIMPLE_PARAMETRIC_WALL_GLSL
#define FORCE_DYNAMICS_SIMPLE_PARAMETRIC_WALL_GLSL

// Generated from C:/_DJ/gPCD/python/base/ForceDynamics.py by tools/ExportForceDynamicsSimpleGLSL.py.
// Parametric curve-wall evaluator for the simple generic model.
// Do not hand edit generated dynamics content.

vec2 ParametricCurvePoint(ParametricCurveSegment segment, float t)
{
    float t2 = t * t;
    vec4 powers = vec4(1.0, t, t2, t2 * t);
    return vec2(
        dot(segment.xCoefficients, powers),
        dot(segment.yCoefficients, powers));
}

vec2 ParametricCurveTangent(ParametricCurveSegment segment, float t)
{
    float t2 = t * t;
    vec4 derivative = vec4(0.0, 1.0, 2.0 * t, 3.0 * t2);
    return vec2(
        dot(segment.xCoefficients, derivative),
        dot(segment.yCoefficients, derivative));
}

vec2 ParametricCurveSecondDerivative(ParametricCurveSegment segment, float t)
{
    vec4 derivative = vec4(0.0, 0.0, 2.0, 6.0 * t);
    return vec2(
        dot(segment.xCoefficients, derivative),
        dot(segment.yCoefficients, derivative));
}

vec3 ParametricCurveClosestPoint(ParametricCurveSegment segment, vec2 point)
{
    const uint sampleCount = 16u;
    const uint iterationCount = 12u;
    const float solverTolerance = 1.0e-6;
    float bestT = 0.0;
    float bestDistanceSq = 3.402823466e+38;
    uint bestIndex = 0u;

    for (uint index = 0u; index <= sampleCount; ++index) {
        float t = float(index) / float(sampleCount);
        vec2 delta = ParametricCurvePoint(segment, t) - point;
        float distanceSq = dot(delta, delta);
        if (distanceSq < bestDistanceSq) {
            bestDistanceSq = distanceSq;
            bestT = t;
            bestIndex = index;
        }
    }

    float lower = float((bestIndex > 0u) ? bestIndex - 1u : 0u) / float(sampleCount);
    float upper = float(min(bestIndex + 1u, sampleCount)) / float(sampleCount);
    for (uint iteration = 0u; iteration < iterationCount; ++iteration) {
        vec2 curvePoint = ParametricCurvePoint(segment, bestT);
        vec2 tangent = ParametricCurveTangent(segment, bestT);
        vec2 secondVector = ParametricCurveSecondDerivative(segment, bestT);
        vec2 delta = curvePoint - point;
        float firstDerivative = dot(delta, tangent);
        float secondDerivative = dot(tangent, tangent) + dot(delta, secondVector);
        if (abs(secondDerivative) <= solverTolerance) { break; }
        float nextT = clamp(bestT - firstDerivative / secondDerivative, lower, upper);
        if (abs(nextT - bestT) <= solverTolerance) {
            bestT = nextT;
            break;
        }
        bestT = nextT;
    }
    return vec3(bestT, ParametricCurvePoint(segment, bestT));
}

// Python source: ForceDynamics.py:139
BoundaryWallSegment EvaluateParametricWallSegment(uint SourceID, uint BoundaryID)
{
    vec2 marker = GetParticlePosition(BoundaryID).xy;
    ParametricCurveSegment selected = CURVE_WALL_SEGMENTS[0];
    float bestMarkerDistanceSq = 3.402823466e+38;
    for (uint index = 0u; index < CURVE_WALL_SEGMENT_COUNT; ++index) {
        ParametricCurveSegment candidate = CURVE_WALL_SEGMENTS[index];
        vec3 closest = ParametricCurveClosestPoint(candidate, marker);
        float distanceSq = dot(closest.yz - marker, closest.yz - marker);
        if (distanceSq < bestMarkerDistanceSq) {
            bestMarkerDistanceSq = distanceSq;
            selected = candidate;
        }
    }

    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    vec3 closest = ParametricCurveClosestPoint(selected, sourcePosition.xy);
    vec2 wallPoint = closest.yz;
    vec2 tangent = ParametricCurveTangent(selected, closest.x);
    float tangentMagnitude = length(tangent);
    if (tangentMagnitude <= EPSILON) {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, selected.wallFlag, false);
    }

    vec3 normal = vec3(tangent.y, -tangent.x, 0.0) / tangentMagnitude;
    float radius = P[SourceID].Data.x;
    float offset = WallContactOffsetDistance(radius);
    vec3 ghost = vec3(wallPoint, sourcePosition.z) + normal * (radius - offset);
    float centerDistance = length(ghost - sourcePosition);
    if (centerDistance >= 2.0 * radius) {
        return BoundaryWallSegment(normal, 0.0, centerDistance, selected.wallFlag, false);
    }

    float overlapArea = particle_overlap_area(radius, radius, centerDistance);
    return BoundaryWallSegment(normal, overlapArea, centerDistance, selected.wallFlag, true);
}

#endif
