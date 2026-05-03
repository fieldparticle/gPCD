/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:04:37 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/mout2_0/mout.cpp $
% $Id: mout.cpp 27 2023-05-03 19:04:37Z jb $
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



********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision: 27 $
%*
%*
%******************************************************************
@doc
@module		MOut.cpp |
			mout is a logging/reporting replacement for cout. It will send
			messages to displays, windows, logfiles, and socket connetions.

@head3		Usage. |
@normal		mout is a global class that is allocated in mout.cpp and externalized
			in mout.hpp. To include it in any source file include mout.hpp.
			The global mout is always defined. mout can be implimented mout in an
			application specific manner in one of two ways.<nl>

			First, call the member function MsgStream::SetOutputCall(..) to call a "C" 
			function of prototype OUTCALL and pass it as a parameter. mout will <nl>
			use this function to perform output.<nl><nl>

			Second pass a pointer to a class which inherits MsgStream in the function<nl>
			MsgStream::SetOutClass(..) which take a pointer to a MsgStream object.<nl>
			This object should override the virtual function MsgStream::Output in order<nl>
			to function.<nl>


			
			A handy define is the 
@iex
			#define MOUT_DBG

@normal	
			which will use cout to report statistics about mout without<nl>
			being dependent on it.<nl>

			mout must be initialized before use by calling :<nl>
  
@iex 		mout.Init("logfile.txt","modulename"); <nl>

@normal		This initializes mout with the name of the logfile (logfile.txt)<nl>
			to which it reports and the module name which it uses in log file<nl>
			records to identify the reporting application.<nl>

			modulename is used to build the configuration file name which<nl>
			will be of the format [modulename].xml. The tags in this file <nl>
			are defined as follows:<nl>

@iex 		<mout queue_size="[size]" logfile="[logfile]" debug_level="[level]"></mout>
@normal<nl>
			where<em-><nl><nl>
			queue_size:<nl>  
			the size of the queue. This is the size the queue will<nl>
			grow to before flushing.<nl>
<nl>
			logfile:<nl> 
			the file to which log messages will be written. This will<nl>
			override the logfile passed in the init call.<nl>
<nl>
			debug_level:<nl>
			the debugging level. From 0-10. The level log<nl>
			messages will have to meet to be logged or printed<nl>
	        to the display. To set a debug print level add the<nl>
			log specification to the mout statement like so:<nl>

@iex		mout << log2 << "Displayed if debug_level>2" << ende;	
@normal
<nl>
			10 will print all messages.<nl>
<nl>
			file_logging:<nl>
			true if mout will write log messages to the log file.<nl>
			false if not.<nl>
<nl>
			sysid:<nl>
			A system specific identification.<nl>
<nl>
			The log file format is as follows:<nl>
<nl>
@iex 		[SystemID];[type];[MM/DD/YY];[HH:MM];[Module];[Message]
@normal

			where:<nl>
			[SystemID] <tab>is the system id from config file sysid.<nl>
			[type]	   <tab>is the log type either "dbg" or "log".<nl>
			[MM/DD/YY] <tab>is month/day/year.<nl>
			[HH:MM]    <tab>is the hour and minute.<nl>
			[Module]   <tab>is the module name.<nl>
			[Message]  <tab>is the system message.<nl>

********************************************************************
***                         CHANGE RECORD                        ***
********************************************************************
* $Header: https://jbworkstation/svn/svnroot/svnproj/cpp/mout/mout.cpp 2 2021-11-11 02:51:46Z jb $
* 10/29/96  Initial development							
*******************************************************************/
//#include "compiler/prewin.hpp"
//#include "types/typedefs.hpp"
//#include "CfgAdaptor/CfgAdaptor.hpp"
//#include "model/model.hpp"

#include <windows.h>
#include <fstream> 
#include <stdio.h>
#include <time.h>

//#include "process/utilities.hpp"

#include "mout2_0/mout.hpp"


#pragma warning(disable:4996)
//using namespace std ;
//using namespace std::rel_ops ;
char			msg[2048];
int				MsgStream::m_QueueSize=1000;
std::string			MsgStream::m_LogFileName;		
char*			MsgStream::m_Queue[MAX_QUEUE];		
int				MsgStream::m_Init = 0;
int				MsgStream::m_Item = 0;
std::ofstream*		MsgStream::m_out = NULL;
//Semaphore*		MsgStream::m_WQS = NULL;
bool			MsgStream::m_KillFlag = true;
//#define MOUT_DBG

