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
#include "csv/csv.hpp"
void GenResourceVertexParticle::WriteTstFile(uint32_t index, benchSetItem* bsi)
{
	std::string dirval	= CfgApp->m_TestDir;
	std::string fulFile = dirval + "/" + m_fileName + ".tst";
	std::string txtFile = "\"" + dirval + "/" + m_fileName + "\"";
	std::string binFile = "\"" + m_FullBinFile + "\"";
	ConfigObj* cfg		= (ConfigObj*)CfgApp;
	
	std::ofstream ostrm(fulFile);
	if (!ostrm.is_open())
	{
		std::string err = "Cannot open benchmarking test file::" + fulFile;
		throw std::runtime_error(err.c_str());
	}

	std::cout << "Processing File:" << fulFile.c_str() << std::endl;
	char densit[6] = { 0 };
	sprintf(densit,"%0.2f\0", m_Cdensity);
	ostrm << "index = " << index << ";" << std::endl;
	ostrm << "CellAryW = " << m_SideLength << ";" << std::endl;
	ostrm << "CellAryH = " << m_SideLength << ";" << std::endl;
	ostrm << "CellAryL = " << m_SideLength << ";" << std::endl;
	ostrm << "radius = " << m_Radius << ";" << std::endl;
	ostrm << "PartPerCell = " << m_PInCell << ";" << std::endl;
	ostrm << "pcount = " << m_CountedParticles + m_CountedBoundaryParticles<< ";" << std::endl;
	ostrm << "colcount =" << m_CountedCollisions << ";" << std::endl;
	ostrm << "dataFile = " << binFile << ";" << std::endl;
	ostrm <<"aprFile = " << txtFile << ";" << std::endl;
	ostrm <<"density = " << densit  << ";" << std::endl;
	ostrm <<"pdensity = " << m_Pdensity << ";" << std::endl;
	ostrm <<"dispatchx = " << bsi->dx + m_CountedBoundaryParticles << ";" << std::endl;
	ostrm <<"dispatchy = " << bsi->dy << ";" << std::endl;
	ostrm <<"dispatchz = " << bsi->dz << ";" << std::endl;
	ostrm <<"workGroupsx =" << bsi->wx << "; " << std::endl;
	ostrm <<"workGroupsy =" << bsi->wy << "; " << std::endl;
	ostrm <<"workGroupsz =" << bsi->wz << "; " << std::endl;
	ostrm <<"ColArySize =" << m_ColArySize << "; " << std::endl;
	ostrm.flush();
	ostrm.close();


	if (m_CountedCollisions != m_TotCollsions && m_TestCollisions == true)
	{
		std::ostringstream  objtxt;
		objtxt << "Counted Collsions:" << m_CountedCollisions << " Expected:" << m_TotCollsions << std::ends;
		throw std::runtime_error(objtxt.str().c_str());

	}
}

int GenResourceVertexParticle::GenBenchSet()
{
	int ret = 0;
	io::CSVReader<18> in(CfgApp->m_TestName);
	in.read_header(io::ignore_extra_column, "wx", "wy", "wz", "dx", "dy", "dz", "tot", "sel", "cols","collision","cdens","radius","vx","vy","vz","px","py","pz");
	std::string sel;
	int wx, wy, wz, dx, dy, dz, tot, cols, collision;
	float cdens,radius,vx,vy,vz,px,py,pz;

	while (in.read_row(wx, wy, wz, dx, dy, dz, tot, sel, cols, collision, cdens,radius,vx,vy,vz,px,py,pz))
		// do stuff with the data
	{
		benchSetItem bsi;
		bsi.wx = wx;
		bsi.wy = wy;
		bsi.wz = wz;
		bsi.dx = dx;
		bsi.dy = dy;
		bsi.dz = dz;
		bsi.vx = vx;
		bsi.vy = vy;
		bsi.vz = vz;
		bsi.px = px;
		bsi.py = py;
		bsi.pz = pz;
		bsi.tot = tot;
		bsi.sel = sel;
		bsi.cols = cols;
		bsi.collision = collision;
		bsi.cdens = cdens;
		bsi.radius = radius;

		if (sel.compare("s") == 0)
		{
			m_BenchSet.push_back(bsi);
#if 0
			std::cout << xx << " "
				<< yy << " "
				<< zz << " "
				<< dx << " "
				<< dy << " "
				<< dz << " "
				<< tot << " "
				<< sel << " "
				<< cols << " "
				<< radius << std::endl;
#endif
		}
		if (sel.compare("c") == 0)
		{
			ret = 1;
			m_NumParticles++;
			m_BenchSet.push_back(bsi);

		}


	}
	return ret;
}

void GenResourceVertexParticle::SaveParticles()
{
	for(uint32_t ii = 0;ii<m_NumParticles;ii++)
	{
		pdata pd = m_PartHold[ii];
		m_DataFile.write((char*)&pd, sizeof(pdata));
		if (m_DataFile.bad())
		{
			std::string err = "Particle bin File write Error::";
			throw std::runtime_error(err.c_str());
		}
	}
	m_DataFile.flush();
	m_PartHold.clear();
	m_PartHold.shrink_to_fit();
	m_Front = 0;
	m_Back = 0 ;


}
void GenResourceVertexParticle::WriteParticle(pdata pd,bool m_PlcFlg)
{
	if (pd.rx+ m_Radius > m_CountedSidelength)
		m_CountedSidelength = static_cast<uint32_t>(pd.rx);
	if (pd.ry + m_Radius > m_CountedSidelength)
		m_CountedSidelength = static_cast<uint32_t>(pd.ry);
	if (pd.rz + m_Radius > m_CountedSidelength)
		m_CountedSidelength = static_cast<uint32_t>(pd.rz);
	
	int lb = 4999, ub = 5200;
	float velx = (rand() % (ub - lb + 1) + lb) / 1000000.00f;
	float vely = (rand() % (ub - lb + 1) + lb) / 1000000.00f;
	float velz = (rand() % (ub - lb + 1) + lb) / 1000000.00f;
	pd.vx = velx;
	pd.vy = vely;
	pd.vz = velz;
	if (m_NumParticles % 2 == 0)
	{
		pd.vx = -pd.vx;
		pd.vz = -pd.vz;
	}
	if (m_NumParticles % 3 == 0)
	{
		pd.vx = -pd.vx;
		pd.vy = -pd.vy; 
	}
	if (m_NumParticles % 5 == 0)
	{
		pd.vy = -pd.vy;
		pd.vz = -pd.vz;
	}
	if (m_NumParticles % 7 == 0)
	{
		pd.vx = -pd.vx;
		pd.vz = -pd.vz;
	}
	if (m_NumParticles % 9 == 0)
	{
		pd.vy = -pd.vy;
		pd.vz = -pd.vz;
	}
	if (m_NumParticles % 11 == 0)
	{
		pd.vx = -pd.vx;
		pd.vy = -pd.vy;
		pd.vz = -pd.vz;
	}
	if(m_PlcFlg == true)
	{
			
		m_PartHold[m_Back] = pd;
		m_Back--;
	}
	else
	{
		if(m_Front > m_NumParticles)
		{
			std::string err = "m_Front exceeds number particles.";
			throw std::runtime_error(err.c_str());
		}
		m_PartHold[m_Front] = pd;
		m_Front++;	
	}
	
	
}

void GenResourceVertexParticle::CloseParticleData()
{
	if (m_DataFile.is_open())
	{
		m_DataFile.flush();
		m_DataFile.close();
	}
}
