#include "particleOnly\ExternalProcess.hpp"
#include <vector>
#include <algorithm>
#include <iostream>

ExternalProcess::ExternalProcess()
    : m_ProcessHandle(nullptr),
      m_ProcessID(0)
{
}


ExternalProcess::~ExternalProcess()
{
    // Closing the handle does NOT terminate the external program.
    if (m_ProcessHandle)
    {
        CloseHandle(m_ProcessHandle);
        m_ProcessHandle = nullptr;
    }
}


bool ExternalProcess::Start(std::string& video_exe, 
                            std::string& video_app_path, 
                            std::string& video_cap_dir,
                            std::string& video_cmd_line)
{
    // Don't start another process if this object already
    // owns a running process.
    if (IsRunning())
        return false;

    // Clean up an old process handle if the previous process
    // has already terminated.
    if (m_ProcessHandle)
    {
        CloseHandle(m_ProcessHandle);
        m_ProcessHandle = nullptr;
        m_ProcessID = 0;
    }
    
    std::replace(video_app_path.begin(), video_app_path.end(), '/', '\\');
    std::string full_command = "\"" + video_app_path + "\\" + video_exe + "\"" + " " + video_cmd_line;
    std::string command_dir = video_app_path;
    

    STARTUPINFOA startupInfo{};
    PROCESS_INFORMATION processInfo{};

    startupInfo.cb = sizeof(startupInfo);

    // CreateProcessA requires a writable command-line buffer.
    std::vector<char> commandWin(
        full_command.begin(),
        full_command.end()
    );

    commandWin.push_back('\0');

    BOOL result = CreateProcessA(
        nullptr,                // Application name
        commandWin.data(),         // Command line
        nullptr,                // Process security
        nullptr,                // Thread security
        FALSE,                  // Inherit handles
        0,                      // Creation flags
        nullptr,                // Environment
        command_dir.c_str(),                // Current directory
        &startupInfo,
        &processInfo
    );

    if (!result)
    {
        DWORD error = GetLastError();

        std::cout << "CreateProcessA failed\n";
        std::cout << "Command: [" << commandWin.data() << "]\n";
        std::cout << "Error code: " << error << "\n";

        char* message = nullptr;

        FormatMessageA(
            FORMAT_MESSAGE_ALLOCATE_BUFFER |
            FORMAT_MESSAGE_FROM_SYSTEM |
            FORMAT_MESSAGE_IGNORE_INSERTS,
            nullptr,
            error,
            0,
            (LPSTR)&message,
            0,
            nullptr
        );

        if (message)
        {
            std::cout << "Error message: " << message << "\n";
            LocalFree(message);
        }

        return false;
    }

    // We don't need the thread handle.
    CloseHandle(processInfo.hThread);

    // Keep the process handle.
    m_ProcessHandle = processInfo.hProcess;
    m_ProcessID = processInfo.dwProcessId;

    return true;
}


bool ExternalProcess::Terminate(UINT exitCode)
{
    if (!m_ProcessHandle)
        return false;

    if (!IsRunning())
    {
        CloseHandle(m_ProcessHandle);

        m_ProcessHandle = nullptr;
        m_ProcessID = 0;

        return true;
    }

    BOOL result = TerminateProcess(
        m_ProcessHandle,
        exitCode
    );

    if (!result)
        return false;

    // TerminateProcess is asynchronous. Wait only here so we know
    // Windows has actually finished terminating the process.
    WaitForSingleObject(
        m_ProcessHandle,
        INFINITE
    );

    CloseHandle(m_ProcessHandle);

    m_ProcessHandle = nullptr;
    m_ProcessID = 0;

    return true;
}


bool ExternalProcess::IsRunning() const
{
    if (!m_ProcessHandle)
        return false;

    DWORD result = WaitForSingleObject(
        m_ProcessHandle,
        0
    );

    return result == WAIT_TIMEOUT;
}


DWORD ExternalProcess::GetProcessID() const
{
    return m_ProcessID;
}


HANDLE ExternalProcess::GetProcessHandle() const
{
    return m_ProcessHandle;
}