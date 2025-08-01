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
void GenResourceVertexParticle::BuildCubeBoundary(size_t num, benchSetItem* bsi)
{
	float sepdist = 0.15f;
		m_Cdensity = bsi->cdens;
		m_NumParticles = bsi->tot;
		if (m_NumParticles == 1024)
			m_NumParticles;

		m_Radius = bsi->radius;
		m_Centerlen = m_Radius * sepdist + 2 * m_Radius;
		m_PinRow = static_cast<uint32_t>(floor(1.00 / m_Centerlen));
		//m_PInLayer		= static_cast<uint32_t>(pow(m_PinRow, 2));
		m_PInCell = (uint32_t)pow(m_PinRow, 3);

		if (m_PInCell > m_NumParticles)
			m_PInCell = m_NumParticles;

		m_ColArySize = m_PInCell+10;
		m_CInCell = std::ceil(static_cast<float>(m_PInCell) * m_Cdensity / 2.0f);
		m_SideLength = CalcSideLength();
		m_TotCell = m_NumParticles / m_PInCell;
		m_TotCollsions = std::ceil(static_cast<uint32_t>(m_TotCell * m_CInCell * 2.0));

		//m_Radius = CfgApp->m_PRadius;
		mout << "Number of particles:" << m_NumParticles << ende;
		mout << "Total Collisions:" << m_CInCell << ende;
		mout << "Total Particles in a cell:" << m_TotCell << ende;
		mout << "Side Length:" << m_SideLength << ende;
		mout << "Total Collsion Density:" << m_Cdensity << ende;
		mout << "Collsion Density per cell:" << m_CInCell << ende;
		std::string dirval = CfgApp->m_TestDir;


		sprintf(FileText, "%04dCollisionDataSet%dX%dX%d\0", (int)num,
			int(m_NumParticles), m_TotCollsions, m_SideLength);
		m_fileName = FileText;
		m_FullBinFile = dirval + "/" + m_fileName + ".bin";

		m_DataFile.open(m_FullBinFile, std::ios::binary);
		if (!m_DataFile.is_open())
		{
			std::string err = "Cannot create benchmarking data file::" + m_FullBinFile;
			throw std::runtime_error(err.c_str());
		}
		uint32_t sl = m_SideLength +1;
		Corner3Side(sl);
		Corner2Side(sl);
		Corner1Side(sl);
}

void GenResourceVertexParticle::DoCubeBoundary()
{
	GenBenchSet();
	for (uint32_t ii = 0; ii < m_BenchSet.size(); ii++)
	{
		BuildCubeBoundary(ii, &m_BenchSet[ii]);
		ProcessBoundaryTestA002(&m_BenchSet[ii]);
		mout << "For File:" << FileText << " Done!" << ende;
		mout << "Counted Particles:" << m_CountedParticles << ende;
		mout << "Counted Collisions:" << m_CountedCollisions << ende;
		mout << "Counted Sidelength:" << m_CountedSidelength << ende;
		CloseParticleData();
		WriteTstFile(ii, &m_BenchSet[ii]);
	}
		
}
void GenResourceVertexParticle::ProcessBoundaryTestA002(benchSetItem* bsi)
{

	m_CountedParticles = 0;
	m_CountedCollisions = 0;
	m_CountedSidelength = 0;


	uint32_t ret = 0;
	for (uint32_t zcell = 1; zcell < m_SideLength; zcell++)
		for (uint32_t ycell = 1; ycell < m_SideLength; ycell++)
			for (uint32_t xcell = 1; xcell < m_SideLength; xcell++)
			{
				ret = AddParticlePatternA002(xcell, ycell, zcell);
				if (m_CountedParticles >= m_NumParticles)
				{
					return;
				}

			}

	mout << "Counted Particles:" << m_CountedParticles << " Required Particles:" << m_NumParticles << ende;
	mout << "Counted Collisions:" << m_CountedCollisions << " Required Collisions:" << m_TotCollsions << ende;
}

