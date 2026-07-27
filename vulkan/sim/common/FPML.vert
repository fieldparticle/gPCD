
bool IsBoundaryParticleForLighting(uint particleID)
{
	return int(round(P[particleID].ptype)) == 2;
}

vec3 BoundaryLightRecordPosition(BoundaryLightRecord record)
{
	uint particleID = record.ids.x;
	return ShaderFlags.positionBuffer == 0u
		? P[particleID].PosLocA.xyz
		: P[particleID].PosLocB.xyz;
}

float BoundaryLightWeight(BoundaryLightRecord source, BoundaryLightRecord other)
{
	if (source.ids.y != other.ids.y || source.ids.z != other.ids.z)
		return 0.0;

	float value = 0.0;
	if (source.ids.y == BOUNDARY_LIGHT_SURFACE_SPHERE)
	{
		vec3 sourceNormal = normalize(source.normal_material.xyz);
		vec3 otherNormal = normalize(other.normal_material.xyz);
		float angle = acos(clamp(dot(sourceNormal, otherNormal), -1.0, 1.0));
		value = 1.0 - angle / BOUNDARY_SPACE_PATCH_ANGLE;
	}
	else if (source.ids.y == BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL)
	{
		float distance = length(
			BoundaryLightRecordPosition(source) - BoundaryLightRecordPosition(other));
		value = 1.0 - distance / BOUNDARY_SPACE_PATCH_RADIUS;
	}

	if (value <= 0.0)
		return 0.0;
	if (BOUNDARY_SPACE_PATCH_FALLOFF_QUADRATIC == 1u)
		value *= value;
	return value;
}

vec4 BoundaryLightColor(uint particleID, vec4 fallbackColor)
{
	if (!IsBoundaryParticleForLighting(particleID)
			|| BOUNDARY_SPACE_PROXY_COUNT == 0u
			|| particleID < BOUNDARY_SPACE_FIRST_PARTICLE_ID)
		return fallbackColor;

	uint boundaryIndex = particleID - BOUNDARY_SPACE_FIRST_PARTICLE_ID;
	if (boundaryIndex >= BOUNDARY_SPACE_PROXY_COUNT)
		return fallbackColor;

	BoundaryLightRecord source = BoundaryLight[boundaryIndex];
	vec3 weightedRgb = vec3(0.0);
	float totalWeight = 0.0;
	for (uint ii = 0u; ii < BOUNDARY_SPACE_PROXY_COUNT; ++ii)
	{
		BoundaryLightRecord other = BoundaryLight[ii];
		if (other.rgb_valid.w < 0.5)
			continue;
		float weight = BoundaryLightWeight(source, other);
		if (weight <= 0.0)
			continue;
		weightedRgb += other.rgb_valid.rgb * weight;
		totalWeight += weight;
	}
	if (totalWeight <= 0.0)
		return vec4(0.0, 0.0, 0.0, 0.0);
	return vec4(clamp(weightedRgb, vec3(0.0), vec3(1.0)), 1.0);
}