int inCount=0;

/*************************************************************************
		   
  	    Description		
@mfunc  Vanilla constructor called by mout.cpp since this object is<nl>
		instanciated automatically.<nl>
		Author/Date<nl>
		Jack Bell/1997<nl>
<nl>
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>	
***********************************************************************/
MsgStream::MsgStream()
{

	m_ModuleName = new char[MAXSYSIDSIZE+1];
	memset(m_ModuleName,0,MAXSYSIDSIZE);
	m_ConfigFile = new char[MAXSYSIDSIZE+1];
	memset(m_ConfigFile,0,MAXSYSIDSIZE);
	m_SysidBuf = new char[MAXSYSIDSIZE+1];
	memset(m_SysidBuf,0,MAXSYSIDSIZE);
	m_Buffer = new char[MOUT_BUFFSIZE+1];
	memset((void*)m_Buffer,0,MOUT_BUFFSIZE);

	m_LogFlag		= 1;
	m_Item			= 0;	
	m_OutClass		= NULL;
	m_NoWaitSuspend	= false;
	m_OutSuspend	= false;
	m_LogSuspend	= false;
	m_StripBuf		= NULL;
	stringStream	= new std::ostrstream(m_Buffer,MOUT_BUFFSIZE);
	stringStream->seekp(0);

	m_OutCallTot	 = 0;
	
}
/*************************************************************************
	   
  		Description		
@mfunc   This is the overridden callback function from XMLReader that <nl>
		delivers the start tags from the configuration file<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	n/a<nl>
 
***********************************************************************/
void MsgStream::CallStartTag(
	std::string& Tag		//@parm String containing the XMLTAG.
)
{

//#ifdef MOUT_DBG
	std::cout << "Starting  :" << m_ModuleName  << "mout configuration is.." << std::endl;
	std::cout << "QueueSize :" << m_QueueSize   << std::endl;
	std::cout << "DebugLevel:" << m_DebugLevel  << std::endl;
	std::cout << "Log File  :" << m_LogFileName << std::endl;
	if(m_LogFlag)
		std::cout << "Logging?  :true"  << std::endl;
	else
		std::cout << "Logging?  :false" << std::endl;
	std::cout << "SysId     :" <<  m_SysidBuf << std::endl;
//#endif

};
/*************************************************************************
		   
  	    Description		
@mfunc	Init is called first thing to set up the logging and to read the<nl>
		configuration file.<nl>
		Author/Date<nl>		
 		Jack Bell/1997<nl>
<nl>	
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
void MsgStream::Init(
const char* FileName, 
const char* ModuleName)
{
	
	if(!m_Init)
	{
		/*CfgAdaptor* Cfg = new CfgAdaptor("mout.cfg","mout.bak");
		Cfg->AddItem("LogFile", "The File to which mout reports", "A Path/File Name");
		Cfg->AddItem("QueueSize", "mout keeps a queue so that it can write when it gets thread time; what size should this queue be(default=1000)", "0-65553");
		Cfg->AddItem("DebugLevel","This is the level of reporting mout will do; lower the number the fewer the messages.","0-10");
		Cfg->AddItem("LogFlag","This tells mout to log to a file or not.","1=log to file,2=do not log to file.");
		Cfg->Open(NULL);
		Cfg->Publish();*/

		//m_WQS = new Semaphore("WriteSemaphore");
		//m_WQS->InitSemaphore(MOUT_SEMEPHORE);
		m_LogFileName	= FileName;
		m_QueueSize 	= 1000;
	
	}
	strncpy(m_ModuleName,ModuleName,MAXSYSIDSIZE);
	
	m_QueueSize			= 1000;
	m_DebugLevel		= 5;
	m_LogFlag			= 1;
	m_LogThisMessage	= MSG_LOG;
	strncpy(m_SysidBuf,"WinApp",6);	
	sprintf(m_ConfigFile,"%s.xml",m_ModuleName);

	if(m_out == NULL)
	{
		m_KillFlag = true;
		m_out = new std::ofstream();
		if(m_KillFlag)
			m_out->open(m_LogFileName);
		else	
			m_out->open(m_LogFileName);

		m_KillFlag=false;

		if(m_out->fail())
		{
		
#ifdef MOUT_DBG
		std::cout << "MsgStream::WriteQueue|Error Opening Log" << std::endl;
#endif
		
			delete m_out;
			m_out = NULL;
			return ;
		}
		std::string InitalText;
		InitalText = "Starting App";
		m_out->write(InitalText.c_str(), InitalText.size());
		m_out->flush();
	}
	