void GenResourceVertexParticle::Corner3Side(uint32_t sl)
{
	pdata ppart;
	for (uint32_t layer = 0; layer <= sl;layer+= sl)
	{
		for (uint32_t row = 0; row <= sl; row += sl)
		{
			for (uint32_t col = 0; col <= sl; col += sl)
			{
				
				ppart = { 0 };
				ppart.rx = col + 1.0;
				ppart.ry = row + 1.0;
				ppart.rz = layer + 1.0;
				ppart.vx = col + 1.0;
				ppart.vy = row + 1.0;
				ppart.vz = layer + 1.0;
				ppart.radius = m_Radius;
				ppart.ptype = 1;
				m_CountedBoundaryParticles++;
				WriteBoundaryParticle(ppart);
			}
		}
	}
}
void GenResourceVertexParticle::WriteBoundaryParticle(pdata pd)
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
void GenResourceVertexParticle::Corner2Side(uint32_t sl)
{
	pdata ppart;

	/// #1
	for (uint32_t layer = 2; layer <= sl;layer++)
	{
		for (uint32_t row = 0; row <= sl; row+= sl)
		{
			for (uint32_t col = sl; col <= sl;col+= sl)
			{
				ppart = { 0 };
				ppart.rx = col + 1.0;
				ppart.ry = row + 1.0;
				ppart.rz = layer;
				ppart.vx = col + 1.0;
				ppart.vy = row + 1.0;
				ppart.vz = 0.0;
				ppart.radius = m_Radius;
				ppart.ptype = 1;
				m_CountedBoundaryParticles++;
				WriteBoundaryParticle(ppart);
				
			}
		}
	}
	/// #2
	for (uint32_t layer = 2; layer <= sl;layer++)
	{
		for (uint32_t row = 0; row <= sl; row+= sl)
		{
			for (uint32_t col = 1; col <= sl;col+= sl)
			{
				ppart = { 0 };
				ppart.rx = col;
				ppart.ry = row + 1.0;
				ppart.rz = layer;
				ppart.vx = col;
				ppart.vy = row + 1.0;
				ppart.vz = 0.0;
				ppart.radius = m_Radius;
				ppart.ptype = 1;
				m_CountedBoundaryParticles++;
				WriteBoundaryParticle(ppart);
				
			}
		}
	}
	/// #3
	for (uint32_t layer = 0; layer <= sl;layer+= sl)
	{
		for (uint32_t row = 0; row <= sl; row+= sl)
		{
			for (uint32_t col = 2; col <= sl;col++)
			{
				ppart = { 0 };
				ppart.rx = col;
				ppart.ry = row + 1.0;
				ppart.rz = layer+1.0;
				ppart.vx = 0.0;
				ppart.vy = row + 1.0;
				ppart.vz = layer+1.0;
				ppart.radius = m_Radius;
				ppart.ptype = 1;
				m_CountedBoundaryParticles++;
				WriteBoundaryParticle(ppart);
				
			}
		}
	}
	/// #4
	for (uint32_t layer = 0; layer <= sl;layer+= sl)
	{
		for (uint32_t row = 2; row <= sl; row++)
		{
			for (uint32_t col = 0; col <= sl;col+=sl)
			{
				ppart = { 0 };
				ppart.rx = col+1;
				ppart.ry = row;
				ppart.rz = layer+1.0;
				ppart.vx = col+1;
				ppart.vy = 0.0;
				ppart.vz = layer+1.0;
				ppart.radius = m_Radius;
				ppart.ptype = 1;
				m_CountedBoundaryParticles++;
				WriteBoundaryParticle(ppart);
				
			}
		}
	}


}
void GenResourceVertexParticle::Corner1Side(uint32_t sl)
{
	pdata ppart;

	/// #1
	for (uint32_t layer = 2; layer <= sl;layer++)
	{
		for (uint32_t row = 0; row <= sl; row+= sl)
		{
			for (uint32_t col = 2; col <= sl;col++)
			{
				ppart = { 0 };
				ppart.rx = col;
				ppart.ry = row + 1.0;
				ppart.rz = layer;
				ppart.vx = 0.0;
				ppart.vy = row + 1.0;
				ppart.vz = 0.0;
				ppart.radius = m_Radius;
				ppart.ptype = 1;
				m_CountedBoundaryParticles++;
				WriteBoundaryParticle(ppart);
				
			}
		}
	}

	/// #2
	for (uint32_t layer = 0; layer <= sl;layer+=sl)
	{
		for (uint32_t row = 2; row <= sl; row++)
		{
			for (uint32_t col = 2; col <= sl;col++)
			{
				ppart = { 0 };
				ppart.rx = col;
				ppart.ry = row ;
				ppart.rz = layer+1.0;
				ppart.vx = 0.0;
				ppart.vy = 0.0;
				ppart.vz = layer+1.0;
				ppart.radius = m_Radius;
				ppart.ptype = 1;
				m_CountedBoundaryParticles++;
				WriteBoundaryParticle(ppart);
				
			}
		}
	}

	/// #3
	for (uint32_t layer = 2; layer <= sl;layer++)
	{
		for (uint32_t row = 2; row <= sl; row++)
		{
			for (uint32_t col = 0; col <= sl;col+=sl)
			{
				ppart = { 0 };
				ppart.rx = col+1.0;
				ppart.ry = row ;
				ppart.rz = layer;
				ppart.vx = col+1;
				ppart.vy = 0.0;
				ppart.vz = 0.0;
				ppart.radius = m_Radius;
				ppart.ptype = 1;
				m_CountedBoundaryParticles++;
				WriteBoundaryParticle(ppart);
				
			}
		}
	}


}


