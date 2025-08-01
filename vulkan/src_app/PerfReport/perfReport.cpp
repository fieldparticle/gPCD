/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mps/main.cpp $
% $Id: main.cpp 31 2023-06-12 20:17:58Z jb $
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
%*$Revision: 31 $
%*
%*
%******************************************************************/
#include "VulkanObj/VulkanApp.hpp"
#include "perfObj.hpp"
#include "csv.hpp"
#include <cstring>
#include <iostream>
MsgStream			mout;


void GenData(ConfigObj* configObj)
{
	
	configObj->GetSettings();
	
	perfObj *po = new perfObj(configObj);
#if 0
	po->m_co = configObj;
	configObj->m_TestName = configObj->m_MMRRTestName;
	configObj->m_TestDir = configObj->m_MMRRTestDir;
	po->ProcessMMRR();

	po->SetTest(1,1);
	configObj->m_TestName = configObj->m_PQBTestName;
	configObj->m_TestDir = configObj->m_PQBTestDir;
	po->OpenPerfData();
	po->ProcessFileList();
	po->ProcessResultsData();

	po->SetTest(1,2);
	configObj->m_TestName = configObj->m_PCDTestName;
	configObj->m_TestDir = configObj->m_PCDTestDir;
	po->OpenPerfData();
	po->ProcessFileList();
	po->ProcessResultsData();

	po->SetTest(1,3);
	configObj->m_TestName = configObj->m_CFBTestName;
	configObj->m_TestDir = configObj->m_CFBTestDir;
	po->OpenPerfData();
	po->ProcessFileList();
	po->ProcessResultsData();
#endif	

	// Run release 
	po->SetTest(2,1);
	configObj->m_TestName = configObj->m_PQBTestName;
	configObj->m_TestDir = configObj->m_PQBTestDir;
	po->OpenPerfData();
	po->ProcessFileList();
	po->ProcessResultsData();
	
	po->SetTest(2,2);
	configObj->m_TestName = configObj->m_PCDTestName;
	configObj->m_TestDir = configObj->m_PCDTestDir;
	po->OpenPerfData();
	po->ProcessFileList();
	po->ProcessResultsData();
		
	po->SetTest(2,3);
	configObj->m_TestName = configObj->m_CFBTestName;
	configObj->m_TestDir = configObj->m_CFBTestDir;
	po->OpenPerfData();
	po->ProcessFileList();
	po->ProcessResultsData();
	
}
void perfObj::ProcessMMRR()
{
	m_TestPair.resize(1);
	m_TestPair[0].tstData.m_AprFile = cfg->m_MMRRTestName;
	GetResultsData(0);
	m_MMRRTestPair=m_TestPair;
	m_TestPair.clear();
	float tfps=0.0;
	float maxfps=0.0;
	float minfps=0.0;
	float avgfps=0.0;
	size_t counter = 1;
	uint32_t itNum = 0;
	for(size_t rloc = 0; rloc< m_MMRRTestPair[0].resultData.size();rloc++)
	{

		tfps += m_MMRRTestPair[itNum].resultData[rloc].fps;
		
		if(m_MMRRTestPair[itNum].resultData[rloc].fps > maxfps)
			maxfps = m_MMRRTestPair[itNum].resultData[rloc].fps;

		if(m_MMRRTestPair[itNum].resultData[rloc].fps < minfps || minfps == 0.0 )
			minfps = m_MMRRTestPair[itNum].resultData[rloc].fps;
		counter++;
	}

	avgfps = tfps/counter;
	maxmmrr = 1.0/minfps;
	minmmrr = 1.0/maxfps;
	avgmmrr = 1.0/avgfps;
	
}



int main() try
{
	std::string filename = "perfReport.log";
	std::string modname = "perfReport";
	mout.Init(filename.c_str(), modname.c_str());
	ConfigObj* configVCUBE = new ConfigObj;
	std::filesystem::path cwd = std::filesystem::current_path();
	mout << "Working Directory :" << cwd.string().c_str() << ende;
	configVCUBE->Create("perfReport.cfg");
	GenData(configVCUBE);
	
	
}

