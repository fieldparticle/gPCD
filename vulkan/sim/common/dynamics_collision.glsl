// Dynamics collision response kernel.
//
// Design boundary:
// - This shader does not do collision detection.
// - A previous compute phase is expected to populate each source particle's
//   ccs[0:sltnum] list with target particle IDs.
// - Duplicate filtering, cell lookup, and CornerList traversal belong to that
//   previous phase.
// - This kernel only consumes the completed ccs list and computes the source
//   particle's collision response.
//
// Thread ownership:
// - One invocation owns one SourceID.
// - The invocation may read target particles, but it writes only P[SourceID].
// - This keeps the response pass free of atomics and friendly to GPU execution.
//
// Current limitations:
// - CircleOverlapArea currently returns 0.0 for unequal radii to match the
//   current equal-radius model.
//
// Permanent parms mapping:
// - parms.x: source particle mass for ApplyOverlapMomentum().
// - parms.y: overlap_momentum_x output from ProcessCollision().
// - parms.z: overlap_momentum_y output from ProcessCollision().
// - parms.w: scalar sum of overlap momentum magnitudes.


const uint CCS_CONTACT_ACTIVE = 1u;
const float EPSILON_DISTANCE = 1.0e-12;

vec2 CurrentLocation(uint particle_id)
{
    // Match the simulation-wide double-buffer selector used by contact
    // detection and rendering.
    Particle particle = P[particle_id];
    if (uint(ShaderFlags.positionBuffer) == 0u) {
        return particle.PosLocA.xy;
    }
    return particle.PosLocB.xy;
}

float ParticleRadius(uint particle_id)
{
    // Data.x is the radius slot defined by the shared Particle structure.
    return P[particle_id].Data.x;
}

float InverseSquareSoftening(uint particle_id)
{
    return max(P[particle_id].Data.y, EPSILON_DISTANCE);
}

float MomentumPerArea(uint particle_id)
{
    return P[particle_id].Data.z;
}

float CircleOverlapArea(float source_radius, float target_radius, float center_distance)
{
    // Equal-radius disk intersection area:
    // 2 r^2 acos(d / 2r) - 0.5 d sqrt(4r^2 - d^2)
    //
    // The Python reference currently raises for unequal radii. The shader
    // cannot raise, so it treats unequal-radius contacts as zero-area until
    // the general formula is added.
    if (abs(source_radius - target_radius) > 1.0e-12) {
        return 0.0;
    }

    float radius = source_radius;
    float distance = clamp(center_distance, 0.0, 2.0 * radius);
    return (
        2.0 * radius * radius * acos(distance / (2.0 * radius))
        - 0.5 * distance * sqrt(max(0.0, 4.0 * radius * radius - distance * distance))
    );
}

float InverseSquareWeight(uint source_id, float distance)
{
    // Softening prevents singular momentum when source and target centers are
    // identical or extremely close.
    float softening = InverseSquareSoftening(source_id);
    return 1.0;// / max(distance * distance, softening * softening);
}

float OverlapMomentum(uint source_id, float overlap_area, float center_distance)
{
    // Memoryless overlap response: current overlap area is converted directly
    // into a momentum amount for this source particle.
    return MomentumPerArea(source_id) * overlap_area * InverseSquareWeight(source_id, center_distance);
}

// Computes narrow-phase geometry for one source-target pair from ccs.
//
// normal points from the source center toward the target center. The source
// response later subtracts normal * momentum, pushing the source away from the
// target.
bool ParticleContactGeometry(
    uint source_id,
    uint target_id,
    out vec2 normal,
    out float overlap_area,
    out float center_distance
) {
    // Read the currently active position buffer for both particles. The ccs
    // record only stores target_id; all geometry comes from live particle state.
    vec2 source_location = CurrentLocation(source_id);
    vec2 target_location = CurrentLocation(target_id);
    // delta points from the source center to the target center. Its length is
    // the center-to-center distance used for both normal direction and overlap.
    vec2 delta = target_location - source_location;
    center_distance = length(delta);

    // Two disks can overlap only when their center distance is smaller than
    // the sum of their radii. Touching exactly at radius_sum is zero overlap.
    float source_radius = ParticleRadius(source_id);
    float target_radius = ParticleRadius(target_id);
    float radius_sum = source_radius + target_radius;
    if (center_distance >= radius_sum) {
        return false;
    }

    // If the centers are coincident, no geometric direction exists. Use a
    // deterministic fallback normal so the response remains finite/repeatable.
    if (center_distance <= EPSILON_DISTANCE) {
        normal = vec2(1.0, 0.0);
    } else {
        normal = delta / center_distance;
    }

    // penetration is the scalar overlap depth along the center line, clamped
    // so extreme overlap cannot imply a contact distance outside the valid
    // circle-overlap formula range.
    float penetration = min(radius_sum - center_distance, min(source_radius, target_radius));
    float contact_distance = radius_sum - penetration;

    // Convert penetration back to an effective center distance for the disk
    // intersection area calculation.
    overlap_area = CircleOverlapArea(source_radius, target_radius, contact_distance);
    return overlap_area > 0.0;
}

