import abc
import asyncio
import concurrent
import logging
import sys
import traceback                     
import threading


from enum import Enum


__version__ = '0.1.3'
__all__ = ('Main', 'Service', 'ServiceStatus', 'ServiceContext')

log = logging.getLogger(__name__)


class Queue:
    def __init__(self, thread_id:int, loop:asyncio.AbstractEventLoop, label:str=""):
        self.thread_id = thread_id
        self._loop = loop
        self._queue = asyncio.Queue()
        self.label = label

    def empty(self):
        return self._queue.empty()

    def qsize(self):
        return self._queue.qsize()

    def task_done(self):
        self._queue.task_done()

    async def put(self, item, thread_id:int=None):
        if thread_id is None:
          thread_id = threading.current_thread().ident
        
        # required for unknow reason
        await asyncio.sleep(0)

        if self.thread_id == thread_id:
            """
            same thread
            """
            self._loop.call_soon(self._queue.put_nowait, item)
        else:
            """
            differents threads
            """
            log.debug(f"[Queue][{self.label}] put 0 [thread id:{threading.current_thread().ident}]")
            async def coro():
              log.debug(f"[Queue][{self.label}] put 1 [thread id:{threading.current_thread().ident}]")
              self._queue.put_nowait(item)
              log.debug(f"[Queue][{self.label}] put 2 [thread id:{threading.current_thread().ident}]")

            asyncio.run_coroutine_threadsafe(coro(), self._loop).result()

    async def get(self):
        return await self._queue.get()


class ServiceStatus(Enum):
    uninitialized = -1
    initialized = 0
    running = 1
    terminated = 2
    error = 3


class ServiceContext():

    def __init__(self, thread_id:int, loop:asyncio.AbstractEventLoop, container):
        self.thread_id = thread_id
        self.loop = loop
        self.container = container

    async def publish(self, queue_name:str, data:map):    
        await self.container.publish(queue_name=queue_name, data=data)
        
    async def subscribe(self, queue_name:str, handler):
        await self.container.subscribe(queue_name=queue_name, handler=handler)

    async def unsubscribe(self, queue_name:str, handler):
        await self.container.unsubscribe(queue_name=queue_name, handler=handler)

    async def dump_queue_tree(self):
        await self.container.dump_queue_tree()


class Service(object):
    __metaclass__ = abc.ABCMeta

    name = "Service"
    status = ServiceStatus.uninitialized

    async def start(self, ctx:ServiceContext):
        log.debug(f"[{self.name}] start [thread id:{ctx.thread_id}] status:{self.status}")
        try:
            if self.status is ServiceStatus.uninitialized:
                self.status = ServiceStatus.initialized
                
                await self.initialize(ctx=ctx)

            if self.status is ServiceStatus.initialized:
                self.status = ServiceStatus.running
                
                await self.run(ctx=ctx)

        except Exception as e:
            self.status = ServiceStatus.error
            log.error(f"[{self.name}] start {self.name} status:{self.status} exception:{e}")
            if True:
              traceback.print_exc(file=sys.stdout)

    async def stop(self, ctx:ServiceContext):
        log.debug(f"[{self.name}] stop [thread id:{ctx.thread_id}] status:{self.status}")
        try:
            if self.status is ServiceStatus.running:
                self.status = ServiceStatus.terminated

                await self.terminate(ctx=ctx)
        except Exception as e:
            self.status = ServiceStatus.error
            log.error(f"[{self.name}] stop [thread id:{ctx.thread_id}] status:{self.status} exception:{e}")

    @abc.abstractmethod
    async def initialize(self, ctx:ServiceContext):
        """Method documentation"""

    @abc.abstractmethod
    async def run(self, ctx:ServiceContext):
        """Method documentation"""

    @abc.abstractmethod
    async def terminate(self, ctx:ServiceContext):
        """Method documentation"""


