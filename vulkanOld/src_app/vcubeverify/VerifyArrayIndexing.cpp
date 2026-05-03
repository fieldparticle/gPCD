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
#include "mpsVerify.hpp"
uint32_t ArrayToIndex(uint32_t x, uint32_t y, uint32_t z, uint32_t len)
{

	//return x + y*len + z * len*len;
	//return ((x * len + y) * len) + z;
	return x + len * (y + len * z);


}
void IndexToArray(uint32_t index, uint32_t len, uint32_t* ary)
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
uint32_t ArrayToIndexV2(uint32_t x, uint32_t y, uint32_t z, 
						uint32_t W,uint32_t H,uint32_t L)
{
	uint32_t w = W+1;
	uint32_t h = H+1;
	return x + w * (y + h * z);


}
void IndexToArrayV2(uint32_t index, uint32_t W,uint32_t H,uint32_t L, uint32_t* ary)
{
	int c1,c2,c3;
	uint32_t w = W+1;
	uint32_t h = H+1;
	c1 = index / (w * h);
	c2 = (index - c1 * w * h) / w;
	c3 = index - w * (c2 + w * c1);

	ary[0] = c3;
	ary[1] = c2;
	ary[2] = c1;

}
struct rptvec {
	uint32_t LocationIndex;
	glm::uvec3 LocationArry;
	uint32_t Err;
};
bool sortByLoc(const rptvec &lhs, const rptvec &rhs) { return (lhs.LocationIndex < rhs.LocationIndex); };

void VerifyArrayIndexingV2()
{
	
	uint32_t Width = 20;
	uint32_t Height = 20;
	uint32_t Length = 64;
	uint32_t ary[3];
	uint32_t start = 0;
	std::vector<rptvec> rptvecout;
	
#if 0
	uint32_t idx = ArrayToIndex(x, y, z, width);
	std::cout << "Index of [" << x << "," << y << "," << z << "]" << " is:" << idx << std::endl;
	IndexToArray(idx, width, ary);
	std::cout << "Array is [" << ary[0] << "," << ary[1] << "," << ary[2] << "]" << std::endl;
#endif	
	std::ostringstream  objtxt;
	objtxt << "VerifyIndex" << Width << ".csv";
	std::ofstream ostrm(objtxt.str().c_str());
	
	
	uint32_t idx;
	for (uint32_t ii = start; ii <= Width; ii++)
	{
		for (uint32_t jj = start; jj <= Height; jj++)
		{
			for (uint32_t kk = start; kk <= Length; kk++)
			{
				rptvec pushvec;
				idx = ArrayToIndexV2(ii, jj, kk, Width, Height, Length);
				IndexToArrayV2(idx, Width, Height, Length, ary);
				pushvec.Err=0;
				if (ary[0] != ii || ary[1] != jj || ary[2] != kk)
				{
					std::cout << "Error:Index of [" << ii << "," << jj << "," << kk << "]" << " is:" << idx << std::endl;
					std::cout << "Array is [" << ary[0] << "," << ary[1] << "," << ary[2] << "]" << std::endl;
					//return;
					pushvec.Err=idx;
				}
				std::cout << "Index of [" << ii << "," << jj << "," << kk << "]" << " is:" << idx << std::endl;
				std::cout << "Array is [" << ary[0] << "," << ary[1] << "," << ary[2] << "]" << std::endl;

				
				pushvec.LocationIndex = idx;
				pushvec.LocationArry = glm::uvec3(ary[0], ary[1], ary[2]);
				rptvecout.push_back(pushvec);
			}
		}
	}


	size_t count = rptvecout.size();
	std::sort(rptvecout.begin(), rptvecout.end(), sortByLoc);
	count = rptvecout.size();
	if (!ostrm.is_open())
	{
		std::string err = "Cannot open report file::" + objtxt.str();
		throw std::runtime_error(err.c_str());
	}
	ostrm << "Index,Xloc,yloc,zloc,err" << std::endl;
	for (uint32_t ii = 0; ii < rptvecout.size(); ii++)
	{
		ostrm << rptvecout[ii].LocationIndex << ","
			<< rptvecout[ii].LocationArry.x << ","
			<< rptvecout[ii].LocationArry.y << ","
			<< rptvecout[ii].LocationArry.z << ","
			<<  rptvecout[ii].Err << std::endl;

	}

	if (ostrm.is_open())
	{
		ostrm.flush();
		ostrm.close();
	}
	
}

void VerifyArrayIndexing()
{
	
	uint32_t len = 3;
	uint32_t width = len+1;
	uint32_t ary[3];
	uint32_t start = 0;
	std::vector<rptvec> rptvecout;
	
#if 0
	uint32_t idx = ArrayToIndex(x, y, z, width);
	std::cout << "Index of [" << x << "," << y << "," << z << "]" << " is:" << idx << std::endl;
	IndexToArray(idx, width, ary);
	std::cout << "Array is [" << ary[0] << "," << ary[1] << "," << ary[2] << "]" << std::endl;
#endif	
	std::ostringstream  objtxt;
	objtxt << "VerifyIndex" << width << ".csv";
	std::ofstream ostrm(objtxt.str().c_str());
	
	
	uint32_t idx;
	for (uint32_t ii = start; ii <= len; ii++)
	{
		for (uint32_t jj = start; jj <= len; jj++)
		{
			for (uint32_t kk = start; kk <= len; kk++)
			{
				idx = ArrayToIndex(ii, jj, kk, width);
				IndexToArray(idx, width, ary);
				if (ary[0] != ii || ary[1] != jj || ary[2] != kk)
				{
					std::cout << "Error:Index of [" << ii << "," << jj << "," << kk << "]" << " is:" << idx << std::endl;
					std::cout << "Array is [" << ary[0] << "," << ary[1] << "," << ary[2] << "]" << std::endl;
					return;
				}
				std::cout << "Index of [" << ii << "," << jj << "," << kk << "]" << " is:" << idx << std::endl;
				std::cout << "Array is [" << ary[0] << "," << ary[1] << "," << ary[2] << "]" << std::endl;

				rptvec pushvec;
				pushvec.LocationIndex = idx;
				pushvec.LocationArry = glm::uvec3(ary[0], ary[1], ary[2]);
				rptvecout.push_back(pushvec);
			}
		}
	}


	size_t count = rptvecout.size();
	std::sort(rptvecout.begin(), rptvecout.end(), sortByLoc);
	count = rptvecout.size();
	if (!ostrm.is_open())
	{
		std::string err = "Cannot open report file::" + objtxt.str();
		throw std::runtime_error(err.c_str());
	}
	ostrm << "Index,Xloc,yloc,zloc" << std::endl;
	for (uint32_t ii = 0; ii < rptvecout.size(); ii++)
	{
		ostrm << rptvecout[ii].LocationIndex << ","
			<< rptvecout[ii].LocationArry.x << ","
			<< rptvecout[ii].LocationArry.y << ","
			<< rptvecout[ii].LocationArry.z << std::endl;

	}

	if (ostrm.is_open())
	{
		ostrm.flush();
		ostrm.close();
	}
	
}
