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



int ParticleBoundaryOnly(PerfObj* perObj, TCPObj* tcp, TCPObj* tcpapp, bool rmtFlag)
{

	VulkanObj* vulkanObj 
		= new VulkanObj;
	PhysDevObj* physDevObj 
		= new PhysDevObj(vulkanObj, "PhysDevObj");
	InstanceObj* instanceObject 
		= new InstanceObj(vulkanObj,"InstanceObject");
	ShaderObj* shaderObj 
		= new ShaderObj(vulkanObj, "ShaderObj");
	ResourceVertexCube* resourceVertexCube
		= new ResourceVertexCube(vulkanObj, "VertexCube");
	ResourceVertexParticle* resourceVertexParticle
		= new ResourceVertexParticle(vulkanObj, "VertexParticle");
	ResourceParticleUBO* resourceParticleUBO
		= new ResourceParticleUBO(vulkanObj, "ParticleUBO");
	ResourceBoundaryUBO* resourceBoundaryUBO
		= new ResourceBoundaryUBO(vulkanObj, "BoundaryUBO");
	ResourceAtomicCompute* resourceAtomicCompute
		= new ResourceAtomicCompute(vulkanObj, "AtomicCompute");
	ResourceAtomicGraphics* resourceAtomicG
		= new ResourceAtomicGraphics(vulkanObj, "AtomicG");
	ResourceParticlePush* resourceParticlePush
		= new ResourceParticlePush(vulkanObj, "PushConstants");
	ResourceCollMatrix* resourceCollMatrix
		= new ResourceCollMatrix(vulkanObj, "CollisionImage");
	ResourceLockMatrix* resourceLockMatrix
		= new ResourceLockMatrix(vulkanObj, "CollisionLockImage");
	ResourceGraphicsContainer* resourceGraphicsContainer
		= new ResourceGraphicsContainer(vulkanObj, "Resource Graphics Container Particle");
	ResourceComputeContainer* resourceComputeContainer
		= new ResourceComputeContainer(vulkanObj, "Resource Compute Container Particle");
	SwapChain* swapChain
		= new SwapChain(vulkanObj, "SwapChain");
	RenderPassSubs* renderPass
		= new RenderPassSubs(vulkanObj, "RenderPassBoundary");
	SubPassBoundary* subPassBoundary 
		= new SubPassBoundary(vulkanObj, "SubpassCube");
	SubPassParticle* subPassParticle 
		= new SubPassParticle(vulkanObj, "SubpassParticle");
	ImageDepth* imageDepth 
		= new ImageDepth(vulkanObj, "DepthImage");
	ImageColor* imageColor
		= new ImageColor(vulkanObj, "ColorImage");
	CommandPoolObj* commandPool = new CommandPoolObj(vulkanObj, "CmdPool");
	CommandObj* commandParticleCompute
		= new  CommandParticleCompute(vulkanObj, "CommandParticleCompute");
	CommandParticleBoundaryOnly* commandParticleGraphicsSub
		= new  CommandParticleBoundaryOnly(vulkanObj, "CommandObjParticleGraphics");
	PipelineGraphicsBoundary* pipelineGraphicsBoundary
		= new PipelineGraphicsBoundary(vulkanObj, "Graphics Pipeline Boundary");
	PipelineGraphicsParticleOnly* pipelineGraphicsParticle
		= new PipelineGraphicsParticleOnly(vulkanObj, "Graphics Pipeline Particle");
	PipelineComputeParticle* pipelineComputeParticle
		= new PipelineComputeParticle(vulkanObj, "Compute Pipeline Particle");
	FrameBufferSubPass* frameBuffer 
		= new FrameBufferSubPass(vulkanObj, "FrameBufferSubPass");
	SyncObj* syncObjects 
		= new SyncObj(vulkanObj, "cubeSyncObj");
	DrawParticleBoundary* drawParticleBoundary
		= new DrawParticleBoundary(vulkanObj, "Draw Instance Particle");
	ExportObject* exportObject = new ExportObject(vulkanObj, "SSBO Export");

	//================================= Create =================================
	
	vulkanObj->Create(CfgApp, physDevObj);
	instanceObject->Create();
	physDevObj->Create(CfgApp);
	swapChain->Create(physDevObj);
	swapChain->SetSizzorMin(0);
	swapChain->SetSizzorMax(1);
	//resourceIndex->Create();
	imageColor->Create(swapChain);
	imageDepth->Create(swapChain);
	// gets only image color
	subPassParticle->Create(swapChain, { imageColor,imageDepth }, 0, 1, 2);
	// Gets only depth
	subPassBoundary->Create(swapChain, { imageColor,imageDepth }, 0, 0, 2);
	renderPass->Create(swapChain, { imageColor,imageDepth }, { subPassParticle,subPassBoundary });
	frameBuffer->Create(renderPass, swapChain);
	resourceVertexParticle->Create(4);
	resourceVertexCube->Create(resourceVertexParticle);
	resourceCollMatrix->Create(3, resourceVertexParticle);
	resourceLockMatrix->Create(6, resourceVertexParticle);
	resourceParticlePush->Create(resourceVertexParticle);
	resourceAtomicCompute->Create(5, perObj);
	resourceAtomicG->Create(5,perObj);
	resourceParticleUBO->Create(2, swapChain, resourceVertexParticle);
	resourceBoundaryUBO->Create(1, swapChain, resourceVertexParticle);
	shaderObj->Create(resourceVertexParticle, resourceCollMatrix, resourceLockMatrix,swapChain);

	resourceGraphicsContainer->Create({ resourceVertexCube,
											resourceVertexParticle,
											resourceParticlePush,
											resourceParticleUBO,
											resourceBoundaryUBO,
											subPassParticle,
											subPassBoundary,			//#####JMB## fix this
											resourceCollMatrix,
											resourceLockMatrix,
											resourceAtomicG, });
	resourceComputeContainer->Create({ 	resourceParticlePush,
										resourceVertexParticle,
										resourceAtomicCompute,
										resourceLockMatrix,
										resourceCollMatrix});
	pipelineGraphicsBoundary->Create(shaderObj, swapChain, resourceGraphicsContainer, renderPass);
	pipelineGraphicsParticle->Create(shaderObj, swapChain, resourceGraphicsContainer, renderPass);
	pipelineComputeParticle->Create(shaderObj, resourceComputeContainer);
	
	// Create coomand for grphics pipline
	commandParticleGraphicsSub->Create(swapChain, 
										frameBuffer, 
										renderPass, 
										resourceGraphicsContainer,
										{ pipelineGraphicsBoundary,pipelineGraphicsParticle }
										);

	commandParticleCompute->Create(swapChain, 
									frameBuffer,
									renderPass, 
									resourceComputeContainer,
									{ pipelineComputeParticle }
									);
	
	commandPool->Create(physDevObj, swapChain, renderPass, frameBuffer,
		{ commandParticleGraphicsSub,commandParticleGraphicsSub,commandParticleCompute });
	exportObject->Create(resourceVertexParticle);
			
	syncObjects->Create();
	syncObjects->AddFence("inflightFence");
	syncObjects->AddFence("computeInflightFence");
	syncObjects->AddWaitSemaphore("imageAvailableSemaphore", VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT);
	syncObjects->AddWaitSemaphore("computeFinishedSemaphore", VK_PIPELINE_STAGE_VERTEX_INPUT_BIT);
	syncObjects->AddSignalImageSemaphore("renderFinishedSemaphore", swapChain->m_NumSwapImages);

	MemStats(vulkanObj);
	Extflg = false;
	if (Extflg == true)
		return 1;

	// Draw object needs command pool, swap chain, render pass, frame buffer, and sync ojects
	drawParticleBoundary->Create(commandPool, swapChain, renderPass, frameBuffer, syncObjects, exportObject);

	double		lastTime = glfwGetTime();
	int			nbFrames = 0;
	
	

	SetCallBacks(vulkanObj);
	int ret = 0;
	ret = Loop(perObj, tcp, tcpapp, drawParticleBoundary, vulkanObj, resourceGraphicsContainer, resourceComputeContainer);
	vulkanObj->CleanAll();
	vulkanObj->Cleanup();
	return ret;
}