#ifdef MOUT_DBG
	std::cout << _getcwd(NULL,0) << endl;
#endif
	

	////////////////////////////////////////////
	// Open and populate the config file based 
	// on the module name.
//	ParseFile(m_ConfigFile);
	m_Init=1;
		
}
/*************************************************************************
		   
  	    Description		
@mfunc	Vanilla destructor.<nl>
		Author/Date<nl>		
 		Jack Bell/1997<nl>
<nl>	
@rdesc 	n/a.<nl>
 
***********************************************************************/
MsgStream::~MsgStream()
{
	//If this object was used as the application specific base 
	// then this will = NULL.
	delete [] m_ModuleName;
	delete [] m_ConfigFile;
	delete [] m_SysidBuf;
	delete [] m_Buffer;

	if(m_Item)
		WriteQueue(m_Queue,m_Item);

	if(stringStream != NULL)
		delete stringStream;

	if(m_StripBuf!=NULL)
		delete m_StripBuf;

//	if(m_WQS)
//		delete m_WQS;

	if(m_out != NULL)
	{
		m_out->close();
		delete m_out;
	}
}
/*************************************************************************
**			   
**   	   Description		
** @func   Ends a line for the mout operators.
** <nl>		Author/Date		
** <nl> 	Jack Bell/1997
** <nl> 			
** <nl>		
** @rdesc 	Always returns passed in MsgStream object for operator chaining.
** 
***********************************************************************/
MsgStream& ende(
MsgStream& e	//@parm pointer to the parent class.
)
{	
	
	if(inCount>0)
		std::cout << "Block Violation."<< std::endl;
	else
		inCount++;

//	WaitForSingleObject(e.m_NWCallSem, INFINITE );
	char* tmp=NULL;
	char  type[32]={0};
	int ty=0;
		
	
	if(e.m_LogSuspend)
	{
		memset(e.GetBuffer(),0,MOUT_BUFFSIZE);
		//e.stringStream->seekp(0);
		//e.m_CurrentLevel=0;
//		ReleaseMutex(e.m_NWCallSem);
   		return e;
	}
	

	size_t len=strlen(e.m_Buffer) + strlen(e.m_ModuleName)+ 32 + strlen(e.m_SysidBuf);
	tmp	= new char[len+16384];
	memset(tmp,0,len+16384);

	
	struct 	tm*	tm;	
	time_t 	t = time(NULL);
	tm = localtime(&t);

	switch(e.m_LogThisMessage)
   	{
   		case MSG_DEBUG:
   			strcpy(type,"dbg");
   			break;
		case MSG_LOG:
			strcpy(type,"log");
			break;
   	}
#if 0
	sprintf(tmp,"\"%s\";%s;[%02d/%02d/%02d];[%02d:%02d];[%s]%s",e.m_SysidBuf,
																type, 
																tm->tm_mon+1,	
																tm->tm_mday,
																tm->tm_year,
																tm->tm_hour,
																tm->tm_min,
																e.m_ModuleName,
																e.m_Buffer);
	
#else


sprintf(tmp,"%s",e.m_Buffer);
#endif
	if(strstr(e.m_ModuleName,"daq.cpp"))
		ty=1;

	memset(e.m_ModuleName,0,sizeof(e.m_ModuleName));
	if(e.stringStream == NULL)
	{
		if(tmp != NULL)
			delete [] tmp;
		return e;	
	}

	/////////////////////////////////////////////////////////
	// Run the dispatch functions.
	if(e.m_CurrentLevel <= e.m_DebugLevel )
	{
		e.AddItemToQueue(tmp,len);

		
		
	}

	if(tmp != NULL)
	{
		delete [] tmp;
		tmp=NULL;
	}

	memset(e.GetBuffer(),0,MOUT_BUFFSIZE);
	e.stringStream->seekp(0);
	e.m_CurrentLevel=0;
	inCount=0;
   	return e;
};
/*************************************************************************
	   
  		Description		
@mfunc   Adds the message to the queue for eventual writing to the log file.<nl>
		Won't add  if there is no queue size (=0), the logflag is set to false,<nl>
		or the LofThisMessage flag is set to off.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	n/a<nl>
 
***********************************************************************/
void MsgStream::AddItemToQueue(const char *Buffer, size_t len)
{
	if(!m_Init)
	{
		std::cout << "mout has not been initialized - using defaults." << std::endl;
		std::cout << "Call Init(..) or check the configuration file." << std::endl;
		return ;
	}
	//m_WQS->BusyWait(MOUT_SEMEPHORE);
	m_Queue[m_Item]	= new char[len];
	memset(m_Queue[m_Item],0,len);
	strncpy(m_Queue[m_Item],Buffer,len);
	m_Item++;

	/////////////////////////////////////////////
	// Define MOUT_THREADED in your code if you
	// intend to call WriteQueue from a thread.
	if(m_Item >=1 || m_KillFlag==true)
		{
			WriteQueue(m_Queue,m_Item);
			m_Item = 0;
		}
	
	//m_WQS->UnLockSemaphore(MOUT_SEMEPHORE);
	
}
/*************************************************************************
	   
  		Description		
@mfunc   WriteQueue flushes the queue. must be called on shut down, or<nl> 
		when you want to spit out the messages before the correct number<nl>
		have built up in the queue.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	n/a<nl>
 
***********************************************************************/
void MsgStream::WriteQueue(char** Queue, size_t Items)
{
	
#ifdef MOUT_DBG
	std::cout << "MsgStream::WriteQueue - in." << std::endl;
#endif


	if(Items == 0)
	{
		
#ifdef MOUT_DBG
		std::cout << "MsgStream::WriteQueue - no write out." << std::endl;
#endif

		return;
	}

	for(int i=0;i<Items;i++)
	{
		//OutputDebugString(Queue[i]);
		//OutputDebugString("\r\n");
		*m_out << Queue[i] << std::endl;
		m_out->flush();

#ifdef MOUT_STDOUT
		std::cout << Queue[i] << std::endl;
#endif
		delete [] Queue[i];
		Queue[i] = NULL;
	}
	m_Item = 0;
	


#ifdef MOUT_DBG
	std::cout << "MsgStream::WriteQueue- write out." << std::endl;
#endif

}
char* MsgStream::strip(char* Message)
{
	if(m_StripBuf)
		delete m_StripBuf;
	m_StripBuf = new char[strlen(Message)*2];
	memset(m_StripBuf,0,strlen(Message)*2);
	
	for(unsigned int i=0;i<strlen(Message);i++)
	{
		if(Message[i] == '\r' || Message[i] == '\n')
			;
		else
			m_StripBuf[i] = Message[i];
	}
	return m_StripBuf;
}

