/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/VulkanObj.hpp $
% $Id: VulkanObj.hpp 31 2023-06-12 20:17:58Z jb $
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

#include "particleOnly/pdata.hpp"
#include "ParticleOnly/SwapChain.hpp"
#include "ParticleBoundary/FrameBufferSubPass.hpp"
#include "ParticleBoundary/RenderPassSubPasses.hpp"
#include "VulkanObj/CommandPoolObj.hpp"
#include "VulkanObj/ObjLoader.hpp"
#include "ParticleOnly/ParticleStruct.hpp"
#include "ParticleOnly/ResourceAtomicCompute.hpp"
#include "ParticleOnly/ResourceAtomicGraphics.hpp"
#include "ParticleOnly/ResourceUBOParticle.hpp"
#include "ParticleBoundary/ResourceUBOBoundary.hpp"
#include "ParticleBoundary/ResourceUBOSphere.hpp"
#include "ParticleOnly/ResourcePushParticle.hpp"
#include "VulkanObj/ShaderObj.hpp"
#include "VulkanObj/CommandPoolObj.hpp"
#include "particleOnly/CommandParticleCompute.hpp"
#include "particleBoundary/CommandParticleGraphicsSub.hpp"
#include "ParticleBoundary/DrawParticleBoundary.hpp"
#include "ParticleBoundary/PipelineGraphicsBoundary.hpp"
#include "ParticleBoundary/ResourceVertexSphere.hpp"
#include "ParticleOnly/PipelineGraphicsParticleOnly.hpp"
#include "particleOnly/PipelineComputeParticle.hpp"
#include "particleOnly/ContainerGraphics.hpp"
#include "particleOnly/ContainerCompute.hpp"
#include "particleOnly/ResourceVertexParticle.hpp"
#include "ParticleBoundary/ResourceVertexCube.hpp"
#include "particleOnly/ResourcePushParticle.hpp"
#include "particleOnly/ResourceCollMatrix.hpp"
#include "particleOnly/ResourceLockMatrix.hpp"
#include "particleOnly/SyncObjParticleOnly.hpp"
#include "ParticleBoundary/ResourceSubpassBoundary.hpp"
#include "ParticleBoundary/ResourceSubpassParticle.hpp"
#include "ParticleBoundary/ImageDepth.hpp"
#include "ParticleBoundary/ImageColor.hpp"


