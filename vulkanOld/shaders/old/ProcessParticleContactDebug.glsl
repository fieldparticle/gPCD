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

uint CalcParticleContact(uint Findex, uint Tindex)
{

    float tol = 0.0000001;
	if(Findex == Tindex)
		return 0;
	
		
	
    vec3 U1x,U1y,U2x,U2y,V1x,V1y,V2x,V2y;

	float xT = P[Findex].PosLoc.x;
    float yT = P[Findex].PosLoc.y;
    float zT = P[Findex].PosLoc.z;
	
	float xP = P[Tindex].PosLoc.x;
    float yP = P[Tindex].PosLoc.y;
    float zP = P[Tindex].PosLoc.z;

    // Get distance between centers
    float dsq = ((xP-xT)*(xP-xT)+
                    (yP-yT)*(yP-yT)+
                    (zP-zT)*(zP-zT));
   
	float rsq = ((P[Findex].PosLoc.w+P[Tindex].PosLoc.w)*(P[Findex].PosLoc.w+P[Tindex].PosLoc.w));
	
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

#if 0 && defined(DEBUG)
		if(ShaderFlags.frameNum == 3.0 && Findex == 1 && Tindex == 2 )
			debugPrintfEXT("Frame:%d, Testing FRM:%d,TO:%d dsq:%0.4f,rsq:%0.4f,r1:%0.2f,r2:%0.2f",
			uint(ShaderFlags.frameNum),
			Findex,Tindex,
			dsq,
			rsq,
			P[Findex].PosLoc.w,P[Tindex].PosLoc.w);
#endif
	
	
	
	if (dsq <= rsq )
    {
		
	
#if 0 && defined(DEBUG)
		if(ShaderFlags.frameNum == 3.0 && Findex == 1 && Tindex == 2 )
		//if(uint(ShaderFlags.frameNum) == 1001 && Findex == 1)
			debugPrintfEXT("Frame:%d, Collison FRM:%d,TO:%d dsq:%0.4f,rsq:%0.4f,r1:%0.2f,r2:%0.2f",
			uint(ShaderFlags.frameNum),
			Findex,Tindex,
			dsq,
			rsq,
			P[Findex].PosLoc.w,P[Tindex].PosLoc.w);
			//P[Findex].wary[0] = vec4(1.0,0.5,0.7,1.0);
#endif
		P[Findex].ColFlg = 1;	
		
		//FrcAng.x = spc2pt(vec2(P[Findex].VelRad.x,P[Findex].VelRad.x);
		//FrcAng.y = spc2pt(vec2(P[Findex].VelRad.x,P[Findex].VelRad.x);
		//FrcAng.z = spc2pt(vec2(P[Findex].VelRad.z,P[Findex].VelRad.y);

		
		return 1;
	}

	return 0;
}