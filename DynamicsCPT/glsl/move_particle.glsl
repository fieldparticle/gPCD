const uint POSITION_BUFFER_A = 0u;
const uint POSITION_BUFFER_B = 1u;

uint CurrentPositionBuffer(uint particle_id)
{
    return P[particle_id].PosLocA.w == 0.0 ? POSITION_BUFFER_A : POSITION_BUFFER_B;
}

void MoveParticle(uint SourceID, uint positionBuffer)
{
    // GLSL equivalent of Python Base.step() position movement plus Base.move():
    // write the next location into the inactive position buffer using the
    // current velocity, then flip the active position flags.
    uint current_buffer = positionBuffer;
    if (current_buffer != POSITION_BUFFER_A && current_buffer != POSITION_BUFFER_B) {
        current_buffer = CurrentPositionBuffer(SourceID);
    }

    vec2 velocity = P[SourceID].VelRad.xy;
    if (current_buffer == POSITION_BUFFER_A) {
        P[SourceID].PosLocB.xy = P[SourceID].PosLocA.xy + velocity * dt;
        P[SourceID].PosLocA.w = 1.0;
        P[SourceID].PosLocB.w = 0.0;
    } else {
        P[SourceID].PosLocA.xy = P[SourceID].PosLocB.xy + velocity * dt;
        P[SourceID].PosLocA.w = 0.0;
        P[SourceID].PosLocB.w = 1.0;
    }
}
