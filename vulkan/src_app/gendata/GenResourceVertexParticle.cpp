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
#define VMA_IMPLEMENTATION
#include "VulkanObj/VulkanApp.hpp"

#include "gendata/GenResourceVertexParticle.hpp"

void GenResourceVertexParticle::DoMotionStudy()
{
#if 0
	bool wflg=true;
	ConfigObj* cfg = (ConfigObj*)CfgApp;
	uint32_t num = 1;
	std::string direction = {};
	std::string dirval = CfgApp->m_TestDir;

	//Boundary only
	if (cfg->m_TestName.find("BX") != std::string::npos)
		direction = "BX";
	if (cfg->m_TestName.find("BY") != std::string::npos)
		direction = "BY";
	if (cfg->m_TestName.find("BZ") != std::string::npos)
		direction = "BZ";
	// X direction
	if (cfg->m_TestName.find("PX") != std::string::npos)
		direction = "PX";
	// Y direction
	if (cfg->m_TestName.find("PY") != std::string::npos)
		direction = "PY";
	// Z direction
	if (cfg->m_TestName.find("PZ") != std::string::npos)
		direction = "PZ";
	// 3D direction
	if (cfg->m_TestName.find("XYZ") != std::string::npos)
		direction = "XYZ";

	sprintf(FileText, "%sCollisionDataSet\0", direction.c_str());
	m_fileName = FileText;
	m_FullBinFile = dirval + "/" + m_fileName + ".bin";
	m_SideLength = CalcSideLength();
	pdata part;
	m_DataFile.open(m_FullBinFile, std::ios::binary);
	if (!m_DataFile.is_open())
	{
		std::string err = "Cannot open benchmarking data file::" + m_FullBinFile;
		throw std::runtime_error(err.c_str());
	}
	for (uint32_t ii = 0; ii < m_BenchSet.size(); ii++)
	{
		part.rx = m_BenchSet[ii].px;
		part.ry = m_BenchSet[ii].py;
		part.rz = m_BenchSet[ii].pz;
		part.vx = m_BenchSet[ii].vx;
		part.vy = m_BenchSet[ii].vy;
		part.vz = m_BenchSet[ii].vz;
		part.radius = m_BenchSet[ii].radius;
		m_Radius = m_BenchSet[ii].radius;
		part.pnum = ii;
		wflg = !wflg;
		WriteParticle(part,wflg);
	}
	SaveParticles();
	CloseParticleData();

	WriteTstFile(0, &m_BenchSet[0]);
#endif
}
void GenResourceVertexParticle::ProcessSet()
{
	
	//m_BenchSet.size()
	for (uint32_t ii = 0; ii < m_BenchSet.size(); ii++)
	{
		OpenParticleDataA002(ii, &m_BenchSet[ii]);
		ProcessTestA002(&m_BenchSet[ii]);
		mout << "For File:" << FileText << " Done!" << ende;
		mout << "Counted Particles:" << m_CountedParticles << ende;
		mout << "Counted Collisions:" << m_CountedCollisions << ende;
		mout << "Counted Sidelength:" << m_CountedSidelength << ende;
		CloseParticleData();
		WriteTstFile(ii, &m_BenchSet[ii]);
	}

}





void GenResourceVertexParticle::Create(uint32_t BindPoint)
{


	
	m_Particles={};
	m_SideLength = 0;
	ConfigObj* cfg = (ConfigObj*)CfgApp;
	cfg->GetParticleSettings();
	m_Pdensity = cfg->m_PDensity;
	m_PInCell = static_cast<uint32_t>(std::floor(uint32_t(cfg->m_MaxPopPerCell * cfg->m_PDensity)));
	//m_TotCell = std::ceil(uint32_t(cfg->m_MaxPopPerCell * cfg->m_PDensity));
	
};



