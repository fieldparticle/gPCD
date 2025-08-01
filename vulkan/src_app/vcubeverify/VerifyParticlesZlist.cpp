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
#include "mpsVerify.hpp"
void VerifyParticlesZlist(mpsverifycfg* configVerify)
{
	std::string datafile = configVerify->GetString("application.dataFile", true);
	mout << "Data File:" << datafile << ende;
	uint32_t missed_link_count = 0;
	// Reading from it
	std::ifstream input_file(datafile, std::ios::binary);
	Particle part_pos;
	uint32_t m_NumParticles = 0;
	uint32_t count = 0;
	while (input_file.peek() != EOF)
	{
		input_file.read((char*)&part_pos, sizeof(part_pos));
		if (!input_file.is_open())
		{
			std::string err = "Unable to open particle data file:" + datafile;
			throw std::runtime_error(err.c_str());
		}
#if 0
		mout << "Particle #" << (float)part_pos.pnum << ende;
		mout << "rx: " << (float)part_pos.rx << ende;
		mout << "ry: " << (float)part_pos.ry << ende;
		mout << "rz: " << (float)part_pos.rz << ende;
		mout << ende;
#endif
		
		for (size_t ii = 0; ii < 1; ii++)
		{
			if (part_pos.zlink[ii].x == 0 &&
				part_pos.zlink[ii].y == 0 &&
				part_pos.zlink[ii].z == 0 &&
				part_pos.zlink[ii].w == 0)
			{
				missed_link_count++;
			}

		}


	}
	mout << "Missed Links Read:" << missed_link_count << ende;
	}