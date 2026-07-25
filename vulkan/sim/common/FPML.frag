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

	if (abs(P[index].ptype - PTYPE_BOUNDARY) >= 0.5)
	{
		outColor = fragColor;
		return;
	}

	vec2 point = gl_PointCoord * 2.0 - 1.0;
	float r2 = dot(point, point);
	if (r2 > 1.0)
	{
		discard;
	}

	float alpha = fragColor.a * smoothstep(1.0, 0.85, r2);
	if (alpha <= 0.0)
	{
		discard;
	}

	outColor = vec4(fragColor.rgb, alpha);
}