MsgStream& MsgStream::mod(
const char* ModuleName //@parm Message type one of...?
)
{
	strncpy(m_ModuleName, ModuleName,64);
	return *this;
}
//No idea what this is.
MsgStream& MsgStream::rpt(
const int CallID)
{
	//m_CurCallID = CallID;
	return *this;
}
MsgStream& MsgStream::mod(const char* ModuleName, const int LineNumber)
{
	char tmp[256]={0};
	char drv[_MAX_DRIVE];
	char dir[_MAX_DIR];
	char fname[_MAX_FNAME];
	char ext[_MAX_EXT];

	_splitpath(ModuleName,drv,dir,fname,ext);

	memset(tmp,0,256);
	memset(m_ModuleName,0,MAXSYSIDSIZE);
	sprintf(tmp,"%s%s,line:%d,t:%ld",fname,ext,LineNumber,GetCurrentThreadId());
	strncpy(m_ModuleName,tmp,MAXSYSIDSIZE);
	return *this;
}
const char* MsgStream::SysID(const char* ApplicationName)
{
	memset(m_SysidBuf,0,MAXSYSIDSIZE);
	strncpy(m_SysidBuf,ApplicationName,MAXSYSIDSIZE);
	return m_SysidBuf;
}
MsgStream& MsgStream::CpyBf(char* OutString, int Size)
{
	//m_SaveOutBuf = OutString;
	//m_SaveOutBufSize = Size;
	return *this;
}
/*void MsgStream::SetOutputCall(OUTCALL Funct)
{
	m_OutCallList[m_OutCallTot] = Funct;
	m_OutCallTot++;
}*/
int MsgStream::UnSetNoWaitCall()
{
	//WaitForSingleObject(m_NWCallSem, INFINITE );
//	m_NWCallTot=0;
	//eleaseMutex(m_NWCallSem);	
	return 0;
}

