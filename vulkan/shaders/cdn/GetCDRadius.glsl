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
const float sec24slp = 0.1f;

const float secx1_beg = 1.0f;
const float secx1_end = 5.0f;
const float secz1     = 10.0f;

const float secx2_beg = 5.0f;
const float secx2_end = 25.0f;
const float secz2     = 10.0f;

const float secx3_beg = 25.0f;
const float secx3_end = 30.0f;
const float secz3     = 8.1f;


const float secx4_beg = 30.0f;
const float secx4_end = 50.0f;
const float secz4     = 10.0f;

const float secx5_beg = 50.0f;
const float secz5     = 10.0f;
// Return the radious of the nozzle based on the 
// z location.
float GetCDRadius(float Z)
{
	//FLAT
	// SEC1 0 included to less than 5
	if(Z >= secx1_beg && Z <= secx1_end)
       return -secz1;
	   
	// SEC1 1 slope down
	// 5.0 included to less than 25
	else if(Z > secx1_end && Z <= secx2_end)
	   return secz2+(Z-secx2_beg)*(-sec24slp);

	// SEC3 Flat 25 	
	else if(Z > secx2_end && Z <= secx3_end)
       return -secz3;
	   
	else if(Z > secx3_end && Z <= secx4_end)
		return secz3+(Z-secx3_end)*(sec24slp);
		
	else if(Z > secx4_end)
        return -secz5;  
		
	else
		return 0;

	return 0;
}