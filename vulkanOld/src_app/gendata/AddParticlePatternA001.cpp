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

uint32_t GenResourceVertexParticle::AddParticlePatternA001(uint32_t xx, uint32_t yy, uint32_t zz)
{
	uint32_t pcountInCell =0;
	uint32_t ccountInCell=0;
	uint32_t halt;
	
	if (m_CountedParticles > 500)
	{	
		halt = 500;
	}
	
	pcountInCell++;
	pdata part;
	// 1 and 2
	// If particles in cell are less than required do
	if(pcountInCell<=m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && (m_CountedCollisions+2)  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 1.25 + xx;
			part.ry = 1.15 + yy;
			part.rz = 1.0 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		
		}
		else
		{
			
			pcountInCell++;
			part.rx = 1.25 + xx;
			part.ry = 1.0 + yy;
			part.rz = 1.0 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
			WriteParticle(part);
			part = { 0 };
			
			pcountInCell++;
			part.rx = 1.25 + xx;
			part.ry = 1.25 + yy;
			part.rz = 1.0 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			WriteParticle(part);
			if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return.
	if (pcountInCell == m_PInCell )
		return 1;
	//----------------------------- 3 - 4 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 0.75 + xx;
			part.ry = 1.15 + yy;
			part.rz = 1.0 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 0.75 + xx;
			part.ry = 1.0 + yy;
			part.rz = 1.0 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		WriteParticle(part);
		part = { 0 };
		
		pcountInCell++;
		part.rx = 0.75 + xx;
		part.ry = 1.25 + yy;
		part.rz = 1.0 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;


	//----------------------------- 5 - 6 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 1.15 + xx;
			part.ry = 0.75 + yy;
			part.rz = 1.0 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 1.0 + xx;
			part.ry = 0.75 + yy;
			part.rz = 1.0 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		
		pcountInCell++;
		part.rx = 1.25 + xx;
		part.ry = 0.75 + yy;
		part.rz = 1.0 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;

	//----------------------------- 7 - 8 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 1.0 + xx;
			part.ry = 1.4 + yy;
			part.rz = 1.0 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 1.0 + xx;
			part.ry = 1.25 + yy;
			part.rz = 1.0 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		
		pcountInCell++;
		part.rx = 1.0 + xx;
		part.ry = 1.5 + yy;
		part.rz = 1.0 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;


	//----------------------------- 9 - 10 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 1.20 + xx;
			part.ry = 0.75 + yy;
			part.rz = 1.25 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 0.75 + xx;
			part.ry = 0.75 + yy;
			part.rz = 1.0 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		pcountInCell++;
		part.rx = 1.25 + xx;
		part.ry = 0.75 + yy;
		part.rz = 1.25 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;

	//----------------------------- 11 - 12 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 1.25 + xx;
			part.ry = 1.15 + yy;
			part.rz = 1.25 + zz;
			part.pnum = m_CountedParticles;
			part.radius = m_Radius;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 1.25 + xx;
			part.ry = 1.0 + yy;
			part.rz = 1.25 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		
		pcountInCell++;
		part.rx = 1.25 + xx;
		part.ry = 1.25 + yy;
		part.rz = 1.25 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;


	//----------------------------- 13 - 14 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 0.75 + xx;
			part.ry = 1.15 + yy;
			part.rz = 1.25 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 0.75 + xx;
			part.ry = 1.0 + yy;
			part.rz = 1.25 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		
		pcountInCell++;
		part.rx = 0.75 + xx;
		part.ry = 1.25 + yy;
		part.rz = 1.25 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;

	//----------------------------- 15 - 16 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 1.0 + xx;
			part.ry = 1.15 + yy;
			part.rz = 1.15 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 1.0 + xx;
			part.ry = 1.25 + yy;
			part.rz = 1.25 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		pcountInCell++;
		part.rx = 1.0 + xx;
		part.ry = 1.0 + yy;
		part.rz = 1.25 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;

	//----------------------------- 17 - 18 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 0.75 + xx;
			part.ry = 0.65 + yy;
			part.rz = 1.25 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 0.98 + xx;
			part.ry = 0.75 + yy;
			part.rz = 1.25 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		
		pcountInCell++;
		part.rx = 0.75 + xx;
		part.ry = 0.75 + yy;
		part.rz = 1.25 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;

	//----------------------------- 19 - 20 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 1.25 + xx;
			part.ry = 1.35 + yy;
			part.rz = 0.75 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 1.25 + xx;
			part.ry = 1.0 + yy;
			part.rz = 0.75 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		
		pcountInCell++;
		part.rx = 1.25 + xx;
		part.ry = 1.25 + yy;
		part.rz = 0.75 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;


	//----------------------------- 21 - 22 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 0.65 + xx;
			part.ry = 1.15 + yy;
			part.rz = 0.75 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 0.65 + xx;
			part.ry = 1.0 + yy;
			part.rz = 0.75 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		pcountInCell++;
		part.rx = 0.65 + xx;
		part.ry = 1.25 + yy;
		part.rz = 0.75 + zz;
		part.pnum = m_CountedParticles;
		part.radius = m_Radius;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;

	//----------------------------- 23 - 24 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 1.0 + xx;
			part.ry = 0.95 + yy;
			part.rz = 0.90 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 1.0 + xx;
			part.ry = 0.725 + yy;
			part.rz = 0.80 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		pcountInCell++;
		part.rx = 1.0 + xx;
		part.ry = 1.00 + yy;
		part.rz = 1.0 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;

	//----------------------------- 25 - 26 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 0.75 + xx;
			part.ry = 0.65 + yy;
			part.rz = 0.75 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 1.25 + xx;
			part.ry = 0.75 + yy;
			part.rz = 0.75 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		
		pcountInCell++;
		part.rx = 0.75 + xx;
		part.ry = 0.75 + yy;
		part.rz = 0.75 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;

	//----------------------------- 27 - 28 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 1.45 + xx;
			part.ry = 1.45 + yy;
			part.rz = 1.4 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 0.9 + xx;
			part.ry = 1.1 + yy;
			part.rz = 1.4 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		
		pcountInCell++;
		part.rx = 1.5 + xx;
		part.ry = 1.5 + yy;
		part.rz = 1.5 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell == m_PInCell )
		return 1;;

	//----------------------------- 29 - 30 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if(ccountInCell < m_CInCell && m_CountedCollisions+2  <= m_TotCollsions)
		{
			
			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions+=2;
			part.rx = 0.85 + xx;
			part.ry = 1.15 + yy;
			part.rz = 0.65 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			
			pcountInCell++;
			part.rx = 1.1 + xx;
			part.ry = 0.9 + yy;
			part.rz = 0.65 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		pcountInCell++;
		part.rx = 0.9 + xx;
		part.ry = 1.2 + yy;
		part.rz = 0.65 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell >= m_PInCell )
		return 1;

	//----------------------------- 31 - 32 -------------------------------
	// If particles in cell are less than required do
	if (pcountInCell <= m_PInCell)
	{
		//If collision per cell is are less than required do
		if (ccountInCell < m_CInCell && m_CountedCollisions + 2 <= m_TotCollsions)
		{

			pcountInCell++;
			ccountInCell+=2;
			m_CountedCollisions += 2;
			part.rx = 1.5 + xx;
			part.ry = 1.15 + yy;
			part.rz = 0.75 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles == m_NumParticles)
			{
				m_CountedCollisions -= 1;
				return 0;
			}
		}
		else
		{
			pcountInCell++;
			part.rx = 1.5 + xx;
			part.ry = 1.0 + yy;
			part.rz = 1.0 + zz;
			part.radius = m_Radius;
			part.pnum = m_CountedParticles;
			if (++m_CountedParticles > m_NumParticles) return 0;
		}
		WriteParticle(part);
		part = { 0 };
		pcountInCell++;
		part.rx = 1.5 + xx;
		part.ry = 1.1 + yy;
		part.rz = 0.65 + zz;
		part.radius = m_Radius;
		part.pnum = m_CountedParticles;
		WriteParticle(part);
		if (++m_CountedParticles > m_NumParticles) return 0;
	}
	// If totals met return 0;.
	if (pcountInCell >= m_PInCell )
		return 1;

	
	
	return 1;

}
