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

#include "TCPCObj.hpp"
#include "mout2_0/mout.hpp"
extern MsgStream			mout;
int TCPCObj::ReadPort()
{
    memset(m_Recvbuf,0,m_Recvbuflen);
    iResult = recv(ConnectSocket, m_Recvbuf, m_Recvbuflen, 0);
    if ( iResult > 0 )
    {
        mout << "Bytes received:" << iResult << ende;
        m_SRecvBuf = m_Recvbuf ;
        return iResult;
    }
    else if ( iResult == 0 )
        mout << "Connection closed." << ende;
    else
        mout << "recv failed with error:" << WSAGetLastError() << ende;
    return 0;

}

int TCPCObj::Close()
{
      // shutdown the connection since no more data will be sent
    iResult = shutdown(ConnectSocket, SD_SEND);
    if (iResult == SOCKET_ERROR) {
        mout << "shutdown failed with error:"<<  WSAGetLastError() << ende;
        closesocket(ConnectSocket);
        WSACleanup();
        return 1;
    }

    // cleanup
    closesocket(ConnectSocket);
    WSACleanup();
    return 0;

}
int TCPCObj::WritePort(std::string Command)
{
    
    iResult = send( ConnectSocket, Command.c_str(), (int)Command.size(), 0 );
    if (iResult == SOCKET_ERROR) 
    {
        mout << "send failed with error:" << WSAGetLastError() << ende;
        closesocket(ConnectSocket);
        WSACleanup();
        return 1;
    }

    mout << "Bytes Sent:" <<  iResult << ende;
    return 0;
}
int TCPCObj::WritePort(char* Buf, int Size)
{
    
    iResult = send( ConnectSocket, Buf, Size, 0 );
    if (iResult == SOCKET_ERROR) 
    {
        mout << "send failed with error:" << WSAGetLastError() << ende;
        closesocket(ConnectSocket);
        WSACleanup();
        return 1;
    }

    mout << "Bytes Sent:" <<  iResult << ende;
    return 0;
}


int TCPCObj::Create()
{

	 // Initialize Winsock
    iResult = WSAStartup(MAKEWORD(2,2), &wsaData);
    if (iResult != 0) {
        mout << "WSAStartup failed with error:" <<  iResult << ende;
        return 1;
    }

    ZeroMemory( &hints, sizeof(hints) );
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;

    // Resolve the server address and port
    iResult = getaddrinfo(m_Server.c_str(), m_PortAddress.c_str(), &hints, &result);
    if ( iResult != 0 ) {
        mout << "getaddrinfo failed with error" <<  iResult << ende;
        WSACleanup();
        return 1;
    }
    mout << "Get addrd Info at port:" << m_PortAddress.c_str() << " at ip:" << m_Server.c_str() << ende;
    // Attempt to connect to an address until one succeeds
    for(ptr=result; ptr != NULL ;ptr=ptr->ai_next) 
    {

        // Create a SOCKET for connecting to server
        ConnectSocket = socket(ptr->ai_family, ptr->ai_socktype, 
            ptr->ai_protocol);
        if (ConnectSocket == INVALID_SOCKET) {
            mout << "socket failed with error:" <<  WSAGetLastError() << ende;
            WSACleanup();
            return 1;
        }

        // Connect to server.
        iResult = connect( ConnectSocket, ptr->ai_addr, (int)ptr->ai_addrlen);
        if (iResult == SOCKET_ERROR)
        {
            closesocket(ConnectSocket);
            ConnectSocket = INVALID_SOCKET;
            continue;
        }
        break;

    }

    mout << "Conected to server at :" << m_Server <<  " Port:" <<  m_PortAddress << ende;

    freeaddrinfo(result);

    if (ConnectSocket == INVALID_SOCKET) {
        mout << "Unable to connect to server!" << ende;
        WSACleanup();
        return 1;
    }

    return 0;
}

uint32_t TCPCObj::SendImgFile()
{
    /*
    ReadPort();

    std::ifstream fin(filename, std::ios_base::in|std::ios::binary );
    if (fin.is_open())
    {
        fin.seekg( 0, std::ios::beg );
        std::streamoff size = fin.tellg();
        fin.seekg( 0, std::ios::end );
        size = fin.tellg();
        float numblocks = static_cast<float>(size)/m_Recvbuflen;
        numblocks = std::ceil(numblocks);
        fin.seekg( 0, std::ios::beg );
        std::ostringstream tcpbuf;
              
        
        tcpbuf << static_cast<int>(numblocks) << "," << filename;
        // 1 for cfg file
        // 2 for report file
        // 3 for image
        
        WritePort(tcpbuf.str().c_str());

        char* buffer = new char[m_Recvbuflen];
        memset(buffer,0,m_Recvbuflen);

        while (true)
        {
           fin.read(buffer, m_Recvbuflen);
           WritePort(buffer,m_Recvbuflen);
           memset(buffer,0,m_Recvbuflen);
           if (fin.eof())
                break;
        }

       // if the bytes of the block are less than 1024,
       // use fin.gcount() calculate the number, put the va
       // into var s
       //std::string s(buffer, fin.gcount());
       //vecstr.push_back(s);

       delete[] buffer;
       fin.close();
   }
   else
   {
        std::cerr << "Cannot open file:" << filename << std::endl;
   }
   */
   return 0;
}
