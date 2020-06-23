import asyncio
import json
import logging

from magic_foundation import Container, Service, ServiceStatus, ServiceContext, Main
from magic_foundation.logging_service import LoggingService

log = logging.getLogger("examples")

logging.basicConfig(level=logging.INFO)
logging.getLogger("magic_foundation").setLevel(logging.INFO)
logging.getLogger("magic_foundation.logging_service").setLevel(logging.DEBUG)


file_path = "logging_out.log"

class TestService(Service):

  def __init__(self, name:str):
      self.name = name      

  async def initialize(self, ctx:ServiceContext):
    log.info(f"[{self.name}] initialize")
    
  async def run(self, ctx:ServiceContext):
    log.info(f"[{self.name}] run")

    index = 0;

    while self.status == ServiceStatus.running:
      index += 1
      data = {"cmd": "log", "index": index}
      
      log.info(f"[{self.name}] push to log file f{file_path} data:{json.dumps(data)}")
      
      await ctx.publish(queue_name=f"log://{file_path}", data=data)
      
      await asyncio.sleep(1.0)

  async def terminate(self, ctx:ServiceContext):
    log.info(f"[{self.name}] terminate")



if __name__ == "__main__":
    main = Main.instance()

    main.service_pools = {
      "backgound" : [
        LoggingService(file_path=file_path, flush_interval_sec=4.0)
      ],
      "main" : [
        TestService(name="Producer")
      ]
    }

    main.run()