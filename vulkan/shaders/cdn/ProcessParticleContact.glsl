/***      m PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date:  $
% $HeadURL:  $
% $Id:  $
%*******************************************************************
%***                         DESCRIPTION                         ***
%*******************************************************************
%@doc
%@module
%			@author: Jackie Michael Bell
%			COPYRIGHT <cp> Jackie Michael Bell
%			Property of Jackie Michael Bell<rtm>. All Rights Reserved.
%			This source code file contains proprietary
%			and confidential information.
%
%
%@head3 		Description. | 
%               
%@normal
%********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision:  $
%*
%*
%******************************************************************/
// Takes the index of two particles and detemines the distance between them
// If the distance is less than the sum of radii squared the are in comllsion.
// If collsiong increment the collsion counter.

uint ProcessParticleContact(uint crnr, uint Findex, uint Tindex, in out vec3 OutVel)
{
	if(Findex == Tindex || Tindex <= bbound)
		return 0;
	
	vec3 U1x,U1y,U2x,U2y,V1x,V1y,V2x,V2y;

	float xT = P[Findex].PosLoc.x;
    float yT = P[Findex].PosLoc.y;
    float zT = P[Findex].PosLoc.z;
	
	float xP = P[Tindex].PosLoc.x;
    float yP = P[Tindex].PosLoc.y;
    float zP = P[Tindex].PosLoc.z;
	
	int slot 	=  -2;
	float Fm 	= P[Findex].MolarMatter;
	float Ft 	= P[Tindex].MolarMatter;
	vec3 InPosF = P[Findex].PosLoc.xyz;
	vec3 InPosT = P[Tindex].PosLoc.xyz;
	vec3 InVelF	= P[Findex].prvvel.xyz;
	vec3 InVelT	= P[Tindex].prvvel.xyz;
	vec3 newVel;
	uint startf = 5996;
	uint endf = 6000;
	uint particl = 3;
    // Get distance between centers
    float dsq = ((xP-xT)*(xP-xT)+
                    (yP-yT)*(yP-yT)+
                    (zP-zT)*(zP-zT));
   
	float rsq = ((P[Findex].PosLoc.w+P[Tindex].PosLoc.w)*(P[Findex].PosLoc.w+P[Tindex].PosLoc.w));
	
	// If square of distance is less than square of radii there is a collision.
	float tdt = rsq/dsq;
	
	if (dsq <= rsq )
    {
		P[Findex].ColFlg = 1;
		
		if(inColl(Findex,Tindex))
		{
#if 0			
			if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) < endf) && Findex == particl)
			{
				debugPrintfEXT("INCOL FRM:%u TO:%u",Findex,Tindex);
			}
#endif
		}
#if 1		
		if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) < endf) && Findex == particl)
		{
			debugPrintfEXT("OLD VEL F:%u FRM:%u VF<%0.3f,%0.3f,%0.3f> TO:%u VT<%0.3f,%0.3f,%0.3f>",
			uint(ShaderFlags.frameNum),
			Findex,P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
			Tindex,P[Tindex].VelRad.x,P[Tindex].VelRad.y,P[Tindex].VelRad.z);
		}	
#endif
		CalcMomentum(Findex,Fm,Ft,InPosF,InPosT,InVelF,InVelT,newVel);
		OutVel=newVel ;
		P[Findex].VelRad.xyz = newVel;
		//P[Findex].PosLoc.xyz = newVel*0.001;
		
		
#if 0
		if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) < endf) && Findex == particl)
		{
			debugPrintfEXT("NEW VEL F:%u FRM:%d To:%u, V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f>",
			uint(ShaderFlags.frameNum),Findex,Tindex,
			OutVel.x,OutVel.y,OutVel.z,
			P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z);
		}	
#endif
		
		
		atomicAdd(collOut.CollisionCount,1);
		return -1;		
	}
	else
	{
		P[Findex].ColFlg = 0;
		ClearCflg(Findex,Tindex);
	}


	return 0;
}