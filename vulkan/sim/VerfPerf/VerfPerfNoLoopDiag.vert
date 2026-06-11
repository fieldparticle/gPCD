#version 460
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#if defined(DEBUG)
	#extension GL_EXT_debug_printf : enable
#endif
#extension GL_EXT_scalar_block_layout :enable
#extension GL_ARB_gpu_shader_int64 : enable

void MaxCellOccupancyError(uint CellOccupancySlot,uint ParticleID, uint CornerIndex);
void MaxCellLocationsError(uint CellArrayIndex, uint ParticleID);
uint AddSlot(uint CornerIndex, uint ParticleID);
void ZeroLocation(uint CornerIndex,uint ParticleID);
#include "params.glsl"
#include "debug.glsl"
#include "../common/constants.glsl"
#include "../common/util.glsl"
#include "../common/push.glsl"
#include "../common/atomicg.glsl"
#include "../common/CollimageIndex.glsl"
#include "../common/Lockimage.glsl"
#include "../common/particle.glsl"



out gl_PerVertex {
    vec4 gl_Position;
	float gl_PointSize;
};
layout(binding = 2) uniform UniformBufferObject{
    mat4 model;
    mat4 view;
    mat4 proj;
} ubo;

// From vertex assembler position of 
// this particle (vertex)
layout(location = 0) in vec4 inPosition;
// Current velocity of this particle.
layout(location = 1) in vec4 incurvel;
// Color of this particle
layout(location = 2) in vec4 inColor;
// Radius and type of this particle.
layout(location = 3) in vec2 inParms;

// Output to fragment shader.
layout(location = 0) out vec3 fragColor;
layout(location = 1) out vec2 outParms;
layout(location = 2) out vec3 matpos;


