uint boundary_light_cell_coord(float value, uint maxValue)
{
	if (maxValue == 0u)
	{
		return 0u;
	}
	if (value <= 0.0)
	{
		return 0u;
	}
	uint lastValue = maxValue - 1u;
	if (value >= float(lastValue))
	{
		return lastValue;
	}
	return uint(floor(value));
}

uint boundary_light_cell_address(vec3 worldPosition)
{
	uint cellID = ArrayToIndex(uvec3(
		boundary_light_cell_coord(worldPosition.x, WIDTH),
		boundary_light_cell_coord(worldPosition.y, HEIGHT),
		boundary_light_cell_coord(worldPosition.z, DEPTH)));
	return cellID;
}

bool boundary_light_record_matches_surface(
	BoundaryLightRecord record,
	uint surfaceType,
	uint surfaceID)
{
	return record.ids.y == surfaceType && record.ids.z == surfaceID;
}

vec4 boundary_light_sample_weighted_cell(
	uvec3 cell,
	uint surfaceType,
	uint surfaceID,
	float weight)
{
	if (weight <= 0.0)
	{
		return vec4(0.0);
	}

	uint cellID = ArrayToIndex(cell);
	if (cellID == npos || cellID >= MAX_CELL_ARRAY_LOCATIONS)
	{
		return vec4(0.0);
	}

	BoundaryLightRecord record = BoundaryLight[cellID];
	if (record.rgb_valid.w < 0.5)
	{
		return vec4(0.0);
	}

	if (!boundary_light_record_matches_surface(record, surfaceType, surfaceID))
	{
		return vec4(0.0);
	}

	return vec4(clamp(record.rgb_valid.rgb, vec3(0.0), vec3(1.0)) * weight, weight);
}

vec4 boundary_light_sample_cell(
	uvec3 cell,
	vec3 worldPosition,
	uint surfaceType,
	uint surfaceID)
{
	vec3 cellCenter = vec3(cell) + vec3(0.5);
	float distanceToCenter = length(worldPosition - cellCenter);
	float weight = max(0.0, 1.0 - distanceToCenter);

	return boundary_light_sample_weighted_cell(
		cell,
		surfaceType,
		surfaceID,
		weight);
}

uint boundary_light_axis_limit(uint axis)
{
	if (axis == 0u)
	{
		return WIDTH;
	}
	if (axis == 1u)
	{
		return HEIGHT;
	}
	return DEPTH;
}

uint boundary_light_dominant_normal_axis(vec3 normal)
{
	vec3 axisWeight = abs(normalize(normal));
	if (axisWeight.x >= axisWeight.y && axisWeight.x >= axisWeight.z)
	{
		return 0u;
	}
	if (axisWeight.y >= axisWeight.z)
	{
		return 1u;
	}
	return 2u;
}

float boundary_light_box_axis_weight(float position, uint cellCoord)
{
	float center = float(cellCoord) + 0.5;
	return max(0.0, 1.0 - abs(position - center));
}

void boundary_light_accumulate_planar_wall_cell(
	inout vec3 weightedRgb,
	inout float totalWeight,
	uvec3 baseCell,
	uint planeAxis,
	uint axisU,
	uint axisV,
	int offsetU,
	int offsetV,
	uint surfaceID)
{
	ivec3 sampleCellSigned = ivec3(baseCell);
	sampleCellSigned[int(axisU)] += offsetU;
	sampleCellSigned[int(axisV)] += offsetV;

	if (sampleCellSigned.x < 0 ||
		sampleCellSigned.y < 0 ||
		sampleCellSigned.z < 0)
	{
		return;
	}

	uvec3 sampleCell = uvec3(sampleCellSigned);
	if (sampleCell[int(axisU)] >= boundary_light_axis_limit(axisU) ||
		sampleCell[int(axisV)] >= boundary_light_axis_limit(axisV) ||
		sampleCell[int(planeAxis)] >= boundary_light_axis_limit(planeAxis))
	{
		return;
	}

	float weight =
		boundary_light_box_axis_weight(
			surfaceWorldPos[int(axisU)],
			sampleCell[int(axisU)]) *
		boundary_light_box_axis_weight(
			surfaceWorldPos[int(axisV)],
			sampleCell[int(axisV)]);

	vec4 sampleValue = boundary_light_sample_weighted_cell(
		sampleCell,
		BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL,
		surfaceID,
		weight);
	weightedRgb += sampleValue.rgb;
	totalWeight += sampleValue.w;
}

vec4 boundary_light_sample_rectangle_wall_surface(uint surfaceID)
{
	uvec3 baseCell = uvec3(
		boundary_light_cell_coord(surfaceWorldPos.x, WIDTH),
		boundary_light_cell_coord(surfaceWorldPos.y, HEIGHT),
		boundary_light_cell_coord(surfaceWorldPos.z, DEPTH));

	uint planeAxis = boundary_light_dominant_normal_axis(surfaceNormal);
	uint axisU = planeAxis == 0u ? 1u : 0u;
	uint axisV = planeAxis == 2u ? 1u : 2u;

	vec3 weightedRgb = vec3(0.0);
	float totalWeight = 0.0;

	for (int offsetU = -1; offsetU <= 1; ++offsetU)
	{
		for (int offsetV = -1; offsetV <= 1; ++offsetV)
		{
			boundary_light_accumulate_planar_wall_cell(
				weightedRgb,
				totalWeight,
				baseCell,
				planeAxis,
				axisU,
				axisV,
				offsetU,
				offsetV,
				surfaceID);
		}
	}

	if (totalWeight <= 0.0)
	{
		return vec4(0.0);
	}

	return vec4(weightedRgb / totalWeight, 1.0);
}

