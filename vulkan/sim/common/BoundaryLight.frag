vec4 boundary_light_sample_sphere(vec3 sphereNormal)
{
	if (surfaceCellId >= MAX_CELL_ARRAY_LOCATIONS)
	{
		return vec4(0.0);
	}

	BoundaryLightRecord record = BoundaryLight[surfaceCellId];
	if (record.rgb_valid.w < 0.5)
	{
		return vec4(0.0);
	}

	if (record.ids.y != 1u || record.ids.z != LIGHTING_BALL_WALL_FLAG)
	{
		return vec4(0.0);
	}

	return vec4(clamp(record.rgb_valid.rgb, vec3(0.0), vec3(1.0)), 1.0);
}

void boundary_light_main()
{
	vec4 surfaceColor = boundary_light_sample_sphere(normalize(surfaceNormal));
	if (surfaceColor.a <= 0.0)
	{
		discard;
	}

	outColor = surfaceColor;
}
