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

uint CalcParticleContact(uint crnr, uint Findex, uint Tindex)
{
	
    
	if(Findex == Tindex)
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
	vec3 InVelF	= P[Findex].VelRad.xyz;
	vec3 InVelT	= P[Tindex].VelRad.xyz;
	vec3 newVel;
	
    // Get distance between centers
    float dsq = ((xP-xT)*(xP-xT)+
                    (yP-yT)*(yP-yT)+
                    (zP-zT)*(zP-zT));
   
	float rsq = ((P[Findex].PosLoc.w+P[Tindex].PosLoc.w)*(P[Findex].PosLoc.w+P[Tindex].PosLoc.w));
	
	// If square of distance is less than square of radii there is a collision.
	float tdt = dsq/rsq;
	if (dsq <= rsq )
    {
	
		if(isDup(Findex,Tindex))
		{
#if 1
			if(uint(ShaderFlags.frameNum) == 5)
			{
				debugPrintfEXT("TRUE F:%d,FRM:%d,TO:%d,penetration:%0.5f,slot:%u,crnr:%u",
				uint(ShaderFlags.frameNum),
				Findex,
				Tindex,
				tdt,
				P[Findex].sltnum,
				crnr);
						
			}
#endif
			return 0;
		}
		else
		{
		#if 0
		if(ShaderFlags.frameNum == 3.0 && Findex == 1 && Tindex == 2 )
		{
			debugPrintfEXT("Frame:%d, FRM:(%d)<%0.4f,%0.4f,%0.4f> TO:(%d),<%0.4f,%0.4f,%0.4f>",uint(ShaderFlags.frameNum),
			Findex,xT,yT,zT,Tindex,xP,yP,zP);
			debugPrintfEXT("Frame:%0.1f, Collison FRM:%d,TO:%d dsq:%0.4f,rsq:%0.4f,r1:%0.2f,r2:%0.2f",
			ShaderFlags.frameNum,
			Findex,Tindex,
			dsq,
			rsq,
			P[Findex].PosLoc.w,P[Tindex].PosLoc.w);
		}
#endif
#if 0
		//	if(uint(ShaderFlags.frameNum) > 3689 && uint(ShaderFlags.frameNum) < 3690)
			{
				debugPrintfEXT("FALSE F:%d,FRM:%d,TO:%d,penetration:%0.5f,slot:%u,crnr:%u",
				uint(ShaderFlags.frameNum),
				Findex,
				Tindex,
				tdt,
				P[Findex].sltnum,
				crnr);
			}
#endif

			
			CalcMomentum(Findex,Fm,Ft,InPosF,InPosT,InVelF,InVelT,newVel);
			P[Findex].PosLoc.xyz = newVel;
			//SetCflg(crnr, Findex, Tindex);
			atomicAdd(collOut.CollisionCount,1);
			return -1;		
		}
	
	}
	else
		ClearCflg(Findex,Tindex);


	return 0;
}