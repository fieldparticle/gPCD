/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/ResourceVertex.hpp $
% $Id: ResourceVertex.hpp 28 2023-05-03 19:30:42Z jb $
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
#ifndef GENRESOURCEVERTEXPARTICLE_HPP
#define GENRESOURCEVERTEXPARTICLE_HPP
struct benchSetItem
{
	float atime;
	float fps;
	float cpums;
	float cms;
	float gms;
	uint32_t expectedp;
	uint32_t loadedp;
	uint32_t shaderp_comp;
	uint32_t shaderp_grph;
	uint32_t expectedc;
	uint32_t shaderc;
	uint32_t threadcount;
	float density;
};
struct tstItem
{
	std::string m_AprFile;
	std::string m_DataFile;
	uint32_t m_CfgSidelen;
	uint32_t m_PartPerCell;
	uint32_t m_wky;
	uint32_t m_wkx;
	uint32_t m_wkz;
	uint32_t m_dkx;
	uint32_t m_dky;
	uint32_t m_dkz;
	uint32_t m_colcount;
	float m_radius;
	float m_density;
	uint32_t m_partcount;
	uint32_t m_MaxCollArray;
	uint32_t m_MaxSingleCollisions;
};

struct testPair
{
	std::string testFile;
	std::string resultsFile;
	std::vector<benchSetItem> resultData;
	tstItem tstData;

};
class perfObj
{
    public:
		std::vector<testPair> m_TestPair;
		std::vector<testPair> m_MMRRTestPair;
		std::string m_testName;
		ConfigObj* m_co;
		// 1 debug
		//2 release
		uint32_t	m_testType;
		// 1 == pqb
		// 2 == pcd
		// 3 == cfb
		uint32_t	m_test;
		std::ofstream dataFile;
		float maxmmrr;
		float minmmrr;
		float avgmmrr;

		

		void ProcessMMRR();
		void SetTest(uint32_t RDType,uint32_t subType)
		{
			m_testType = subType;
			m_test = RDType;
			if(RDType == 1)
			{
				if(subType == 1)
					m_testName = "PQB Test in Debug";
				if(subType == 2)
					m_testName = "pcd Test in Debug";
				if(subType == 3)
					m_testName = "cfb Test in Debug";
			}

			if(RDType == 2)
			{
				if(subType == 1)
					m_testName = "PQB Test in Release";
				if(subType == 2)
					m_testName = "PCD Test in Release";
				if(subType == 3)
					m_testName = "CFB Test in Release";
			}


		}
		void OpenPerfData();
		void PerformanceReport(size_t ploc);
		void ProcessFileList();
		void ProcessResultsData();
		void GetResultsData(size_t itNum);
		void CheckWriteData(size_t itNum);
		void PerformDebugTests(size_t ploc);
				
		virtual void AskObject(uint32_t AnyNumber) {};
		ConfigObj* cfg;
		perfObj(ConfigObj* CFGObj)
		{
			cfg = CFGObj;
		};
		
		
	void CreateLayout() {};

	void Cleanup()
	{
        
    };

	

};
#endif