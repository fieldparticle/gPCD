/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:04:37 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/mout2_0/mout.hpp $
% $Id: mout.hpp 27 2023-05-03 19:04:37Z jb $
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
%*$Revision: 27 $
%*
%*
%******************************************************************/

#ifndef _MSGSTREAM_HPP
#define _MSGSTREAM_HPP
typedef char flag;
#pragma warning(disable:4996)

#include <iostream>
#include <strstream>
#include <sys/types.h>
#include <time.h>



//@const Forces a logging for debug (error) messages.
const flag 	MSG_DEBUG 			= 1;
//@const Forces a logging for log messages.
const flag 	MSG_LOG				= 2;

//@const Maximum size of the queue.
const int 	MAX_QUEUE  			= 1000;
const int	MOUT_BUFFSIZE		= 2048;
const int   MOUT_MAX_THRD_BUFS	= 10;

//@const Maximum size of the unique system ID.
const int	MAXSYSIDSIZE		= 1024;

const int	MOUT_SEMEPHORE		= 0;
/*
@class The is the actual replacement for cout.
*/

typedef float GLMATRIX[16];


class MsgStream  
{
	//@access Private Members
public:
		
		unsigned int	m_OutCallTot;
		char*			m_ModuleName;
		char*			m_Buffer;
		double			m_ThreadId;
		char			m_tmp[256];
		char			m_drv[_MAX_DRIVE];
		char			m_dir[_MAX_DIR];
		char			m_fname[_MAX_FNAME];
		char			m_ext[_MAX_EXT];
				
		//@cmember  Output call class based on MsgStream
		MsgStream*	m_OutClass;

		//@cmember	Buffer holding the string.
		char*		m_StripBuf;

		//@cmember	Flag indicating whether messages will be written to file.
		int			m_LogFlag;

		//@cmember	Indicates that this implimentation is threaded.
//		int			m_Threaded;	
		//@cmember  Inidcates that mout has been initialized properly.
		
		//@cmember  Safe null return for <string>
		char		m_Safe[1];
		//CfgAdaptor*	m_Config;

		
	//@access Public Members	
	public:
		//@cmember	Override all commands to the contrary and 
		//			write this message to the log file.
		int			m_LogThisMessage;
		//@cmember	The XML configuration file name.
		char* 		m_ConfigFile;
		//@cmember	Holds a unique id for this module.
		char*		m_SysidBuf;
		//@cmember	The level of messages that will be displayed - should be 
		//			log level.
		int			m_DebugLevel;
		//@cmember	Current log level as indicated by logl[X] or 0 for default.
		int 		m_CurrentLevel;

		//@cmember	This stores the message for output.
		std::ostrstream*	stringStream;

		//@cmember	Vanilla Constructor
					MsgStream();

		//@cmember	Vanilla Destructor
		virtual		~MsgStream();

		//@cmember	Sets the output class.
		void		SetOutClass(MsgStream* OutClass)
					{
						m_OutClass = OutClass;
					}
				
		
		bool		m_NoWaitSuspend;
		//char const* gl_error_string(GLenum const err);
		
		void		SuspendNoWaitCall(){m_NoWaitSuspend = true;};
		void		ResumeNoWaitCall(){m_NoWaitSuspend = false;};
		bool		m_OutSuspend;
		void		SuspendOutCall(){m_OutSuspend = true;};
		void		ResumeOutCall(){m_OutSuspend = false;};
		bool		m_LogSuspend;
		void		SuspendLogging(){m_LogSuspend = true;};
		void		ResumeResumeLogging(){m_LogSuspend = false;};
		int			UnSetNoWaitCall();
		
		//@cmember	Set the thread flag.
		void		SetThreadFlag()
					{
//						m_Threaded=1;
					};

		//@cmember	Ths working init - must always be called.
		void 		Init(const char* FileName, const char* ModuleName);

		//@cmember	Set the config file outside init.
		void 		SetConfig(char* Config)
					{
						strcpy(m_ConfigFile,Config);
					};

		//@cmember	Reset the buffer pointer and grab a char*.
		char*		GetBuffer()
					{
						stringStream->seekp(0);
						return m_Buffer;
					};

		//@cmember	Manually set the debug level.
		void		SetDebugLevel(int level)
					{
						m_DebugLevel = level;
					};

		//@cmember	Add an item to the queue.
		//@cmember	The number of currently items in the queue.
		static std::ofstream		*m_out;
		static int			m_Item;
		static int   		m_QueueSize;
		static void			AddItemToQueue(const char *Buffer, size_t len);
		static char* 		m_Queue[MAX_QUEUE];
		static std::string		m_LogFileName;
		static bool			m_KillFlag;
		static std::ofstream		m_OutFile;
		//static Semaphore* 	m_WQS;
		static void			WriteQueue(char** Queue, size_t Items);
		static int			m_Init;
		static void		SetKillFlag()
					{
						m_KillFlag=true;
					};

