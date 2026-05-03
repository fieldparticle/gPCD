#version 460
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#extension GL_EXT_debug_printf : enable
#extension GL_EXT_scalar_block_layout :enable
#extension GL_KHR_shader_subgroup_basic:enable
#include "../params.glsl"
#include "../common/constants.glsl"
#include "../common/atomicg.glsl"
#include "../common/push.glsl"
#include "../common/CollimageIndex.glsl"
#include "../common/Lockimage.glsl"
#include "../common/particle.glsl"
#include "../common/util.glsl"
#include "../common/ChangePos.glsl"
#include "../common/CheckFragDups.glsl"


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

out gl_PerVertex
{
	float gl_PointSize ;
	vec4 gl_Position;
	
};


// Output to fragment shader.
layout(location = 0) out vec3 fragColor;
layout(location = 1) out vec4 outpos;

void main(){
	
	 
	int index 		= gl_VertexIndex;
	if(index == 0)
	{
		collIn.numParticles = 0;
		return;
	}	
	
	#ifdef DEBUG
		atomicAdd(collIn.numParticles,1);	
	#endif
	// Set point size 
	gl_PointSize = 3.0;
	
	// Apply view to location
	vec3 posLocNDC =  P[index].PosLoc.xyz;
  	gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPosition.xyz, 1.0);
	outpos = ubo.proj * ubo.view * ubo.model * vec4(inPosition.xyz, 1.0);
	
	#if 0 && defined(DEBUG)
	if(index == 6000 && ShaderFlags.actualFrame == 500.0  )
		debugPrintfEXT("GRAPHPART velocity:%d vx=%0.3f,vy=%0.3f,vz=%0.3f,",
		0,P[index].VelRad.x,P[index].VelRad.y,P[index].VelRad.z);
	#endif	
	
	#if !defined(VERPONLY)
	// If the particle is not live return.		
	if(uint(P[index].parms.x) > uint(ShaderFlags.actualFrame))
		return;	
		
	if(uint(P[index].prvvel.w) == 1)
		return;
	
	#endif	
	//clear zlink
	for(uint jj=0;jj<MAX_OCCUPANCY;jj++)
	{
		P[index].zlink[jj].ploc = 0;
		P[index].zlink[jj].pindex =0;
		//P[index].wary[jj].x = 0.0;
	}
	if(index > bbound)
	{
		#ifdef VERPIPE
			ChangePosPipe(index);	
		#endif
		#if  !defined(VERPIPE) && !defined(VERCDNOZ)
			ChangePos(index);	
		#endif
		#ifdef VERCDNOZ
			if(ChangePosCDNoz(index) != 0)
				return;
		#endif
	}
		
	
	uint Loc[8];
	float cx 		= P[index].PosLoc.x;
	float cy 		= P[index].PosLoc.y;
	float cz 		= P[index].PosLoc.z;
	float R			= P[index].PosLoc.w;
	
	P[index].zlink[0].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz-R))));
	if(P[index].zlink[0].ploc == npos)
	{
		collIn.ExcessSlots = P[index].zlink[0].ploc;
		collIn.ErrorReturn = 2;
	}
	
	if(CheckFragDups(index,P[index].zlink[1].ploc,1))
		P[index].zlink[1].ploc = 0;	
	
												//++-
	P[index].zlink[1].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz+R))));
	if(P[index].zlink[1].ploc == npos)
	{
		collIn.ExcessSlots = P[index].zlink[0].ploc;
		collIn.ErrorReturn = 2;
	}
	
	if(CheckFragDups(index,P[index].zlink[1].ploc,1))
		P[index].zlink[1].ploc = 0;	
												//+--
	P[index].zlink[2].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz+R))));
	if(P[index].zlink[2].ploc == npos)
	{
		collIn.ExcessSlots = P[index].zlink[0].ploc;
		collIn.ErrorReturn = 2;
	}
	
	
		
	if(CheckFragDups(index,P[index].zlink[2].ploc,2))
		P[index].zlink[2].ploc = 0;	
		
											//---
	P[index].zlink[3].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz-R))));
	if(P[index].zlink[3].ploc == npos)
	{
		collIn.ExcessSlots = P[index].zlink[0].ploc;
		collIn.ErrorReturn = 2;
	}
		
	if(CheckFragDups(index,P[index].zlink[3].ploc,3))
		P[index].zlink[3].ploc = 0;	
		
		
	//##############
	P[index].zlink[4].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz+R))));
	if(P[index].zlink[4].ploc == npos)
	{
		collIn.ExcessSlots = P[index].zlink[0].ploc;
		collIn.ErrorReturn = 2;
	}
		
	if(CheckFragDups(index,P[index].zlink[4].ploc,4))
		P[index].zlink[4].ploc = 0;	
		
												//-++
	P[index].zlink[5].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz-R))));
	if(P[index].zlink[5].ploc == npos)
	{
		collIn.ExcessSlots = P[index].zlink[0].ploc;
		collIn.ErrorReturn = 2;
	}
	if(CheckFragDups(index,P[index].zlink[5].ploc,5))
		P[index].zlink[5].ploc = 0;	
	
												//-+-
	P[index].zlink[6].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz+R))));
	if(P[index].zlink[6].ploc == npos)
	{
		collIn.ExcessSlots = P[index].zlink[0].ploc;
		collIn.ErrorReturn = 2;
	}
						
	if(CheckFragDups(index,P[index].zlink[6].ploc,6))
		P[index].zlink[6].ploc = 0;	
							//+-+
	P[index].zlink[7].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz-R))));
	if(P[index].zlink[7].ploc == npos)
		{
		collIn.ExcessSlots = P[index].zlink[0].ploc;
		collIn.ErrorReturn = 2;
	}
		
	if(CheckFragDups(index,P[index].zlink[7].ploc,7))
		P[index].zlink[7].ploc = 0;	
		
