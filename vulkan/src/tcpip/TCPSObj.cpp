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
#include <filesystem>
#include "TCPSObj.hpp"
#include "../mout2_0/mout.hpp"
extern MsgStream mout;
namespace fs = std::filesystem;

int TCPObj::WritePort(std::string Message)
{
    
    iSendResult = send( ClientSocket, Message.c_str(),  static_cast<int>(Message.size()),0);
    if (iSendResult == SOCKET_ERROR) 
    {
        printf("send failed with error: %d\n", WSAGetLastError());
        closesocket(ClientSocket);
        WSACleanup();
        return 1;
    }
    //printf("Bytes sent: %d\n", iSendResult);
    return 0;

}
int TCPObj::WritePort(const char* Block,uint32_t Len)
{
    iSendResult = send( ClientSocket, Block, Len,0);
    if (iSendResult == SOCKET_ERROR) 
    {
        printf("send failed with error: %d\n", WSAGetLastError());
        closesocket(ClientSocket);
        WSACleanup();
        return 1;
    }
    //printf("Bytes sent: %d\n", iSendResult);
    return 0;

}

int TCPObj::CompareCommand()
{
    if(m_SRecvBuf.compare("quit") == 0)
        return 1;
    else if(m_SRecvBuf.compare("stop") == 0)
        return 2;
    return 0;
}

int TCPObj::ReadPortN()
{
    fd_set ReadFDs;
    FD_ZERO(&ReadFDs);
    FD_SET(ClientSocket, &ReadFDs);
    // No longer need server socket
    closesocket(ListenSocket);
    timeval tm;
    tm.tv_sec = 5;
    tm.tv_usec = static_cast<long>(0.0011);

    // Receive until the peer shuts down the connection
    if (select(0, &ReadFDs, NULL, NULL, &tm) > 0)
    {
    
        memset(m_Recvbuf,0,m_Recvbuflen);
        if (FD_ISSET(ClientSocket, &ReadFDs))
        {
            iResult = recv(ClientSocket, m_Recvbuf, m_Recvbuflen, 0);
            if (iResult > 0) 
            {
                std::cout << "Bytes received:" << iResult << " Message:" << m_Recvbuf << std::endl;
                mout << "Bytes received:" << iResult << " Message:" << m_Recvbuf << ende;
                m_SRecvBuf = m_Recvbuf;
                return 0;
                // Echo the buffer back to the sender
            }
            else  
            {
                printf("recv failed with error: %d\n", WSAGetLastError());
                return 1;
            }
        }
    }
    return 0;
}
std::string TCPObj::ReadPortString()
{
    ReadPort();
    return GetBuffer();
}
int TCPObj::ReadPort()
{
    fd_set ReadFDs;
    FD_ZERO(&ReadFDs);
    FD_SET(ClientSocket, &ReadFDs);
    // No longer need server socket
    closesocket(ListenSocket);
    timeval tm;
    tm.tv_sec = 10;
    tm.tv_usec = 0;
    // Receive until the peer shuts down the connection
    if (select(0, &ReadFDs, NULL, NULL, &tm) > 0)
    {
    
        memset(m_Recvbuf,0,m_Recvbuflen);
        if (FD_ISSET(ClientSocket, &ReadFDs))
        {
            iResult = recv(ClientSocket, m_Recvbuf, m_Recvbuflen, 0);
            if (iResult > 0) 
            {
                mout << "Bytes received:" << iResult << " Message:" << m_Recvbuf << ende;
                m_SRecvBuf = m_Recvbuf;
                return iResult;
                // Echo the buffer back to the sender
            }
            else  
            {
                mout << "Recieve Failed with WSA error:" <<  WSAGetLastError() << ende;
                printf("recv failed with error: %d\n", WSAGetLastError());
                return iResult;
            }
        }
    }

    std::cout << "TimeOut" << std::endl;
    return -2;
}
int TCPObj::Connect()
{

    
    iResult = listen(ListenSocket, SOMAXCONN);
    if (iResult == SOCKET_ERROR) {
        printf("listen failed with error: %d\n", WSAGetLastError());
        closesocket(ListenSocket);
        WSACleanup();
        return 1;
    }
   
    // Accept a client socket
    ClientSocket = accept(ListenSocket, NULL, NULL);
    if (ClientSocket == INVALID_SOCKET) {
        printf("accept failed with error: %d\n", WSAGetLastError());
        closesocket(ListenSocket);
        WSACleanup();
        return 1;
    }
    std::cout << "Client Accepted" << std::endl;
    mout << "Client Accepted" << ende;
    return 0;


}

int TCPObj::Create()
{
    	    
    // Initialize Winsock
    iResult = WSAStartup(MAKEWORD(2,2), &wsaData);
    if (iResult != 0) {
        printf("WSAStartup failed with error: %d\n", iResult);
        return 1;
    }

    ZeroMemory(&hints, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;
    hints.ai_flags = AI_PASSIVE;

    // Resolve the server address and port
    iResult = getaddrinfo(NULL, m_PortAddress.c_str(), &hints, &result);
    if ( iResult != 0 ) {
        printf("getaddrinfo failed with error: %d\n", iResult);
        WSACleanup();
        return 1;
    }

    // Create a SOCKET for the server to listen for client connections.
    ListenSocket = socket(result->ai_family, result->ai_socktype, result->ai_protocol);
    if (ListenSocket == INVALID_SOCKET) {
        printf("socket failed with error: %ld\n", WSAGetLastError());
        freeaddrinfo(result);
        WSACleanup();
        return 1;
    }

    // Setup the TCP listening socket
    iResult = bind( ListenSocket, result->ai_addr, (int)result->ai_addrlen);
    if (iResult == SOCKET_ERROR) {
        printf("bind failed with error: %d\n", WSAGetLastError());
        freeaddrinfo(result);
        closesocket(ListenSocket);
        WSACleanup();
        return 1;
    }

    freeaddrinfo(result);

    return 0;
}
int TCPObj::Close()
{
     // shutdown the connection since we're done
    iResult = shutdown(ClientSocket, SD_SEND);
    if (iResult == SOCKET_ERROR) {
        printf("shutdown failed with error: %d\n", WSAGetLastError());
        closesocket(ClientSocket);
        WSACleanup();
        return 1;
    }
    // cleanup
    closesocket(ClientSocket);
    WSACleanup();
    return 0;
}

std::vector<std::string> TCPObj::SendPerfFile(const char* filename, uint32_t Type)
{
    std::vector<std::string> vecstr;

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
              
     	std::string stripflnm =  fs::path(filename).filename().string();   
        tcpbuf << Type << "," << static_cast<int>(numblocks) << "," << stripflnm;
        // 1 for pqb
        // 2 for report file
        // 3 for image
        
        WritePort(tcpbuf.str().c_str());
        tcpbuf.clear();
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

   return vecstr;
}
std::vector<std::string> TCPObj::SendImgFile(const char* filename)
{
    std::vector<std::string> vecstr;

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

   return vecstr;
}