void fpml_vert_main(){
	
	int index 		= gl_VertexIndex;
	
#if 0 && defined(DEBUG)
	if(uint(ShaderFlags.frameNum) == 0 && index == 0)
	{
		//debugPrintfEXT("Testing Indexing H:%d,W:%d,CMEM %d, ACTMEM %d",HEIGHT,WIDTH,HEIGHT*HEIGHT*HEIGHT,);
		P[index].parms.w = 0;
		uint ret = TestArrayToIndex(0,10);
		
		if (ret != 0)
		{
			debugPrintfEXT("Indexing Failed H:%d,W:%d at #:%d",HEIGHT,WIDTH,ret);
			P[0].colFlg = 1;
		}
		else
			debugPrintfEXT("Indexing passed H:%d,W:%d at #:%d",HEIGHT,WIDTH,ret);
	}
#endif

	if(index == 0)
	{
		collIn.numParticles = 0;
		return;
	}	

	
	
	// Set point size 
	gl_PointSize = point_size;
	if(uint(ShaderFlags.frameNum) == 0u)
	{
		gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
		gl_PointSize = 0.0;
		return;
	}
	
	// Clear this particle's corner array. Inactive particles must not leave
	// stale cell-locality state behind.
	for (uint kk = 0;kk<8;kk++)
		P[index].CornerList[kk].ploc = npos;

	if(!IsParticleActiveForLifecycle(uint(index)))
	{
		gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
		gl_PointSize = 0.0;
		fragColor = vec4(0.0, 0.0, 0.0, 0.0);
		return;
	}

	float cx=0.0;
	float cy=0.0;
	float cz=0.0;
	float R			= P[index].Data.x;
	
	if (ShaderFlags.positionBuffer == 0u) 
	{
		cx 		= P[index].PosLocA.x;
		cy 		= P[index].PosLocA.y;
		cz 		= P[index].PosLocA.z;
	} 
	else{
		cx 		= P[index].PosLocB.x;
		cy 		= P[index].PosLocB.y;
		cz 		= P[index].PosLocB.z;
	}

	// Render the particle from the same selected position buffer used to build
	// the corner list and drive compute collision detection. The vertex input
	// position is PosLocA; do not add the SSBO position a second time.
	gl_Position = ubo.proj * ubo.view * ubo.model * vec4(cx, cy, cz, 1.0);

	uint duplist[8];
	uint dupcntr = 0;
	uint CornerLocation = 0;
	uint count = 0;
	
	float min_x = cx - R;
	float min_y = cy - R;
	float min_z = cz - R;
	float max_x = cx + R;
	float max_y = cy + R;
	float max_z = cz + R;

	#if 0 && defined(DEBUG)
	if(uint(ShaderFlags.frameNum) == 366)
	{
		debugPrintfEXT("Boundary->P:%d,min:<%0.3f,%0.3f,%0.3f> max:<%0.3f,%0.3f,%0.3f>",
			index,min_x,min_y,min_z,max_x,max_y,max_z);
	}
	#endif
		
	if (min_x < 0 || min_y < 0 || min_z < 0
		|| max_x >= float(WIDTH) || max_y >= float(HEIGHT) || max_z >= float(DEPTH))
	{
		#if 1 && defined(DEBUG)
			debugPrintfEXT("F:%d,Boundary->P:=%d,min:<%0.3f,%0.3f,%0.3f> max:<%0.3f,%0.3f,%0.3f>",
				uint(ShaderFlags.frameNum),index,min_x,min_y,min_z,max_x,max_y,max_z);
		#endif
		collIn.ExcessSlots = 0;
		collIn.particleNumber = index;
		collIn.ErrorReturn = 4;
		collIn.maxCells = MAX_CELL_ARRAY_LOCATIONS;
		collIn.FrameNumber = uint(ShaderFlags.frameNum);
		return;
	}

	CornerLocation = ArrayToIndex(uvec3(uint(max_x), uint(max_y), uint(min_z)));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(max_x), uint(max_y), uint(max_z)));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(min_x), uint(max_y), uint(max_z)));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(min_x), uint(max_y), uint(min_z)));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(max_x), uint(min_y), uint(max_z)));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(max_x), uint(min_y), uint(min_z)));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(min_x), uint(min_y), uint(max_z)));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(min_x), uint(min_y), uint(min_z)));
	count += addUniqueCell(index, CornerLocation, count);
	
	
//#################################################################
//################### Populate the cell array with this particles corners
//#################################################################
	//Need this to get the number particles count correct (?!)
#ifdef DEBUG
	atomicAdd(collIn.numParticles,1);	
