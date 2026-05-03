#include "VulkanObj/VulkanApp.hpp"


void MemStats(VulkanObj* vulkanObj)
{

	mout << "Total Memory Allocated:" << vulkanObj->m_TotalMemoryBytes << ende;
	VmaTotalStatistics memuse;
	vmaCalculateStatistics(vulkanObj->m_vmaAllocator, &memuse);

	for (size_t mm = 0; mm < VK_MAX_MEMORY_TYPES; mm++)
	{
		if (memuse.memoryType[mm].statistics.blockCount >= 1)
		{
			mout << "VmaTotalStatistics.memoryType[mm].statistics.blockCount:"
				<< memuse.memoryType[mm].statistics.blockCount << ende;
			mout << "VmaTotalStatistics.memoryType[mm].statistics.blockBytes:"
				<< memuse.memoryType[mm].statistics.blockBytes << ende;
			mout << "VmaTotalStatistics.memoryType[mm].statistics.allocationBytes:"
				<< memuse.memoryType[mm].statistics.allocationBytes << ende;
			mout << "VmaTotalStatistics.memoryType[mm].statistics.allocationCount:"
				<< memuse.memoryType[mm].statistics.allocationCount << ende;
		}
	}

	for (size_t mm = 0; mm < VK_MAX_MEMORY_HEAPS; mm++)
	{
		if (memuse.memoryHeap[mm].statistics.blockCount >= 1)
		{
			mout << "VmaTotalStatistics.memoryHeap[mm].statistics.blockCount:"
				<< memuse.memoryHeap[mm].statistics.blockCount << ende;
			mout << "VmaTotalStatistics.memoryHeap[mm].statistics.blockBytes:"
				<< memuse.memoryHeap[mm].statistics.blockBytes << ende;
			mout << "VmaTotalStatistics.memoryHeap[mm].statistics.allocationBytes:"
				<< memuse.memoryHeap[mm].statistics.allocationBytes << ende;
			mout << "VmaTotalStatistics.memoryHeap[mm].statistics.allocationCount:"
				<< memuse.memoryHeap[mm].statistics.allocationCount << ende;
		}
	}

	mout << "VmaTotalStatistics.total.statistics.allocationCount:"
		<< memuse.total.statistics.allocationCount << ende;
	mout << "VmaTotalStatistics.total.statistics.blockBytes:"
		<< memuse.total.statistics.blockBytes << ende;
	mout << "VmaTotalStatistics.total.statistics.allocationBytes:"
		<< memuse.total.statistics.allocationBytes << ende;
	mout << "VmaTotalStatistics.total.statistics.allocationCount:"
		<< memuse.total.statistics.allocationCount << ende;
}