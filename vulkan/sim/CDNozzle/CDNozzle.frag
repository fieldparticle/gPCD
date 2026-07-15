#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#include "debug.glsl"
#if defined(DEBUG)
	#extension GL_EXT_debug_printf : enable
#endif
#extension GL_EXT_scalar_block_layout :enable

layout(location = 0) out vec4 outColor;
layout(location = 0) in vec4 fragColor;
#include "..\common\Boundary.frag"
void main() 
{
	
    	boundary_vert_main() ;
	
	
}