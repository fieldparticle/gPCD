#pragma once

#include <string>
//class VulkanApp;

class ExportObject : public BaseObj
{
    VkDevice m_Device = VK_NULL_HANDLE;
    VkQueue m_Queue = VK_NULL_HANDLE;
    uint32_t m_QueueFamilyIndex = 0;
    VmaAllocator m_Allocator = VK_NULL_HANDLE;
    VkCommandPool m_CommandPool = VK_NULL_HANDLE;
    Resource *m_RO = VK_NULL_HANDLE;

public:
    ExportObject(VulkanObj* App, std::string Name) : BaseObj(Name, 0, App) {};
    ~ExportObject() {};
    void Cleanup();
    void Create(Resource* RO);

    bool ExportBuffer(const std::string& outputFile);

private:
  
    VkCommandBuffer BeginExportCommands();
    void EndExportCommands(VkCommandBuffer commandBuffer);

    bool WriteBinaryFile(
        const std::string& outputFile,
        const void* data,
        VkDeviceSize bufferSize);

};