catch (const std::exception& e)
{

	mout << "EXITING| TYPE:" << typeid(e).name() << " MSG:" << e.what() << ende;

	exit(1);
}
void perfObj::OpenPerfData()
{
	m_TestPair.clear();
	 // Define the directory path to list files from 
    std::filesystem::path directorypath = cfg->m_TestDir;
	using recursive_directory_iterator = std::filesystem::recursive_directory_iterator;
	std::string ftype = "tst";
    // To check if the directory exists or not 
    if (exists(directorypath) 
        && is_directory(directorypath)) { 
        // Loop through each item (file or subdirectory) in 
        // the directory 
        for (const auto& entry : recursive_directory_iterator(directorypath)) 
		{ 
			
			std::string pth = entry.path().generic_string();
			if(std::strstr(pth.c_str(),".tst"))
			{
				
				testPair tst;
				tst.testFile = pth;
				size_t lastindex = pth.find_last_of("."); 
				std::string rawname = pth.substr(0, lastindex-1); 
				tst.resultsFile = rawname + "D.csv";
				m_TestPair.push_back(tst);
				std::cout << "Test File: " << tst.testFile << std::endl;
				std::cout<< "Results File:" << tst.resultsFile << std::endl; 
			}
        } 
    } 
    else { 
        // Handle the case where the directory doesn't exist 
        std::cerr << "Directory not found." << std::endl; 
    } 
  
    
}
void perfObj::ProcessFileList()
{

	config_t 			m_cfg;
	config_setting_t* m_setting;

	for(int ii = 0; ii< m_TestPair.size(); ii++)
	{
		config_init(&m_cfg);
		m_co->ReadConfigFile(m_TestPair[ii].testFile);
		// The genrating file uses the whole directoy eith drive.
		m_TestPair[ii].tstData.m_AprFile =  m_co->GetString("aprFile", true);
		if(m_testType == 1)
		{
			m_TestPair[ii].tstData.m_AprFile = m_TestPair[ii].tstData.m_AprFile + "D.csv";
			mout << "Verifying " << m_TestPair[ii].tstData.m_AprFile << ende;
		}
		if(m_testType == 2)
		{
			m_TestPair[ii].tstData.m_AprFile = m_TestPair[ii].tstData.m_AprFile + "R.csv";
			mout << "Performance analysis on " << m_TestPair[ii].tstData.m_AprFile << ende;
		}
		m_TestPair[ii].tstData.m_AprFile = m_TestPair[ii].tstData.m_AprFile;
		m_TestPair[ii].tstData.m_DataFile = m_co->GetString("dataFile", true);
		//m_TestPair[ii].tstData.m_CfgSidelen = m_co->GetUInt("Sidelen", true);
		m_TestPair[ii].tstData.m_PartPerCell = m_co->GetUInt("PartPerCell", true);
		m_TestPair[ii].tstData.m_wky = m_co->GetInt("workGroupsy", true);
		m_TestPair[ii].tstData.m_wkx = m_co->GetInt("workGroupsx", true);
		m_TestPair[ii].tstData.m_wkz = m_co->GetInt("workGroupsz", true);
		m_TestPair[ii].tstData.m_dkx = m_co->GetInt("dispatchx", true);
		m_TestPair[ii].tstData.m_dky = m_co->GetInt("dispatchy", true);
		m_TestPair[ii].tstData.m_dkz = m_co->GetInt("dispatchz", true);
		m_TestPair[ii].tstData.m_colcount = m_co->GetInt("colcount", true);
		m_TestPair[ii].tstData.m_radius = m_co->GetFloat("radius", true);
		m_TestPair[ii].tstData.m_density = m_co->GetFloat("density", true);
		m_TestPair[ii].tstData.m_partcount = m_co->GetInt("pcount", true);
		m_TestPair[ii].tstData.m_MaxCollArray = m_co->GetInt("ColArySize", true);
		m_TestPair[ii].tstData.m_MaxSingleCollisions = m_co->GetInt("MaxSingleCollisions", false);
		

	}
};
void perfObj::ProcessResultsData()
{
	if(m_testType == 2)
	{
		
		std::string fileName;
		if(m_test == 1)
			fileName = cfg->m_TestDir + "/PQBReport.csv";
		if(m_test == 2)
			fileName = cfg->m_TestDir + "/PCDReport.csv"; 
		if(m_test == 3)
			fileName = cfg->m_TestDir + "/CFBReport.csv"; 

		dataFile.open(fileName);
		if (!dataFile.is_open())
		{
			std::string err = "Cannot open report data file::" + fileName;
			throw std::runtime_error(err.c_str());
		}
		dataFile << "file" << 
				"," << "numparticles"
				<< "," << "numcollsions"
				<< "," << "avgfps"
				<< "," << "avgcpums"
				<< "," << "avgcms"
				<< "," << "avggms"
				<< "," << "minfps"
				<< "," << "mincpums"
				<< "," << "mincms"
				<< "," << "mingms"
				<< "," << "maxfps"
				<< "," << "maxcpums"
				<< "," << "maxcms"
				<< "," << "maxgms" 
				<< "," << "maxspf" 
				<< "," << "minspf"
				<< "," << "avgspf" 
				<< "," << "maxmmrr" 
				<< "," << "minmmrr" 
				<< "," << "avgmmrr"  
				<< "," << "maxarr" 
				<< "," << "minarr" 
				<< "," << "avgarr"  
				<< std::endl;
	}
	for(int ii = 0; ii< m_TestPair.size(); ii++)
	{
		GetResultsData(ii);
		CheckWriteData(ii);
	}

	if(m_testType == 2)
	{
		dataFile.flush();
		dataFile.close();

	}
}
void perfObj::CheckWriteData(size_t itNum)
{

		if(m_testType == 1)
		{
			PerformDebugTests(itNum);
		}	
		if(m_testType == 2)
		{
			PerformanceReport(itNum);

		}
	
	mout << m_testName << " for:" << m_TestPair[itNum].testFile <<  " SUCCESSFUL!" << ende;

}
void perfObj::PerformanceReport(size_t itNum)
{
	float tfps = 0.0;
	float tcpums= 0.0;
	float tcms= 0.0;
	float tgms= 0.0;
	
	float afps = 0.0;
	float acpums= 0.0;
	float acms= 0.0;
	float agms= 0.0;

	float minfps = 0.0;
	float mincpums= 0.0;
	float mincms= 0.0;
	float mingms= 0.0;

	float maxfps = 0.0;
	float maxcpums= 0.0;
	float maxcms= 0.0;
	float maxgms= 0.0;

	float minarr;
	float maxarr;
	float avgarr;



	
	uint32_t counter=1;
	for(size_t rloc = 0; rloc< m_TestPair[itNum].resultData.size();rloc++)
	{

		tfps += m_TestPair[itNum].resultData[rloc].fps;
		tcpums += m_TestPair[itNum].resultData[rloc].cpums;
		tcms += m_TestPair[itNum].resultData[rloc].cms;
		tgms += m_TestPair[itNum].resultData[rloc].gms;

		if(m_TestPair[itNum].resultData[rloc].fps > maxfps)
			maxfps = m_TestPair[itNum].resultData[rloc].fps;

		if(m_TestPair[itNum].resultData[rloc].fps < minfps || minfps == 0.0 )
			minfps = m_TestPair[itNum].resultData[rloc].fps;

		//----------------
		if(m_TestPair[itNum].resultData[rloc].cpums > maxcpums)
			maxcpums = m_TestPair[itNum].resultData[rloc].cpums;

		if(m_TestPair[itNum].resultData[rloc].cpums < mincpums || mincpums == 0.0)
			mincpums = m_TestPair[itNum].resultData[rloc].cpums;

		//----------------
		if(m_TestPair[itNum].resultData[rloc].cms > maxcms)
			maxcms = m_TestPair[itNum].resultData[rloc].cms;

		if(m_TestPair[itNum].resultData[rloc].cms < mincms || mincms == 0.0)
			mincms = m_TestPair[itNum].resultData[rloc].cms;

		//----------------
		if(m_TestPair[itNum].resultData[rloc].gms > maxgms)
			maxgms = m_TestPair[itNum].resultData[rloc].gms;

		if(m_TestPair[itNum].resultData[rloc].gms < mingms || mingms == 0.0)
			mingms = m_TestPair[itNum].resultData[rloc].gms;

		counter++;
	} 

	afps = tfps/counter;
	acpums= tcpums/counter;
	acms= tcms/counter;
	agms= tgms/counter;
	float maxspf = 1.0/minfps;
	float minspf = 1.0/maxfps;
	float avgspf = 1.0/afps;

	maxarr = maxmmrr/maxspf; 
	minarr = minmmrr/minspf;
	avgarr = avgmmrr/avgspf;
	


	dataFile << m_TestPair[itNum].testFile << "," << m_TestPair[itNum].tstData.m_partcount 
				<< "," << m_TestPair[itNum].tstData.m_colcount
				<< "," << afps << "," << acpums << "," << acms << "," << agms << 
				"," << minfps << "," << mincpums << "," << mincms << "," << mingms << 
				"," << maxfps << "," << maxcpums << "," << maxcms << "," << maxgms << 
				"," << maxspf << "," << minspf << "," << avgspf << 
				"," << maxmmrr << "," << minmmrr << "," << avgmmrr << 
				"," << maxarr << "," << minarr << "," << avgarr << 
				std::endl;
	
}
void perfObj::PerformDebugTests(size_t itNum)
{
	
	std::ostringstream objtxt; 
	for(size_t rloc = 0; rloc< m_TestPair[itNum].resultData.size();rloc++)
	{
	
		if(m_TestPair[itNum].resultData[rloc].expectedp != m_TestPair[itNum].resultData[rloc].loadedp)
		{
			objtxt.clear();
			 objtxt << m_testName << " " << m_TestPair[itNum].testFile 
				 << " Expected Number of particles:" 
				<< m_TestPair[itNum].resultData[rloc].expectedp
				<< " Not euqal to loaded number of particles:"
				<< m_TestPair[itNum].resultData[rloc].loadedp << '\0';

			mout << objtxt.str().c_str() << ende;
			//throw std::runtime_error(objtxt.str());
		}
		if(m_TestPair[itNum].resultData[rloc].expectedp != m_TestPair[itNum].resultData[rloc].shaderp_comp)
		{
			objtxt.clear();
			objtxt << m_testName << " " << m_TestPair[itNum].testFile 
				<< " Expected Number of particles:" 
				<< m_TestPair[itNum].resultData[rloc].expectedp
				<< " Not equal to particles counted by compute:"
				<< m_TestPair[itNum].resultData[rloc].shaderp_comp << '\0';;
				
			mout << objtxt.str().c_str() << ende;
			//throw std::runtime_error(objtxt.str());
		}
#if 0
		if(m_TestPair[itNum].resultData[rloc].expectedp != m_TestPair[itNum].resultData[rloc].shaderp_grph)
		{
			objtxt.clear();
			objtxt << m_testName << " " << m_TestPair[itNum].testFile 
				<< " Expected Number of particles:" 
				<< m_TestPair[itNum].resultData[rloc].expectedp
				<< " Not equal to particles counted by vertex:"
				<< m_TestPair[itNum].resultData[rloc].shaderp_grph << '\0';
				
			mout << objtxt.str().c_str() << ende;
			//throw std::runtime_error(objtxt.str());
		}
#endif
		if(m_TestPair[itNum].resultData[rloc].expectedc != m_TestPair[itNum].resultData[rloc].shaderc)
		{
			objtxt.clear();
			objtxt << m_testName << " " << m_TestPair[itNum].testFile 
				<< " Expected Number of collisions:" 
				<< m_TestPair[itNum].resultData[rloc].expectedc
				<< " Not equal to collisions counted by compute:"
				<< m_TestPair[itNum].resultData[rloc].shaderc << '\0';;
				
			mout << objtxt.str().c_str() << ende;
			//throw std::runtime_error(objtxt.str());
		}
	}
}
#include <cstring>
#include <iostream>
void perfObj::GetResultsData(size_t itNum)
{
	int ret = 0;
#if 0
	std::ofstream dataFile;
	dataFile.open(m_TestPair[itNum].tstData.m_AprFile);
	if (!dataFile.is_open())
	{
		if(std::strstr(m_TestPair[itNum].tstData.m_AprFile.c_str(), "R.csv"))
		{
			std::ostringstream  objtxt;
			objtxt << "Report file not found - this is normal if you have not run the release version. File:" 
				<< m_TestPair[itNum].tstData.m_AprFile.c_str() << std::ends;
			throw std::runtime_error(objtxt.str());
		}
	}
	dataFile.close();
#endif
	io::CSVReader<16> in(m_TestPair[itNum].tstData.m_AprFile);
	in.read_header(io::ignore_extra_column, "time", "fps", "cpums", "cms", "gms", "expectedp", "loadedp", 
		"shaderp_comp", "shaderp_grph","expectedc","shaderc","threadcount","sidelen","density","PERR","CERR");

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
	uint32_t sidelen;
	float density;
	float PERR;
	float CERR;
	size_t count = 0;
	while (in.read_row(atime, fps, cpums, cms, gms, expectedp, loadedp, shaderp_comp, shaderp_grph,
			expectedc,shaderc,threadcount,sidelen, density,PERR,CERR))
		// do stuff with the data
	{
		benchSetItem bsi;
		bsi.atime = atime;
		bsi.fps = fps;
		bsi.cpums = cpums;
		bsi.cms = cms;
		bsi.gms= gms;
		bsi.expectedp = expectedp;
		bsi.loadedp = loadedp;
		bsi.shaderp_comp = shaderp_comp;
		bsi.shaderp_grph = shaderp_grph;
		bsi.expectedc = expectedc;
		bsi.shaderc = shaderc;
		bsi.threadcount = threadcount;
		bsi.density = density;
		m_TestPair[itNum].resultData.push_back(bsi);
	}


}

