///
// Use this one with 000_ParticleVerfPerfCountOnly.comp to
// see the effect of finding the particle AABB corners and eliminating duplicates.
//
////
void main(){
	
	int index 		= gl_VertexIndex;
#if 0 && defined(DEBUG)
	if(uint(ShaderFlags.frameNum) == 0 && index == 0)
	{
		//debugPrintfEXT("Testing Indexing H:%d,W:%d,CMEM %d, ACTMEM %d",HEIGHT,WIDTH,HEIGHT*HEIGHT*HEIGHT);
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
#ifdef DEBUG
	atomicAdd(collIn.numParticles,1);	
#endif

	if(index == 0)
		return;
	// Set point size 
	gl_PointSize = 1.0;
	
	// Apply view to location
	//gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPosition.xyz, 1.0);
	gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPosition.xyz, 1.0);
	
	float cx 		= P[index].PosLocA.x;
	float cy 		= P[index].PosLocA.y;
	float cz 		= P[index].PosLocA.z;
	float R			= P[index].Data.x;
	
	#if 1
	if(cx < 0.5 || cy < 0.5 || cz < 0.5)
		debugPrintfEXT("Invalid Particle slot>F:%u,P:%d,loc:<%0.2f,%0.2f,%0.2f>",
		uint(ShaderFlags.frameNum),index,P[index].PosLocA.x,P[index].PosLocA.y,P[index].PosLocA.z);
	#endif	
	
	uint duplist[8];
	uint dupcntr = 0;
	uint cnr_index = 0;
	
	#if 0
	P[index].CornerList[0].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz-R))));
	P[index].CornerList[1].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz+R))));
	P[index].CornerList[2].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz+R))));
	P[index].CornerList[3].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz-R))));
	P[index].CornerList[4].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz+R))));
	P[index].CornerList[5].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz-R))));
	P[index].CornerList[6].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz+R))));
	P[index].CornerList[7].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz-R))));
	#endif
	
		
	
	// Clear this paricles corner array
	for (uint kk = 0;kk<8;kk++)
		P[index].CornerList[kk].ploc = 0;
	
	uint cellOccupancySlot = 0;
	uint err = 0;
	//######################################### ADD SLOTS START ##############################
	
	// First corner always written since there is no possibility of duplicate
	// Get the index location in the cell array the first particle corner
	
	//-----------------------------------------------------------------------------------
	// Slot 1 ---------------------------------------
	cnr_index = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz-R))));
	duplist[0] = cnr_index;
	P[index].CornerList[0].ploc = cnr_index;
	err = AddSlot(cnr_index, index);
	
	
	// Slot 2 ---------------------------------------
	cnr_index = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz+R))));
	if (cnr_index != P[index].CornerList[0].ploc)
	{
		dupcntr++;
		P[index].CornerList[dupcntr].ploc = cnr_index;
		err = AddSlot(cnr_index, index);
		
	}
	
	// Slot 3 ---------------------------------------
	cnr_index = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz+R))));
	if (cnr_index != P[index].CornerList[0].ploc && 
		cnr_index != P[index].CornerList[1].ploc)
	{
		dupcntr++;
		P[index].CornerList[dupcntr].ploc = cnr_index;
		err = AddSlot(cnr_index, index);
		
	}
		
	// Slot 4 ---------------------------------------
	cnr_index = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz-R))));
	if (cnr_index != P[index].CornerList[0].ploc && 
		cnr_index != P[index].CornerList[1].ploc &&
		cnr_index != P[index].CornerList[2].ploc)
	{
		dupcntr++;
		P[index].CornerList[dupcntr].ploc = cnr_index;
		err = AddSlot(cnr_index, index);
		
	}
		
	// Slot 5 ---------------------------------------
	cnr_index = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz+R))));
	if (cnr_index != P[index].CornerList[0].ploc && 
		cnr_index != P[index].CornerList[1].ploc &&
		cnr_index != P[index].CornerList[2].ploc &&
		cnr_index != P[index].CornerList[3].ploc)
	{
		dupcntr++;
		P[index].CornerList[dupcntr].ploc = cnr_index;
		err = AddSlot(cnr_index, index);
		
	}
	
	// Slot 6 ---------------------------------------
	cnr_index = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz-R))));
	if (cnr_index != P[index].CornerList[0].ploc && 
		cnr_index != P[index].CornerList[1].ploc &&
		cnr_index != P[index].CornerList[2].ploc &&
		cnr_index != P[index].CornerList[3].ploc &&
		cnr_index != P[index].CornerList[4].ploc)
	{
		dupcntr++;
		P[index].CornerList[dupcntr].ploc = cnr_index;
		err = AddSlot(cnr_index, index);
		
	}
		
	// Slot 7 ---------------------------------------
	cnr_index = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz+R))));
	if (cnr_index != P[index].CornerList[0].ploc && 
		cnr_index != P[index].CornerList[1].ploc &&
		cnr_index != P[index].CornerList[2].ploc &&
		cnr_index != P[index].CornerList[3].ploc &&
		cnr_index != P[index].CornerList[4].ploc &&
		cnr_index != P[index].CornerList[5].ploc)
	{
		dupcntr++;
		P[index].CornerList[dupcntr].ploc = cnr_index;
		err = AddSlot(cnr_index, index);
		
		
	}
		
	// Slot 8 ---------------------------------------
	cnr_index = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz-R))));
	if (cnr_index != P[index].CornerList[0].ploc && 
		cnr_index != P[index].CornerList[1].ploc &&
		cnr_index != P[index].CornerList[2].ploc &&
		cnr_index != P[index].CornerList[3].ploc &&
		cnr_index != P[index].CornerList[4].ploc &&
		cnr_index != P[index].CornerList[5].ploc&&
		cnr_index != P[index].CornerList[6].ploc)
	{
		dupcntr++;
		P[index].CornerList[dupcntr].ploc = cnr_index;
		err = AddSlot(cnr_index, index);
		
	}
