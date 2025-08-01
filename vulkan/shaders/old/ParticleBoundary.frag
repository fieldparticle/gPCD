#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#extension GL_EXT_debug_printf : enable
#extension GL_EXT_scalar_block_layout :enable

layout(location = 0) out vec4 outColor;
layout(location = 0) in vec4 fragColor;



float  rn(float xx){
        float v0 = fract(sin(xx*.4686)*3718.927);          
        return v0;
}
void main() 
{
	
    	outColor = fragColor;
	
	
}