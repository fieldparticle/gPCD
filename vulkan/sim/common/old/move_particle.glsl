const uint POSITION_BUFFER_A = 0u;
const uint POSITION_BUFFER_B = 1u;

void MoveParticle(uint SourceID, uint positionBuffer, float dt)
{
    vec2 velocity = P[SourceID].VelRad.xy;

    if (positionBuffer == POSITION_BUFFER_A)
	{
        P[SourceID].PosLocB.xy = P[SourceID].PosLocA.xy + velocity * dt;
        P[SourceID].PosLocA.w = 1.0;
        P[SourceID].PosLocB.w = 0.0;
    }
    else
	{
        P[SourceID].PosLocA.xy = P[SourceID].PosLocB.xy + velocity * dt;
        P[SourceID].PosLocA.w = 0.0;
        P[SourceID].PosLocB.w = 1.0;
    }
}
