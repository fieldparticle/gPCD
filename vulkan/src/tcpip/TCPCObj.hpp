/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/CommandObj.hpp $
% $Id: CommandObj.hpp 31 2023-06-12 20:17:58Z jb $
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

#pragma once
#define WIN32_LEAN_AND_MEAN
#include <iostream>
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdlib.h>
#include <stdio.h>
#include <vector>
#include <fstream>
#include <strstream>
#include <sstream>


// Need to link with Ws2_32.lib, Mswsock.lib, and Advapi32.lib
#pragma comment (lib, "Ws2_32.lib")
#pragma comment (lib, "Mswsock.lib")
#pragma comment (lib, "AdvApi32.lib")


#define DEFAULT_BUFLEN 512
#define DEFAULT_PORT "50004"
class TCPCObj
{
	
	public:
	
		
	 WSADATA wsaData;
	 SOCKET ConnectSocket = INVALID_SOCKET;
	 struct addrinfo *result = NULL,
					 *ptr = NULL,
					 hints;
	 const char *sendbuf = "quit";
	 
	int iResult;
	char* m_Recvbuf;
	int m_Recvbuflen;
	std::string m_Server = "127.0.0.1";
	std::string m_PortAddress = "50004";
	std::string m_ReadBuffer;
	std::string m_SRecvBuf;
	
	void SetServerIP(std::string IPAddress)
	{
		m_Server = 	IPAddress;
	};
		
	void SetServerPort(std::string PortAddress)
	{
		m_PortAddress = PortAddress;
	};
	uint32_t SendImgFile();
	void SetBufSize(uint32_t BufSize)
	{
        m_Recvbuflen = BufSize;
        m_Recvbuf = new char[m_Recvbuflen];
        memset(m_Recvbuf,0,m_Recvbuflen);


	}
    std::string GetBuffer()
    {
        return m_SRecvBuf;

    }
	int Create();
	int ReadPort();
	int WritePort(std::string Command);
	int WritePort(char* buf, int Size);
	int Close();
};