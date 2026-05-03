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


@head3 		Description. |
@normal


********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision: 28 $
%*
%*
%******************************************************************/
vec3 CalcBoundaryVel(uint index, vec3 Pos, vec3 Vel, uint Center) 
{
	uint startf = 4465;
	uint endf = 4470;
	uint particl = 4704;
	
	vec3 pointA;
	vec3 pointB;
	vec3 pointC;
	float radA;
	float radB;
	float lowZ;
	vec3 rvel;
	// Move a bit away from it to get a second parallel point 
	// on the plane.
	float angxy = atan2piPt(vec2(Pos.x-Center,Pos.y-Center));
	
	// Get the radius at this point.
	radA = GetCDRadius(Pos.z);
	#if 1
	//if the radius is negative we are on a flat 
	// so just revers xyvelocity
	if(radA < 0.0)
	{
		rvel.x = -Vel.x;
		rvel.y = -Vel.y;
		rvel.z = Vel.z;
	#if 0
		debugPrintfEXT("CALVELFLAT F:%u P:%u,angxy:%0.3f,Rad:%0.3f,PC<%0.3f,%0.3f,%0.3f>,VIN<%0.3f,%0.3f,%0.3f>",
				uint(ShaderFlags.frameNum),index,
				angxy,
				radA,
				Pos.x,Pos.y,Pos.z,
				Vel.x,Vel.y,Vel.z);	
		#endif
		return rvel;
	}
	#endif
	pointA.x = radA*cos(angxy)+Center;
	pointA.y = radA*sin(angxy)+Center;
	pointA.z = Pos.z;
	
	// Get point B if we are on the converging
	// or diverging sections
	if(Pos.z >= secx2_beg && Pos.z  < secx2_end - 10) 
		lowZ = pointA.z+4.0;
		
	else if(Pos.z >= secx2_beg+10.0 && Pos.z < secx2_end)
		lowZ = pointA.z-4.0;
		
	if(Pos.z >= secx4_beg && Pos.z < secx4_end - 10 ) 
		lowZ = pointA.z+4.0;
		
	else if(Pos.z >= secx4_beg+10.0 && Pos.z < secx4_end )
		lowZ = pointA.z-4.0;	
	
	radB = GetCDRadius(lowZ);
	pointB.x = radB*cos(angxy)+Center;
	pointB.y = radB*sin(angxy)+Center;
	pointB.z = lowZ;
	
	pointC.x = radB*cos(angxy+PI/64)+Center;
	pointC.y = radB*sin(angxy+PI/64)+Center;
	pointC.z = lowZ;
	
	

	// Get the plane normal
	vec3 param1 = pointA-pointB;
	vec3 param2 = pointA-pointC;
	vec3 normvec = cross(pointA-pointB, pointA-pointC);
	float D = -dot(normvec,	pointA);
    vec3 nnormvec = normalize(normvec);
	// Caclulate velocity resitiution.
	rvel = Vel - 2.0*(dot(Vel,nnormvec)*nnormvec);
	
	#if 0
	//if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) <= endf) && index == particl)
	if(isnan(rvel.x) || isnan(rvel.y) || isnan(rvel.z))
	{

			debugPrintfEXT("CALVEL F:%u P:%u,angxy:%0.3f, PP<%0.3f,%0.3f,%0.3f>,PA<%0.3f,%0.3f,%0.3f>,PB<%0.3f,%0.3f,%0.3f>,PC<%0.3f,%0.3f,%0.3f>,VIN<%0.3f,%0.3f,%0.3f>",uint(ShaderFlags.frameNum),index,angxy,
					Pos.x,Pos.y,Pos.z,
					pointA.x,pointA.y,pointA.z,
					pointB.x,pointB.y,pointB.z,
					pointC.x,pointC.y,pointC.z,
					Vel.x,Vel.y,Vel.z);	
	
	}
#endif
#if 0
	////// Checks
	vec3 slopevec = pointA-pointB;
	
	//Calc angle of incedence
	float angi = atan(length(cross(slopevec,Vel)),dot(slopevec,Vel));

	//Angle of reflection
	float angr = atan(length(cross(slopevec,rvel)),dot(slopevec,rvel));

	//if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) <= endf) && index == particl)
	if(isnan(rvel.x) || isnan(rvel.y) || isnan(rvel.z))
	{

	debugPrintfEXT("CALVEL F:%u P:%u, angi:%0.5f,angr:%0.5f,angxy:%0.5f,NV<%0.3f,%0.3f,%0.3f,%0.3f>,VOUT<%0.3f,%0.3f,%0.3f>",
					uint(ShaderFlags.frameNum),index,
					angi,angr,angxy,
					normvec.x,normvec.y,normvec.z,D,
					rvel.x,rvel.y,rvel.z);	


		
	}

#endif
	return rvel;

}