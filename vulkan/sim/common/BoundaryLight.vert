vec4 boundary_light_render_decal_albedo(
	uint surfaceType,
	uint surfaceID,
	uint vertexID,
	vec4 fallbackAlbedo)
{
	if (surfaceType != BOUNDARY_LIGHT_SURFACE_SPHERE ||
		surfaceID != LIGHTING_SPHERE_DECAL_MAP_SURFACE_ID)
	{
		return fallbackAlbedo;
	}

	for (uint objectIndex = 0u; objectIndex < LIGHTING_SURFACE_OBJECT_COUNT; ++objectIndex)
	{
		LightingSurfaceObjectMetadata surfaceObject =
			LIGHTING_SURFACE_OBJECTS[objectIndex];
		if (surfaceObject.surfaceType != surfaceType ||
			surfaceObject.surfaceID != surfaceID ||
			surfaceObject.sphereLonSegments == 0u ||
			vertexID < surfaceObject.vertexOffset ||
			vertexID >= surfaceObject.vertexOffset + surfaceObject.vertexCount)
		{
			continue;
		}

		uint localVertexID = vertexID - surfaceObject.vertexOffset;
		uint ring = localVertexID / surfaceObject.sphereLonSegments;
		uint segment = localVertexID % surfaceObject.sphereLonSegments;
		for (uint cellIndex = 0u; cellIndex < LIGHTING_SPHERE_DECAL_MAP_COUNT; ++cellIndex)
		{
			uvec4 cell = LIGHTING_SPHERE_DECAL_MAP_CELLS[cellIndex];
			if (cell.x == ring && cell.y == segment)
			{
				vec4 decalAlbedo = LIGHTING_SPHERE_DECAL_MAP_ALBEDOS[cellIndex];
				if (decalAlbedo.a > 0.0)
				{
					return decalAlbedo;
				}
			}
		}
	}

	return fallbackAlbedo;
}

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
		surfaceAlbedo = boundary_light_render_decal_albedo(
			renderSurfaceType,
			renderSurfaceID,
			surfaceCellId,
			inAlbedo);
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
