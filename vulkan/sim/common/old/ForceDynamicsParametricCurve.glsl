#ifndef FORCE_DYNAMICS_PARAMETRIC_CURVE_GLSL
#define FORCE_DYNAMICS_PARAMETRIC_CURVE_GLSL

// Generated from base/ForceDynamics.py by tools/ExportForceDynamicsGLSL.py.
// Parametric boundary-wall helpers. Requires reservoir.glsl,
// ForceDynamics.glsl, and ForceDynamicsBoundaryParticle.glsl.
// Do not hand edit generated dynamics content.

vec2 ParametricCurvePoint(ParametricCurveSegment segment, float t)
{
    float t2 = t * t;
    vec4 powers = vec4(1.0, t, t2, t2 * t);
    return vec2(dot(segment.xCoefficients, powers),
        dot(segment.yCoefficients, powers));
}

vec2 ParametricCurveTangent(ParametricCurveSegment segment, float t)
{
    float t2 = t * t;
    vec4 derivative = vec4(0.0, 1.0, 2.0 * t, 3.0 * t2);
    return vec2(dot(segment.xCoefficients, derivative),
        dot(segment.yCoefficients, derivative));
}

vec2 ParametricCurveSecondDerivative(
    ParametricCurveSegment segment, float t)
{
    vec4 derivative = vec4(0.0, 0.0, 2.0, 6.0 * t);
    return vec2(dot(segment.xCoefficients, derivative),
        dot(segment.yCoefficients, derivative));
}

vec3 ParametricCurveClosestPoint(
    ParametricCurveSegment segment, vec2 point)
{
    const uint sampleCount = 16u;
    const uint iterationCount = 12u;
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
    float lower = float((bestIndex > 0u) ? bestIndex - 1u : 0u)
        / float(sampleCount);
    float upper = float(min(bestIndex + 1u, sampleCount))
        / float(sampleCount);
    for (uint iteration = 0u; iteration < iterationCount; ++iteration) {
        vec2 curvePoint = ParametricCurvePoint(segment, bestT);
        vec2 tangent = ParametricCurveTangent(segment, bestT);
        vec2 secondVector =
            ParametricCurveSecondDerivative(segment, bestT);
        vec2 delta = curvePoint - point;
        float firstDerivative = dot(delta, tangent);
        float secondDerivative = dot(tangent, tangent)
            + dot(delta, secondVector);
        if (abs(secondDerivative) <= 1.0e-14) { break; }
        float nextT = clamp(
            bestT - firstDerivative / secondDerivative, lower, upper);
        if (abs(nextT - bestT) <= 1.0e-7) {
            bestT = nextT;
            break;
        }
        bestT = nextT;
    }
    return vec3(bestT, ParametricCurvePoint(segment, bestT));
}

// Forward declarations for parametric wall methods.
BoundaryWallSegment EvaluateParametricWallSegment(uint SourceID, uint BoundaryID);

// Python source: ForceDynamics.py:493
BoundaryWallSegment EvaluateParametricWallSegment(uint SourceID, uint BoundaryID)
{
    vec2 marker = GetParticlePosition(BoundaryID).xy;
    ParametricCurveSegment selected = CURVE_WALL_SEGMENTS[0];
    float best_marker_distance_sq = 3.402823466e+38;
    for (uint index = 0u; index < CURVE_WALL_SEGMENT_COUNT; ++index) {
        ParametricCurveSegment candidate = CURVE_WALL_SEGMENTS[index];
        vec3 closest = ParametricCurveClosestPoint(candidate, marker);
        float distance_sq = dot(closest.yz - marker, closest.yz - marker);
        if (distance_sq < best_marker_distance_sq) {
            best_marker_distance_sq = distance_sq;
            selected = candidate;
        }
    }
    vec3 source_position = GetParticlePosition(SourceID).xyz;
    vec3 closest = ParametricCurveClosestPoint(selected, source_position.xy);
    float parameter = closest.x;
    vec2 wall_point = closest.yz;
    vec2 tangent = ParametricCurveTangent(selected, parameter);
    float tangent_magnitude = length(tangent);
    if (tangent_magnitude <= EPSILON) {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, selected.wallFlag, false);
    }
    vec3 normal = vec3(0.0);
    if (selected.wallFlag == 3u) {
        normal = vec3(tangent.y, -tangent.x, 0.0) / tangent_magnitude;
    } else if (selected.wallFlag == 4u) {
        normal = vec3(-tangent.y, tangent.x, 0.0) / tangent_magnitude;
    } else {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, selected.wallFlag, false);
    }
    float radius = P[SourceID].Data.x;
    float offset = WallContactOffsetDistance(radius);
    vec3 ghost = vec3(wall_point, source_position.z)
        + normal * (radius - offset);
    float center_distance = length(ghost - source_position);
    if (center_distance >= 2.0 * radius) {
        return BoundaryWallSegment(normal, 0.0, center_distance, selected.wallFlag, false);
    }
    float overlap_area = particle_overlap_area(radius, radius, center_distance);
    return BoundaryWallSegment(
        normal, overlap_area, center_distance, selected.wallFlag, true);
}


#endif
