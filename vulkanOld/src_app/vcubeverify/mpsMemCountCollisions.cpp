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

#include <thread>
#include "VulkanObj/pdata.hpp"
uint32_t NumParticles;
float radius = 0;
uint32_t ColTask(uint32_t thnum, uint32_t Frm, uint32_t To, std::vector<pdata>& m_Particle);


uint32_t coLocCount = 0;
uint32_t missed_link_count = 0;
uint32_t* colary;
uint32_t CountCollisions(bool CountCollisions)
{
	//pdata* m_Particle;
	uint32_t readcount = 0;

	mout.Init("mpsverify.log", "MPS");
#if 0
	ConfigObj* configCube = new ConfigObj;
	configCube->Create("mps.cfg");
	mout << "Particle Count::" << configCube->m_partcount << ende;
	mout << "Data File:" << configCube->m_DataFile << ende;
#endif
	
	NumParticles = cfg->m_partcount;
	std::vector<pdata> m_Particle;
	
	std::string dataFile = cfg->m_TestDir + "/" + cfg->m_TestName;
	std::ifstream input_file(dataFile, std::ios::binary);
	
	if (!input_file.is_open())
	{
		std::string err = "Unable to open particle data file:" + cfg->m_DataFile;
		throw std::runtime_error(err.c_str());
	}
	

	while (input_file.peek() != EOF)
	{
		pdata part_pos;
		input_file.read((char*)&part_pos, sizeof(part_pos));
		readcount++;
		

		m_Particle.push_back(part_pos);
		
#if 0
		mout << "Particle #" << (float)part_pos.pnum << ende;
		mout << "rx: " << (float)part_pos.rx << ende;
		mout << "ry: " << (float)part_pos.ry << ende;
		mout << "rz: " << (float)part_pos.rz << ende;
		mout << ende;
#endif
		radius = (float)part_pos.radius;

		
	}
	
	mout << "Number of particles Counted:" << readcount << " Number particles expected:" << NumParticles  << ende;
	if (readcount != NumParticles)
	{
		mout << "ERROR: Number of particles Counted do not MATCH:" << ende;
		return 1;
	
	}
	if (CountCollisions == true)
	{

		const auto start{ std::chrono::steady_clock::now() };
		uint32_t numThreads = 1;
		colary = new uint32_t[numThreads];
		memset(colary, 0, sizeof(uint32_t) * numThreads);
		uint32_t colcount = ColTask(0, 0, readcount, m_Particle);
		const auto end{ std::chrono::steady_clock::now() };
		const std::chrono::duration<double> elapsed_seconds{ end - start };
		if (colcount != cfg->m_colcount)
		{

			mout << "ERROR: Number of collisions Counted do not MATCH:" << ende;
			mout << "Expected cols:" << cfg->m_colcount << " Counted Cols:" << colcount << ende;
			return 1;
		}
		std::cout << "Collisons:"
			<< colcount << " Of :" << readcount
			<< " Particles,"
			<< " Colocated:" << coLocCount
			<< " Radius:" << radius
			<< " Duration:" << elapsed_seconds.count() << " s" << std::endl;

		mout << "Expected Collisons:" << cfg->m_colcount
			<< " Counted Collisions:"  
			<< colcount << " Of :" << readcount
			<< " Particles,"
			<< " Colocated:" << coLocCount
			<< " Radius:" << radius
			<< " Duration:" << elapsed_seconds.count() << " s" << ende;

		std::ostringstream  flnmtxt;
		flnmtxt << "J:/FPIBGDATA/perfdataPQB" << readcount << "x" << colcount << ".csv" << std::ends;
		std::string filename = flnmtxt.str().c_str();
		{
			std::ofstream ostrm(filename);
			ostrm << "Particles,collisoncount,colocated" << std::endl;
			ostrm << readcount << "," << colcount << "," << coLocCount << std::endl;
		}
	}
	return 0;
}
uint32_t ColTask(uint32_t thnum, uint32_t Frm, uint32_t To, std::vector<pdata> &m_Particle)
{
	
	double xT = 0;
	double yT = 0;
	double zT = 0;
	double xP = 0;
	double yP = 0;
	double zP = 0;
	double dsq = 0;
	double rsq = 0;
	uint32_t colCount = 0;
	
	
	
	for (uint32_t ii = Frm; ii < To; ii++)
	{
		const auto start{ std::chrono::steady_clock::now() };

		xT = m_Particle[ii].rx;
		yT = m_Particle[ii].ry;
		zT = m_Particle[ii].rz;
		
		if (ii == 1)
			return 0;
		for (uint32_t jj = 0; jj < To; jj++)
		{

			if (ii != jj)
			{
				xP = m_Particle[jj].rx;
				yP = m_Particle[jj].ry;
				zP = m_Particle[jj].rz;

				dsq = pow((xP - xT), 2) + pow((yP - yT), 2) + pow((zP - zT), 2);
				rsq = m_Particle[jj].radius+ m_Particle[ii].radius;
				rsq = rsq * rsq;
				if (abs((dsq - rsq)) < 0.00001)
					coLocCount++;
				if (dsq < rsq)
					colCount++;

				
				
			}

			
			if (jj % (To-1) == 0 && jj != 0)
			{
				std::cout << "For::" << ii << " At:" << jj << " ColCount:" << colCount << std::endl;
				const auto end{ std::chrono::steady_clock::now() };
				const std::chrono::duration<double> elapsed_seconds{ end - start };
				double timepertest = elapsed_seconds.count()/(To-1);

				mout << "jj:" << jj << " ii:" << ii << " tpt:" << timepertest << " duration:" << elapsed_seconds.count() << " s" << ende;
			}

		}
		
	}
	return colCount;

}