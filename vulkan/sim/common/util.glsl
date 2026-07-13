
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
    uint d = DEPTH;

    if (loc.x >= w || loc.y >= h || loc.z >= d) {
        return npos;
    }

    uint indxLoc = loc.x + w * (loc.y + h * loc.z);
    if (indxLoc >= MAX_CELL_ARRAY_LOCATIONS) {
        return npos;
    }
    return indxLoc;
	

}

uint TestArrayToIndex(uint start,uint stop)
{
	uvec3 ary = uvec3(0,0,0);
	uint idx = 0;
	uint count = 0;
	#if 0 && defined(DEBUG)
		debugPrintfEXT("W:%d H:%d",WIDTH,HEIGHT);
	#endif
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
				#if 0 && defined(DEBUG)
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