vec4 boundary_light_sample_reflecting_wall_light_map(uint surfaceID)
{
#if defined(REFLECTING_WALL_LIGHT_MAP_DEFINED)
	if (REFLECTING_WALL_LIGHT_MAP_ENABLED == 0u ||
		surfaceID != REFLECTING_WALL_LIGHT_MAP_SURFACE_ID ||
		REFLECTING_WALL_LIGHT_MAP_WIDTH == 0u ||
		REFLECTING_WALL_LIGHT_MAP_HEIGHT == 0u)
	{
		return vec4(0.0);
	}

	return vec4(0.0);

	vec2 uv = clamp(surfaceUV, vec2(0.0), vec2(1.0));
	uint x = min(
		uint(floor(uv.x * float(REFLECTING_WALL_LIGHT_MAP_WIDTH))),
		REFLECTING_WALL_LIGHT_MAP_WIDTH - 1u);
	uint y = min(
		uint(floor(uv.y * float(REFLECTING_WALL_LIGHT_MAP_HEIGHT))),
		REFLECTING_WALL_LIGHT_MAP_HEIGHT - 1u);
	uint index = y * REFLECTING_WALL_LIGHT_MAP_WIDTH + x;
	if (index >= REFLECTING_WALL_LIGHT_MAP_COUNT)
	{
		return vec4(0.0);
	}

	vec4 light = ReflectingWallLightMap[index].light;
	if (light.w <= 0.0)
	{
		return vec4(0.0);
	}

	return vec4(clamp(light.rgb, vec3(0.0), vec3(1.0)), 1.0);
#else
	return vec4(0.0);
#endif
}

vec4 boundary_light_sample_surface(uint surfaceType, uint surfaceID)
{
	if (surfaceType == BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL)
	{
		return boundary_light_sample_rectangle_wall_surface(surfaceID);
	}

	uvec3 baseCell = uvec3(
		boundary_light_cell_coord(surfaceWorldPos.x, WIDTH),
		boundary_light_cell_coord(surfaceWorldPos.y, HEIGHT),
		boundary_light_cell_coord(surfaceWorldPos.z, DEPTH));

	vec3 weightedRgb = vec3(0.0);
	float totalWeight = 0.0;

	vec4 sampleValue = boundary_light_sample_cell(
		baseCell,
		surfaceWorldPos,
		surfaceType,
		surfaceID);
	weightedRgb += sampleValue.rgb;
	totalWeight += sampleValue.w;

	if (baseCell.x + 1u < WIDTH)
	{
		sampleValue = boundary_light_sample_cell(
			baseCell + uvec3(1u, 0u, 0u),
			surfaceWorldPos,
			surfaceType,
			surfaceID);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}
	if (baseCell.x > 0u)
	{
		sampleValue = boundary_light_sample_cell(
			baseCell - uvec3(1u, 0u, 0u),
			surfaceWorldPos,
			surfaceType,
			surfaceID);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}
	if (baseCell.y + 1u < HEIGHT)
	{
		sampleValue = boundary_light_sample_cell(
			baseCell + uvec3(0u, 1u, 0u),
			surfaceWorldPos,
			surfaceType,
			surfaceID);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}
	if (baseCell.y > 0u)
	{
		sampleValue = boundary_light_sample_cell(
			baseCell - uvec3(0u, 1u, 0u),
			surfaceWorldPos,
			surfaceType,
			surfaceID);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}
	if (baseCell.z + 1u < DEPTH)
	{
		sampleValue = boundary_light_sample_cell(
			baseCell + uvec3(0u, 0u, 1u),
			surfaceWorldPos,
			surfaceType,
			surfaceID);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}
	if (baseCell.z > 0u)
	{
		sampleValue = boundary_light_sample_cell(
			baseCell - uvec3(0u, 0u, 1u),
			surfaceWorldPos,
			surfaceType,
			surfaceID);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}

	if (totalWeight <= 0.0)
	{
		return vec4(0.0);
	}

	return vec4(weightedRgb / totalWeight, 1.0);
}

vec4 boundary_light_sample_sphere(vec3 sphereNormal)
{
	return boundary_light_sample_surface(
		BOUNDARY_LIGHT_SURFACE_SPHERE,
		LIGHTING_BALL_WALL_FLAG);
}

vec4 boundary_light_sample_rectangle_wall(uint wallFlag)
{
	return boundary_light_sample_surface(
		BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL,
		wallFlag);
}

void boundary_light_main()
{
	if (renderSurfaceType == BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL)
	{
		vec4 lightMapColor =
			boundary_light_sample_reflecting_wall_light_map(renderSurfaceID);
		if (lightMapColor.a > 0.0)
		{
			outColor = lightMapColor;
			return;
		}

#if defined(REFLECTING_WALL_LIGHT_MAP_DEFINED)
		if (REFLECTING_WALL_LIGHT_MAP_ENABLED != 0u &&
			renderSurfaceID == REFLECTING_WALL_LIGHT_MAP_SURFACE_ID)
		{
			discard;
		}
#endif

		outColor = vec4(fragColor.rgb * surfaceAlbedo.rgb, fragColor.a);
		if (outColor.a <= 0.0)
		{
			discard;
		}
		return;
	}

	if (renderSurfaceType == BOUNDARY_LIGHT_SURFACE_SPHERE)
	{
		outColor = vec4(fragColor.rgb * surfaceAlbedo.rgb, fragColor.a);
		if (outColor.a <= 0.0)
		{
			discard;
		}
		return;
	}

	vec4 surfaceColor = boundary_light_sample_surface(
		renderSurfaceType,
		renderSurfaceID);
	if (surfaceColor.a <= 0.0)
	{
		discard;
	}

	outColor = surfaceColor;
}
