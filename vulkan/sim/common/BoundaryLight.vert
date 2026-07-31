void boundary_light_main()
{
	if (ShaderFlags.DrawInstance == 2.0)
	{
		vec3 worldPosition = inPosition.xyz;
		gl_Position = ubo.proj * ubo.view * ubo.model * vec4(worldPosition, 1.0);
		surfaceNormal = normalize(inNormalFlag.xyz);
		surfaceCellId = uint(inMeta.z + 0.5);
		surfaceWorldPos = worldPosition;
		renderSurfaceType = uint(inMeta.w + 0.5);
		renderSurfaceID = uint(inPosition.w + 0.5);
		fragColor = inLight;
		surfaceAlbedo = inAlbedo;
		return;
	}

	if (LIGHTING_BALL_ENABLED != 1u)
	{
		gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
		fragColor = vec4(0.0);
		surfaceNormal = vec3(0.0);
		surfaceCellId = 0u;
		surfaceWorldPos = vec3(0.0);
		renderSurfaceType = BOUNDARY_LIGHT_SURFACE_NONE;
		renderSurfaceID = 0u;
		surfaceAlbedo = vec4(1.0);
		return;
	}

	vec3 sphereNormal = normalize(inPosition.xyz);
	vec3 worldPosition = LIGHTING_BALL_CENTER + sphereNormal * LIGHTING_BALL_RADIUS;
	gl_Position = ubo.proj * ubo.view * ubo.model * vec4(worldPosition, 1.0);
	surfaceNormal = sphereNormal;
	surfaceCellId = uint(inMeta.z + 0.5);
	surfaceWorldPos = worldPosition;
	renderSurfaceType = BOUNDARY_LIGHT_SURFACE_SPHERE;
	renderSurfaceID = LIGHTING_BALL_WALL_FLAG;
	fragColor = vec4(0.0);
	surfaceAlbedo = vec4(1.0);
}