#endif

	// Traverse the particles corner array if there is not a global error 
	// which is stored in the 0th partcle parms emlent
	for( uint ii = 0; ii < 8 && P[index].CornerList[ii].ploc!=npos; ii++)
	{
		// Location index for this slot.
		uint sltidx = 0;
		// Resrved slot
		uint slot 	= 0;
		
		
		// Get the first non-duplicate corner.
		sltidx = P[index].CornerList[ii].ploc;
		
	
		// Cell index 0 is valid for cell location (0,0,0), so only invalid
		// corners are excluded by the npos sentinel.
		
		
		if(sltidx >= MAX_CELL_ARRAY_LOCATIONS)
		{
			#if 0 && defined(DEBUG)
				debugPrintfEXT("ParticleVerfPerf sltidx > MaxLocation:P=%d,sltidx=%d,MaxLocation=%d",index,sltidx,MAX_CELL_ARRAY_LOCATIONS);
			#endif	
			collIn.ExcessSlots = sltidx;
			collIn.particleNumber = index;
			collIn.ErrorReturn = 3;
			collIn.maxCells = MAX_CELL_ARRAY_LOCATIONS;
			collIn.FrameNumber = uint(ShaderFlags.frameNum);
			P[index].parms.w = 1.0;
			P[0].colFlg = 1;
			break;
		}
		
		// Reserve a slot for this location in the cell array occupancy list
		// atomic add increments the value in the lock array and returns the 
		// *previous value*.
		slot = atomicAdd(L[sltidx],1);
		#if 0 && defined(DEBUG)
			if((uint(ShaderFlags.frameNum) == 55 || uint(ShaderFlags.frameNum) == 56) && ii <3)
				debugPrintfEXT("F:%d,P:%d,Slot:%d, Corner Loc:%d, loc<%f,%f,%f> R:%f",uint(ShaderFlags.frameNum),index,slot,sltidx,cx,cy,cz,R);
		#endif	
		// If the array at this index of the particle-cell hash 
		// does not have enough slots to handle the particle density
		// then report it.
		if(slot >= MAX_CELL_OCCUPANY)
		{
			uvec3 badloc;
			#if 0 && defined(DEBUG)
				//IndexToArray(sltidx,badloc);
				debugPrintfEXT("ParticleVerfPerf slot>F:%u,P:%d,MAX_CELL_OCCUPANY:%d,at loc: %d",
				uint(ShaderFlags.frameNum),index,MAX_CELL_OCCUPANY,slot);
			#endif
			collIn.ExcessSlots = slot;
			collIn.ErrorReturn = 2;
			P[0].colFlg = 1;
			P[index].parms.w = 2.0;
			collIn.FrameNumber = uint(ShaderFlags.frameNum);
			break;
		}
		

		// Insert the location of this particle in the particle-cell 
		// hash table.
		
		#if 0 && defined(DEBUG)
			if(index == 3 && uint(ShaderFlags.frameNum) == 100)
			{
				debugPrintfEXT("VerfPerf particle %d added to cell %d slot %d.",index,sltidx,slot);
			}
		#endif	
		
	#if 0 && defined(DEBUG)
		if(uint(ShaderFlags.frameNum) == 8 && index == 1)
		{
			debugPrintfEXT("P:%u,CNRIDX:%u,CNRL:%u,LOC:%u,SLT:%u ",index,ii,P[index].CornerList[ii].ploc, sltidx,slot);
		}
	#endif

		// If everythin is valid add this particles corner to the 
		// cell array at the indoctaed location and slot in the cell occupancy array
		// NOTE: particle 0 is a dummy particle so that the particle 0-based index matches
		// the particle number
		clink[sltidx].idx[slot] = index;
	
	#if 0 && defined(DEBUG)
		if(uint(ShaderFlags.frameNum) == 8 && index == 1)
		{
			debugPrintfEXT("P:%u,CNRIDX:%u,CELLARYVAL:%u ",index,ii,clink[sltidx].idx[slot]);
		}
	#endif
		
	}
	vec4 mappedColor = color_map(uint(index));
	if (IsBoundaryParticleForLighting(uint(index)))
	{
		uint materialID = uint(round(P[index].material_id));
		if (material_debug_visible(materialID) != 1u)
		{
			gl_PointSize = 0.0;
			fragColor = vec4(0.0);
			return;
		}
		fragColor = material_debug_color(materialID);
		return;
	}
	fragColor = mappedColor;
	
	
}
