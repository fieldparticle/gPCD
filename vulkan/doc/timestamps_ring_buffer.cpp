#include <vulkan/vulkan.h>
#include <vector>
#include <iostream>
#include <stdexcept>

constexpr uint32_t TIMESTAMP_COUNT = 6;   // start, broad, narrow, pre-render, post-render, end
constexpr uint32_t FRAME_LAG       = 3;   // how many frames we wait before reading

struct GPUTimer {
    VkQueryPool pool;
    std::vector<uint64_t> results;
    bool ready = false;
};

std::vector<GPUTimer> gpuTimers;

VkQueryPool createTimestampPool(VkDevice device) {
    VkQueryPoolCreateInfo qpInfo{};
    qpInfo.sType = VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO;
    qpInfo.queryType = VK_QUERY_TYPE_TIMESTAMP;
    qpInfo.queryCount = TIMESTAMP_COUNT;

    VkQueryPool qp;
    if (vkCreateQueryPool(device, &qpInfo, nullptr, &qp) != VK_SUCCESS) {
        throw std::runtime_error("Failed to create query pool");
    }
    return qp;
}

void initGPUTimers(VkDevice device, uint32_t swapchainImages) {
    gpuTimers.resize(swapchainImages);
    for (auto &timer : gpuTimers) {
        timer.pool = createTimestampPool(device);
        timer.results.resize(TIMESTAMP_COUNT);
    }
}

void recordTimingMarkers(VkCommandBuffer cmd, VkQueryPool qp) {
    vkCmdResetQueryPool(cmd, qp, 0, TIMESTAMP_COUNT);

    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, qp, 0);
    // compute broad phase...
    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, qp, 1);
    // compute narrow phase...
    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, qp, 2);
    // barrier to graphics
    // render pre-pass
    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, qp, 3);
    // render pass
    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, qp, 4);
    // end of frame
    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, qp, 5);
}

void fetchTimingResults(VkDevice device, VkPhysicalDevice physDev, uint32_t frameIndex) {
    auto &timer = gpuTimers[frameIndex];
    if (!timer.ready) return; // not yet used N frames ago

    VkResult res = vkGetQueryPoolResults(
        device,
        timer.pool,
        0,
        TIMESTAMP_COUNT,
        sizeof(uint64_t) * TIMESTAMP_COUNT,
        timer.results.data(),
        sizeof(uint64_t),
        VK_QUERY_RESULT_64_BIT // no WAIT_BIT — don't block
    );

    if (res == VK_NOT_READY) {
        // GPU still working on that old frame — skip reporting
        return;
    } else if (res != VK_SUCCESS) {
        std::cerr << "Error reading query results\n";
        return;
    }

    VkPhysicalDeviceProperties props;
    vkGetPhysicalDeviceProperties(physDev, &props);
    double period_ns = props.limits.timestampPeriod;

    auto ms = [period_ns](uint64_t delta) {
        return (delta * period_ns) / 1e6;
    };

    double tBroad  = ms(timer.results[1] - timer.results[0]);
    double tNarrow = ms(timer.results[2] - timer.results[1]);
    double tRender = ms(timer.results[4] - timer.results[3]);
    double tFrame  = ms(timer.results[5] - timer.results[0]);

    std::cout << "[Frame " << frameIndex << "] Broad: " << tBroad
              << " ms, Narrow: " << tNarrow
              << " ms, Render: " << tRender
              << " ms, Total: " << tFrame << " ms\n";

    timer.ready = false; // mark as consumed
}

void onFrameStart(uint32_t currentFrame) {
    // Mark the query pool for this frame as ready for reuse in FRAME_LAG frames
    gpuTimers[currentFrame].ready = true;
}

// In your main loop, you’d call:
// onFrameStart(frameIndex);
// recordTimingMarkers(cmdBuf, gpuTimers[frameIndex].pool);
// submit...
// fetchTimingResults(device, physicalDevice, (frameIndex + FRAME_LAG) % swapchainImages);
