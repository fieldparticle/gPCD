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


int ParticleLighting(PerfObj* perObj, TCPObj* tcp, TCPObj* tcpapp, bool rmtFlag)
{

	VulkanObj* vulkanObj
		= new VulkanObj;
	PhysDevObj* physDevObj
		= new PhysDevObj(vulkanObj, "PhysDevObj");
	InstanceObj* instanceObject
		= new InstanceObj(vulkanObj,"InstanceObject");
	ShaderObj* shaderObj
		= new ShaderObj(vulkanObj, "ShaderObj");
	//ResourceLightingSphere* resourceVertexSphere
	//	= new ResourceLightingSphere(vulkanObj, "VertexSphere");
	//ResourceLightingCube* resourceVertexCube
		//= new ResourceLightingCube(vulkanObj, "VertexCube");
	ResourceLightingParticle* resourceLightingParticle
		= new ResourceLightingParticle(vulkanObj, "VertexParticle");
	ResourceParticleUBO* resourceParticleUBO
		= new ResourceParticleUBO(vulkanObj, "ParticleUBO");
	ResourceBoundaryUBO* resourceBoundaryUBO
		= new ResourceBoundaryUBO(vulkanObj, "BoundaryUBO");
	ResourceUBOSphere* resourceUBOSphere
		= new ResourceUBOSphere(vulkanObj, "SphereUBO");
	ResourceAtomicCompute* resourceAtomicCompute
		= new ResourceAtomicCompute(vulkanObj, "AtomicCompute");
	ResourceAtomicGraphics* resourceAtomicG
		= new ResourceAtomicGraphics(vulkanObj, "AtomicG");
	ResourceParticlePush* resourceParticlePush
		= new ResourceParticlePush(vulkanObj, "PushConstants");
	ResourceCollMatrix* resourceCollMatrix
		= new ResourceCollMatrix(vulkanObj, "CollisionImage");
	ResourceLighting* resourceLighting
		= new ResourceLighting(vulkanObj, "LightingResources");
	ResourceLightingSurface* resourceLightingSurface
		= new ResourceLightingSurface(vulkanObj, "LightingSurfaces");
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
	CommandLightingGraphics* commandParticleGraphicsSub
		= new  CommandLightingGraphics(vulkanObj, "CommandObjParticleGraphics");
	PipelineGraphicsLighting* pipelineGraphicsLighting
		= new PipelineGraphicsLighting(vulkanObj, "Graphics Pipeline Boundary");
	PipelineGraphicsParticleOnly* pipelineGraphicsParticle
		= new PipelineGraphicsParticleOnly(vulkanObj, "Graphics Pipeline Particle");
	PipelineComputeLighting* pipelineComputeParticle
		= new PipelineComputeLighting(vulkanObj, "Compute Pipeline Lighting");
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
	resourceLightingParticle->Create(4);
	//resourceVertexSphere->Create(resourceLightingParticle);
	//resourceVertexCube->Create(resourceLightingParticle);
	resourceCollMatrix->Create(3, resourceLightingParticle);
	resourceLightingSurface->Create(9, resourceLightingParticle);

	resourceLockMatrix->Create(6, resourceLightingParticle);
	resourceLighting->Create(8, resourceLightingParticle);
	resourceParticlePush->Create(resourceLightingParticle);
	resourceAtomicCompute->Create(5, perObj);
	resourceAtomicG->Create(5,perObj);
	resourceParticleUBO->Create(2, swapChain, resourceLightingParticle);
	resourceBoundaryUBO->Create(1, swapChain, resourceLightingParticle);
	resourceUBOSphere->Create(7, swapChain, resourceLightingParticle);
	shaderObj->Create(resourceLightingParticle, resourceCollMatrix, resourceLockMatrix,swapChain);

	resourceGraphicsContainer->Create({ 	
											resourceLightingParticle,
											resourceParticlePush,
											resourceParticleUBO,
											resourceBoundaryUBO,
											resourceUBOSphere,
											subPassParticle,
											subPassBoundary,			//#####JMB## fix this
											resourceLighting,
											resourceCollMatrix,
											resourceLockMatrix,
											resourceLightingSurface,
											resourceAtomicG});
	resourceGraphicsContainer->ClearTempMemory();
	resourceComputeContainer->Create({ 	resourceParticlePush,
										resourceLighting,
										resourceLightingParticle,
										resourceAtomicCompute,
										resourceLockMatrix,
										resourceCollMatrix,
										resourceLightingSurface });
	resourceComputeContainer->ClearTempMemory();
	pipelineGraphicsLighting->Create(shaderObj, swapChain, resourceGraphicsContainer, renderPass);
	pipelineGraphicsParticle->Create(shaderObj, swapChain, resourceGraphicsContainer, renderPass);
	pipelineComputeParticle->Create(shaderObj, resourceComputeContainer);

	// Create coomand for grphics pipline
	commandParticleGraphicsSub->Create(swapChain,
										frameBuffer,
										renderPass,
										resourceGraphicsContainer,
										{ pipelineGraphicsLighting,pipelineGraphicsParticle }
										);

	commandParticleCompute->Create(swapChain,
									frameBuffer,
									renderPass,
									resourceComputeContainer,
									{ pipelineComputeParticle }
									);

	commandPool->Create(physDevObj, swapChain, renderPass, frameBuffer,
		{ commandParticleGraphicsSub,commandParticleCompute });
	exportObject->Create(resourceLightingParticle);

	syncObjects->Create();
	syncObjects->AddFence("inflightFence");
	syncObjects->AddFence("computeInflightFence");
	syncObjects->AddWaitSemaphore("imageAvailableSemaphore", VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT);
	syncObjects->AddWaitSemaphore("computeFinishedSemaphore", VK_PIPELINE_STAGE_VERTEX_INPUT_BIT | VK_PIPELINE_STAGE_VERTEX_SHADER_BIT | VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT);
	syncObjects->AddSignalImageSemaphore("renderFinishedSemaphore", swapChain->m_NumSwapImages);

	MemStats(vulkanObj);
	Extflg = false;
	if (Extflg == true)
		return 1;

	// Draw object needs command pool, swap chain, render pass, frame buffer, and sync ojects
	drawParticleBoundary->Create(commandPool, swapChain, renderPass, frameBuffer, syncObjects,exportObject);

	double		lastTime = glfwGetTime();
	int			nbFrames = 0;



	SetCallBacks(vulkanObj);
	int ret = 0;
	ret = Loop(perObj, tcp, tcpapp, drawParticleBoundary, vulkanObj, resourceGraphicsContainer, resourceComputeContainer);
	vulkanObj->CleanAll();
	vulkanObj->Cleanup();
	return ret;

}
