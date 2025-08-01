

#include "mout2_0/mout.hpp"
extern MsgStream			mout;    

#include "TCPCObj.hpp"
#include <vector>
#include "libconfig.h"
#include "ConfigObj.hpp"
MsgStream			mout;    
int __cdecl main(int argc, char **argv) 
{
    
    ConfigObj*			MpsApp;   
    TCPCObj* tcpc = new TCPCObj;
    std::string cmd;
    mout.Init("particle.log", "Particle");
    MpsApp = new ConfigObj;
	MpsApp->Create("mps.cfg");
    
    std::cout << "Press enter to connect";
    std::cin >> cmd;
	tcpc->SetServerPort(MpsApp->GetString("capture_cmd_port",true));
	tcpc->SetServerIP(MpsApp->GetString("capture_cmd_ip",true));
	tcpc->SetBufSize(MpsApp->GetInt("buffer_size",true));
	tcpc->Create();

    while(1) 
    {
        std::cout << "Enter Command:";
        std::cin >> cmd;
        if(cmd.compare("quit") == 0)
        {
            tcpc->WritePort(cmd);     
            tcpc->Close();
            break;
        }
       tcpc->WritePort(cmd);     
       tcpc->ReadPort();
    }
  

    return 0;
}