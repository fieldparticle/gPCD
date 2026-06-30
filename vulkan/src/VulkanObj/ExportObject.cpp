#include "VulkanObj/VulkanApp.hpp"

#include <fstream>
#include <stdexcept>

void ExportObject::Create(Resource* RO)

{

    m_Device = m_App->m_LogicalDevice;
    m_Queue = m_App->m_GraphicsQueue;
    m_QueueFamilyIndex  = m_App->m_GraphicsQueueIndex;
    m_Allocator         = m_App->m_vmaAllocator;
    m_RO = RO;
    VkCommandPoolCreateInfo poolInfo{};
    poolInfo.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    poolInfo.queueFamilyIndex = m_QueueFamilyIndex;
    poolInfo.flags = VK_COMMAND_POOL_CREATE_TRANSIENT_BIT;

    VkResult result = vkCreateCommandPool(
        m_Device,
        &poolInfo,
        nullptr,
        &m_CommandPool);

    if (result != VK_SUCCESS)
        throw std::runtime_error("ExportObject failed to create command pool.");
};

void ExportObject::Cleanup()
{
    if (m_CommandPool != VK_NULL_HANDLE)
    {
        vkDestroyCommandPool(
            m_Device,
            m_CommandPool,
            nullptr);

        m_CommandPool = VK_NULL_HANDLE;
    }
}

bool ExportObject::ExportBuffer(const std::string& outputFile)
{
    if (m_RO->m_Buffers[0] == VK_NULL_HANDLE)
        return false;

    if (m_RO->m_BufSize == 0)
        return false;

    VkBuffer stagingBuffer = VK_NULL_HANDLE;
    VmaAllocation stagingAllocation = VK_NULL_HANDLE;

    VmaAllocationCreateInfo allocInfo{};
    allocInfo.usage = VMA_MEMORY_USAGE_AUTO;
    allocInfo.flags =
        VMA_ALLOCATION_CREATE_HOST_ACCESS_RANDOM_BIT |
        VMA_ALLOCATION_CREATE_MAPPED_BIT;

    VkBufferCreateInfo bufferInfo{};
    bufferInfo.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bufferInfo.size = m_RO->m_BufSize;
    bufferInfo.usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT;
    bufferInfo.sharingMode = VK_SHARING_MODE_EXCLUSIVE;

    VkResult result = vmaCreateBuffer(
        m_Allocator,
        &bufferInfo,
        &allocInfo,
        &stagingBuffer,
        &stagingAllocation,
        nullptr);

    if (result != VK_SUCCESS)
        return false;

    VkCommandBuffer commandBuffer =
        BeginExportCommands();

    VkBufferCopy copyRegion{};
    copyRegion.srcOffset = 0;
    copyRegion.dstOffset = 0;
    copyRegion.size = m_RO->m_BufSize;

    vkCmdCopyBuffer(
        commandBuffer,
        m_RO->m_Buffers[0],
        stagingBuffer,
        1,
        &copyRegion);

    EndExportCommands(commandBuffer);

    void* mappedData = nullptr;

    result = vmaMapMemory(
        m_Allocator,
        stagingAllocation,
        &mappedData);

    if (result != VK_SUCCESS)
    {
        vmaDestroyBuffer(
            m_Allocator,
            stagingBuffer,
            stagingAllocation);

        return false;
    }

    bool success =
        WriteBinaryFile(
            outputFile,
            mappedData,
            m_RO->m_BufSize);

    vmaUnmapMemory(
        m_Allocator,
        stagingAllocation);

    vmaDestroyBuffer(
        m_Allocator,
        stagingBuffer,
        stagingAllocation);

    return success;
}

VkCommandBuffer ExportObject::BeginExportCommands()
{
    VkCommandBufferAllocateInfo allocInfo{};
    allocInfo.sType =
        VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    allocInfo.commandPool = m_CommandPool;
    allocInfo.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    allocInfo.commandBufferCount = 1;

    VkCommandBuffer commandBuffer = VK_NULL_HANDLE;

    VkResult result = vkAllocateCommandBuffers(
        m_Device,
        &allocInfo,
        &commandBuffer);

    if (result != VK_SUCCESS)
        throw std::runtime_error("ExportObject failed to allocate command buffer.");

    VkCommandBufferBeginInfo beginInfo{};
    beginInfo.sType =
        VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    beginInfo.flags =
        VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;

    result = vkBeginCommandBuffer(
        commandBuffer,
        &beginInfo);

    if (result != VK_SUCCESS)
        throw std::runtime_error("ExportObject failed to begin command buffer.");

    return commandBuffer;
}

void ExportObject::EndExportCommands(
    VkCommandBuffer commandBuffer)
{
    VkResult result = vkEndCommandBuffer(commandBuffer);

    if (result != VK_SUCCESS)
        throw std::runtime_error("ExportObject failed to end command buffer.");

    VkSubmitInfo submitInfo{};
    submitInfo.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    submitInfo.commandBufferCount = 1;
    submitInfo.pCommandBuffers = &commandBuffer;

    result = vkQueueSubmit(
        m_Queue,
        1,
        &submitInfo,
        VK_NULL_HANDLE);

    if (result != VK_SUCCESS)
        throw std::runtime_error("ExportObject failed to submit command buffer.");

    vkQueueWaitIdle(m_Queue);

    vkFreeCommandBuffers(
        m_Device,
        m_CommandPool,
        1,
        &commandBuffer);
}

bool ExportObject::WriteBinaryFile(
    const std::string& outputFile,
    const void* data,
    VkDeviceSize bufferSize)
{
    std::ofstream out(
        outputFile,
        std::ios::binary | std::ios::out);

    if (!out.is_open())
        return false;

    out.write(
        reinterpret_cast<const char*>(data),
        static_cast<std::streamsize>(bufferSize));

    out.close();

    return out.good();
}