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

uint isParticleContact(uint crnr, uint Findex, uint Tindex, uint Pindex)
{

	if(Findex == Tindex )
		return 0;
	float xT = 0.0;
	float yT = 0.0;
	float zT = 0.0;
	
	float xP = 0.0;
	float yP = 0.0;
	float zP = 0.0;
	
	if (Pindex == 1)
	{
		xT = P[Findex].PosLocA.x;
		yT = P[Findex].PosLocA.y;
		zT = P[Findex].PosLocA.z;
		
		xP = P[Tindex].PosLocA.x;
		yP = P[Tindex].PosLocA.y;
		zP = P[Tindex].PosLocA.z;
	}
	else
	{
		xT = P[Findex].PosLocB.x;
		yT = P[Findex].PosLocB.y;
		zT = P[Findex].PosLocB.z;
		
		xP = P[Tindex].PosLocB.x;
		yP = P[Tindex].PosLocB.y;
		zP = P[Tindex].PosLocB.z;
	}
	
		 // Get distance between centers
    float dsq = ((xP-xT)*(xP-xT)+
                    (yP-yT)*(yP-yT)+
                    (zP-zT)*(zP-zT));
	float rF = P[Findex].Data.x;  // only if Data.x is radius
	float rT = P[Tindex].Data.x;

	float rsum = rF + rT;
	float rsq = rsum * rsum;
	
	//float rsq = ((P[Findex].PosLoc.w+P[Tindex].PosLoc.w)*(P[Findex].PosLoc.w+P[Tindex].PosLoc.w));
	//float rsq = ((P[Findex].Data.x+P[Tindex].Data.x)*(P[Findex].Data.x+P[Tindex].Data.x));
	// If square of distance is less than square of radii there is a collision.
	float tdt = rsq/dsq;
	#if 0 && defined(DEBUG)
		if(uint(ShaderFlags.frameNum) == 9989 )
			debugPrintfEXT("Collison Frame(%0.1f),FRM:%d,TO:%d dsq:%0.8f,rsq:%0.8f,rddiff:%0.8f,Radius1:%0.4f,Radius2:%0.4f",
			ShaderFlags.frameNum,
			Findex,
			Tindex,dsq,rsq,dsq-rsq,P[Findex].Data.x,P[Tindex].Data.x);
	#endif
	
	float rddiff = dsq-rsq;	
	//if (dsq <= rsq )
	if(rddiff < 0.00001)
    {
		#if 0 && defined(DEBUG)
		if(uint(ShaderFlags.frameNum) == 3)// && Findex == 1)
			debugPrintfEXT("Collison Frame(%0.1f),FRM:%d,TO:%d dsq:%0.4f,rsq:%0.4f,Radius1:%0.4f,Radius2:%0.4f",
			ShaderFlags.frameNum,
			Findex,
			Tindex,dsq,rsq,P[Findex].PosLoc.w,P[Tindex].PosLoc.w);
		#endif	
	
		return 1;
	}

	return 0;
}