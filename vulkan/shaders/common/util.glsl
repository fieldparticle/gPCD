
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
// Transform a space vector to the origin, usually to calulate angle.
vec2 spc2pt(vec4 SpcVec)
{
    return vec2(SpcVec[2]-SpcVec[0],SpcVec[3]-SpcVec[1]);
}   
// Get angle on 0-2PI range
float atan2piPt(in vec2 pt)
{
	if(pt.y == 0.0 || pt.x == 0.0)
		return 0.0;
    float angle = mod(atan(pt.y,pt.x),2*PI);
	
	return angle;
}	
//Convert world length to device c=lemgth
float w2dLen(float world, uint dim)
{
	return world/dim;
}
// World to device corrdinate.
float w2d(float world, uint Dim)
{
	return (2.0/(Dim))*world-1.0;
} 
//Device to world coordinate
float d2w(float device, uint Dim)
{
	return (float(Dim)/2.0)*(device+1.0);
} 
// Flip angle 180 deg.
float flipang(float Ang)
{
    return mod((Ang+PI),2*PI);
}
// spc2pt3(Vec)
//  Transfor space vector to origin vector
//  Vec     = 6 compnent space vector
//returns
//   outvec  = 3 component origin vector

vec3 spc2pt3(vec3 VecF,vec3 VecT)
{
    return vec3(VecT.x-VecF.x,VecT.y-VecF.y,VecT.z-VecF.z);
}


void IndexToArray(uint index, inout uvec3 ary)
{
	uint c1,c2,c3;
	uint w = WIDTH;
	uint h = HEIGHT;
	c1 = index / (w * h);
	c2 = (index - c1 * w * h) / w;
	c3 = index - w * (c2 + w * c1);

	ary[0] = c3;
	ary[1] = c2;
	ary[2] = c1;
}
uint ArrayToIndex(uvec3 loc)
{
		
	uint w = WIDTH;
	uint h = HEIGHT;
	
	uint indxLoc =  loc.x + w * (loc.y + h * loc.z);
	if(indxLoc > MAX_CELL_ARRAY_LOCATIONS)
		return npos;
	else
		return indxLoc;

}
uint TestArrayToIndex(uint start,uint stop)
{
	uvec3 ary = uvec3(0,0,0);
	uint idx = 0;
	uint count = 0;
	debugPrintfEXT("W:%d H:%d",WIDTH,HEIGHT);
	for (uint ii=start;ii<WIDTH;ii++)
	{
		for (uint jj=0;jj<WIDTH;jj++)
		{
			for (uint kk=0;kk<WIDTH;kk++)
			{
				ary[0] = kk;
				ary[1] = jj;
				ary[2] = ii;
				idx = ArrayToIndex(ary);
				#if 0
				if (stop != 0)
					debugPrintfEXT("I:%d<%d,%d,%d>",idx,kk,jj,ii);
				#endif
				if (count != idx)
					return count;
				if (count == stop)
					return 0;
				count++;
			}
		}
	}
	return 0;
}				


#if 0
vec4 DrawLegend()
{
	vec2 mv;
	
	float xx = gl_FragCoord.x;
	float yy = gl_FragCoord.y;
	if (gl_FragCoord.x > 640.00 
			&& gl_FragCoord.x < 790.0 
				&& gl_FragCoord.y > 10.0 
					&& gl_FragCoord.y < 150.0)
	{
	
		//uv.x 			= (fragTexCoord.x+650/800.0);
		//uv.y 			= (fragTexCoord.y+10/800.0);
		
		mv.x 			= (xx+635-75)/150;
		mv.y 			= (yy)/150;
		
		
		return texture(sampler2D(textures[0], texSampler), mv);
		
	}
	else
		return vec4(0.0);
}
#endif


vec3 hsv2rgb(in vec3 hsv)
{
///H, S and V input range = 0 ÷ 1.0
//R, G and B output range = 0 ÷ 255
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
	