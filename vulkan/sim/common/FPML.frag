void fpml_frag_main()
{
	uint index = gl_PrimitiveID;
	if (index == 0)
	{
		discard;
	}
	if (fragColor.a <= 0.0)
	{
		discard;
	}

	// Lighting-specific point-sprite shaping belongs here. The next pass can
	// use gl_PointCoord to turn boundary particles into soft surface patches.
	outColor = fragColor;
}
