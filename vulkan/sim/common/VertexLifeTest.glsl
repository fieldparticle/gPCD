bool ParticleLifeActive(uint SourceID,uint FrameNum)
{
    float state_flag = P[SourceID].Data.w;

    if (state_flag < 0.0)
        return false;

    if (state_flag > float(FrameNum))
        return false;

    return true;
}