//######################################### ADD SLOTS END##############################	
	
	#if 1 && defined(DEBUG)
		if(index == 3 && uint(ShaderFlags.frameNum) == 100)
		{
			debugPrintfEXT("p:%d,H:%d,W:%d[%d,%d,%d,%d,%d,%d,%d,%d]",index,WIDTH,HEIGHT,
				P[index].CornerList[0].ploc,
				P[index].CornerList[1].ploc,
				P[index].CornerList[2].ploc,
				P[index].CornerList[3].ploc,
				P[index].CornerList[4].ploc,
				P[index].CornerList[5].ploc,
				P[index].CornerList[6].ploc,
				P[index].CornerList[7].ploc);
		}
	#endif
//Need this to get the number particles count correct

	if(uint(P[index].colFlg) == 1)
		fragColor = vec3(1.0,0.0,0.0);	
	else 
		fragColor = vec3(0.0,1.0,0.0);	
}
	
uint AddSlot(uint CornerIndex, uint ParticleID)
{
	if (CornerIndex == 0)
	{
		ZeroLocation(CornerIndex,ParticleID);
		return 1;
	}
	if(CornerIndex >= MAX_CELL_ARRAY_LOCATIONS)
	{
		MaxCellLocationsError(CornerIndex,ParticleID);
		return 1;
	}
	
	uint cellOccupancySlot = atomicAdd(L[CornerIndex],1);
	
	if(cellOccupancySlot >= MAX_CELL_OCCUPANY)
	{
		MaxCellOccupancyError(cellOccupancySlot,ParticleID,CornerIndex);
		return 1;
	}
	
	clink[CornerIndex].idx[cellOccupancySlot] = ParticleID;
	return 0;


}
// Location requested was outside avaiable cells
void MaxCellLocationsError(uint CellArrayIndex, uint ParticleID )
{
	#if 1
	#if 1 && defined(DEBUG)
		debugPrintfEXT("ParticleVerfPerf sltidx > MaxLocation:P=%d,sltidx=%d,MaxLocation=%d",ParticleID,CellArrayIndex,MAX_CELL_ARRAY_LOCATIONS);
	#endif
	
	collIn.ExcessSlots = CellArrayIndex;
	collIn.ErrorReturn = 3;
	collIn.particleNumber = ParticleID;
	collIn.maxCells = MAX_CELL_ARRAY_LOCATIONS;
	P[ParticleID].parms.w = 1.0;
	P[0].colFlg = 1;
	#endif

}
void ZeroLocation(uint CornerIndex,uint ParticleID)
{

	// If the array at this index of the particle-cell hash 
	// does not have enough slots to handle the particle density
	// then report it.
	#if 1 && defined(DEBUG)
		debugPrintfEXT("ParticleVerfPerf zero location>F:%u,P:%d at loc: %d loc<%0.2f,%0.2f,%0.2f>",
		uint(ShaderFlags.frameNum),ParticleID,CornerIndex,P[ParticleID].PosLocA.x,P[ParticleID].PosLocA.y,P[ParticleID].PosLocA.z);
		
	#endif
	collIn.maxCells = MAX_CELL_OCCUPANY;
	collIn.particleNumber = ParticleID;
	collIn.ExcessSlots = CornerIndex;
	atomicAdd(collIn.ErrorReturn,3);



}

void MaxCellOccupancyError(uint CellOccupancySlot,uint ParticleID,uint CornerIndex)
{
	// If the array at this index of the particle-cell hash 
	// does not have enough slots to handle the particle density
	// then report it.
	#if 1 && defined(DEBUG)
		debugPrintfEXT("ParticleVerfPerf slot>F:%u,P:%d,MAX_CELL_OCCUPANY:%d,Occupancy index:%d and cornerid: (%d) loc<%0.2f,%0.2f,%0.2f>",
		uint(ShaderFlags.frameNum),ParticleID,MAX_CELL_OCCUPANY,CellOccupancySlot,CornerIndex,P[ParticleID].PosLocA.x,P[ParticleID].PosLocA.y,P[ParticleID].PosLocA.z);
		
	#endif
	collIn.maxCells = MAX_CELL_OCCUPANY;
	collIn.particleNumber = ParticleID;
	collIn.ExcessSlots = CellOccupancySlot;
	atomicAdd(collIn.ErrorReturn,2);
	

}
		