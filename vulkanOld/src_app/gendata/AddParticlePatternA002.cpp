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
void GenResourceVertexParticle::OpenParticleDataA002(size_t num, benchSetItem* bsi)
{
	float sepdist = 0.15f;
	m_Cdensity		= bsi->cdens;
	m_NumParticles	= bsi->tot;
	if (m_NumParticles == 1024)
		m_NumParticles;
		
	m_Radius		= bsi->radius;
	m_Centerlen		= m_Radius* sepdist + 2*m_Radius;
	m_PinRow		= static_cast<uint32_t>(floor(1.00 / m_Centerlen));
	//m_PInLayer		= static_cast<uint32_t>(pow(m_PinRow, 2));
	m_PInCell		= (uint32_t)pow(m_PinRow,3);

	if (m_PInCell > m_NumParticles)
		m_PInCell = m_NumParticles;
	m_ColArySize = m_PInCell+10;

	m_CInCell		= std::ceil(static_cast<float>(m_PInCell) * m_Cdensity/2.0f);
	m_SideLength	= CalcSideLength();

	m_TotCell = m_NumParticles / m_PInCell;
	m_TotCollsions = std::ceil(static_cast<uint32_t>(m_TotCell *m_CInCell*2.0 ));

	//m_Radius = CfgApp->m_PRadius;
	mout << "Number of particles:" << m_NumParticles << ende;
	mout << "Total Collisions:" << m_CInCell << ende;
	mout << "Total Particles in a cell:" << m_TotCell << ende;
	mout << "Side Length:" << m_SideLength << ende;
	mout << "Total Collsion Density:" << m_Cdensity << ende;
	mout << "Collsion Density per cell:" << m_CInCell << ende;
	std::string dirval = CfgApp->m_TestDir;

	m_PartHold.resize(m_NumParticles);
	m_Back = m_NumParticles-1;
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
}
void GenResourceVertexParticle::ProcessTestA002(benchSetItem* bsi)
{

	m_CountedParticles = 0;
	m_CountedCollisions = 0;
	m_CountedSidelength = 0;


	uint32_t ret = 0;
	for (uint32_t zcell = 0; zcell < m_SideLength - 1; zcell++)
		for (uint32_t ycell = 0; ycell < m_SideLength - 1; ycell++)
			for (uint32_t xcell = 0; xcell < m_SideLength - 1; xcell++)
			{



				ret = AddParticlePatternA002(xcell, ycell, zcell);
				if (m_CountedParticles >= m_NumParticles)
				{
					SaveParticles();
					return;
					
				}

			}
	SaveParticles();
	mout << "Counted Particles:" << m_CountedParticles << " Required Particles:" << m_NumParticles << ende;
	mout << "Counted Collisions:" << m_CountedCollisions << " Required Collisions:" << m_TotCollsions << ende;
}

uint32_t GenResourceVertexParticle::AddParticlePatternA002(uint32_t xcell, 
															uint32_t ycell, 
															uint32_t zcell)
{
	PInCellCount = 0;
	CInCellCount = 0;
	bool wflg = true;
	pdata ppart;
	ppart = { 0 };
	for (size_t zlayers = 0; zlayers < m_PinRow; zlayers++)
	{
		
		for (size_t ycols = 0; ycols < m_PinRow; ycols++)
		{

			for (size_t xrows = 0; xrows < m_PinRow; xrows++)
			{
				//------------------ If the current total number of particles is less than
				// the specified number of particles then add this particle
				if (m_CountedParticles <= m_NumParticles )
				{
					if (PInCellCount <= m_PInCell)
					{
						if (CInCellCount < m_CInCell && (xrows % 2) != 0 && m_CountedCollisions < m_TotCollsions)
						{
							CInCellCount++;
							m_CountedCollisions+=2;
							ppart.rx = 0.5 + m_Radius/2 + m_Centerlen * xrows + xcell;
						}
						else
							ppart.rx = 0.5 + m_Radius + 0.15 * m_Radius + m_Centerlen * xrows+xcell;
						ppart.ry = 0.5 + m_Radius + 0.15 * m_Radius + m_Centerlen * ycols+ycell;
						ppart.rz = 0.5 + m_Radius + 0.15 * m_Radius + m_Centerlen * zlayers+zcell;
						ppart.radius = m_Radius;
						ppart.pnum = m_CountedParticles++;
						wflg = !wflg;
						WriteParticle(ppart,wflg);
						ppart = { 0 };
						PInCellCount++;
					}
					
				}
				
			}

		}
	}
	
	return 0;
}
