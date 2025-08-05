import asyncio

async def run_command(cmd):
    """
    Executes a shell command asynchronously and captures its output.
    """
    proc = await asyncio.create_subprocess_shell(
        cmd,cwd="../vulkan/run/ParticleOnly"        
    )
  
    print("done")
async def main():
    await run_command("particleR.exe -application.doAuto true -application.doAutoSingleFile true -application.auto_sleep 30 -application.perfTest testdirPQB")
    #await run_command("echo Hello, async subprocess!")

if __name__ == "__main__":
    asyncio.run(main())