void boundary_light_main()
{
	if (LIGHTING_BALL_ENABLED != 1u)
	{
		gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
		fragColor = vec4(0.0);
		surfaceNormal = vec3(0.0);
		surfaceCellId = 0u;
		surfaceWorldPos = vec3(0.0);
		return;
	}

	vec3 sphereNormal = normalize(inPosition.xyz);
	vec3 worldPosition = LIGHTING_BALL_CENTER + sphereNormal * LIGHTING_BALL_RADIUS;
	gl_Position = ubo.proj * ubo.view * ubo.model * vec4(worldPosition, 1.0);
	surfaceNormal = sphereNormal;
	surfaceCellId = uint(inColor.w + 0.5);
	surfaceWorldPos = worldPosition;
	fragColor = vec4(1.0);
}
