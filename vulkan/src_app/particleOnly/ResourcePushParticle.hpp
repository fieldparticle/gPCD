
/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/ResourcePush.hpp $
% $Id: ResourcePush.hpp 28 2023-05-03 19:30:42Z jb $
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
#ifndef RESOURCEPARTICLEPUSH
#define RESOURCEPARTICLEPUSH

class ResourceParticlePush : public Resource
{
    public:
    
	struct ShaderFlags 
	{
		float DrawInstance;
		float SideLength;
		float Ptot;
		float dt;
		float systemp;
		float ColorMap;		// 1.0 = Color Collision 
						// 2.0 = Color velocity angle.
		float Boundary; //0.0 off, 1.0 on
		float StopFlg;
		float frameNum;
		float actualFrame;
	} m_ShaderFlags;


	float m_numParts = 0.0;
	void Create(ResourceVertexParticle* vertP);
	ResourceVertexParticle* m_VertP{};
	ResourceParticlePush(VulkanObj* App, std::string Name) : Resource(App,Name, VBW_DESCRIPTOR_TYPE_PUSH_CONSTANT)
	{
	};
	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions() { return {}; };
	VkVertexInputBindingDescription* GetBindingDescription() { return {}; };
	virtual void AskObject(uint32_t AnyNumber) {};
	void PushMem(uint32_t currentBuffer);
	 	void PullMem(uint32_t currentBuffer){};
	
};
#endif