#if 0
	
	//if(uint(ShaderFlags.frameNum) == 8 && index == 16)
	
	{
		if(P[index].zlink[0].ploc > MaxLocation ||
		P[index].zlink[1].ploc > MaxLocation ||
		P[index].zlink[2].ploc > MaxLocation ||
		P[index].zlink[3].ploc > MaxLocation ||
		P[index].zlink[4].ploc > MaxLocation ||
		P[index].zlink[5].ploc > MaxLocation ||
		P[index].zlink[6].ploc > MaxLocation ||
		P[index].zlink[7].ploc > MaxLocation)
		debugPrintfEXT("VERTINDEX 0 P:%u,%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			index,P[index].zlink[0].ploc,uint(round(cx+R)), uint(round(cy+R)), uint(round(cz-R)),
			cx+R,cy+R,cz-R);
		debugPrintfEXT("VERTINDEX 0 P:%u,%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			index,P[index].zlink[1].ploc,uint(round(cx+R)), uint(round(cy+R)), uint(round(cz+R)),
			cx+R,cy+R,cz+R);
		debugPrintfEXT("VERTINDEX 0 P:%u,%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			index,P[index].zlink[2].ploc,uint(round(cx-R)), uint(round(cy+R)), uint(round(cz-R)),
			cx-R,cy+R,cz-R);
		debugPrintfEXT("VERTINDEX 0 P:%u,%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			index,P[index].zlink[3].ploc,uint(round(cx-R)), uint(round(cy+R)), uint(round(cz+R)),
			cx-R,cy+R,cz+R);			
		debugPrintfEXT("VERTINDEX 0 P:%u,%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			index,P[index].zlink[4].ploc,uint(round(cx+R)), uint(round(cy-R)), uint(round(cz+R)),
			cx+R,cy-R,cz+R);
		debugPrintfEXT("VERTINDEX 0 P:%u,%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			index,P[index].zlink[5].ploc,uint(round(cx+R)), uint(round(cy-R)), uint(round(cz-R)),
			cx+R,cy-R,cz-R);
		debugPrintfEXT("VERTINDEX 0 P:%u,%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			index,P[index].zlink[6].ploc,uint(round(cx-R)), uint(round(cy-R)), uint(round(cz+R)),
			cx-R,cy-R,cz+R);
		debugPrintfEXT("VERTINDEX 0 P:%u,%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			index,P[index].zlink[7].ploc,uint(round(cx-R)), uint(round(cy-R)), uint(round(cz-R)),
			cx-R,cy-R,cz-R);			
			
	}
	#endif
//Debug 	
#if 0 && defined(DEBUG)
	if(uint(ShaderFlags.frameNum) == 3 && index == 32)
	{
		debugPrintfEXT(",,,-------------------------");
		for(uint ii = 0; ii< MAX_OCCUPANCY;ii++)
			debugPrintfEXT("GRAPHPART:%d,%d,%d",index,ii,P[index].zlink[ii].ploc);
	}
#endif	
	uint kk = 0;
	
#if 0
	//*******************************************************
	// Removed location duplicates.
	//*******************************************************
    for (uint ii = 0; ii < MAX_OCCUPANCY; ii++) 
	{

		for (uint jj = 0; jj < MAX_OCCUPANCY;jj++)
        {
			if (jj != ii)
			{
				if (P[index].zlink[ii].ploc == P[index].zlink[jj].ploc) 
				{
						P[index].zlink[jj].ploc = 0;
				}
				else
				{
					kk++;
				}
			}
		}
	}
#endif
				
	if(uint(ShaderFlags.ColorMap) == 0)				
	{
		
		if(P[index].ColFlg == 1.0)
			fragColor = vec3(0.5,1.0,0.4);
		else
			fragColor = vec3(1.0,0.3,0.3);	
	}
	if(uint(ShaderFlags.ColorMap) == 1)				
	{
		fragColor  = hsv2rgb(vec3(P[index].FrcAng.w,1.0,1.0));
	}
		
	
	
}