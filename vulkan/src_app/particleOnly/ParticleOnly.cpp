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
#include "TCPIP/TCPSObj.hpp"


int ParticleOnly(PerfObj* perObj, TCPObj* tcp, TCPObj* tcpapp, bool rmtFlag)
{
	
	VulkanObj* vulkanObj = new VulkanObj;
	PhysDevObj* physDevObj = new PhysDevObj(vulkanObj, "PhysDevObj");
	InstanceObj* instanceObject = new InstanceObj(vulkanObj,"InstanceObject");
	ShaderObj* shaderObj = new ShaderObj(vulkanObj, "ShaderObj");
	//ResourceVertexCube* resourceVertexCube
	ResourceVertexParticle* resourceVertexParticle
		= new ResourceVertexParticle(vulkanObj, "VertexParticle");
	ResourceParticleUBO* resourceUBO
		= new ResourceParticleUBO(vulkanObj, "ParticleUBO");
	ResourceAtomicCompute* resourceAtomic
		= new ResourceAtomicCompute(vulkanObj, "ComputeAtomic");
	ResourceAtomicGraphics* resourceAtomicG
		= new ResourceAtomicGraphics(vulkanObj, "GraphicsAtomic");
	ResourceParticlePush* resourceParticlePush
		= new ResourceParticlePush(vulkanObj, "PushConstants");
	ResourceCollMatrix* resourceCollMatrix
		= new ResourceCollMatrix(vulkanObj, "CollisionImage");
	ResourceLockMatrix* resourceLockMatrix
		= new ResourceLockMatrix(vulkanObj, "CollisionLockImage");
	ResourceGraphicsContainer* resourceGraphicsContainer
		= new ResourceGraphicsContainer(vulkanObj, "GraphicsContainerParticle");
	ResourceComputeContainer* resourceComputeContainer
		= new ResourceComputeContainer(vulkanObj, "ResourceContainerCompute");
	SwapChain* swapChain
		= new SwapChain(vulkanObj, "SwapChain");
	CommandPoolObj* commandPool = new CommandPoolObj(vulkanObj, "CmdPool");
	
	CommandParticleGraphics* commandParticleGraphics
			= new  CommandParticleGraphics(vulkanObj, "CommandObjParticleGraphics");
	CommandParticleCompute* commandParticleCompute
			= new  CommandParticleCompute(vulkanObj, "CommandParticleCompute");

	RenderPassObj* renderPass = new RenderPassPOnly(vulkanObj, "RenderPassPOnly");
		
	PipelineGraphicsParticleOnly* pipelineGraphicsParticle
		= new PipelineGraphicsParticleOnly(vulkanObj, "Graphics Pipeline Particle");

	PipelineComputeParticle* pipelineComputeParticle
		= new PipelineComputeParticle(vulkanObj, "Compute Pipeline Particle");

	FrameBufferObj* frameBuffer = new FrameBuffer(vulkanObj, "FrameBuffer");

	SyncObj* syncObjects = new SyncObj(vulkanObj, "cubeSyncObj");
	DrawParticleOnly* drawParticleOnly = new DrawParticleOnly(vulkanObj, "Draw Instance Particle");
	

	//================================= Create =================================
	
	vulkanObj->Create(CfgApp,physDevObj);
	instanceObject->Create();
	physDevObj->Create(CfgApp);
	swapChain->Create(physDevObj);
	swapChain->SetSizzorMin(0);
	swapChain->SetSizzorMax(1);
	// Render pass needs swap chain
	renderPass->Create(swapChain);
	// Frame Buffer needs render pass and swapchain
	frameBuffer->Create(renderPass, swapChain);
	// Particle buffer contains particle list
	// needs binding point
	resourceVertexParticle->Create(4);
	// Particle cell hash table needs bind point and particle list
	resourceCollMatrix->Create(3, resourceVertexParticle);
	// Atomic counter array needs bind point and particle list
	resourceLockMatrix->Create(6, resourceVertexParticle);
	// Push constants need particle list.
	resourceParticlePush->Create(resourceVertexParticle);
	// Compute atomic counters for debugging
	resourceAtomic->Create(5,perObj);
	// Graphics atomic counters for debugging
	resourceAtomicG->Create(5,perObj);
	// UBO for model,projectsion, and view matricies
	resourceUBO->Create(2, swapChain, resourceVertexParticle);
	// Shader object needs particle list, particle cell hash table.  
	shaderObj->Create(resourceVertexParticle, resourceCollMatrix, resourceLockMatrix, swapChain);

	// Store all resources for graphics pipline
	resourceGraphicsContainer->Create({ resourceVertexParticle,
										resourceParticlePush,
										resourceUBO,
										resourceCollMatrix,
										resourceLockMatrix,
										resourceAtomicG });
	// Store all resources for compute pipline
	resourceComputeContainer->Create({ 	resourceParticlePush,
										resourceUBO,
										resourceVertexParticle,
										resourceAtomic,
										resourceLockMatrix,
										resourceCollMatrix});

	// Create graphics pipeline which needs swap chain, resource container, and render pass.
	pipelineGraphicsParticle->Create(shaderObj,swapChain, resourceGraphicsContainer, renderPass);
	// Create compute pipeline which needs compute resource container.
	pipelineComputeParticle->Create(shaderObj,resourceComputeContainer);
	
	// Create coomand for grphics pipline
	commandParticleGraphics->Create(swapChain, frameBuffer, { renderPass },
		resourceGraphicsContainer,{pipelineGraphicsParticle });
	commandParticleCompute->Create(swapChain, frameBuffer, { },
		resourceComputeContainer,{pipelineComputeParticle });
	// Create command pool which needs physical device, swap chain, render pass
	// frame buffer and pipelines
	commandPool->Create(physDevObj,swapChain, renderPass, frameBuffer,
			{ commandParticleGraphics,commandParticleCompute });
	Extflg = false;
	if(Extflg == true)
			return 1;

	syncObjects->Create();
	syncObjects->AddFence("inflightFence");
	syncObjects->AddFence("computeInflightFence");
	syncObjects->AddWaitSemaphore("imageAvailableSemaphore", VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT);
	syncObjects->AddWaitSemaphore("computeFinishedSemaphore", VK_PIPELINE_STAGE_VERTEX_INPUT_BIT);
	syncObjects->AddSignalSemaphore("renderFinishedSemaphore");

	MemStats(vulkanObj);

	if(Extflg == true)
			return 1;
	
	// Draw object needs command pool, swap chain, render pass, frame buffer, and sync ojects
	drawParticleOnly->Create(commandPool, swapChain, renderPass, frameBuffer, syncObjects);
	
	double		lastTime = glfwGetTime();
	int			nbFrames = 0;

	SetCallBacks(vulkanObj);
	int ret = 0;

	if(rmtFlag == false)
		ret = Loop(perObj, tcp,tcpapp, drawParticleOnly,vulkanObj, resourceGraphicsContainer, resourceComputeContainer);
	else
		ret = NoPerfLoop(perObj, tcp, tcpapp,drawParticleOnly,vulkanObj, resourceGraphicsContainer, resourceComputeContainer);
	
	vulkanObj->CleanAll();
	vulkanObj->Cleanup();
#if 1 // ##JMB## MAKE THIS A config item
	if (CfgApp->GetBool("application.doAuto", true))
		Sleep(1000);
#endif	
	return ret;

}