bool BoundaryWallContactGeometry(
    uint source_id,
    uint wall_flag,
    out vec2 normal,
    out float overlap_area,
    out float center_distance
) {
    vec2 source_location = CurrentLocation(source_id);
    float radius = ParticleRadius(source_id);
    float distance_to_wall = 0.0;

    if (wall_flag == 1u) {
        distance_to_wall = source_location.x - BOUNDARY_XMIN;
        normal = vec2(-1.0, 0.0);
    } else if (wall_flag == 2u) {
        distance_to_wall = BOUNDARY_XMAX - source_location.x;
        normal = vec2(1.0, 0.0);
    } else if (wall_flag == 3u) {
        distance_to_wall = source_location.y - BOUNDARY_YMIN;
        normal = vec2(0.0, -1.0);
    } else if (wall_flag == 4u) {
        distance_to_wall = BOUNDARY_YMAX - source_location.y;
        normal = vec2(0.0, 1.0);
    } else {
        return false;
    }

    if (distance_to_wall >= radius) {
        return false;
    }

    center_distance = max(0.0, 2.0 * distance_to_wall);
    float penetration = min(2.0 * radius - center_distance, radius);
    float contact_distance = 2.0 * radius - penetration;
    overlap_area = CircleOverlapArea(radius, radius, contact_distance);
    return overlap_area > 0.0;
}

void ProcessBoundaryCollisions(
    uint SourceID,
    inout vec2 overlap_momentum,
    inout float overlap_momentum_sum
) {
    if (BOUNDARY_ENABLED == 0u) {
        return;
    }

    for (uint wall_flag = 1u; wall_flag <= 4u; ++wall_flag) {
        vec2 normal;
        float overlap_area;
        float center_distance;
        if (!BoundaryWallContactGeometry(SourceID, wall_flag, normal, overlap_area, center_distance)) {
            continue;
        }

        float momentum = OverlapMomentum(SourceID, overlap_area, center_distance);
        overlap_momentum -= normal * momentum;
        overlap_momentum_sum += momentum;
    }
}

void ProcessCollision(uint SourceID)
{
    // GLSL equivalent of Python Dynamics.process_source_collision().
    //
    // Preconditions:
    // - SourceID is a valid particle index.
    // - P[SourceID].ccs[0:sltnum] contains the collision list built by the
    //   detection phase.
    //
    // Outputs:
    // - P[SourceID].parms.yzw receive overlap momentum results.
    vec2 overlap_momentum = vec2(0.0);
    float overlap_momentum_sum = 0.0;

    // sltnum is filled by the detection phase and should never exceed ccs[12],
    // but clamp it here so a bad source particle cannot read past its fixed
    // contact storage.
    uint contact_count = min(P[SourceID].sltnum, 12u);
    for (uint slot = 0u; slot < contact_count; ++slot) {
        // Each active ccs slot names exactly one target particle. Empty or
        // disabled slots are skipped; this response pass does not compact or
        // repair the contact list.
        ccoll contact_record = P[SourceID].ccs[slot];
        if (contact_record.clflg != CCS_CONTACT_ACTIVE) {
            continue;
        }

        // The detector is expected to avoid invalid/self contacts, but keep
        // this guard so response cannot walk outside P[] or process SourceID
        // against itself if bad data reaches this pass.
        uint TargetID = contact_record.pindex;
        if (TargetID >= NUMPARTS || TargetID == SourceID) {
            continue;
        }

        // Recompute narrow-phase geometry from the current source/target state.
        // The ccs list only records that a contact candidate exists; geometry
        // is intentionally derived here from current particle buffers.
        vec2 normal;
        float overlap_area;
        float center_distance;
        if (!ParticleContactGeometry(SourceID, TargetID, normal, overlap_area, center_distance)) {
            continue;
        }

        float momentum = OverlapMomentum(SourceID, overlap_area, center_distance);
        // normal points from source to target, so the source response is the
        // opposite direction.
        overlap_momentum -= normal * momentum;
        overlap_momentum_sum += momentum;
    }

    ProcessBoundaryCollisions(SourceID, overlap_momentum, overlap_momentum_sum);

    P[SourceID].parms.y = overlap_momentum.x;
    P[SourceID].parms.z = overlap_momentum.y;
    P[SourceID].parms.w = overlap_momentum_sum;
}

void ApplyOverlapMomentum(uint SourceID)
{
    // Optional second-stage update that mirrors Python apply_overlap_momentum().
    // main() does not call this yet because the Python model keeps momentum
    // calculation and velocity application as separate passes.
    float mass = max(P[SourceID].parms.x, EPSILON_DISTANCE);
    P[SourceID].VelRad.x += P[SourceID].parms.y / mass;
    P[SourceID].VelRad.y += P[SourceID].parms.z / mass;

    // VelRad.w is the cached velocity direction in radians. Keep it aligned
    // with the updated velocity vector; a zero-speed particle has no direction,
    // so store 0.0 as the stable default.
    vec2 velocity = P[SourceID].VelRad.xy;
    P[SourceID].VelRad.w = length(velocity) > 0.0 ? atan(velocity.y, velocity.x) : 0.0;
}
