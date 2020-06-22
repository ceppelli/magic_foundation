import asyncio
import json
import logging

from magic_foundation import Container, Service, ServiceStatus, ServiceContext, Main
from magic_foundation.websocket_service import WebSocketService

log = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)
logging.getLogger("magic_foundation").setLevel(logging.INFO)
logging.getLogger("magic_foundation.websocket_service").setLevel(logging.DEBUG)


class TestService(Service):

  def __init__(self, name:str):
      self.name = name

  async def initialize(self, ctx:ServiceContext):
    log.info(f"[{self.name}] initialize")
    
  async def run(self, ctx:ServiceContext):
    log.info(f"[{self.name}] run")

    async def handler(data):
      log.info(f"[{self.name}] handler inbound data:{data}")
      req = json.loads(data)
      res = json.dumps({"status": "OK", "timestamp": req["timestamp"]})
      await ctx.publish(queue_name="ws://outbound/client", data=res)

    await ctx.subscribe(queue_name="ws://inbound/client", handler=handler)

    while self.status == ServiceStatus.running:
      await ctx.dump_queue_tree()
      log.info(f"[{self.name}] run sleeping")
      await asyncio.sleep(5.0)

  async def terminate(self, ctx:ServiceContext):
    log.info(f"[{self.name}] terminate")



if __name__ == "__main__":
    main = Main.instance()

    main.service_pools = {
      "main" : [
        WebSocketService(host="localhost", port=8765),
        TestService(name="Consumer"), 
      ]
    }

    main.run()