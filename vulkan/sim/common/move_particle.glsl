const uint POSITION_BUFFER_A = 0u;
const uint POSITION_BUFFER_B = 1u;

void MoveParticle(uint SourceID, uint positionBuffer, float dt)
{

    vec2 velocity = P[SourceID].VelRad.xy;
    if (positionBuffer == 1u) 
	{
        P[SourceID].PosLocA.xy = P[SourceID].PosLocA.xy + velocity * dt;
    } else 
	{
        P[SourceID].PosLocB.xy = P[SourceID].PosLocB.xy + velocity * dt;
    }
}
