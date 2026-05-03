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
#include "VulkanApp.hpp"

MsgStream			mout;

int particleBoundary(VCUBECfg* configVCube)
{
	
	VulkanObj* vulkanObj = new VulkanObj;
	ShaderObj* shaderObj = new ShaderObj(vulkanObj, "ShaderObj");
	ResourceVertexParticle* resourceVertexParticle 
			= new ResourceVertexParticle(vulkanObj, "VertexParticle");
	ResourceUBO* resourceUBO 
			= new ResourceUBO(vulkanObj, "UBO");
	ResourceAtomic* resourceAtomic
		= new ResourceAtomic(vulkanObj, "Atomic");
	ResourceAtomicGraphics* resourceAtomicG
		= new ResourceAtomicGraphics(vulkanObj, "AtomicG");
	ResourceParticlePush* resourceParticlePush
			= new ResourceParticlePush(vulkanObj, "PushConstants");
	ResourceCollMatrix* resourceCollMatrix 
			= new ResourceCollMatrix(vulkanObj, "CollisionImage");
	ResourceLockMatrix* resourceLockMatrix
		= new ResourceLockMatrix(vulkanObj, "CollisionLockImage");
	CommandPoolParticleOnly* commandPoolParticleOnly
		= new  CommandPoolParticleOnly(vulkanObj, "CommandObj");
	ResourceGraphicsContainer* resourceGraphicsContainer
			= new ResourceGraphicsContainer(vulkanObj, "Resource Graphics Container Particle");
	ResourceComputeContainer* resourceComputeContainer
			= new ResourceComputeContainer(vulkanObj, "Resource Compute Container Particle");
	SwapChain* swapChain 
			= new SwapChain(vulkanObj, "SwapChain");
	RenderPassPOnly* renderPassPOnly 
			= new RenderPassPOnly(vulkanObj, "RenderPassPOnly");
	PipelineGraphicsParticleOnly* pipelineGraphicsParticle
			= new PipelineGraphicsParticleOnly(vulkanObj, "Graphics Pipeline Particle");
	PipelineComputeParticle* pipelineComputeParticle
		= new PipelineComputeParticle(vulkanObj, "Compute Pipeline Particle");
	FrameBuffer* frameBuffer 
			= new FrameBuffer(vulkanObj, "FrameBuffer");
	SyncObj* syncObjects 
			= new SyncObj(vulkanObj, "cubeSyncObj");
	DrawIParticle* drawICube = new DrawIParticle(vulkanObj, "Draw Instance Particle");
	
	vulkanObj->Create(configVCube);

	

	swapChain->Create();
	

	swapChain->SetSizzorMin(0);
	swapChain->SetSizzorMax(1);
	
	renderPassPOnly->Create(swapChain);
	

	frameBuffer->Create(renderPassPOnly, swapChain);
	resourceVertexParticle->Create(4);
	resourceCollMatrix->Create(3, resourceVertexParticle);
	resourceLockMatrix->Create(6, resourceVertexParticle);
	resourceParticlePush->Create(resourceVertexParticle);
	resourceAtomic->Create(5);
	resourceAtomicG->Create(5);
	
	resourceUBO->Create(2, swapChain, resourceVertexParticle);
	shaderObj->Create(resourceVertexParticle, resourceCollMatrix, swapChain);
	resourceGraphicsContainer->Create({ resourceVertexParticle,
										resourceParticlePush,
										resourceUBO,
										resourceCollMatrix,
										resourceLockMatrix,
										resourceAtomicG });
	resourceComputeContainer->Create({ 	resourceParticlePush,
										resourceUBO,
										resourceVertexParticle,
										resourceAtomic,
										resourceCollMatrix});
	
	pipelineGraphicsParticle->Create(swapChain, resourceGraphicsContainer, renderPassPOnly);
	
	pipelineComputeParticle->Create(resourceComputeContainer);
	
	commandPoolParticleOnly->Create(swapChain, renderPassPOnly, frameBuffer, 
		{ resourceGraphicsContainer,resourceComputeContainer },
		{ pipelineGraphicsParticle,pipelineComputeParticle });
	

	
	syncObjects->AddFence("inflightFence");
	syncObjects->AddFence("computeInflightFence");
	syncObjects->AddWaitSemaphore("imageAvailableSemaphore", VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT);
	syncObjects->AddWaitSemaphore("computeFinishedSemaphore", VK_PIPELINE_STAGE_VERTEX_INPUT_BIT);
	syncObjects->AddSignalSemaphore("renderFinishedSemaphore");


	//vulkanObj->createSemaphores();
	drawICube->Create(commandPoolParticleOnly, swapChain,
		renderPassPOnly, frameBuffer, syncObjects,
		{ resourceGraphicsContainer, resourceComputeContainer }, 
		{ pipelineGraphicsParticle,pipelineComputeParticle });
	

	double		lastTime = glfwGetTime();
	int			nbFrames = 0;
	VCUBECfg* cfg = (VCUBECfg*)vulkanObj->m_CFG;
	SetCallBacks(vulkanObj);
	mout << "In to loop" << ende;
	return Loop(drawICube,vulkanObj);

}

int main() try
{
	mout.Init("mps.log", "MPS");
	VCUBECfg* configVCUBE = new VCUBECfg;
	std::filesystem::path cwd = std::filesystem::current_path();
	mout << "Working Directory :" << cwd.string().c_str() << ende;
	configVCUBE->Create("mps.cfg");
	particleBoundary(configVCUBE);
	
	
}
catch (const std::exception& e)
{

	mout << "EXITING| TYPE:" << typeid(e).name() << " MSG:" << e.what() << ende;

	exit(1);
}
int VulkanObj::createSemaphores()
{
	VkSemaphoreCreateInfo semaphoreInfo = {};
	semaphoreInfo.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
	semaphoreInfo.pNext = nullptr;
	semaphoreInfo.flags = 0;

	vk_res = vkCreateSemaphore(GetLogicalDevice(), &semaphoreInfo, nullptr,
		&s_imageAvailableSemaphore);
	ASSERT_VK(vk_res);

	vk_res = vkCreateSemaphore(GetLogicalDevice(), &semaphoreInfo, nullptr,
		&s_renderFinishedSemaphore);
	ASSERT_VK(vk_res);

	return EXIT_SUCCESS;
}