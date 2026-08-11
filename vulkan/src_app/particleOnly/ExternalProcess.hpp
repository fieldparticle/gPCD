#pragma once

#include <string>
#include "windows.h"
class ExternalProcess
{
public:
    ExternalProcess();
    ~ExternalProcess();

    // Prevent accidental copying of the Windows HANDLE.
    ExternalProcess(const ExternalProcess&) = delete;
    ExternalProcess& operator=(const ExternalProcess&) = delete;

    bool Start(std::string& video_exe, 
        std::string& video_app_path, 
        std::string& video_cap_dir,
        std::string& video_cmd_line);
    bool Terminate(UINT exitCode = 0);

    bool IsRunning() const;

    DWORD GetProcessID() const;
    HANDLE GetProcessHandle() const;

private:
    HANDLE m_ProcessHandle;
    DWORD  m_ProcessID;
};