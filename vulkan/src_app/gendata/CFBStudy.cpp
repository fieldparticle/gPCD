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



#if 0
void GenResourceVertexParticle::OpenParticleDataA003()
{



	m_SideLengths.clear();	
	ConfigObj* cfg = (ConfigObj*)CfgApp;
	m_Cdensity = cfg->m_CDensity;
	m_Radius = cfg->m_Radius;
	float sepdist = 0.15f;
	m_Centerlen = cfg->m_Radius * sepdist + 2 * cfg->m_Radius;
	m_PinRow = static_cast<uint32_t>(floor(1.00 / m_Centerlen));
	m_PInCell = (uint32_t)pow(m_PinRow, 3);
	///FIXTHIS
	m_ColArySize = m_PInCell;
	m_SideLength = cfg->m_startSideLength;
	m_NumParticles = 117649;
	m_CInCell = std::ceil(static_cast<float>(m_PInCell) * m_Cdensity / 2.0f);
	m_SideLength = CalcSideLength();
	m_SideLengths.push_back(m_SideLength);
	benchSetItem bsi;
	bsi.wx = 1;
	bsi.wy = 1;
	bsi.wz = 1;
	bsi.dx = m_NumParticles + 1;
	bsi.dy = 1;
	bsi.dz = 1;
	bsi.vx = 0.0;
	bsi.vy = 0.0;
	bsi.vz = 0.0;
	bsi.px = 0.0;
	bsi.py = 0.0;
	bsi.pz = 0.0;
	bsi.tot = m_NumParticles;
	bsi.sel = "s";
	bsi.cols = m_PInCell;
	bsi.collision = 0;
	bsi.cdens = 0.5;
	bsi.radius = m_Radius;
	m_BenchSet.push_back(bsi);
	while((m_SideLength=GetNextSideLength())!=0)
	{

		benchSetItem bsi;
		bsi.wx = 1;
		bsi.wy = 1;
		bsi.wz = 1;
		bsi.dx = m_NumParticles+1;
		bsi.dy = 1;
		bsi.dz = 1;
		bsi.vx = 0.0;
		bsi.vy = 0.0;
		bsi.vz = 0.0;
		bsi.px = 0.0;
		bsi.py = 0.0;
		bsi.pz = 0.0;
		bsi.tot = m_NumParticles;
		bsi.sel = "s";
		bsi.cols = m_PInCell;
		bsi.collision = 0;
		bsi.cdens = 0.5;
		bsi.radius = m_Radius;
		m_BenchSet.push_back(bsi);
		
	}

	ProcessSet();

}
#endif
void GenResourceVertexParticle::OpenParticleDataA003()
{

	ConfigObj* cfg = (ConfigObj*)CfgApp;
	std::string dirval = cfg->m_TestDir;
	sprintf(FileText, "CFBStudyEntries");

	m_fileName = FileText;
	std::string FullBinFile = dirval + "/" + m_fileName + ".csv";
	
	
	m_CFBDataFile.open(FullBinFile, std::ios::binary);
	if (!m_CFBDataFile.is_open())
	{
		std::string err = "Cannot open benchmarking data file::" + m_FullBinFile;
		throw std::runtime_error(err.c_str());
	}
	m_CFBDataFile << "wx"
				<< "," << "wy"
				<< "," << "wz"
				<< "," << "dx"
				<< "," << "dy"
				<< "," << "dz"
				<< "," << "ptot"
				<< "," << "ColArySize"
				<< "," << "NumColl"
				<< "," << "cdens"
				<< "," << "radius"
				<< "," << "sidelen"
				<< std::endl;
				


	m_SideLengths.clear();	
	m_Cdensity = m_BenchSet[0].cdens;		
	m_NumParticles = m_BenchSet[0].tot;
	m_Radius = m_BenchSet[0].radius+0.01;
	m_BenchSet.clear();

	while((m_SideLength=GetNextSideLength())!=0)
	{
	
		float sepdist = 0.15f;
		//m_Centerlen = m_Radius * sepdist + 2 * m_Radius;
		//m_PinRow = static_cast<uint32_t>(floor(1.00 / m_Centerlen));
		//m_PInCell = (uint32_t)pow(m_PinRow, 3);
		m_ColArySize = m_PInCell;
		m_CInCell = std::ceil(static_cast<float>(m_PInCell) * m_Cdensity / 2.0f);
		m_SideLength = CalcSideLength();
		m_SideLengths.push_back(m_SideLength);

		benchSetItem bsi;
		bsi.wx = 1;
		bsi.wy = 1;
		bsi.wz = 1;
		bsi.dx = m_NumParticles + 1;
		bsi.dy = 1;
		bsi.dz = 1;
		bsi.vx = 0.0;
		bsi.vy = 0.0;
		bsi.vz = 0.0;
		bsi.px = 0.0;
		bsi.py = 0.0;
		bsi.pz = 0.0;
		bsi.tot = m_NumParticles;
		bsi.sel = "s";
		bsi.cols = m_PInCell;
		bsi.collision = 0;
		bsi.cdens = 0.5;
		bsi.radius = m_Radius;
		m_BenchSet.push_back(bsi);
		WriteEntry(&bsi);
	}

	ProcessSet();

}

uint32_t GenResourceVertexParticle::GetNextSideLength()
{
	
	float radius = m_Radius;
	uint32_t sideLen = m_SideLength;
	float sepdist = 0.15f;
	for (uint32_t ii = 0; ii < 100; ii++)
	{
		radius = radius - 0.01;
		
		m_Centerlen = radius * sepdist + 2 * radius;
		m_PinRow = static_cast<uint32_t>(floor(1.00 / m_Centerlen));
		m_PInCell = (uint32_t)pow(m_PinRow, 3);
		sideLen = CalcSideLength();
		if (sideLen != m_SideLength)
		{
			m_SideLength = sideLen;
			m_Radius = radius;
			return m_SideLength;

		}

	}
	m_CFBDataFile.flush();
	m_CFBDataFile.close();
	return 0;

}
uint32_t GenResourceVertexParticle::CalcSideLength()
{
	uint32_t ii = 0;
	while (1)
	{
		ii++;
		if (ii > 1000)
			return 0;
		if (ii * ii * ii * m_PInCell >= m_NumParticles)
		{
			return ii+1;
		}
	}
}

void GenResourceVertexParticle::WriteEntry(benchSetItem* bsi)
{


	m_CFBDataFile << bsi->wx
				<< "," << bsi->wy
				<< "," << bsi->wz
				<< "," << bsi->dx
				<< "," << bsi->dy
				<< "," << bsi->dz
				<< "," << bsi->tot
				<< "," << bsi->cols
				<< "," << bsi->collision
				<< "," << bsi->cdens
				<< "," << bsi->radius
				<< "," << m_SideLength
				<< std::endl;
				


}