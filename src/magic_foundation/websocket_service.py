import asyncio
import logging

from websockets import serve as WSServer
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from magic_foundation import Service, ServiceStatus, ServiceContext


__all__ = ('WebSocketService')

log = logging.getLogger(__name__)


class WebSocketService(Service):

    def __init__(self, host="localhost", port=8080):
        self.name = f"WebSocketService:{host}:{port}"
        self.host = host
        self.port = port
        self.wss = None

    async def initialize(self, ctx:ServiceContext):
        log.info(f"[{self.name}] initialize")

    async def run(self, ctx:ServiceContext):
        log.info(f"[{self.name}] run")

        async def handler(websocket, path):
            log.debug(f"[{self.name}] handler path:{path} ws_id:{id(websocket)}")
        
            async def inbound_handler():
                running = True
                while running:
                    try:
                        log.debug(f"[{self.name}] handler inbound_handler path:{path} ws_id:{id(websocket)}")
                        msg = await websocket.recv()
                        await ctx.publish(queue_name=f"ws://inbound{path}", data=msg)                    
                    except ConnectionClosedOK:
                        log.debug(f"[{self.name}] handler inbound_handler path:{path} ws_id:{id(websocket)} ConnectionClosedOK")
                        running = False
                    except ConnectionClosedError:
                        log.debug(f"[{self.name}] handler inbound_handler path:{path} ws_id:{id(websocket)} ConnectionClosedError")
                        running = False
                    except Exception as e:
                        log.error(f"[{self.name}] handler inbound_handler path:{path} ws_id:{id(websocket)} ERROR type:{type(e)} error:{e}")
                        running = False

            async def outbound_handler(data):
                try:
                    await websocket.send(data)
                except ConnectionClosedOK:
                    log.debug(f"[{self.name}] handler outbound_handler path:{path} ws_id:{id(websocket)} ConnectionClosedOK")                
                except ConnectionClosedError:
                    log.debug(f"[{self.name}] handler outbound_handler path:{path} ws_id:{id(websocket)} ConnectionClosedError")
                except Exception as e:
                    log.error(f"[{self.name}] handler outbound_handler path:{path} ws_id:{id(websocket)} ERROR type:{type(e)} error:{e}")

            try:
                inbound_task:asyncio.Task = asyncio.ensure_future(inbound_handler())

                #print(f"ws://outbound{path}/{id(websocket)}")

                out_queue_name = f"ws://outbound{path}"

                await ctx.subscribe(queue_name=out_queue_name, handler=outbound_handler)

                done, pending = await asyncio.wait(
                    [inbound_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for task in pending:
                    task.cancel()

                log.debug(f"[{self.name}] handler penging handlers has been cancelled")

                await ctx.unsubscribe(queue_name=out_queue_name, handler=outbound_handler)

                log.debug(f"[{self.name}] handler the outbound_handler has been unsubscribed from queue_name={out_queue_name}")
                
            except Exception as e:
                log.error(f"[{self.name}] handler path:{path} ws_id:{id(websocket)} ERROR! type:{type(e)} error:{e}")
          
        self.wss = await WSServer(ws_handler=handler, host=self.host, port=self.port)

        log.info(f"[{self.name}] run wss is serving:{self.wss.is_serving()} on port:{self.port}")

    async def terminate(self, ctx:ServiceContext):
        log.info(f"[{self.name}] terminate")

        if self.wss.is_serving():
            log.debug(f"[{self.name}] terminate wss is serving:{self.wss.is_serving()}")
            self.wss.close()
            await self.wss.wait_closed()
            log.debug(f"[{self.name}] terminate wss is serving:{self.wss.is_serving()}")

    