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
#pragma once

class PerfObj
{
	public:
		struct ReportType
		{
			uint32_t Second;
			float		FrameRate;
			float		SecondPerFrame;
			double		ComputeExecutionTime;
			double		GraphicsExecutionTime;
			uint32_t	NumParticlesGenerated;
			uint32_t	NumParticlesLoaded;
			uint32_t	NumParticlesComputeCount;
			uint32_t	NumParticlesGraphicsCount;
			uint32_t	NumCollisionsGenerated;
			uint32_t	NumCollisionsComputeCount;
			uint32_t	ThreadCountComp;
			uint32_t	SideLengthLoaded;
			uint32_t	SideLengthGraphics;
			uint32_t	SideLengthCompute;
		};
		std::vector< ReportType> m_ReportBuffer;
		bool						m_SingleFileTest=false;
		std::string					m_TestName;
		std::string					m_TestDir;
		std::string					m_TestCFG;
		std::string					m_testPQBSDir;
		std::string					m_testPQBRDir;
		std::string					m_testPQBDir;
		std::string					m_testCFBDir;
		std::string					m_testPCDDir;
		std::string					m_testDUPDir;
		
		uint32_t					m_SeriesLength = 0;
		std::string					m_AprFile;
		std::string					m_DataFile;

		// From specific test file
		uint32_t					m_colcount = 0;
		float						m_density = 0;
		int							m_partcount = 0;


	void Create();
	PerfObj(){};
	std::ostringstream AssembleRow(uint32_t rowNum);
	uint32_t DoStudy(TCPObj* tcps,TCPObj* tcpcapp, bool rmtFlag);
	int Doperf(DrawObj* DrawInstance, VulkanObj* VulkanWin,TCPObj* tcp, size_t aprCount);

};