/*************************************************************************
**			   
**   	    Description		
** @func    Establishes a message type. I think this is obsolete.
** <nl>		Author/Date		
** <nl> 	Jack Bell/1997
** <nl> 			
** <nl>		
** @rdesc 	Always returns passed in MsgStream object for operator chaining.
** 
***********************************************************************/
MsgStream& mt(
MsgStream& e,	//@parm pointer to the parent class.
int MessageType //@parm Message type one of...?
)
{
	return e;
}
/*************************************************************************
**			   
**   	    Description		
** @func    Windows Message Text
** <nl>		Author/Date		
** <nl> 	Jack Bell/1997
** <nl> 			
** <nl>		
** @rdesc 	Always returns passed in MsgStream object for operator chaining.
** 
***********************************************************************/
#ifdef _BGWIN
#include <windows.h>

MsgStream& WMT(MsgStream& e)
{
		LPTSTR lpMsgBuf;
		FormatMessage( 
			FORMAT_MESSAGE_ALLOCATE_BUFFER | 
			FORMAT_MESSAGE_FROM_SYSTEM | 
			FORMAT_MESSAGE_IGNORE_INSERTS,
			NULL,
			GetLastError(),
			MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), 
			(LPTSTR) &lpMsgBuf,
			0,
			NULL
		);
	
	if((e.stringStream->rdbuf()->in_avail()) == 0)
		return e;
	int l=strlen((const char*)lpMsgBuf);
	memset((void*)&lpMsgBuf[l-3],0,3);
	*(e.stringStream) << (char*)lpMsgBuf;
		return e;
	LocalFree( lpMsgBuf );
}
#endif
#ifdef _USES_OPENGL
#include "gl/glut.h"
MsgStream& OGLE(MsgStream& e)
{
	char tmp[256];
	memset(tmp,0,sizeof(tmp));
	int err = glGetError();
	if(err)
	{
		sprintf(tmp,"|OpenGL Error: %d is %s| ",err,gluErrorString(err));
	}
	//if ((e.stringStream->rdbuf()->in_avail()) == 0)
	//	return e;
	*(e.stringStream) << tmp;
	return e;
}
MsgStream& OGLE(MsgStream& e, int Error)
{
	char tmp[256];
	
	sprintf(tmp,"|OpenGL Error: %d is %s| ",Error, e.gl_error_string(Error));
	//if ((e.stringStream->rdbuf()->in_avail()) == 0)
//		return e;
	*(e.stringStream) << tmp;
	return e;
}
char const* MsgStream::gl_error_string(GLenum const err)
{
	switch (err)
	{
		// opengl 2 errors (8)
	case GL_NO_ERROR:
		return "GL_NO_ERROR";

	case GL_INVALID_ENUM:
		return "GL_INVALID_ENUM";

	case GL_INVALID_VALUE:
		return "GL_INVALID_VALUE";

	case GL_INVALID_OPERATION:
		return "GL_INVALID_OPERATION";

	case GL_STACK_OVERFLOW:
		return "GL_STACK_OVERFLOW";

	case GL_STACK_UNDERFLOW:
		return "GL_STACK_UNDERFLOW";

	case GL_OUT_OF_MEMORY:
		return "GL_OUT_OF_MEMORY";

	case GL_TABLE_TOO_LARGE:
		return "GL_TABLE_TOO_LARGE";

		// opengl 3 errors (1)
	case GL_INVALID_FRAMEBUFFER_OPERATION:
		return "GL_INVALID_FRAMEBUFFER_OPERATION";

		// gles 2, 3 and gl 4 error are handled by the switch above
	default:
		
		return nullptr;
	}
}

