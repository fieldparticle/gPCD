void boundary_vert_main()
{
	uint ModelInstance = gl_InstanceIndex + 1u;

	if (ShaderFlags.DrawInstance == 1.0)
	{
#if defined(HAS_BOUNDARY)
		gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPosition.xyz, 1.0);
		fragColor = inColor;
#else
		gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
		fragColor = vec4(0.0);
#endif
		return;
	}

#if defined(HAS_SPHERE)
	if (P[ModelInstance].ptype > 0.5)
	{
		gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
		fragColor = vec4(0.0);
		return;
	}

	vec3 sphereOffset = inPosition.xyz * P[ModelInstance].Data.x;
	vec4 newPos = vec4(sphereOffset + P[ModelInstance].PosLocA.xyz, 1.0);
	gl_Position = ubo.proj * ubo.view * ubo.model * newPos;
	fragColor = color_map(ModelInstance);
#else
	gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
	fragColor = vec4(0.0);
#endif
}
