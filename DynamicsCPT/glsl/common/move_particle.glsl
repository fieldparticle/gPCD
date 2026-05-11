const uint POSITION_BUFFER_A = 0u;
const uint POSITION_BUFFER_B = 1u;

void MoveParticle(uint SourceID, uint positionBuffer, float dt)
{

    vec2 velocity = P[SourceID].VelRad.xy;
    if (positionBuffer == POSITION_BUFFER_A) 
	{
        P[SourceID].PosLocB.xy = P[SourceID].PosLocA.xy + velocity * dt;
    } else 
	{
        P[SourceID].PosLocA.xy = P[SourceID].PosLocB.xy + velocity * dt;
    }
}
