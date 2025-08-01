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
uint32_t ResourceVertexParticle::CalcSideLength(size_t PartPerCell)
{
	uint32_t ii = 0;
	while (1)
	{
		ii++;
		if (ii * ii * ii * PartPerCell >= m_NumParticles)
		{
			return ii;
		}
	}
}
float ResourceVertexParticle::CalcSpeedLimit(float max_vel, float radius)
{
	return radius / (3 * max_vel);
}
void ResourceVertexParticle::Create(uint32_t BindPoint)
{
	
	m_MaxColls				= MAXSPCOLLS;
	m_thisFramesBuffered	= 1;
	m_Particles				= {};
	m_BindPoint				= BindPoint;
	m_SideLength			= 0;

	CreateLayout();

	m_Radius				= CfgTst->GetFloat("radius", true);
	std::string dataFile	= CfgTst->GetString("particle_data_bin_file", true);
	uint32_t dataStart		= 0;
	BoundaryParticleLimit	= 0;
	

	mout << "Data File:" << dataFile << ende;
	

	// Reading from it
	std::ifstream input_file(dataFile, std::ios::binary);
	if (!input_file.is_open())
	{
		std::string err = "Cannot open benchmarking data file::" + dataFile;
		throw std::runtime_error(err.c_str());
	}

	pdata part_pos;

	//--- DUMMY PARTICLE ADDED IN GEN SOFTWARE
	// Add dummy partic le at index 0
	// Need this becasue zero means the end of the linked list.
#if 0
	Particle part0{};
	m_Particles.push_back(part0);
	m_NumParticles = 1;
#endif
	m_NumParticles = 0;
	if (m_App->m_dt == 0.0)
	{
		// Get dt from radious and temp speed.
		m_App->m_dt = CalcSpeedLimit(0.5200f, m_Radius);
	}
	
	uint32_t count = 0;
	
	while (input_file.peek() != EOF)
	{
		input_file.read((char*)&part_pos, sizeof(part_pos));
		Particle part{};
#if 1
		if (part_pos.rx < 0.5 || part_pos.ry < 0.5 || part_pos.rz < 0.5)
		{
			std::ostringstream  objtxt;
			if (m_NumParticles != 0)
			{
				objtxt << m_Name << "ResourceVertexParticle::Particle location below bounds P:" <<
					part_pos.pnum << "<" << part_pos.rx << "," << part_pos.ry  << "," << part_pos.rz
						<< ">" << std::ends;
				throw std::runtime_error(objtxt.str().c_str());
			}
		}
#endif		
		part.PosLoc			= glm::vec4(part_pos.rx, part_pos.ry,part_pos.rz, part_pos.radius);
		part.pnum			= m_NumParticles;
		part.VelRad			= glm::vec4(part_pos.vx, part_pos.vy, part_pos.vz,1.0);
		part.FrcAng			= glm::vec4(0.0, 0.0, 0.0,1.0);
		part.MolarMatter	= static_cast<float>(1.0);
		part.temp_vel		= static_cast<float>(0.04);
		part.parms		=  glm::vec4(part_pos.seq, 0.0,0.0, 0.0);
		part.colFlg			= 0;


		if (part_pos.ptype == 1.0)
			BoundaryParticleLimit++;

		count++;

		if (count > dataStart)
		{
			m_NumParticles++;
			m_Particles.push_back(part);
		}
	}
	
	uint32_t sidelen = CfgTst->GetUInt("CellAryL", true);
	m_SideLength = static_cast<float>(sidelen);
	/*
	* ##JMB How can they match you just add one ot it
	if(cfg->m_CfgSidelen != m_SideLength)
	{
		std::ostringstream  objtxt;
		objtxt << m_Name << "ResourceVertexParticle::Side length mismatch - cfg:"
			<< cfg->m_CfgSidelen << " calculated:" << m_SideLength  << std::ends;

		//throw std::runtime_error(objtxt.str().c_str());
	}*/

	m_App->m_SideLength = m_SideLength;
	size_t styrsz = sizeof(Particle);
	mout << "Particle Read:" << m_NumParticles << " Side Length =" << m_SideLength << " ParticleStruct Size:" 
		<< styrsz << ende;

	m_BufSize = sizeof(Particle) * m_NumParticles;

	mout << "MEMALLOC:ResourceVertexParticle:" << m_BufSize << ende;
	m_App->m_Numparticles = m_NumParticles;

	// Check number of particles match - add 1 for null particle
	if (m_NumParticles != CfgTst->GetUInt("num_particles", true)+1)
	{
		std::ostringstream  objtxt;
		objtxt << m_Name << "ResourceVertexParticle::Particle count does not match: Number read from tst file:" 
			<<  CfgTst->GetUInt("num_particles", true) 
			<< " Number read from bin file:" << m_NumParticles << std::ends;

		throw std::runtime_error(objtxt.str().c_str());
	}


#if 0
	int rem = sizeof(Particle) % 16;
	if (rem != 0)
	{
		std::ostringstream  objtxt;
		objtxt << m_Name << "ResourceVertexParticle::Create Particle size:" 
			<< sizeof(Particle) << " not 16 aligned." << std::ends;

		throw std::runtime_error(objtxt.str().c_str());
	}
#endif	

	mout << "Max SideLength is:" << m_SideLength << ende;
	if (m_NumParticles == 0 || m_SideLength == 0)
	{
		std::ostringstream  objtxt;
		objtxt << m_Name << "ResourceVertexParticle::Create Particle Zero Problem:m_NumParticles="
			<< m_NumParticles  << " m_SideLength=." << m_SideLength << std::ends;
		throw std::runtime_error(objtxt.str().c_str());
	}

	std::ostringstream  objtxt;
	m_NumElements = m_NumParticles;
	m_Buffers.resize(m_thisFramesBuffered);
	m_BuffersMemory.resize(m_thisFramesBuffered);
	m_BuffersMapped.resize(m_thisFramesBuffered);
	m_BufferInfo.resize(m_thisFramesBuffered);
	m_DescriptorWrite.resize(m_thisFramesBuffered);
	m_Allocation.resize(m_thisFramesBuffered);
	VkBuffer buf = {};

	for (size_t i = 0; i < m_thisFramesBuffered; i++)
	{
		objtxt << m_Name << " Number:" << i << std::ends;
		m_App->VMACreateDeviceBuffer(m_BufSize,
			VK_BUFFER_USAGE_TRANSFER_DST_BIT |
			VK_BUFFER_USAGE_VERTEX_BUFFER_BIT |
			VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
			VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
			m_Buffers[i], m_Allocation[i], objtxt.str());


		m_BufferInfo[i].buffer = m_Buffers[i];
		m_BufferInfo[i].offset = 0;
		m_BufferInfo[i].range = sizeof(Particle) * m_Particles.size();

		m_DescriptorWrite[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
		m_DescriptorWrite[i].dstBinding = m_BindPoint;
		m_DescriptorWrite[i].dstArrayElement = 0;
		m_DescriptorWrite[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
		m_DescriptorWrite[i].descriptorCount = 1;
		m_DescriptorWrite[i].pBufferInfo = &m_BufferInfo[i];
		objtxt.clear();

	}
	vmaCopyMemoryToAllocation(m_App->m_vmaAllocator, m_Particles.data(), m_Allocation[0],
		0, m_BufSize);
	m_Particles.clear();
    
}


void ResourceVertexParticle::CreateLayout()
{

	// Step 1: Add layout biding definition.
	m_LayoutBinding.resize(1);
	m_LayoutBinding[0].binding = m_BindPoint;
	m_LayoutBinding[0].descriptorCount = 1;
	m_LayoutBinding[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_LayoutBinding[0].pImmutableSamplers = nullptr;
	m_LayoutBinding[0].stageFlags = VK_SHADER_STAGE_ALL;
}
VkVertexInputBindingDescription* 
ResourceVertexParticle::GetBindingDescription()
{
	
	m_BindingDescription.binding = m_BindPoint;
	m_BindingDescription.stride = sizeof(Particle);
	m_BindingDescription.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;
	

	return &m_BindingDescription;
}
std::vector<VkVertexInputAttributeDescription>*
ResourceVertexParticle::GetAttributeDescriptions()
{

	VkVertexInputAttributeDescription ad{};
	ad.binding = m_BindPoint;
	ad.location = 0;
	ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
	ad.offset = offsetof(Particle, PosLoc);

	m_AttributeDescriptions.push_back(ad);

	ad.binding = m_BindPoint;
	ad.location = 1;
	ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
	ad.offset = offsetof(Particle, VelRad);
	m_AttributeDescriptions.push_back(ad);

	ad.binding = m_BindPoint;
	ad.location = 2;
	ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
	ad.offset = offsetof(Particle, FrcAng);
	m_AttributeDescriptions.push_back(ad);

	ad.binding = m_BindPoint;
	ad.location = 3;
	ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
	ad.offset = offsetof(Particle, prvvel);
	m_AttributeDescriptions.push_back(ad);
	
	
	return &m_AttributeDescriptions;
}
