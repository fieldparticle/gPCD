#ifndef FORCE_DYNAMICS_LINEAR_RESERVOIR_GLSL
#define FORCE_DYNAMICS_LINEAR_RESERVOIR_GLSL

// Generated from base/ForceDynamics.py by tools/ExportForceDynamicsGLSL.py.
// Finite linear-wall helpers. Requires reservoir.glsl,
// ForceDynamics.glsl, and ForceDynamicsBoundaryParticle.glsl.
// Do not hand edit generated dynamics content.

// Forward declarations for finite linear-wall methods.
BoundaryWallSegment EvaluateLinearWallSegment(uint SourceID, uint BoundaryID);

// Python source: ForceDynamics.py:425
BoundaryWallSegment EvaluateLinearWallSegment(uint SourceID, uint BoundaryID)
{
    vec3 source_position = GetParticlePosition(SourceID).xyz;
    vec2 marker = GetParticlePosition(BoundaryID).xy;
    LinearWallSegment selected = LINEAR_CHAMBER_SEGMENTS[0];
    float best_distance_sq = 3.402823466e+38;
    bool found = false;
    for (uint group = 0u; group < 2u; ++group) {
        uint count = (group == 0u)
            ? LINEAR_CHAMBER_SEGMENT_COUNT : LINEAR_WALL_SEGMENT_COUNT;
        for (uint index = 0u; index < count; ++index) {
            LinearWallSegment candidate = (group == 0u)
                ? LINEAR_CHAMBER_SEGMENTS[index] : LINEAR_WALL_SEGMENTS[index];
            vec2 start_point = candidate.endpoints.xy;
            vec2 end_point = candidate.endpoints.zw;
            vec2 extent = end_point - start_point;
            float extent_sq = dot(extent, extent);
            if (extent_sq <= EPSILON) { continue; }
            float t = clamp(dot(marker - start_point, extent) / extent_sq, 0.0, 1.0);
            vec2 closest = start_point + t * extent;
            float distance_sq = dot(marker - closest, marker - closest);
            if (!found || distance_sq < best_distance_sq) {
                found = true;
                best_distance_sq = distance_sq;
                selected = candidate;
            }
        }
    }
    if (!found) {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);
    }
    float normal_magnitude = length(selected.abc.xy);
    if (normal_magnitude <= EPSILON) {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, selected.wallFlag, false);
    }
    vec3 normal = vec3(selected.abc.xy / normal_magnitude, 0.0);
    float signed_distance = (dot(selected.abc.xy, source_position.xy)
        + selected.abc.z) / normal_magnitude;
    vec2 wall_point = source_position.xy - signed_distance * normal.xy;
    vec2 segment_start = selected.endpoints.xy;
    vec2 segment_extent = selected.endpoints.zw - segment_start;
    float segment_extent_sq = dot(segment_extent, segment_extent);
    float projection = dot(wall_point - segment_start, segment_extent)
        / segment_extent_sq;
    if (projection < -EPSILON || projection > 1.0 + EPSILON) {
        return BoundaryWallSegment(normal, 0.0, 0.0, selected.wallFlag, false);
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
    return BoundaryWallSegment(normal, overlap_area, center_distance, selected.wallFlag, true);
}


#endif
