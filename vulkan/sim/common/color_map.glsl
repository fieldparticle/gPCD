
/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/DescriptorSSBO.cpp $
% $Id: DescriptorSSBO.cpp 28 2023-05-03 19:30:42Z jb $
%*******************************************************************
%***                         DESCRIPTION                         ***
%*******************************************************************
@doc
@module
			@author: Jackie Michael Bell<nl>
			COPYRIGHT <cp> Jackie Michael Bell<nl>
			Property of Jackie Michael Bell<rtm>. All Rights Reserved.<nl>
			This source code file contains proprietary<nl>
			and confidential information.<nl>


@head3 		Description. 
@normal


********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision: 28 $
%*
%*
%******************************************************************/

#if defined(DEBUG)
	#extension GL_EXT_debug_printf : enable
#endif
vec3 hsv2rgb(in vec3 hsv);
vec3 colorizeVelocity(float v_ang, float sat, float val);
uint material_color_scheme(uint materialID);
vec4 color_from_scheme(uint index, uint colorScheme);
vec4 solid_color(uint colorScheme);

vec4 color_map(uint index)
{
	if (P[index].ptype > 0.5)
		return vec4(1.0, 1.0, 1.0, 1.0);

	uint materialID = uint(round(P[index].material_id));
	uint colorScheme = material_color_scheme(materialID);
	return color_from_scheme(index, colorScheme);

}

uint material_color_scheme(uint materialID)
{
	for (uint ii = 0u; ii < MATERIAL_PROPERTY_COUNT; ++ii)
	{
		if (MATERIAL_PROPERTIES[ii].materialID == materialID)
			return MATERIAL_PROPERTIES[ii].colorScheme;
	}

	return COLOR_SCHEME_COLLISION;
}

vec4 color_from_scheme(uint index, uint colorScheme)
{
	if (colorScheme == COLOR_SCHEME_HSV)
	{
		float velocityAngle = ShaderFlags.positionBuffer == 0u
			? P[index].VelRadA.w
			: P[index].VelRadB.w;
		return vec4(colorizeVelocity(velocityAngle, HSV_SAT, HSV_VAL), 1.0);
	}

	if (colorScheme == COLOR_SCHEME_COLLISION)
	{
		if (uint(P[index].colFlg) == 1u)
			return vec4(colcolor, 1.0);
		return vec4(ncolcolor, 1.0);
	}

	return solid_color(colorScheme);
}

vec4 solid_color(uint colorScheme)
{
	if (colorScheme == COLOR_SCHEME_WHITE)
		return vec4(1.0, 1.0, 1.0, 1.0);
	if (colorScheme == COLOR_SCHEME_RED)
		return vec4(1.0, 0.0, 0.0, 1.0);
	if (colorScheme == COLOR_SCHEME_GREEN)
		return vec4(0.0, 1.0, 0.0, 1.0);
	if (colorScheme == COLOR_SCHEME_BLUE)
		return vec4(0.2, 0.6, 1.0, 1.0);

	return vec4(1.0, 1.0, 1.0, 1.0);
}

vec3 hsv2rgb(in vec3 hsv)
{
///H, S and V input range = 0 Ã· 1.0
//R, G and B output range = 0 Ã· 255
	float H = hsv.r;
	float S = hsv.g;
	float V = hsv.b;
	float var_r;
	float var_g;
	float var_b;
	float R = 0;
	float G = 0;
	float B = 0;
	
	vec3 ret_clr = vec3(0.0);
	if ( S == 0 )
	{
	   R = V * 255;
	   G = V * 255;
	   B = V * 255;
	}
	else
	{
	   float var_h = H * 6;
	   if ( var_h == 6 ) var_h = 0 ; 
	   //H must be < 1
	   float var_i = int( var_h );             //Or ... var_i = floor( var_h )
	   float var_1 = V * ( 1 - S );
	   float var_2 = V * ( 1 - S * ( var_h - var_i ) );
	   float var_3 = V * ( 1 - S * ( 1 - ( var_h - var_i ) ) );

	   if( var_i == 0 ) 
	   { 
			var_r = V; 
			var_g = var_3 ; 
			var_b = var_1; 
		}
	   else if ( var_i == 1 ) 
	   { 
			var_r = var_2 ; 
			var_g = V     ; 
			var_b = var_1; 
		}
	   else if ( var_i == 2 ) 
	   { 
			var_r = var_1 ; 
			var_g = V     ; 
			var_b = var_3 ;
		}
	   else if ( var_i == 3 ) 
	   { 
			var_r = var_1 ; 
			var_g = var_2 ; 
			var_b = V ;
		}
	   else if ( var_i == 4 ) 
	   { 
			var_r = var_3 ; 
			var_g = var_1 ; 
			var_b = V; 
		}
	   else
	   { 
			var_r = V     ; 
			var_g = var_1 ; 
			var_b = var_2 ;
		};

	   R = var_r * 255;
	   G = var_g * 255;
	   B = var_b * 255;
	}
	ret_clr = vec3(R/255,G/255,B/255);
	return ret_clr;
}

vec3 colorizeVelocity(float v_ang, float sat, float val)
{
	float hue = fract(v_ang / 6.28318530718);
	return hsv2rgb(vec3(hue, clamp(sat, 0.0, 1.0), clamp(val, 0.0, 1.0)));
}
	
