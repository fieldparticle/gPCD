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

vec4 boundary_light_sample_cell(uvec3 cell, vec3 worldPosition)
{
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

	if (record.ids.y != 1u || record.ids.z != LIGHTING_BALL_WALL_FLAG)
	{
		return vec4(0.0);
	}

	vec3 cellCenter = vec3(cell) + vec3(0.5);
	float distanceToCenter = length(worldPosition - cellCenter);
	float weight = max(0.0, 1.0 - distanceToCenter);
	if (weight <= 0.0)
	{
		return vec4(0.0);
	}

	return vec4(clamp(record.rgb_valid.rgb, vec3(0.0), vec3(1.0)) * weight, weight);
}

vec4 boundary_light_sample_sphere(vec3 sphereNormal)
{
	uvec3 baseCell = uvec3(
		boundary_light_cell_coord(surfaceWorldPos.x, WIDTH),
		boundary_light_cell_coord(surfaceWorldPos.y, HEIGHT),
		boundary_light_cell_coord(surfaceWorldPos.z, DEPTH));

	vec3 weightedRgb = vec3(0.0);
	float totalWeight = 0.0;

	vec4 sampleValue = boundary_light_sample_cell(baseCell, surfaceWorldPos);
	weightedRgb += sampleValue.rgb;
	totalWeight += sampleValue.w;

	if (baseCell.x + 1u < WIDTH)
	{
		sampleValue = boundary_light_sample_cell(baseCell + uvec3(1u, 0u, 0u), surfaceWorldPos);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}
	if (baseCell.x > 0u)
	{
		sampleValue = boundary_light_sample_cell(baseCell - uvec3(1u, 0u, 0u), surfaceWorldPos);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}
	if (baseCell.y + 1u < HEIGHT)
	{
		sampleValue = boundary_light_sample_cell(baseCell + uvec3(0u, 1u, 0u), surfaceWorldPos);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}
	if (baseCell.y > 0u)
	{
		sampleValue = boundary_light_sample_cell(baseCell - uvec3(0u, 1u, 0u), surfaceWorldPos);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}
	if (baseCell.z + 1u < DEPTH)
	{
		sampleValue = boundary_light_sample_cell(baseCell + uvec3(0u, 0u, 1u), surfaceWorldPos);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}
	if (baseCell.z > 0u)
	{
		sampleValue = boundary_light_sample_cell(baseCell - uvec3(0u, 0u, 1u), surfaceWorldPos);
		weightedRgb += sampleValue.rgb;
		totalWeight += sampleValue.w;
	}

	if (totalWeight <= 0.0)
	{
		return vec4(0.0);
	}

	return vec4(weightedRgb / totalWeight, 1.0);
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
