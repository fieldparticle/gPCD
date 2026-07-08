#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#include "debug.glsl"
#if defined(DEBUG)
	#extension GL_EXT_debug_printf : enable
#endif
#extension GL_EXT_scalar_block_layout :enable
#include "params.glsl"
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

	vec3 delta = vec3(0.5,0.5,0.5);
	mat4 trans = BuildTranslation(delta);
	uint ModelInstance = gl_InstanceIndex+1;
	if(ShaderFlags.DrawInstance == 1.0)
	{
		gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPosition.xyz, 1.0);
		fragColor = inColor;
	}
	else
	{
		vec3 sphereOffset = inPosition.xyz * P[ModelInstance].Data.x;
		vec4 newPos = vec4(sphereOffset + P[ModelInstance].PosLocA.xyz, 1.0);
		gl_Position = subo.proj * subo.view * subo.model * newPos;
		if(HSV_ON == 1)
		{
			if (P[ModelInstance].ptype == 0)
			{
				float velocityAngle = ShaderFlags.positionBuffer == 0u
					? P[ModelInstance].VelRadA.w
					: P[ModelInstance].VelRadB.w;
				fragColor = vec4(colorizeVelocity(velocityAngle, HSV_SAT, HSV_VAL),1.0);
			}
			else
				fragColor = vec4(1.0, 1.0, 1.0,1.0);
		}
		else
		{
			if(uint(P[ModelInstance].colFlg) == 1)
				fragColor = vec4(1.0,0.0,0.0,1.0);	
			else if(uint(P[ModelInstance].colFlg) == 0)
				fragColor = vec4(0.0,1.0,0.0,1.0);	
		}
	
	}
}