		char* strip(char* Message);	
		//@cmember		Output, override in OS specific classes.
		virtual	void	Output(char *Message);
	
		//@cmember		overridden from XMLReader
		virtual void	CallStartTag(std::string& Tag);

		//@cmember		overridden from XMLReader
		virtual void	CallEndTag(std::string& Tag);

		//@cmember		overridden from XMLReader
		virtual void	CallLiteral(std::string& Literal);

		//@cmember	MsgStream object only operator.
		MsgStream& operator<< (MsgStream& (*f)(MsgStream&))
		{ 
			return (*f)(*this) ; 
		}

		MsgStream& operator<< (MsgStream&) 
		{ 
			return (*this) ; 
		}

					
		//@cmember unsigned int operator.
		MsgStream& operator<< (unsigned int Value)
		{
			if(stringStream == NULL)
				return *this;
		   *stringStream << Value;
			return *this;
		};
		
		//@cmember int operator.
		MsgStream& operator<< (int Value)
		{
			if(stringStream == NULL)
				return *this;
		   *stringStream << Value;
			return *this;
		};

		//@cmember unsigned char operator.
		MsgStream& operator<<(unsigned char Value)
		{
			if(stringStream == NULL)
				return *this;
		   *stringStream << Value;
			return *this;
		};

		//@cmember char operator.
		MsgStream& operator<<(char Value)
		{
			if(stringStream == NULL)
				return *this;
		   *stringStream << Value;
			return *this;
		};

		MsgStream& operator<<(double Value)
		{
			if(stringStream == NULL)
				return *this;
		   *stringStream << Value;
			return *this;
		};



		/*MsgStream& operator<<(time_t Value)
		{
			if(stringStream == NULL)
				return *this;
		   *stringStream << Value;
			return *this;
		};*/
		
		//@cmember float operator.
		MsgStream& operator<<(float Value)
		{
			if(stringStream == NULL)
				return *this;
		   *stringStream << Value;
			return *this;
		};

		//@cmember char* operator.
		MsgStream& operator<<(char* Value)
		{
			
			if(Value == NULL)
				return *this;
			if(stringStream == NULL)
				return *this;
			if(strlen(Value)==0)
				return *this;
		   *stringStream << Value;
			return *this;
		};

		//@cmember const char* operator.
		MsgStream& operator<<(const char* Value)
		{
			if(stringStream == NULL)
				return *this;
			if(Value == NULL)
				return *this;
			if(strlen(Value)==0)
				return *this;
		   *stringStream << Value;
			return *this;
		};

		//@cmember string object
		MsgStream& operator<<(std::string& Value)
		{
			if(stringStream == NULL)
				return *this;
			*stringStream << Value.data();
			return *this;
		};

		//@cmember long operator.
		MsgStream& operator<<(long Value)
		{
			if(stringStream == NULL)
				return *this;
			*stringStream << Value;
			return *this;
		};
		MsgStream& operator<<(uint64_t Value)
		{
			if (stringStream == NULL)
				return *this;
			*stringStream << Value;
			return *this;
		};

	MsgStream& CpyBf(char* OutString, int Size);
	MsgStream& mod(const char* ModuleName);
	MsgStream& rpt(const int CallId);
	MsgStream& mod(const char* ModuleName, const int LineNumber);
	//MsgStream& s(char* Message);
	const char* SysID(const char* ApplicationName);

};
extern MsgStream mout;

MsgStream& ende(MsgStream& e);
MsgStream& log(MsgStream& e);
MsgStream& debug(MsgStream& e);
MsgStream& logl1(MsgStream& e);
MsgStream& logl2(MsgStream& e);
MsgStream& logl3(MsgStream& e);
MsgStream& logl4(MsgStream& e);
MsgStream& logl5(MsgStream& e);
MsgStream& logl6(MsgStream& e);
MsgStream& logl7(MsgStream& e);
MsgStream& logl8(MsgStream& e);
MsgStream& logl9(MsgStream& e);
MsgStream& logl10(MsgStream& e);

#ifdef _BGWIN
MsgStream& WMT(MsgStream& e);
#endif

#ifdef _USES_OPENGL
MsgStream& OGLE(MsgStream& e);
MsgStream& OGLE(MsgStream& e, int Error);
#endif

#endif //_MSTREAM_HPP




