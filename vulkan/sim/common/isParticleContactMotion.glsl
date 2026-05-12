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

uint isParticleContact(uint crnr, uint SourceID, uint TargetID, uint Pindex)
{

	if(SourceID == TargetID )
		return 0;
	float xT = 0.0;
	float yT = 0.0;
	float zT = 0.0;
	
	float xP = 0.0;
	float yP = 0.0;
	float zP = 0.0;
	
	if (Pindex == 0u)
	{
		xT = P[SourceID].PosLocA.x;
		yT = P[SourceID].PosLocA.y;
		zT = P[SourceID].PosLocA.z;
		
		xP = P[TargetID].PosLocA.x;
		yP = P[TargetID].PosLocA.y;
		zP = P[TargetID].PosLocA.z;
	}
	else
	{
		xT = P[SourceID].PosLocB.x;
		yT = P[SourceID].PosLocB.y;
		zT = P[SourceID].PosLocB.z;
		
		xP = P[TargetID].PosLocB.x;
		yP = P[TargetID].PosLocB.y;
		zP = P[TargetID].PosLocB.z;
	}
	
		 // Get distance between centers
    float dsq = ((xP-xT)*(xP-xT)+
                    (yP-yT)*(yP-yT)+
                    (zP-zT)*(zP-zT));
	float rF = P[SourceID].Data.x;  // only if Data.x is radius
	float rT = P[TargetID].Data.x;

	float rsum = rF + rT;
	float rsq = rsum * rsum;
	
	//float rsq = ((P[SourceID].PosLoc.w+P[TargetID].PosLoc.w)*(P[SourceID].PosLoc.w+P[TargetID].PosLoc.w));
	//float rsq = ((P[SourceID].Data.x+P[TargetID].Data.x)*(P[SourceID].Data.x+P[TargetID].Data.x));
	// If square of distance is less than square of radii there is a collision.
	float tdt = rsq/dsq;
	#if 0 && defined(DEBUG)
		if(SourceID == 1 )
			debugPrintfEXT("Collison Frame(%0.1f),FRM:%d,TO:%d dsq:%0.8f,rsq:%0.8f,rddiff:%0.8f,Radius1:%0.4f,Radius2:%0.4f",
			ShaderFlags.frameNum,
			SourceID,
			TargetID,dsq,rsq,dsq-rsq,P[SourceID].Data.x,P[TargetID].Data.x);
	#endif
	
	float rddiff = dsq-rsq;	
	//if (dsq <= rsq )
	if(rddiff < 0.00001)
    {
		#if 0 && defined(DEBUG)
		if(uint(ShaderFlags.frameNum) == 3)// && SourceID == 1)
			debugPrintfEXT("Collison Frame(%0.1f),FRM:%d,TO:%d dsq:%0.4f,rsq:%0.4f,Radius1:%0.4f,Radius2:%0.4f",
			ShaderFlags.frameNum,
			SourceID,
			TargetID,dsq,rsq,P[SourceID].PosLoc.w,P[TargetID].PosLoc.w);
		#endif	
	
		return 1;
	}

	return 0;
}