class Container(threading.Thread):

    class QRef:
        def __init__(self, queue_ref):
            self.queue = queue_ref
            self.handlers = []

    class Event:
        def __init__(self, queue_name:str, data):
            self.queue_name = queue_name
            self.data = data 


    name = "Container"

    
    def __init__(self, k, services):
        self.k = k
        self.services = services
        self.thread_id = None
        self.loop = None
        self.start_task = None

        self.q_inbound = None
        threading.Thread.__init__(self)        

    def run(self):
        self.thread_id = self.ident
                
        log.debug(f"[{self.name}][{self.k}] starting [thread id:{self.thread_id}]")
        
        async def inbound_handler():
            log.debug(f"[{self.name}][{self.k}] inbound_handler 1 [thread id:{self.thread_id}]")
            await asyncio.sleep(0)
            running = True
            while running:
                try:
                    log.debug(f"[{self.name}][{self.k}] inbound_handler 2 [thread id:{self.thread_id}]")
                    event:Container.Event = await self.q_inbound.get()
                    self.q_inbound.task_done()

                    queue_name = event.queue_name
                    if queue_name in self.queues:
                      if self.thread_id in self.queues[queue_name]:
                        for handler in self.queues[queue_name][self.thread_id].handlers:
                          asyncio.ensure_future(handler(data=event.data), loop=self.loop)

                    log.debug(f"[{self.name}][{self.k}] inbound_handler 3 [thread id:{self.thread_id}] event:{event}")
                except concurrent.futures.CancelledError as e:
                    log.debug(f"[{self.name}][{self.k}] inbound_handler 4 [thread id:{self.thread_id}] has been cancelled")
                    running = False
                except Exception as e:
                    log.error(f"[{self.name}][{self.k}] inbound_handler 5 [thread id:{self.thread_id}] Exception type:{type(e)} error:{e}")
                    running = False
                    if True:
                      traceback.print_exc(file=sys.stdout)
        
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            self.q_inbound = Queue(thread_id=self.thread_id, loop=self.loop, label=f"{self.thread_id}")
            self.ctx = ServiceContext(thread_id=self.thread_id, loop=self.loop, container=self)   

            self.loop.run_until_complete(self._services_start())

            self.inbound_task:asyncio.Task = asyncio.ensure_future(inbound_handler(), loop=self.loop)

            self.loop.run_forever()
        except Exception as e:
            log.error(f"[{self.k}][Container] starting exception:{e}")
        finally:
            if self.inbound_task is not None and not self.inbound_task.cancelled():
              self.inbound_task.cancel()   
            
            log.debug(f"[{self.k}][Container] ------ terminate services ------")
            self.loop.run_until_complete(self._services_stop())
            self.loop.close()

    async def terminate(self):
        log.debug(f"[{self.k}][Container] terminate")
        try:
            if self.inbound_task is not None and not self.inbound_task.cancelled():
              self.inbound_task.cancel()            
            
            if self.loop is not None and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)
                await asyncio.sleep(0.5)
        except Exception as e:
            log.error(f"[{self.k}][Container] terminate exception:{e}")
        finally:
            log.debug(f"[{self.k}][Container] terminate finally loop is running:{self.loop.is_running()}")

    async def _services_start(self):
        self.start_task = asyncio.gather(
            *map(lambda instance: instance.start(ctx=self.ctx), self.services),
            return_exceptions=True
        )
        return self.start_task

    async def _services_stop(self):
        await asyncio.gather(
            *map(lambda instance: instance.stop(ctx=self.ctx), reversed(self.services)),
            return_exceptions=True
        )

    # static
    queues = {}

    async def publish(self, queue_name: str, data: map):    
        log.debug(f"[{self.name}] publish name:{queue_name} data:{data}")

        if queue_name in self.queues:
            for thread_id in self.queues[queue_name]:
                await self.queues[queue_name][thread_id].queue.put(Container.Event(queue_name, data))
                 
    async def subscribe(self, queue_name: str, handler) -> map:
        log.debug(f"[{self.name}] subscribe name:{queue_name}")
        if queue_name not in self.queues:
            self.queues[queue_name] = {}

        if self.thread_id not in self.queues[queue_name]:
            self.queues[queue_name][self.thread_id] = Container.QRef(queue_ref=self.q_inbound)

        self.queues[queue_name][self.thread_id].handlers.append(handler)

    async def unsubscribe(self, queue_name: str, handler) -> map:
        log.debug(f"[{self.name}] unsubscribe name:{queue_name}")

        if queue_name in self.queues:
            
            qref_to_remove = []

            for thread_id in self.queues[queue_name]:
                q_ref = self.queues[queue_name][thread_id]
                
                if handler in q_ref.handlers: 
                    q_ref.handlers.remove(handler)

                if len(q_ref.handlers) == 0:
                    qref_to_remove.append(thread_id)

            for thread_id in qref_to_remove:
                del self.queues[queue_name][thread_id]

    async def dump_queue_tree(self):
        log.info(f"|========================================================")
        for queue_name in self.queues:
            log.info(f"|-- {queue_name}")
            for thread_id in self.queues[queue_name]:
                log.info(f"|  |-- {thread_id}")
                q_ref = self.queues[queue_name][thread_id]
                for handler in q_ref.handlers:
                    log.info(f"|     |-- {handler}")
        log.info(f"|========================================================")


class Main:

    __instance = None

    @staticmethod
    def instance():
      if Main.__instance is None:
          Main()
      return Main.__instance

    def __init__(self):
        if Main.__instance is not None:
            raise Exception("Main class is a singleton!")
        else:
            Main.__instance = self

    service_pools = None        
    
    loop = None

    def run(self):
        self.loop = asyncio.get_event_loop()
        try:
            threads = [Container(k, self.service_pools[k]) for k in self.service_pools]
            [t.start() for t in threads]
            [t.join() for t in threads]
        except KeyboardInterrupt:
            log.debug(f"[main] KeyboardInterrupt")
        except RuntimeError:
            log.error(f"[main] RuntimeError")
        finally:
            [self.loop.run_until_complete(t.terminate()) for t in threads]
            self.loop.close()