#endif
/*************************************************************************
	   
  		Description		
@mfunc   This is the overridden callback function from XMLReader that <nl>
		delivers the end tags from the configuration file<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	n/a<nl>
 
***********************************************************************/
void MsgStream::CallEndTag(
	std::string& Tag		//@parm String containing the XMLTAG.
)
{

};
/*************************************************************************
	   
  		Description		
@mfunc   This is the overridden callback function from XMLReader that <nl>
		delivers the literal strings from the configuration file.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	n/a<nl>
 
***********************************************************************/
void MsgStream::CallLiteral(
	std::string& Literal	//@parm String containing the literal.
)
{
	
};
/*************************************************************************
	   
  		Description		
@mfunc   Specific output function. Override this function to do<nl>
		display output. The defaule assumes a C++ cout console.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	n/a<nl>
 
***********************************************************************/
void MsgStream::Output(
char *Message	//@parm The message from mout.
)
{
	/*if(m_OutputCall != NULL)
		m_OutputCall(Message);
	else if(m_OutClass != NULL)
		m_OutClass->Output(Message);	
	else */
	std::cout << Message << std::endl;
}
/*************************************************************************
	   
  		Description		
@func   Zero level log. If Debug level is 0 then these are the only<nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& log(
MsgStream& e	//@parm MsgStream object.
)
{
	e.m_LogThisMessage=MSG_LOG;
	return e;
}
/*************************************************************************
	   
  		Description		
@func   1 level log. If Debug level is 1 then these are the only<nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& logl1(
MsgStream& e	//@parm MsgStream object.
)
{
	e.m_CurrentLevel=1;
	e.m_LogThisMessage=MSG_LOG;
	return e;
}
/*************************************************************************
	   
  		Description		
@func   2 level log. If Debug level is 2 then these are the only<nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& logl2(
MsgStream& e	//@parm MsgStream object.
)
{
	e.m_CurrentLevel=2;
	e.m_LogThisMessage=MSG_LOG;
	return e;
}
/*************************************************************************
	   
  		Description		
@func   3 level log. If Debug level is 3 then these are the only<nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& logl3(
MsgStream& e	//@parm MsgStream object.
)
{
	e.m_CurrentLevel=3;
	e.m_LogThisMessage=MSG_LOG;
	return e;
}
/*************************************************************************
	   
  		Description		
@func   4 level log. If Debug level is 4 then these are the only<nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& logl4(
MsgStream& e	//@parm MsgStream object.
)
{
	e.m_CurrentLevel=4;
	e.m_LogThisMessage=MSG_LOG;
	return e;
}
/*************************************************************************
	   
  		Description		
@func   5 level log. If Debug level is 5 then these are the only<nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& logl5(
MsgStream& e	//@parm MsgStream object.
)
{
	e.m_CurrentLevel=5;
	e.m_LogThisMessage=MSG_LOG;
	return e;
}
/*************************************************************************
	   
  		Description		
@func   6 level log. If Debug level is 6 then these are the only<nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& logl6(
MsgStream& e	//@parm MsgStream object.
)
{
	e.m_CurrentLevel=6;
	e.m_LogThisMessage=MSG_LOG;
	return e;
}
/*************************************************************************
	   
  		Description		
@func   7 level log. If Debug level is 7 then these are the only<nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& logl7(
MsgStream& e	//@parm MsgStream object.
)
{
	e.m_CurrentLevel=7;
	e.m_LogThisMessage=MSG_LOG;
	return e;
}
/*************************************************************************
	   
  		Description		
@func  8 level log. If Debug level is 8 then these are the only<nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& logl8(
MsgStream& e		//@parm MsgStream object.
)
{
	e.m_CurrentLevel=8;
	e.m_LogThisMessage=MSG_LOG;
	return e;
}
/*************************************************************************
	   
  		Description		
@func   9 level log. If Debug level is 9 then these are the only<nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& logl9(
MsgStream& e		//@parm MsgStream object.
)
{
	e.m_CurrentLevel=9;
	e.m_LogThisMessage=MSG_LOG;
	return e;
}
/*************************************************************************
	   
  		Description		
@func   10 level log. If Debug level is 10 then these are the only<nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& logl10(
MsgStream& e	//@parm MsgStream object.
)
{
	e.m_CurrentLevel=10;
	e.m_LogThisMessage=MSG_LOG;
	return e;
}
/*************************************************************************
	   
  		Description		
@func   debug level log. Always logs this message - indicates an error. <nl>
		messages displayed.<nl>
		Author/Date<nl>	
		Jack Bell/1997<nl>
			
@rdesc 	Always returns passed in MsgStream object for operator chaining.<nl>
 
***********************************************************************/
MsgStream& debug(MsgStream& e)
{
	e.m_LogThisMessage=MSG_DEBUG;
	return e;
}
