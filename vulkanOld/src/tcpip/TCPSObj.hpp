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
class TCPObj
{

	public:

	WSADATA wsaData;
    int iResult;

    SOCKET ListenSocket = INVALID_SOCKET;
    SOCKET ClientSocket = INVALID_SOCKET;

    struct addrinfo *result = NULL;
    struct addrinfo hints;

    int iSendResult;
    char* m_Recvbuf;
    int m_Recvbuflen;

    std::string m_SRecvBuf;
    std::string m_PortAddress;

    TCPObj(){};
    int Create();
    int ReadPort();
    int CompareCommand();
    int Close();
    std::vector<std::string> SendPerfFile(const char* filename, uint32_t Type);
    std::vector<std::string> SendImgFile(const char* filename);
    int Connect();
    int ReadPortN();
    std::string ReadPortString();
    int WritePort(std::string Message);
    int WritePort(const char* Block,uint32_t Len);
    void Reset()
    {
        iResult = 0;
        memset(m_Recvbuf,0,m_Recvbuflen);
        iSendResult = 0;
        m_SRecvBuf = "";
    };

	void SetServerPort(std::string PortAddress)
	{
		m_PortAddress = PortAddress;
	};

    std::string GetServerPort()
	{
		return m_PortAddress;
	};
	void SetBufSize(uint32_t BufSize)
	{
        m_Recvbuflen = BufSize;
        m_Recvbuf = new char[m_Recvbuflen];
        memset(m_Recvbuf,0,m_Recvbuflen);


	}
    std::vector <std::string> GetSplitBuffer()
    {
        std::vector<std::string> result;
        std::stringstream ss;
        ss << m_SRecvBuf;
        while( ss.good() )
        {
            std::string substr;
            getline( ss, substr, ',' );
            result.push_back( substr );
        }
     return result;
    }
    std::string GetBuffer()
    {
        return m_SRecvBuf;

    }
};