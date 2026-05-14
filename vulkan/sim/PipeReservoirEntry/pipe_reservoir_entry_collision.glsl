#ifndef PIPE_RESERVOIR_ENTRY_COLLISION_GLSL
#define PIPE_RESERVOIR_ENTRY_COLLISION_GLSL

void PipeReservoirProcessBoundaryCollisions(
    uint SourceID,
    inout vec2 overlap_momentum,
    inout float overlap_momentum_sum
) {
    if (BOUNDARY_ENABLED == 0u) {
        return;
    }

    for (uint wall_flag = 3u; wall_flag <= 4u; ++wall_flag) {
        vec2 normal;
        float overlap_area;
        float center_distance;
        if (!BoundaryWallContactGeometry(SourceID, wall_flag, normal, overlap_area, center_distance)) {
            continue;
        }

        P[SourceID].ColFlg = 1;
        float momentum = OverlapMomentum(SourceID, overlap_area, center_distance);
        overlap_momentum -= normal * momentum;
        overlap_momentum_sum += momentum;
    }
}

void PipeReservoirProcessCollision(uint SourceID)
{
    vec2 overlap_momentum = vec2(0.0);
    float overlap_momentum_sum = 0.0;

    uint contact_count = min(P[SourceID].sltnum, 12u);
    for (uint slot = 0u; slot < contact_count; ++slot) {
        ccoll contact_record = P[SourceID].ccs[slot];
        if (contact_record.clflg != CCS_CONTACT_ACTIVE) {
            continue;
        }

        uint TargetID = contact_record.pindex;
        if (TargetID >= NUMPARTS || TargetID == SourceID || !PipeReservoirIsActive(TargetID)) {
            continue;
        }

        vec2 normal;
        float overlap_area;
        float center_distance;
        if (!ParticleContactGeometry(SourceID, TargetID, normal, overlap_area, center_distance)) {
            continue;
        }

        P[SourceID].ColFlg = 1;
        float momentum = OverlapMomentum(SourceID, overlap_area, center_distance);
        overlap_momentum -= normal * momentum;
        overlap_momentum_sum += momentum;
    }

    PipeReservoirProcessBoundaryCollisions(SourceID, overlap_momentum, overlap_momentum_sum);

    P[SourceID].parms.y = overlap_momentum.x;
    P[SourceID].parms.z = overlap_momentum.y;
    P[SourceID].parms.w = overlap_momentum_sum;
}

#endif
