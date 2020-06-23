import aiofiles
import asyncio
import datetime
import json
import logging


from magic_foundation import Service, ServiceStatus, ServiceContext


__all__ = ('LoggingService')

log = logging.getLogger(__name__)


class LoggingService(Service):

    def __init__(self, file_path:str, flush_interval_sec=5.0):
        self.name = f"LoggingService:{file_path}"
        self.file_path = file_path
        self.flush_interval_sec = flush_interval_sec
        self.queue_name = f"log://{self.file_path}"

    async def initialize(self, ctx:ServiceContext):
        log.info(f"[{self.name}] initialize")

        self.writer = await aiofiles.open(self.file_path, mode='a', encoding="utf-8", newline='\n')

    async def run(self, ctx:ServiceContext):
        log.info(f"[{self.name}] run")

        async def handler(data:map):
            await self.writer.write(f"{json.dumps(data)}\n")

        self.handler = handler

        await ctx.subscribe(queue_name=self.queue_name, handler=self.handler)
        
        while self.status is ServiceStatus.running:
            log.debug(f"[{self.name}] run flush the {self.file_path} file")
            await self.writer.flush()
            await asyncio.sleep(self.flush_interval_sec)        

    async def terminate(self, ctx:ServiceContext):
        log.info(f"[{self.name}] terminate")

        if self.writer is not None:
            await self.writer.flush()

        await ctx.unsubscribe(queue_name=self.queue_name, handler=self.handler)