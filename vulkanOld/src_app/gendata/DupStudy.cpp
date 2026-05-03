/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/ResourceVertex.cpp $
% $Id: ResourceVertex.cpp 28 2023-05-03 19:30:42Z jb $
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

#include "gendata/GenResourceVertexParticle.hpp"

void GenResourceVertexParticle::ProcessDUP()
{
	
	//m_BenchSet.size()
	for (uint32_t ii = 0; ii < m_BenchSet.size(); ii++)
	{
		m_CountedBoundaryParticles = 0;
		m_NumParticles = m_BenchSet[ii].tot;
		m_TotCollsions = m_BenchSet[ii].collision;
		m_Radius =  m_BenchSet[ii].radius;
		for(uint32_t jj =0; jj < m_NumParticles;jj+=4)
			m_SideLength+=3;

		m_CountedCollisions = m_TotCollsions;
		sprintf(FileText, "%04dCollisionDataSet%dX%dX%d\0", (int)ii,
			int(m_NumParticles), m_TotCollsions, m_SideLength);

		m_fileName = FileText;
		
		std::string dirval = CfgApp->m_TestDir;
		m_FullBinFile = dirval + "/" + m_fileName + ".bin";
	
		mout << "Processing:" << m_FullBinFile << ende;
		std::cout << "Processing:" << m_FullBinFile << std::endl;
		m_DataFile.open(m_FullBinFile, std::ios::binary);
		if (!m_DataFile.is_open())
		{
			std::string err = "Cannot create benchmarking data file::" + m_FullBinFile;
			throw std::runtime_error(err.c_str());
		}

		ProcessTestDUP(&m_BenchSet[ii]);
		 
		
		mout << "For File:" << FileText << " Done!" << ende;
		mout << "Counted Particles:" << m_CountedParticles << ende;
		mout << "Counted Collisions:" << m_CountedCollisions << ende;
		mout << "Counted Sidelength:" << m_CountedSidelength << ende;
		CloseParticleData();
		m_CountedCollisions = CountCollisions();
		m_TestCollisions = false;

		m_ColArySize  = m_BenchSet[ii].cols;
		m_PInCell = 3;
		WriteTstFile(ii,&m_BenchSet[ii]);
		
	}

}
void GenResourceVertexParticle::ProcessTestDUP(benchSetItem* bsi)
{

	m_CountedParticles = 0;
	m_CountedCollisions = 0;
	m_CountedSidelength = 0;

	uint32_t ycell=0;
	uint32_t xcell=0;
	uint32_t zcell=0;

	uint32_t ret = 0;
	for (uint32_t counter = 0; counter <= (m_SideLength-2)/2; counter++)
	{
		xcell;
		ycell;
		zcell;
		ret = ProcessDUPPattern(xcell, ycell,zcell);

		xcell++;
		ycell;
		zcell;
		ret = ProcessDUPPattern(xcell, ycell,zcell);
		
		xcell;
		ycell++;
		ret = ProcessDUPPattern(xcell, ycell,zcell);
		
		xcell--;
		ycell;
		zcell;
		ret = ProcessDUPPattern(xcell, ycell,zcell);
		

		//ret = ProcessDUPPattern(xcell, ycell,zcell);
		zcell++;	
		m_CountedSidelength++;
		xcell = 0;
		ycell = 0;
		
	}
	mout << "Counted Particles:" << m_CountedParticles << " Required Particles:" << m_NumParticles << ende;
	mout << "Counted Collisions:" << m_CountedCollisions << " Required Collisions:" << m_TotCollsions << ende;
}
uint32_t GenResourceVertexParticle::ProcessDUPPattern(uint32_t xcell, uint32_t ycell, uint32_t zcell)
{

	PInCellCount = 0;
	CInCellCount = 0;
	bool wflg = true;
	pdata ppart;
	ppart = { 0 };
	//------------------ If the current total number of particles is less than
	// the specified number of particles then add this particle
		if(m_CountedParticles > m_NumParticles)
		{
			m_CountedParticles--;
			return 0;
		}
		ppart.rx = 1.5+xcell;
		ppart.ry = 1.5+ycell;
		ppart.rz = 1.5+zcell;
		ppart.radius = m_Radius;
		
		ppart.pnum = m_CountedParticles++;
		if(m_CountedParticles > m_NumParticles)
		{
			m_CountedParticles--;
			return 0;
		}
		m_CountedCollisions++;
		wflg = !wflg;
		WriteDUPParticle(ppart);
		
		PInCellCount++;
		ppart = { 0 };
		ppart.rx = 1.2+xcell;
		ppart.ry = 1.5+ycell;
		ppart.rz = 1.5+zcell;
		ppart.radius = m_Radius;
		
		ppart.pnum = m_CountedParticles++;
		if(m_CountedParticles > m_NumParticles)
		{
			m_CountedParticles--;
			return 0;
		}
		m_CountedCollisions++;
		wflg = !wflg;
		PInCellCount++;
		WriteDUPParticle(ppart);
		
		ppart = { 0 };
		ppart.rx = 1.8+xcell;
		ppart.ry = 1.5+ycell;
		ppart.rz = 1.5+zcell;
		ppart.radius = m_Radius;
		
		ppart.pnum = m_CountedParticles++;
		if(m_CountedParticles > m_NumParticles)
			return 0 ;
		m_CountedCollisions++;
		wflg = !wflg;
		WriteDUPParticle(ppart);
		PInCellCount++;
		

	return 0;
}
void GenResourceVertexParticle::WriteDUPParticle(pdata pd)
{
	pd.ptype = 1;
	m_DataFile.write((char*)&pd, sizeof(pdata));
	if (m_DataFile.bad())
	{
		std::string err = "Particle bin File write Error::";
		throw std::runtime_error(err.c_str());
	}
	m_DataFile.flush();
}