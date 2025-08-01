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

#include "VulkanObj/VulkanApp.hpp"
#include "VulkanObj/pdata.hpp"
#include "gendata/GenResourceVertexParticle.hpp"
uint32_t m_SideLength = 0;
uint32_t GenResourceVertexParticle::CountCollisions()
{
	std::vector< pdata> m_Particle;
	uint32_t coLocCount = 0;
	
	uint32_t missed_link_count = 0;
	// Reading from it
	std::ifstream input_file(m_FullBinFile, std::ios::binary);
	if (!input_file.is_open())
	{
		std::string err = "Cannot create collsion verification data file::" + m_FullBinFile;
			throw std::runtime_error(err.c_str());
	}
	pdata part_pos;
	uint32_t m_NumParticles = 0;
	uint32_t count			= 0;
	float radius			= 0;

	while (input_file.peek() != EOF)
	{
		input_file.read((char*)&part_pos, sizeof(part_pos));
		if (!input_file.is_open())
		{
			std::string err = "Unable to open particle data file:" + m_FullBinFile;
			throw std::runtime_error(err.c_str());
		}
		m_Particle.push_back(part_pos);

	}
	radius = (float)part_pos.radius;
	uint32_t colCount	= 0;
	double xT			= 0;
	double yT			= 0;
	double zT			= 0;
	double xP			= 0;
	double yP			= 0;
	double zP			= 0;
	double dsq			= 0;
	double rsq			= 0;

	const auto start{ std::chrono::steady_clock::now()};
	
	
	for (uint32_t ii = 0; ii < m_Particle.size(); ii++)
	{
		count++;
		for (uint32_t jj = 0; jj < m_Particle.size(); jj++)
		{
			if (ii != jj )
			{
				xT = m_Particle[jj].rx;
				yT = m_Particle[jj].ry;
				zT = m_Particle[jj].rz;
		
				xP = m_Particle[ii].rx;
				yP = m_Particle[ii].ry;
				zP = m_Particle[ii].rz;

				dsq = pow((xP - xT), 2) + pow((yP - yT), 2) + pow((zP - zT), 2);
				rsq = pow((m_Particle[ii].radius+m_Particle[jj].radius),2);
				if (dsq < rsq)
				{
					colCount++;
					mout << "Collision From:" << ii << " To:" << jj << ende;
				}
			}
		}
		if (count % 1000 == 0)
			std::cout << "At:" << count << " ColCount:" << colCount << std::endl;
	}	
	const auto end{ std::chrono::steady_clock::now() };
	const std::chrono::duration<double> elapsed_seconds{ end - start };
	std::cout << "Collison Verification:" 
		<< colCount << " Of :" << count 
		<< " Particles," 
		<< " Colocated:" << coLocCount 
		<< " SideLen:" << m_SideLength
		<< " Radius:" << radius  
		<< " Duration:" << elapsed_seconds.count() << " s" << std::endl;

	mout << "Collisons Verification:"
		<< colCount << " Of :" << count
		<< " Particles,"
		<< " Colocated:" << coLocCount
		<< " SideLen:" << m_SideLength
		<< " Radius:" << radius
		<< " Duration:" << elapsed_seconds.count() << " s" << ende;

	return colCount;
}