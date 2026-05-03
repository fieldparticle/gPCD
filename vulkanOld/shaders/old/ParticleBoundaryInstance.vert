#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#extension GL_EXT_debug_printf : enable
#extension GL_EXT_scalar_block_layout :enable
#include "..\params.glsl"
#include "..\common\constants.glsl"
#include "..\common\atomicg.glsl"
#include "..\common\push.glsl"
#include "..\common\CollimageIndex.glsl"
#include "..\common\Lockimage.glsl"
#include "..\common\particle.glsl"
#include "..\common\util.glsl"


layout(binding = 1) uniform UniformBufferObject{
    mat4 model;
    mat4 view;
    mat4 proj;
} ubo;

layout(binding = 7) uniform UniformBufferObjectS{
    mat4 model;
    mat4 view;
    mat4 proj;
} subo;

out gl_PerVertex {
    vec4 gl_Position;
	float gl_ClipDistance[3];
};

layout(location = 0) in vec4 inPosition;
layout(location = 1) in vec4 inColor;

layout(location = 0) out vec4 fragColor;
mat4 BuildTranslation(vec3 delta)
{
    return mat4(
        vec4(1.0, 0.0, 0.0, 0.0),
        vec4(0.0, 1.0, 0.0, 0.0),
        vec4(0.0, 0.0, 1.0, 0.0),
        vec4(delta, 1.0));
}

void main()
{
#if 0
	if(ShaderFlags.DrawInstance == 2.0 
		&& ShaderFlags.frameNum == 5.0 && gl_VertexIndex == 1)
		{
		debugPrintfEXT("VERTBOUND:Instance %d",gl_InstanceIndex);
	}
#endif
	vec3 delta = vec3(0.5,0.5,0.5);
	mat4 trans = BuildTranslation(delta);
	uint ModelInstance = gl_InstanceIndex+1;
	
	if(ShaderFlags.DrawInstance == 1.0)
	{
		gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPosition);
	}
	else
	{
		vec4 newPos = vec4(inPosition.x+P[ModelInstance].PosLoc.x,inPosition.y+P[ModelInstance].PosLoc.y,inPosition.z+P[ModelInstance].PosLoc.z,1.0);
		gl_Position = subo.proj * subo.view * subo.model * newPos;
	}
		
	#if 0
	if(ShaderFlags.DrawInstance == 1.0 
		&& ShaderFlags.frameNum == 5.0 && gl_VertexIndex == 1)
	{
		debugPrintfEXT("BOUNDRYVERTEX Particle Pos:%d px=%0.3f,py=%0.3f,pz=%0.3f,",
			1,P[1].PosLoc.x,P[1].PosLoc.y,P[1].PosLoc.z);
	}
	#endif
	#if 0
	if(ShaderFlags.DrawInstance == 2.0 
		&& ShaderFlags.frameNum == 5.0 && gl_VertexIndex == 1)
	{
		debugPrintfEXT("BOUNDRYVERTEX:Square Pos:%d px=%0.3f,py=%0.3f,pz=%0.3f,",
			0,inPosition.x,inPosition.y,inPosition.z);
	
	}
	#endif
	
	gl_ClipDistance[0] = 0.0;
	gl_ClipDistance[1] = 0.0;
	gl_ClipDistance[2] = 0.0;
	if(ShaderFlags.DrawInstance == 1.0)
		fragColor = inColor;
	else
	{
		if(ModelInstance > bbound)
		{
			
			// If the particle is not live return.		
			if(uint(P[ModelInstance].parms.x) > uint(ShaderFlags.frameNum))
				return;	
		
			if(uint(ShaderFlags.ColorMap) == 0)				
			{
				if(P[ModelInstance].ColFlg == 1.0)
					fragColor = vec4(1.0,0.0,1.0,1.0); //vec4(hsvout,1.0);
				else
					fragColor = vec4(0.0,0.0,1.0,1.0); //vec4(hsvout,1.0);
			}
			if(uint(ShaderFlags.ColorMap) == 1)				
			{
				vec3 tmpclr = hsv2rgb(vec3(P[ModelInstance].FrcAng.w,1.0,1.0));
				fragColor  = vec4(tmpclr,1.0);
			}
		}
		else
		{
			return;
			fragColor = vec4(0.0,0.0,0.0,1.0);;	
		}
	}
}