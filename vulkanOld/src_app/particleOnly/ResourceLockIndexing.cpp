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
#include "VulkanObj/VulkanApp.hpp"
uint32_t ResourceLockMatrix::ArrayToIndex(uint32_t x, uint32_t y, uint32_t z, uint32_t len)
{

	//return x + y*len + z * len*len;
	//return ((x * len + y) * len) + z;
	return x + len * (y + len * z);


}
void ResourceLockMatrix::IndexToArray(uint32_t index, uint32_t len, uint32_t* ary)
{

	int c1,c2,c3;
	c1 = index / (len * len);
	c2 = (index - c1 * len * len) / len;
	c3 = index - len * (c2 + len * c1);

	ary[0] = c3;
	ary[1] = c2;
	ary[2] = c1;

#if 0
	ary[0] = index % len;
	ary[1] = (index / len) % len;
	ary[2] = index / (len*len);
#endif
}
bool ResourceLockMatrix::sortByLoc( rptvec lhs, rptvec rhs)
{ 
	return (lhs.LocationIndex < rhs.LocationIndex); 
};

void ResourceLockMatrix::IndexLockArray()
{
	
	
	uint32_t len = static_cast<uint32_t>(m_particle->m_SideLength);
	uint32_t width = len+1;
	uint32_t ary[3];

	uint32_t idx;
	for (uint32_t ii = 0; ii <= len; ii++)
	{
		for (uint32_t jj = 0; jj <= len; jj++)
		{
			for (uint32_t kk = 0; kk <= len; kk++)
			{
				idx = ArrayToIndex(ii, jj, kk, width);
				IndexToArray(idx, width, ary);
				if (ary[0] != ii || ary[1] != jj || ary[2] != kk)
				{
					//std::cout << "Error:Index of [" << ii << "," << jj << "," << kk << "]" << " is:" << idx << std::endl;
					//std::cout << "Array is [" << ary[0] << "," << ary[1] << "," << ary[2] << "]" << std::endl;
					return;
				}
				//std::cout << "Index of [" << ii << "," << jj << "," << kk << "]" << " is:" << idx << std::endl;
				//std::cout << "Array is [" << ary[0] << "," << ary[1] << "," << ary[2] << "]" << std::endl;

				rptvec pushvec;
				pushvec.LocationIndex = idx;
				pushvec.LocationArry = glm::uvec3(ary[0], ary[1], ary[2]);
				m_RptVec.push_back(pushvec);
			}
		}
	}


	size_t count = m_RptVec.size();
	std::sort(m_RptVec.begin(), m_RptVec.end(), sortByLoc);
	count = m_RptVec.size();

#if 0
	std::ostringstream  objtxt;
	objtxt << "VerifyIndex" << width << ".csv";
	std::ofstream ostrm(objtxt.str().c_str());
	if (!ostrm.is_open())
	{
		std::string err = "Cannot open report file::" + objtxt.str();
		throw std::runtime_error(err.c_str());
	}
	ostrm << "Index,Xloc,yloc,zloc" << std::endl;
	for (uint32_t ii = 0; ii < m_RptVec.size(); ii++)
	{
		ostrm << m_RptVec[ii].LocationIndex << ","
			<< m_RptVec[ii].LocationArry.x << ","
			<< m_RptVec[ii].LocationArry.y << ","
			<< m_RptVec[ii].LocationArry.z << std::endl;

	}

	if (ostrm.is_open())
	{
		ostrm.flush();
		ostrm.close();
	}
#endif
}
