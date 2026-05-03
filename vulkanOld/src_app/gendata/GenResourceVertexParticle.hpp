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

	int wx;
	int wy;
	int wz;
	int dx;
	int dy;
	int dz;
	float vx;
	float vy;
	float vz;
	float px;
	float py;
	float pz;

	int tot;
	int cols;
	int collision;
	float cdens;
	std::string sel;
	float radius;
};



class GenResourceVertexParticle : public Resource
{
    public:
		ConfigObj* m_cfg;
		char FileText[256] = { 0 };
		bool m_InitFlag = false;
		uint32_t  m_SideLength = 0;
		uint32_t  m_Front = 0;
		uint32_t  m_Back = 0;
		std::vector<uint32_t> m_SideLengths = {};
		std::vector<Particle>	m_Particles;
		uint32_t				m_NumParticles = 0;
		std::vector<benchSetItem> m_BenchSet;
		std::ofstream m_DataFile;
		std::ofstream m_CFBDataFile;
		std::string m_fileName;
		std::string m_FullBinFile;
		///Counting variables
		pdata pdata_t;
		std::vector<pdata> m_PartHold;
		uint32_t m_TotCell = 0;
		float m_Cdensity = 0;
		float m_Pdensity = 0;
		
		uint32_t m_TotCollsions = 0;
		float m_Radius = 0;
		uint32_t m_CountedParticles = 0;
		uint32_t m_CountedCollisions = 0;
		uint32_t m_CountedSidelength = 0;
		uint32_t m_CountedBoundaryParticles = 0;
		float m_Centerlen = 0.0;
		bool m_TestCollisions = true;
		uint32_t m_ColArySize = 0;
		uint32_t m_PinRow = 0;
		uint32_t m_PInCell = 0;
		uint32_t m_PInLayer = 0;
		uint32_t m_CInCell = 0;
		uint32_t PInCellCount = 0;
		uint32_t CInCellCount = 0;
		void WriteEntry(benchSetItem* bsi);
		void SaveParticles();
		void DoMotionStudy();
		void WriteTstFile(uint32_t index, benchSetItem* bsi);
		uint32_t CalcSideLength();
		int GenBenchSet();
		void ProcessPQB()
		{
			
			ProcessSet();
			m_BenchSet.clear();
		};
		void ProcessPCD()
		{
			ProcessSet();
			m_BenchSet.clear();
		};

		void ProcessCFB()
		{
			OpenParticleDataA003();
			m_BenchSet.clear();
		};
		void ProcessAll();
		void ProcessDUP();
		void WriteDUPParticle(pdata pd);
		uint32_t CountCollisions();
		void ProcessTestDUP(benchSetItem* bsi);
		void OpenDUPParticleData(size_t num, benchSetItem* bsi);
		uint32_t  ProcessDUPPattern(uint32_t xcell, uint32_t ycell, uint32_t zcell);
		void ProcessSet();
		void ProcessTestA001(benchSetItem* bsi);
		void ProcessTestA002(benchSetItem* bsi);
		void ProcessBoundaryTestA002(benchSetItem* bsi);
		uint32_t GetNextSideLength();
		void GenCellVPDensity();
		void OpenParticleDataA003();
		void DoCubeBoundary();
		void BuildCubeBoundary(size_t num, benchSetItem* bsi);
		void Corner3Side(uint32_t sl);
		void Corner2Side(uint32_t sl);
		void Corner1Side(uint32_t sl);
		void GetRandVel(pdata *pd);
		void WriteBoundaryParticle(pdata pd);
		uint32_t AddParticlePatternA001(uint32_t xx, uint32_t yy, uint32_t zz);
		uint32_t AddParticlePatternA002( uint32_t xcell, uint32_t ycell, uint32_t zcell);
		void WriteParticle(pdata pd, bool m_PlcFlg);
		void OpenParticleDataA001(size_t num, benchSetItem* bsi);
		void OpenParticleDataA002(size_t num, benchSetItem* bsi);
		void CloseParticleData();
		GenResourceVertexParticle() {};
		void CleanFiles();
		virtual void AskObject(uint32_t AnyNumber) {};

		GenResourceVertexParticle(VulkanObj *App, std::string Name):
					Resource(App, Name, VBW_DESCRIPTOR_TYPE_PARTICLE)
				{
				
				};
		
	void Create(ConfigObj* CFG)
	{
		
		m_cfg = CFG;
		
	};		
	virtual void Create(uint32_t BindPoint);
	void CreateLayout() {};
#if 0
	int createVertexBufferWithStaging(std::vector<Vertex> data,
		size_t size, size_t stride,
		VkBufferUsageFlags usage, VkBuffer& buffer,
		VkDeviceMemory& bufferMemory) {};
#endif
	//============================================================
	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions() { return nullptr; };
	VkVertexInputBindingDescription* GetBindingDescription() { return nullptr; };
	
	virtual void PushMem(uint32_t f) {};
	virtual void PullMem(uint32_t f) {};
	void Cleanup()
	{
        
    };

	

};
#endif