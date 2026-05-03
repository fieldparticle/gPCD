/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/DescriptorSSBO.cpp $
% $Id: DescriptorSSBO.cpp 28 2023-05-03 19:30:42Z jb $
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

class mpsverifycfg : public ConfigObj 
{
	public:
		uint32_t								m_StudyFlag;
		uint32_t								m_SubStudyFlag;
		uint32_t								m_studyType;


		std::vector<std::string>				m_textureNames;
		uint32_t								m_numTextures;

		uint32_t								m_NumParticles;
		uint32_t								m_srcParticle;
		glm::vec2								m_part_pos;
		glm::vec2								m_part_vel;
		std::vector<Particle>					m_particleStruct{};
		std::vector<Particle>					m_boundryStruct{};
		float									m_dt;
	
		mpsverifycfg() : ConfigObj(){};
		void GetSettings();
		

};